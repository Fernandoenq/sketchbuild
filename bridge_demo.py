"""
Demo da Sketchup Bridge: conecta no servidor Ruby que roda dentro do
SketchUp e abre um modelo .skp real, sem ctypes, sem crash.

Pre-requisito: o SketchUp precisa estar aberto com a bridge carregada.
No Ruby Console do SketchUp:

    load 'C:/Users/Fernando/sketchbuild/ruby_bridge/sketchup_bridge.rb'

Uso:
    py -3 bridge_demo.py                    -> so testa ping()
    py -3 bridge_demo.py caminho.skp         -> abre o modelo e resume
"""

import sys

from app.infra.bridge_client import BridgeError, SketchUpBridgeClient


def main() -> None:
    try:
        with SketchUpBridgeClient() as bridge:
            info = bridge.ping()
            print(f"Conectado na Sketchup Bridge: {info}")

            if len(sys.argv) > 1:
                caminho_skp = sys.argv[1]
                print(f"Abrindo modelo via Ruby API oficial: {caminho_skp}")
                bridge.open_model(caminho_skp)

                resumo = bridge.model_summary()
                print("Resumo do modelo ativo:")
                for chave, valor in resumo.items():
                    print(f"  {chave}: {valor}")
            else:
                print("Nenhum .skp informado -- pulei a abertura de modelo.")
    except ConnectionError as e:
        print(
            "Nao foi possivel conectar na Sketchup Bridge.\n"
            "Verifique se o SketchUp esta aberto e se o script Ruby foi "
            "carregado (ver docstring deste arquivo).\n"
            f"Detalhe: {e}"
        )
        sys.exit(1)
    except BridgeError as e:
        print(f"A bridge respondeu com erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
