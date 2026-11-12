"""Gera, pela SketchUpAPI (Python 3.12), uma face com textura posicionada por UV (SUMaterialInput) para o REA.

  uv_padrao.skp  face texturizada sem UV explícito (projeção padrão)
  uv_posic.skp   mesma face com UV (0,0)-(2,0)-(2,2)-(0,2) e outra com (0,0)-(1,0)-(1,1)-(0,1)

NOTA (12/11/2026): o crash antigo era a ordem dos campos de SUMaterialInput. Lida no REA da SketchUpAPI.dll (112 bytes):
num_uv_coords, uv_coords[4] (pares u,v), vertex_indices[4] e, por último, o material (offset 0x68).

Uso:  py -3.12 tools/gerar_uv_api.py PASTA  e depois  tools/tlv_diff.py uv_padrao.skp uv_posic.skp
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUEntitiesRef, SUPoint3D  # noqa: E402
from tools.gerar_textura_api import png_xadrez  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class _P2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class _MatInput(ctypes.Structure):
    # ordem lida no REA da SketchUpAPI.dll (112 bytes; o material fica no offset 0x68, por último)
    _fields_ = [("num_uv_coords", ctypes.c_size_t), ("uv_coords", _P2 * 4), ("vertex_indices", ctypes.c_size_t * 4), ("material", _Ref)]


def gerar(pasta: str, com_uv: bool, escala: float = 2.0, uvs=None, nome: str = None) -> str:
    """`uvs` = 4 pares (u, v) para os cantos (0,0),(100,0),(100,100),(0,100); padrão: ladrilho de 100/escala."""
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, nome or ("uv_posic.skp" if com_uv else "uv_padrao.skp"))
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    P = ctypes.POINTER
    try:
        m = api.create_blank_model()
        mr = type(m._model)
        e = m.get_entities()
        png = os.path.join(pasta, "xadrez.png")
        png_xadrez(png)
        tex, mat = _Ref(), _Ref()
        d.SUTextureCreateFromFile.argtypes = [P(_Ref), ctypes.c_char_p, ctypes.c_double, ctypes.c_double]
        assert d.SUTextureCreateFromFile(ctypes.byref(tex), png.encode("utf-8"), 1.0, 1.0) == 0
        d.SUMaterialCreate.argtypes = [P(_Ref)]
        assert d.SUMaterialCreate(ctypes.byref(mat)) == 0
        d.SUMaterialSetName.argtypes = [_Ref, ctypes.c_char_p]
        assert d.SUMaterialSetName(mat, b"Mat") == 0
        d.SUMaterialSetTexture.argtypes = [_Ref, _Ref]
        assert d.SUMaterialSetTexture(mat, tex) == 0
        d.SUModelAddMaterials.argtypes = [mr, ctypes.c_size_t, P(_Ref)]
        assert d.SUModelAddMaterials(m._model, 1, (_Ref * 1)(mat)) == 0

        gi = _Ref()
        d.SUGeometryInputCreate.argtypes = [P(_Ref)]
        assert d.SUGeometryInputCreate(ctypes.byref(gi)) == 0
        d.SUGeometryInputAddVertex.argtypes = [_Ref, P(SUPoint3D)]
        for x, y in ((0, 0), (100, 0), (100, 100), (0, 100)):
            p = SUPoint3D()
            p.x, p.y, p.z = x, y, 0
            assert d.SUGeometryInputAddVertex(gi, ctypes.byref(p)) == 0
        lp = _Ref()
        d.SULoopInputCreate.argtypes = [P(_Ref)]
        assert d.SULoopInputCreate(ctypes.byref(lp)) == 0
        d.SULoopInputAddVertexIndex.argtypes = [_Ref, ctypes.c_size_t]
        for i in range(4):
            assert d.SULoopInputAddVertexIndex(lp, i) == 0
        d.SUGeometryInputAddFace.argtypes = [_Ref, P(_Ref), P(ctypes.c_size_t)]
        idx = ctypes.c_size_t()
        assert d.SUGeometryInputAddFace(gi, ctypes.byref(lp), ctypes.byref(idx)) == 0
        if com_uv:
            mi = _MatInput()
            mi.material = mat
            mi.num_uv_coords = 4
            for i, (u, v) in enumerate(uvs or ((0, 0), (escala, 0), (escala, escala), (0, escala))):
                mi.uv_coords[i] = _P2(u, v)
                mi.vertex_indices[i] = i
            d.SUGeometryInputFaceSetFrontMaterial.argtypes = [_Ref, ctypes.c_size_t, P(_MatInput)]
            assert d.SUGeometryInputFaceSetFrontMaterial(gi, idx.value, ctypes.byref(mi)) == 0
        d.SUEntitiesFill.argtypes = [SUEntitiesRef, _Ref, ctypes.c_bool]
        assert d.SUEntitiesFill(e, gi, True) == 0
        if not com_uv:
            faces = api.get_faces(e)
            d.SUFaceToDrawingElement.restype = _Ref
            d.SUFaceToDrawingElement.argtypes = [type(faces[0])]
            d.SUDrawingElementSetMaterial.argtypes = [_Ref, _Ref]
            assert d.SUDrawingElementSetMaterial(d.SUFaceToDrawingElement(faces[0]), mat) == 0
        m.save(destino)
        m.close()
    finally:
        api.terminate()
    return destino


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "uv")
    print(gerar(pasta, False))
    print(gerar(pasta, True))
    # variantes para fixar a convenção da matriz (cantos (0,0),(100,0),(100,100),(0,100) do quadrado de 100)
    print(gerar(pasta, True, nome="uv_escala4.skp", uvs=((0, 0), (4, 0), (4, 4), (0, 4))))
    print(gerar(pasta, True, nome="uv_desloc.skp", uvs=((0.25, 0.5), (2.25, 0.5), (2.25, 2.5), (0.25, 2.5))))
    print(gerar(pasta, True, nome="uv_rot90.skp", uvs=((0, 0), (0, 2), (-2, 2), (-2, 0))))
