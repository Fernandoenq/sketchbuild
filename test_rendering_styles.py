import os
import sys
import tempfile
import zipfile
import io
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:\Users\Fernando\sketchup_companion")
from core.su_api import SketchUpAPI
from core.skp_binary_writer import SkpBinaryWriter

def test_front_19_rendering_styles():
    """Valida a Frente 19: Injeção e controle nativo de Estilos de Renderização e Exibição Visual
    (Hidden Line, X-Ray, Perfis grossos, Sky e Background Color) em Pure Python (Zero DLL)."""
    src_skp = r"C:\Users\Fernando\Documents\Sem nome.skp"
    dst_skp = os.path.join(tempfile.gettempdir(), "test_style_technical_factory.skp")
    if os.path.exists(dst_skp):
        os.remove(dst_skp)

    # 1. Abre sessão Zero DLL e configura o Estilo Técnico
    session = SkpBinaryWriter.open_session(src_skp)

    res_style = SkpBinaryWriter.set_rendering_style(
        mode="hidden_line",
        xray=True,
        profiles_width=4,
        background_rgb=(240, 240, 245),
        sky_rgb=(135, 206, 235)
    )
    print("[Zero DLL Writer] Estilo configurado:", res_style)

    saved_path = SkpBinaryWriter.save_session(dst_skp, overwrite_confirmed=True)
    SkpBinaryWriter.close_session()
    print("[Zero DLL Writer] Arquivo gravado em:", saved_path)

    # 2. Validação direta do XML do estilo dentro do pacote ZIP
    with open(saved_path, "rb") as f:
        full_data = f.read()

    idx = full_data.find(b"PK\x03\x04")
    with zipfile.ZipFile(io.BytesIO(full_data[idx:])) as z:
        style_xml = z.read("styles/[Simple Style]/style.xml").decode("utf-8")

    root = ET.fromstring(style_xml)
    items = {}
    for it in root.findall(".//{http://sketchup.google.com/schemas/sketchup/1.0/style}item"):
        items[it.get("id")] = "".join(it.itertext()).strip()

    print("[Zero DLL Checker] Itens verificados no style.xml:")
    print(f"  Item 2001 (Face Mode): {items.get('2001')} (Esperado: 1 = Hidden Line)")
    assert items.get("2001") == "1"

    print(f"  Item 2004 (X-Ray Mode): {items.get('2004')} (Esperado: 1 = Ativado)")
    assert items.get("2004") == "1"

    print(f"  Item 1005 (Profiles Width): {items.get('1005')} (Esperado: 4 pixels)")
    assert items.get("1005") == "4"

    print(f"  Item 4002 (Sky Enabled): {items.get('4002')} (Esperado: 1 = Ativado)")
    assert items.get("4002") == "1"

    print(">>> [Zero DLL Checker] XML DE ESTILOS 100% CONFORME! <<<")

    # 3. Validação Cruzada com Trimble C++ API Oficial
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(saved_path)
        print(">>> [TRIMBLE C++ API] MODELO COM NOVO ESTILO ABRIU COM STATUS 0 (SU_ERROR_NONE)! <<<")
        model.close()
    finally:
        api.terminate()

if __name__ == "__main__":
    test_front_19_rendering_styles()
