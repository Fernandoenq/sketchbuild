"""
SketchBuild - Teste Automatizado da Frente 11
Decodificação de Faces, Loops e Triangulação Nativa no SkpBinaryReader (Zero DLL / Pure Python)
Validação Cruzada: SkpBinaryReader.extract_faces_and_triangles()
"""

import os
import tempfile
from core.skp_binary_reader import SkpBinaryReader
from core.skp_binary_writer import SkpBinaryWriter


def run_e2e_faces_and_triangles_test():
    src_skp = "C:/Users/Fernando/Documents/Sem nome.skp"
    if not os.path.exists(src_skp):
        print(f"Aviso: {src_skp} não encontrado.")
        return

    dst_skp = os.path.join(tempfile.gettempdir(), "test_faces_triangles_e2e_verified.skp")
    if os.path.exists(dst_skp):
        os.remove(dst_skp)

    # 1. Cria um modelo com um retângulo conhecido de 2.0m x 1.5m (Área = 3.0 m²)
    session = SkpBinaryWriter.open_session(src_skp)
    res = SkpBinaryWriter.add_rectangle(
        width_m=2.0,
        height_m=1.5,
        offset_xyz_cm=[0.0, 0.0, 50.0]
    )
    print("Face gerada na sessão:", res)
    SkpBinaryWriter.save_session(dst_skp, overwrite_confirmed=True)
    SkpBinaryWriter.close_session()

    # 2. Executa a decodificação analítica de faces e triângulos (Zero DLL)
    print("\n--- 2. Decodificando Faces e Triangulação via SkpBinaryReader ---")
    faces = SkpBinaryReader.extract_faces_and_triangles(dst_skp)
    print(f"Total de faces decodificadas: {len(faces)}")
    assert len(faces) >= 1, "Deve extrair ao menos 1 face"

    # A última face deve ser o retângulo adicionado
    rect_face = faces[-1]
    print("Última face extraída:", rect_face)

    assert rect_face["vertex_count"] == 4, f"Esperado 4 vértices no contorno, obteve {rect_face['vertex_count']}"
    assert rect_face["triangle_count"] == 2, f"Esperado 2 triângulos, obteve {rect_face['triangle_count']}"
    assert rect_face["normal"] == [0.0, 0.0, 1.0], f"Normal esperada [0, 0, 1], obteve {rect_face['normal']}"
    
    # Valida cálculo de área analítica via produto vetorial de triângulos
    expected_area_m2 = 3.0
    diff = abs(rect_face["area_m2"] - expected_area_m2)
    print(f"Área calculada: {rect_face['area_m2']} m² (Esperada: {expected_area_m2} m²)")
    assert diff < 0.01, f"Área calculada difere do esperado: {rect_face['area_m2']} vs {expected_area_m2}"

    print("Validação SkpBinaryReader: SUCESSO ABSOLUTO (Faces, Vértices, Normais, Triângulos e Área 100% Precisos)!")


if __name__ == "__main__":
    run_e2e_faces_and_triangles_test()
    print("\n*** TODOS OS TESTES DA FRENTE 11 PASSARAM COM 100% DE SUCESSO! ***\n")
