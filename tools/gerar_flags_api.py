"""Gera, pela SketchUpAPI (Python 3.12), arquivos para decifrar os bits de 0x07d3 (flags do cabeçalho das entidades).

Cada variação muda UMA propriedade de uma face (ou das arestas dela) e o resultado é lido do model.dat.
Uso:  py -3.12 tools/gerar_flags_api.py   (imprime os valores de 0x07d3 por variação)
"""
import ctypes
import io
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skp_hidden_pruner import _parse  # noqa: E402
from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUEntitiesRef  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


# (nome, alvo, função da DLL, valor)
VARIACOES = [
    ("base", None, None, None),
    ("face_sem_sombra_projetada", "face", "SUDrawingElementSetCastsShadows", False),
    ("face_sem_sombra_recebida", "face", "SUDrawingElementSetReceivesShadows", False),
    ("face_oculta", "face", "SUDrawingElementSetHidden", True),
    ("aresta_suave", "aresta", "SUEdgeSetSoft", True),
    ("aresta_lisa", "aresta", "SUEdgeSetSmooth", True),
    ("aresta_sem_sombra", "aresta", "SUDrawingElementSetCastsShadows", False),
    ("aresta_oculta", "aresta", "SUDrawingElementSetHidden", True),
]


def _flags(caminho: str) -> dict:
    b = open(caminho, "rb").read()
    d = zipfile.ZipFile(io.BytesIO(b[b.find(b"PK" + bytes([3, 4])):])).read("model.dat")
    out = {"faces": [], "arestas": []}

    def andar(p, e, caminho_):
        for t, l, q in _parse(d, p, e):
            if t in (0x0DAC, 0x0BB8):
                for a, ll, qq in _parse(d, q + 6, q + 6 + l):
                    if a == 0x07D0:
                        for x, lx, qx in _parse(d, qq + 6, qq + 6 + ll):
                            if x == 0x07D3:
                                out["faces" if t == 0x0DAC else "arestas"].append(d[qx + 6])
            elif l >= 6 and t in (0x01F4, 0x01F6, 0x1388, 0x138A, 0x138B):
                andar(q + 6, q + 6 + l, caminho_ + [t])

    andar(0, len(d), [])
    return out


def gerar(pasta: str) -> dict:
    resultado = {}
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        for nome, alvo, fn, val in VARIACOES:
            m = api.create_blank_model()
            e = m.get_entities()
            api.add_face(e, [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0)])
            if alvo:
                d.SUFaceToDrawingElement.restype = _Ref
                d.SUEdgeToDrawingElement.restype = _Ref
                if alvo == "face":
                    d.SUFaceToDrawingElement.argtypes = [type(api.get_faces(e)[0])]
                    de = [d.SUFaceToDrawingElement(api.get_faces(e)[0])]
                else:
                    n = ctypes.c_size_t()
                    d.SUEntitiesGetNumEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.POINTER(ctypes.c_size_t)]
                    d.SUEntitiesGetNumEdges(e, False, ctypes.byref(n))
                    arr = (_Ref * n.value)()
                    d.SUEntitiesGetEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.c_size_t, ctypes.POINTER(_Ref), ctypes.POINTER(ctypes.c_size_t)]
                    d.SUEntitiesGetEdges(e, False, n.value, arr, ctypes.byref(ctypes.c_size_t()))
                    d.SUEdgeToDrawingElement.argtypes = [_Ref]
                    de = [d.SUEdgeToDrawingElement(arr[0])]  # só a primeira aresta
                f = getattr(d, fn)
                direto = fn.startswith("SUEdge")
                f.argtypes = [_Ref, ctypes.c_bool]
                alvo_ref = arr[0] if direto else de[0]
                assert f(alvo_ref, val) == 0, fn
            caminho = os.path.join(pasta, nome + ".skp")
            m.save(caminho)
            m.close()
            resultado[nome] = _flags(caminho)
    finally:
        api.terminate()
    return resultado


if __name__ == "__main__":
    pasta = tempfile.mkdtemp()
    for k, v in gerar(pasta).items():
        print(f"{k:28s} faces={[hex(x) for x in v['faces']]} arestas={[hex(x) for x in v['arestas']]}")
