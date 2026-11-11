# frozen_string_literal: true

# Conta entidades ocultas e visiveis de um .skp escolhido, SOMENTE LEITURA:
# nao altera, nao salva e nao apaga nada. Para cada definicao (grupo/componente e a
# raiz do modelo) conta instancias, arestas e faces, cada definicao uma unica vez
# (a mesma convencao da varredura binaria do model.dat).
#
# O ORIGINAL NUNCA E ABERTO: o script copia o .skp para uma pasta temporaria e abre a
# copia. Nenhum comando de escrita e usado (sem save, erase!, hide!).
#
# Como rodar (SketchUp aberto; qualquer modelo ativo serve, ele nao e tocado):
#   Window > Ruby Console, depois:
#   load 'C:/caminho/para/sketchup_companion/ruby_bridge/contar_ocultos.rb'
# Escolha o .skp na janela. O arquivo abre em outra janela do SketchUp (demora em
# arquivos grandes). Saida: resumo no console e JSON em <home>/sketchup_ocultos_saida.

require 'json'
require 'fileutils'

module ContarOcultos
  OUT_DIR = File.join(Dir.home, 'sketchup_ocultos_saida') unless const_defined?(:OUT_DIR)
  TMP_DIR = File.join(OUT_DIR, 'tmp') unless const_defined?(:TMP_DIR)

  module_function

  def novo_contador
    { total: 0, ocultos: 0, visiveis: 0 }
  end

  def conta(c, oculto)
    c[:total] += 1
    oculto ? c[:ocultos] += 1 : c[:visiveis] += 1
  end

  def analisa(model)
    inst = novo_contador
    edges = novo_contador
    faces = novo_contador
    combo_arestas = Hash.new(0) # hidden/soft/smooth, para decifrar os bits do byte de flags
    instancias_ocultas = []
    travadas = 0
    com_formula = []
    por_definicao = {}
    tab = {} # por definicao: arestas/faces proprias e instancias filhas

    defs = [[model, model.entities, 'Raiz do modelo']] +
           model.definitions.reject(&:image?).map { |d| [d, d.entities, d.name] }
    defs.each do |dobj, ents, nome|
      d_inst = novo_contador
      d_edges = novo_contador
      d_faces = novo_contador
      filhos = []
      ents.each do |e|
        case e
        when Sketchup::Group, Sketchup::ComponentInstance
          filhos << [e.definition, e.hidden? || !e.layer.visible?]
          conta(inst, e.hidden?)
          conta(d_inst, e.hidden?)
          travadas += 1 if e.locked?
          da = e.attribute_dictionary('dynamic_attributes')
          formula = da && da['_hidden_formula']
          com_formula << { nome: e.name.to_s, definicao: e.definition.name, dentro_de: nome, formula: formula.to_s, oculta_pelo_flag: e.hidden? } if formula
          next unless e.hidden?

          instancias_ocultas << {
            nome: e.name.to_s,
            definicao: e.definition.name,
            dentro_de: nome,
            posicao_cm: e.transformation.origin.to_a.map { |v| (v.to_f * 2.54).round(1) },
            travada: e.locked?,
            tag: e.layer.name,
            ha_visivel_de_mesma_definicao: ents.grep(Sketchup::ComponentInstance).any? { |o| !o.hidden? && o.definition == e.definition } ||
                                            ents.grep(Sketchup::Group).any? { |o| !o.hidden? && o.definition == e.definition }
          }
        when Sketchup::Edge
          conta(edges, e.hidden?)
          conta(d_edges, e.hidden?)
          combo_arestas["oculta=#{e.hidden? ? 1 : 0} suave=#{e.soft? ? 1 : 0} liso=#{e.smooth? ? 1 : 0}"] += 1
        when Sketchup::Face
          conta(faces, e.hidden?)
          conta(d_faces, e.hidden?)
        end
      end
      tab[dobj] = { e: d_edges, f: d_faces, filhos: filhos }
      next if d_inst[:ocultos].zero? && d_edges[:ocultos].zero? && d_faces[:ocultos].zero?

      por_definicao[nome] = { instancias: d_inst, arestas: d_edges, faces: d_faces }
    end

    {
      arquivo: model.path,
      efetivo: efetivo(model, tab),
      sketchup: Sketchup.version,
      definicoes: defs.size,
      tags: model.layers.map { |l| { nome: l.name, visivel: l.visible? } },
      instancias: inst,
      arestas: edges,
      faces: faces,
      instancias_travadas: travadas,
      combinacoes_de_arestas: combo_arestas,
      definicoes_com_ocultos: por_definicao,
      instancias_com_hidden_formula: com_formula,
      instancias_ocultas: instancias_ocultas
    }
  end

  # Visibilidade efetiva: o que o SketchUp mostra de fato. Uma instancia oculta (ou em tag
  # invisivel) esconde todo o conteudo da sua definicao, e cada USO conta (multiplicidade).
  def efetivo(model, tab)
    memo = {}
    soma = lambda do |d|
      memo[d] ||= begin
        t = tab[d] || { e: novo_contador, f: novo_contador, filhos: [] }
        r = { ev: t[:e][:visiveis], eh: t[:e][:ocultos], fv: t[:f][:visiveis], fh: t[:f][:ocultos] }
        t[:filhos].each do |dc, oculto|
          s = soma.call(dc)
          if oculto
            r[:eh] += s[:ev] + s[:eh]
            r[:fh] += s[:fv] + s[:fh]
          else
            r.each_key { |k| r[k] += s[k] }
          end
        end
        r
      end
    end
    r = soma.call(model)
    { arestas_visiveis: r[:ev], arestas_ocultas: r[:eh], faces_visiveis: r[:fv], faces_ocultas: r[:fh] }
  end

  def run
    caminho = UI.openpanel('Escolha o .skp para contar ocultos (somente leitura)', '', 'SketchUp|*.skp||')
    return puts('[ocultos] cancelado') unless caminho

    t0 = Time.now
    FileUtils.mkdir_p(TMP_DIR)
    copia = File.join(TMP_DIR, "copia_#{Time.now.strftime('%H%M%S')}_#{File.basename(caminho)}")
    puts "[ocultos] copiando para #{copia} (o original nao sera aberto) ..."
    FileUtils.cp(caminho, copia)
    Sketchup.open_file(copia, with_status: true)
    model = Sketchup.active_model
    unless File.expand_path(model.path.to_s) == File.expand_path(copia)
      return puts('[ocultos] o modelo ativo nao e a copia; abortado sem ler nada')
    end

    r = analisa(model)
    r[:arquivo] = caminho
    FileUtils.mkdir_p(OUT_DIR)
    saida = File.join(OUT_DIR, "#{File.basename(caminho, '.skp')}_ocultos.json")
    File.write(saida, JSON.pretty_generate(r))
    %i[instancias arestas faces].each do |k|
      c = r[k]
      puts "[ocultos] #{k}: total #{c[:total]} | ocultos #{c[:ocultos]} | visiveis #{c[:visiveis]}"
    end
    puts "[ocultos] instancias travadas: #{r[:instancias_travadas]} | tags: #{r[:tags].map { |t| "#{t[:nome]}=#{t[:visivel]}" }.join(', ')}"
    r[:combinacoes_de_arestas].each { |k, v| puts "[ocultos]   arestas #{k}: #{v}" }
    ef = r[:efetivo]
    puts "[ocultos] EFETIVO (com multiplicidade e heranca): arestas visiveis #{ef[:arestas_visiveis]} | ocultas #{ef[:arestas_ocultas]} | faces visiveis #{ef[:faces_visiveis]} | ocultas #{ef[:faces_ocultas]}"
    fo = r[:instancias_com_hidden_formula]
    puts "[ocultos] instancias com _hidden_formula: #{fo.size} (ocultas tambem pelo flag: #{fo.count { |x| x[:oculta_pelo_flag] }})"
    puts "[ocultos] #{r[:definicoes_com_ocultos].size} definicoes com ocultos; JSON: #{saida} (#{(Time.now - t0).round}s)"
  end
end

ContarOcultos.run
