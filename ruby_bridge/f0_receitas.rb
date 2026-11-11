# frozen_string_literal: true

# F0 do plano de modelagem (docs/PLANO-MODELAGEM.md): roda receitas de modelagem
# no SketchUp real e grava, para cada uma, contagem de vertices/arestas/faces,
# areas e lacos, mais o .skp gerado. Serve de "verdade" para testar o nucleo de
# topologia do SketchBuild.
#
# Como rodar (SketchUp aberto com um modelo NOVO e VAZIO):
#   Window > Ruby Console, depois:
#   load 'C:/caminho/para/sketchup_companion/ruby_bridge/f0_receitas.rb'
#
# Saida: pasta SKETCHBUILD_F0_OUT (padrao: <home>/sketchup_f0_saida) com
# f0_resultados.json e um .skp por receita.
#
# Seguranca: nao abre porta de rede nem executa codigo recebido de fora. Aborta
# se o modelo ativo tiver caminho ou alteracoes, para nunca descartar trabalho.

require 'json'
require 'fileutils'

module SketchbuildF0
  OUT_DIR = ENV['SKETCHBUILD_F0_OUT'] || File.join(Dir.home, 'sketchup_f0_saida')

  module_function

  # -- medicao ---------------------------------------------------------------

  def snap(model)
    ents = model.entities
    edges = ents.grep(Sketchup::Edge)
    faces = ents.grep(Sketchup::Face)
    verts = edges.flat_map(&:vertices).uniq
    bb = Geom::BoundingBox.new
    verts.each { |v| bb.add(v.position) }
    {
      vertices: verts.size,
      edges: edges.size,
      faces: faces.size,
      face_areas_in2: faces.map { |f| f.area.round(4) }.sort,
      face_loops: faces.map { |f| f.loops.size }.sort,
      face_vertex_counts: faces.map { |f| f.vertices.size }.sort,
      face_normals: faces.map { |f| f.normal.to_a.map { |c| c.round(3) } }.sort,
      edges_by_face_count: edges.map { |e| e.faces.size }.group_by { |n| n }.transform_values(&:size),
      soft_edges: edges.count(&:soft?),
      bounds_in: verts.empty? ? nil : { min: bb.min.to_a.map { |c| c.round(4) }, max: bb.max.to_a.map { |c| c.round(4) } }
    }
  end

  def square(ents, x0, y0, x1, y1, z = 0)
    ents.add_face([[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]])
  end

  def cube(ents, size = 100, height = 50)
    f = square(ents, 0, 0, size, size)
    f.reverse! if f.normal.z < 0
    f.pushpull(height)
    f
  end

  def top_face(model)
    model.entities.grep(Sketchup::Face).max_by { |f| f.bounds.center.z + f.normal.z }
  end

  # -- receitas: cada uma devolve { "etapa" => snap } --------------------------

  RECEITAS = {
    'r01_linha_solta' => lambda do |m|
      m.entities.add_line([0, 0, 0], [100, 0, 0])
      { 'depois' => snap(m) }
    end,

    'r02_laco_fechado_de_linhas' => lambda do |m|
      e = m.entities
      e.add_line([0, 0, 0], [100, 0, 0])
      e.add_line([100, 0, 0], [100, 100, 0])
      e.add_line([100, 100, 0], [0, 100, 0])
      e.add_line([0, 100, 0], [0, 0, 0])
      antes = snap(m)
      e.grep(Sketchup::Edge).first.find_faces
      { 'apos_4_linhas' => antes, 'apos_find_faces' => snap(m) }
    end,

    'r03_retangulo_add_face' => lambda do |m|
      square(m.entities, 0, 0, 100, 100)
      { 'depois' => snap(m) }
    end,

    'r04_pushpull_retangulo' => lambda do |m|
      cube(m.entities)
      { 'depois' => snap(m) }
    end,

    'r05_pushpull_volta_ao_plano' => lambda do |m|
      cube(m.entities)
      cheio = snap(m)
      top_face(m).pushpull(-50)
      { 'cubo' => cheio, 'apos_pushpull_negativo_total' => snap(m) }
    end,

    'r06_linha_divide_face' => lambda do |m|
      e = m.entities
      square(e, 0, 0, 100, 100)
      e.add_line([50, 0, 0], [50, 100, 0])
      { 'depois' => snap(m) }
    end,

    'r07_linha_em_T' => lambda do |m|
      e = m.entities
      e.add_line([0, 0, 0], [100, 0, 0])
      e.add_line([50, 50, 0], [50, 0, 0])
      { 'depois' => snap(m) }
    end,

    'r08_linhas_em_X' => lambda do |m|
      e = m.entities
      e.add_line([0, 0, 0], [100, 100, 0])
      e.add_line([0, 100, 0], [100, 0, 0])
      { 'depois' => snap(m) }
    end,

    'r09_circulo' => lambda do |m|
      e = m.entities
      edges = e.add_circle([0, 0, 0], [0, 0, 1], 50, 24)
      antes = snap(m)
      e.add_face(edges)
      { 'so_arestas' => antes, 'com_face' => snap(m) }
    end,

    'r10_face_dentro_de_face' => lambda do |m|
      e = m.entities
      square(e, 0, 0, 200, 200)
      square(e, 50, 50, 150, 150)
      { 'depois' => snap(m) }
    end,

    'r11_furo_vazado_pushpull' => lambda do |m|
      e = m.entities
      cube(e)
      e.add_face([[30, 30, 50], [70, 30, 50], [70, 70, 50], [30, 70, 50]])
      com_marca = snap(m)
      miolo = e.grep(Sketchup::Face).find { |f| f.normal.z > 0.99 && f.loops.size == 1 && f.area < 2000 }
      miolo.pushpull(-50)
      { 'cubo_com_face_no_topo' => com_marca, 'apos_pushpull_vazado' => snap(m) }
    end,

    'r12_apagar_aresta_compartilhada' => lambda do |m|
      e = m.entities
      square(e, 0, 0, 100, 100)
      e.add_line([50, 0, 0], [50, 100, 0])
      dividido = snap(m)
      meio = e.grep(Sketchup::Edge).find { |x| x.start.position.x.round(3) == 50 && x.end.position.x.round(3) == 50 }
      meio.erase!
      { 'dividido' => dividido, 'apos_apagar_aresta' => snap(m) }
    end,

    'r13_arco_fatia' => lambda do |m|
      e = m.entities
      arco = e.add_arc([0, 0, 0], [1, 0, 0], [0, 0, 1], 50, 0, 90.degrees, 12)
      e.add_line([0, 0, 0], arco.first.start.position)
      e.add_line([0, 0, 0], arco.last.end.position)
      antes = snap(m)
      e.grep(Sketchup::Edge).first.find_faces
      { 'arco_e_raios' => antes, 'apos_find_faces' => snap(m) }
    end,

    'r14_follow_me' => lambda do |m|
      e = m.entities
      caminho = e.add_edges([0, 0, 0], [0, 0, 100], [100, 0, 100])
      perfil = e.add_face([[-5, -5, 0], [5, -5, 0], [5, 5, 0], [-5, 5, 0]])
      perfil.followme(caminho)
      { 'depois' => snap(m) }
    end
  }.freeze

  # -- execucao --------------------------------------------------------------

  def run
    model = Sketchup.active_model
    if !model.path.to_s.empty? || model.modified?
      UI.messagebox('F0 abortada: abra um modelo NOVO e VAZIO (sem caminho e sem alteracoes) e rode de novo.')
      return false
    end

    FileUtils.mkdir_p(OUT_DIR)
    resultados = { sketchup: Sketchup.version, ruby: RUBY_VERSION, unidade_interna: 'polegadas', receitas: {} }

    RECEITAS.each do |nome, receita|
      Sketchup.file_new
      m = Sketchup.active_model
      begin
        resultados[:receitas][nome] = { ok: true, etapas: receita.call(m) }
        m.save(File.join(OUT_DIR, "#{nome}.skp"))
      rescue StandardError => e
        resultados[:receitas][nome] = { ok: false, erro: "#{e.class}: #{e.message}" }
      end
      puts "[F0] #{nome}: #{resultados[:receitas][nome][:ok] ? 'ok' : resultados[:receitas][nome][:erro]}"
    end

    File.write(File.join(OUT_DIR, 'f0_resultados.json'), JSON.pretty_generate(resultados))
    Sketchup.file_new
    puts "[F0] pronto: #{OUT_DIR}"
    true
  end
end

SketchbuildF0.run
