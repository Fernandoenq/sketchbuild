# frozen_string_literal: true
# Como rodar (SketchUp aberto, Window > Ruby Console): load 'C:/caminho/para/ruby_bridge/gerar_anotacoes_reais.rb'
# Precisa de tex.png na pasta de saída. Fecha o SketchUp ao terminar (remova a última linha para manter aberto).
# Gera, no SketchUp real, modelos com texto, cota, textura posicionada e instância girada (oráculo do REA).
require 'fileutils'
OUT = File.join(Dir.home, 'sketchup_f0_saida', 'reais_anotacoes')
LOG = File.join(OUT, 'log.txt')
def log(m); File.open(LOG, 'a') { |f| f.puts(m) }; end
def novo
  Sketchup.file_new
  Sketchup.active_model
end
def salvar(m, nome)
  m.save(File.join(OUT, nome))
  log("salvo #{nome}")
end
begin
  m = novo
  salvar(m, 'base.skp')
  m = novo
  m.entities.add_text('Nota', [10, 20, 30])
  salvar(m, 'texto_com_ponto.skp')
  m = novo
  m.entities.add_text('Nota', [10, 20, 30], [0, 0, 40])
  salvar(m, 'texto_com_seta.skp')
  m = novo
  m.entities.add_dimension_linear([0, 0, 0], [100, 0, 0], [0, 20, 0])
  salvar(m, 'cota_linear.skp')
  m = novo
  f = m.entities.add_face([0, 0, 0], [100, 0, 0], [100, 100, 0], [0, 100, 0])
  salvar(m, 'face_sem_textura.skp')
  png = File.join(OUT, 'tex.png')
  if File.exist?(png)
    m = novo
    mat = m.materials.add('Tex')
    mat.texture = png
    f = m.entities.add_face([0, 0, 0], [100, 0, 0], [100, 100, 0], [0, 100, 0])
    f.material = mat
    salvar(m, 'face_textura_padrao.skp')
    m = novo
    mat = m.materials.add('Tex')
    mat.texture = png
    f = m.entities.add_face([0, 0, 0], [100, 0, 0], [100, 100, 0], [0, 100, 0])
    f.position_material(mat, [[0, 0, 0], [0, 0], [50, 0, 0], [1, 0]], true)
    salvar(m, 'face_textura_posicionada.skp')
  end
  # instâncias para a regra da caixa limite
  [[0, 'inst_0'], [90, 'inst_90'], [33, 'inst_33']].each do |ang, nome|
    m = novo
    d = m.definitions.add('Peca')
    d.entities.add_face([0, 0, 0], [60, 0, 0], [60, 20, 0], [0, 20, 5])
    d.entities.add_face([0, 0, 40], [10, 0, 40], [10, 10, 70], [0, 10, 40])
    t = Geom::Transformation.translation([100, 200, 0]) * Geom::Transformation.rotation([0, 0, 0], [0, 0, 1], ang.degrees)
    m.entities.add_instance(d, t)
    salvar(m, "#{nome}.skp")
  end
  m = novo
  d = m.definitions.add('Peca')
  d.entities.add_face([0, 0, 0], [60, 0, 0], [60, 20, 0], [0, 20, 5])
  g = m.entities.add_group
  g.entities.add_face([0, 0, 0], [60, 0, 0], [60, 20, 0], [0, 20, 5])
  g.transform!(Geom::Transformation.rotation([0, 0, 0], [0, 0, 1], 33.degrees))
  salvar(m, 'grupo_33.skp')
  log('FIM')
rescue Exception => e
  log("ERRO #{e.class}: #{e.message}\n#{e.backtrace.first(5).join("\n")}")
end
UI.start_timer(1, false) { Sketchup.quit }
