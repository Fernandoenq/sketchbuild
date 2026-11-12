# frozen_string_literal: true

# B4: abre cada .skp gerado pelo SketchBuild (pasta ~/sketchup_gerados) e confere com esperado.json.
# Os arquivos GERADOS sao abertos direto (nao sao originais de ninguem). Nada e salvo nem apagado.
#
# Como rodar (SketchUp aberto):
#   Window > Ruby Console, depois:
#   load 'C:/Users/Fernando/sketchup_companion/ruby_bridge/conferir_gerados.rb'
#
# Saida: resumo no console e JSON em ~/sketchup_gerados/resultado_sketchup.json

require 'json'

module ConferirGerados
  PASTA = File.join(Dir.home, 'sketchup_gerados') unless const_defined?(:PASTA)

  module_function

  def medir(model)
    faces = edges = 0
    area = 0.0
    model.entities.each do |e|
      case e
      when Sketchup::Face then faces += 1; area += e.area
      when Sketchup::Edge then edges += 1
      end
    end
    r = { 'faces' => faces, 'edges' => edges, 'area_total' => area.round(3) }
    r['curvas'] = model.entities.grep(Sketchup::Edge).map(&:curve).compact.uniq.size
    r['grupos'] = model.entities.grep(Sketchup::Group).size
    r['componentes'] = model.entities.grep(Sketchup::ComponentInstance).size
    face = model.entities.grep(Sketchup::Face).first
    if face
      r['cor_frente'] = face.material ? face.material.color.to_a.first(3) : nil
      r['cor_verso'] = face.back_material ? face.back_material.color.to_a.first(3) : nil
    end
    r
  end

  # compara so o que o esperado.json traz (arquivos antigos nao tem curvas/grupos/cores)
  def confere?(got, esp)
    return false unless got['faces'] == esp['faces'] && got['edges'] == esp['edges']
    return false unless (got['area_total'] - esp['area_total']).abs < 0.01
    %w[curvas grupos componentes].all? { |k| !esp.key?(k) || got[k] == esp[k] } &&
      %w[cor_frente cor_verso].all? { |k| !esp.key?(k) || got[k] == esp[k] }
  end

  def run
    esperado = JSON.parse(File.read(File.join(PASTA, 'esperado.json')))
    resultado = {}
    esperado.each do |nome, esp|
      caminho = File.join(PASTA, nome)
      begin
        Sketchup.open_file(caminho, with_status: true)
        got = medir(Sketchup.active_model)
        ok = confere?(got, esp)
        resultado[nome] = { 'ok' => ok, 'esperado' => esp, 'sketchup' => got }
        puts "[gerados] #{ok ? 'OK ' : 'FALHOU'} #{nome}: SketchUp #{got.inspect} | esperado #{esp.inspect}"
      rescue StandardError => e
        resultado[nome] = { 'ok' => false, 'erro' => "#{e.class}: #{e.message}" }
        puts "[gerados] ERRO #{nome}: #{e.class}: #{e.message}"
      end
    end
    File.write(File.join(PASTA, 'resultado_sketchup.json'), JSON.pretty_generate(resultado))
    puts "[gerados] #{resultado.count { |_, v| v['ok'] }}/#{resultado.size} arquivos conferem"
  end
end

ConferirGerados.run
