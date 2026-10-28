# frozen_string_literal: true

# Sketchup Bridge -- servidor TCP local que roda DENTRO do processo do
# SketchUp (via Ruby API oficial) e expoe comandos simples em JSON
# por linha para o SketchBuild Python conversar com o SketchUp sem
# precisar chamar a C API nativa a frio via ctypes.
#
# Por que isso existe: ver REVERSE_ENGINEERING_NOTES.md secao 9.5/9.7.
# SUModelCreateFromFileWithStatus crasha nesta build (std::function
# interno nao mapeado). Em vez de insistir nisso, usamos o interpretador
# Ruby oficial (x64-ucrt-ruby320.dll) que ja roda dentro do SketchUp,
# via Sketchup.open_file / Sketchup.active_model -- API 100% oficial e
# suportada, sem risco de ABI incerta.
#
# Como carregar (modo desenvolvimento, sem instalar como extensao):
#   1. Abra o SketchUp.
#   2. Window > Ruby Console.
#   3. load 'C:/caminho/para/sketchup_companion/ruby_bridge/sketchup_bridge.rb'
#   4. O servidor comeca a escutar em 127.0.0.1:9876 (ver PORT abaixo).
#
# Para instalar como extensao de verdade (carrega sozinho no startup):
#   copiar este arquivo (ou um wrapper que faça `require`) para
#   C:\Users\<usuario>\AppData\Roaming\SketchUp\SketchUp 2026\SketchUp\Plugins
#
# Protocolo: TCP, uma linha de texto = um objeto JSON, terminada em "\n".
#   Requisicao: {"id": 1, "cmd": "ping", "params": {}}
#   Resposta ok:    {"id": 1, "ok": true,  "result": {...}}
#   Resposta erro:  {"id": 1, "ok": false, "error": "mensagem"}
#
# Threading: SketchUp roda a Ruby API inteira na thread principal (UI).
# NAO usamos Thread.new nem sockets bloqueantes -- usamos
# accept_nonblock/read_nonblock dentro de um UI.start_timer periodico,
# que e o padrao seguro usado por extensoes que falam com processos
# externos (ex.: live-reload de servidores de dev web).

require 'socket'
require 'json'

module SketchupBridge
  PORT = 9876
  HOST = '127.0.0.1'
  POLL_INTERVAL_S = 0.05 # 50ms

  module_function

  def start
    stop # idempotente: se já tiver uma instância rodando, para antes
    @server = TCPServer.new(HOST, PORT)
    @server.listen(8)
    @clients = {} # socket => buffer de bytes ainda não processados
    @timer_id = UI.start_timer(POLL_INTERVAL_S, true) { tick }
    puts "[SketchupBridge] escutando em #{HOST}:#{PORT}"
    true
  rescue => e
    puts "[SketchupBridge] falha ao iniciar: #{e.class}: #{e.message}"
    false
  end

  def stop
    if @timer_id
      UI.stop_timer(@timer_id)
      @timer_id = nil
    end
    @clients&.each_key { |sock| safe_close(sock) }
    @clients = {}
    safe_close(@server) if @server
    @server = nil
    puts '[SketchupBridge] parado'
    true
  end

  def running?
    !@server.nil?
  end

  # -- loop de polling (chamado pelo timer) ---------------------------------

  def tick
    accept_new_clients
    read_from_clients
  rescue => e
    # nunca deixa uma excecao no timer derrubar o SketchUp
    puts "[SketchupBridge] erro no tick: #{e.class}: #{e.message}"
  end

  def accept_new_clients
    loop do
      client = @server.accept_nonblock
      @clients[client] = +''
      puts "[SketchupBridge] cliente conectado (#{@clients.size} ativos)"
    rescue IO::WaitReadable, Errno::EINTR
      break
    end
  end

  def read_from_clients
    @clients.each_key.to_a.each do |sock|
      begin
        data = sock.read_nonblock(4096)
        @clients[sock] << data
        process_buffer(sock)
      rescue IO::WaitReadable
        # nada pra ler agora, normal
      rescue EOFError, Errno::ECONNRESET, Errno::EPIPE
        puts '[SketchupBridge] cliente desconectou'
        safe_close(sock)
        @clients.delete(sock)
      end
    end
  end

  def process_buffer(sock)
    buf = @clients[sock]
    while (newline_idx = buf.index("\n"))
      line = buf.slice!(0, newline_idx + 1)
      handle_line(sock, line.strip)
    end
  end

  def handle_line(sock, line)
    return if line.empty?

    request = JSON.parse(line)
    id = request['id']
    cmd = request['cmd']
    params = request['params'] || {}

    result = dispatch(cmd, params)
    respond(sock, id: id, ok: true, result: result)
  rescue => e
    respond(sock, id: request && request['id'], ok: false, error: "#{e.class}: #{e.message}")
  end

  def respond(sock, payload)
    sock.write(JSON.generate(payload) + "\n")
  rescue Errno::EPIPE, Errno::ECONNRESET
    # cliente ja fechou, ignora
  end

  def safe_close(io)
    io.close unless io.closed?
  rescue StandardError
    nil
  end

  # -- comandos expostos ao Python ------------------------------------------

  def dispatch(cmd, params)
    case cmd
    when 'ping'
      cmd_ping
    when 'open_model'
      cmd_open_model(params)
    when 'model_summary'
      cmd_model_summary
    when 'close_model'
      cmd_close_model
    else
      raise "comando desconhecido: #{cmd.inspect}"
    end
  end

  def cmd_ping
    {
      pong: true,
      sketchup_version: Sketchup.version,
      ruby_version: RUBY_VERSION,
      bridge_port: PORT,
    }
  end

  def cmd_open_model(params)
    path = params['path']
    raise 'parametro "path" obrigatorio' if path.nil? || path.empty?
    raise "arquivo nao encontrado: #{path}" unless File.exist?(path)

    # Sketchup.open_file: API oficial, documentada, carrega o .skp como
    # o modelo ativo da aplicacao (mesma coisa que File > Open na UI).
    # Retorna true/false. Isso roda na mesma thread do dispatch, que já
    # é a thread principal do SketchUp -- sem problema de concorrência.
    ok = Sketchup.open_file(path)
    raise "Sketchup.open_file retornou false para #{path}" unless ok

    { opened: true, path: path }
  ensure
    # BUG CONFIRMADO em 27/10/2026 (ver REVERSE_ENGINEERING_NOTES.md
    # secao 10.8): depois de Sketchup.open_file trocar o modelo ativo,
    # o UI.start_timer registrado em start() para de disparar sozinho
    # -- a bridge fica muda (nem "ping" responde) ate religar o timer
    # manualmente. Reagimos aqui, sempre, mesmo se open_file falhar,
    # porque o timer pode ter parado so pela troca de documento.
    rearm_timer
  end

  def rearm_timer
    UI.stop_timer(@timer_id) if @timer_id
    @timer_id = UI.start_timer(POLL_INTERVAL_S, true) { tick }
  end

  def cmd_model_summary
    model = Sketchup.active_model
    raise 'nenhum modelo ativo' if model.nil?

    entities = model.entities
    {
      title: model.title,
      path: model.path,
      guid: model.guid,
      faces: entities.grep(Sketchup::Face).size,
      edges: entities.grep(Sketchup::Edge).size,
      groups: entities.grep(Sketchup::Group).size,
      component_instances: entities.grep(Sketchup::ComponentInstance).size,
      number_of_definitions: model.definitions.size,
    }
  end

  def cmd_close_model
    # Nao existe "fechar sem abrir outro" na Ruby API publica; o
    # equivalente suportado e criar um modelo novo em branco.
    Sketchup.file_new
    { closed: true }
  end
end

SketchupBridge.start
