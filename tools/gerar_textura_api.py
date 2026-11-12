"""Gera, pela SketchUpAPI (Python 3.12), dois .skp para o REA de textura (compare com tools/tlv_diff.py):

  cor.skp      uma face com material de cor lisa (controle)
  textura.skp  a mesma face com material que leva uma imagem PNG (xadrez 8x8)

Uso:  py -3.12 tools/gerar_textura_api.py PASTA
"""
import ctypes
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUColor  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


def png_xadrez(caminho: str, lado: int = 8) -> None:
    linhas = b""
    for y in range(lado):
        linhas += b"\x00" + b"".join(b"\xff\x00\x00" if (x + y) % 2 else b"\x00\x00\xff" for x in range(lado))

    def bloco(tipo, dados):
        c = zlib.crc32(tipo + dados) & 0xFFFFFFFF
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", c)

    with open(caminho, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", lado, lado, 8, 2, 0, 0, 0))
                 + bloco(b"IDAT", zlib.compress(linhas)) + bloco(b"IEND", b""))


def gerar(pasta: str, textura: bool, nome: str = "Mat") -> str:
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, "textura.skp" if textura else "cor.skp")
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        e = m.get_entities()
        api.add_face(e, [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0)])
        face = api.get_faces(e)[0]
        P = ctypes.POINTER
        d.SUMaterialCreate.argtypes = [P(_Ref)]
        d.SUMaterialSetName.argtypes = [_Ref, ctypes.c_char_p]
        mat = _Ref()
        assert d.SUMaterialCreate(ctypes.byref(mat)) == 0
        assert d.SUMaterialSetName(mat, nome.encode("utf-8")) == 0
        if textura:
            png = os.path.join(pasta, "xadrez.png")
            png_xadrez(png)
            tex = _Ref()
            d.SUTextureCreateFromFile.argtypes = [ctypes.POINTER(_Ref), ctypes.c_char_p, ctypes.c_double, ctypes.c_double]
            r = d.SUTextureCreateFromFile(ctypes.byref(tex), png.encode("utf-8"), 1.0, 1.0)
            assert r == 0, f"SUTextureCreateFromFile {r}"
            d.SUMaterialSetTexture.argtypes = [_Ref, _Ref]
            assert d.SUMaterialSetTexture(mat, tex) == 0
        else:
            cor = SUColor(red=0, green=0, blue=255, alpha=255)
            d.SUMaterialSetColor.argtypes = [_Ref, ctypes.POINTER(SUColor)]
            assert d.SUMaterialSetColor(mat, ctypes.byref(cor)) == 0
        d.SUModelAddMaterials.argtypes = [type(m._model), ctypes.c_size_t, ctypes.POINTER(_Ref)]
        assert d.SUModelAddMaterials(m._model, 1, (_Ref * 1)(mat)) == 0
        d.SUFaceToDrawingElement.restype = _Ref
        d.SUFaceToDrawingElement.argtypes = [type(face)]
        d.SUDrawingElementSetMaterial.argtypes = [_Ref, _Ref]
        assert d.SUDrawingElementSetMaterial(d.SUFaceToDrawingElement(face), mat) == 0
        m.save(destino)
        m.close()
    finally:
        api.terminate()
    return destino


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "textura")
    print(gerar(pasta, False))
    print(gerar(pasta, True))
