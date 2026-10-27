"""
Parser standalone de .skp via ctypes contra a SketchUpAPI.dll oficial
da Trimble -- nao precisa do SketchUp instalado/aberto. Carrega a DLL,
inicializa o SDK, le a versao da API e, se um arquivo .skp for
passado, abre o modelo e imprime contagens basicas (faces/arestas/
instancias) do nivel raiz e um resumo da extracao de malha completa
(definicoes + instancias, via core.mesh_extractor).

REQUER Python 3.12 (ver REVERSE_ENGINEERING_NOTES.md secao 15 -- o
Python 3.14.3 tem uma regressao confirmada no ctypes que crasha o
processo nesta chamada).

Uso:
    py -3.12 main.py                 -> so inicializa e mostra a versao da API
    py -3.12 main.py caminho.skp     -> abre, resume entidades e extrai a malha
"""

import sys

from core.su_api import SketchUpAPI
from core.mesh_extractor import extract_scene


def main() -> None:
    api = SketchUpAPI()

    with api:  # chama SUInitialize()/SUTerminate() automaticamente
        major, minor = api.get_api_version()
        print(f"SketchUpAPI carregada. Versao da API: {major}.{minor}")

        if len(sys.argv) > 1:
            caminho_skp = sys.argv[1]
            with api.open_model(caminho_skp) as modelo:
                resumo = modelo.count_summary()
                print(f"Modelo aberto: {caminho_skp}")
                for chave, valor in resumo.items():
                    print(f"  {chave}: {valor}")

                scene = extract_scene(api, modelo)
                total_vertices = sum(len(d["vertices"]) // 3 for d in scene["definitions"])
                total_triangulos = sum(len(d["indices"]) // 3 for d in scene["definitions"])
                print(
                    f"Malha extraida: {len(scene['definitions'])} definicoes, "
                    f"{len(scene['instances'])} instancias, "
                    f"{total_vertices} vertices, {total_triangulos} triangulos"
                )
        else:
            print("Nenhum .skp informado -- pulei a abertura de modelo.")


if __name__ == "__main__":
    main()
