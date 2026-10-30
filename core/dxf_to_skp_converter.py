import os
import struct
from typing import List, Tuple, Dict, Any, Optional

from core.skp_binary_writer import SkpBinaryWriter
from core.skp_binary_reader import SkpBinaryReader

class DxfToSkpConverter:
    """Conversor Nativo Direto de Arquivos CAD (.dxf) para SketchUp (.skp)
    em Pure Python (Zero DLL / sem runtime do SketchUp ou AutoCAD)."""

    @classmethod
    def parse_dxf(cls, dxf_path: str) -> Dict[str, Any]:
        """Faz o parsing analítico de um arquivo DXF (LINE, 3DFACE, POLYLINE)."""
        lines = []
        faces_3d = []

        with open(dxf_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.readlines()

        i = 0
        n = len(content)
        in_entities = False

        while i < n - 1:
            code_str = content[i].strip()
            val_str = content[i + 1].strip()
            i += 2

            if code_str == "0" and val_str == "SECTION":
                if i < n - 1 and content[i].strip() == "2" and content[i + 1].strip() == "ENTITIES":
                    in_entities = True
            elif code_str == "0" and val_str == "ENDSEC":
                in_entities = False

            if in_entities and code_str == "0":
                if val_str == "LINE":
                    # Lê propriedades da linha
                    p0 = [0.0, 0.0, 0.0]
                    p1 = [0.0, 0.0, 0.0]
                    while i < n - 1:
                        c = content[i].strip()
                        v = content[i + 1].strip()
                        if c == "0":
                            break
                        if c == "10": p0[0] = float(v)
                        elif c == "20": p0[1] = float(v)
                        elif c == "30": p0[2] = float(v)
                        elif c == "11": p1[0] = float(v)
                        elif c == "21": p1[1] = float(v)
                        elif c == "31": p1[2] = float(v)
                        i += 2
                    lines.append((p0, p1))
                elif val_str == "3DFACE":
                    # Lê 4 vértices da face
                    pts = [[0.0, 0.0, 0.0] for _ in range(4)]
                    while i < n - 1:
                        c = content[i].strip()
                        v = content[i + 1].strip()
                        if c == "0":
                            break
                        if c == "10": pts[0][0] = float(v)
                        elif c == "20": pts[0][1] = float(v)
                        elif c == "30": pts[0][2] = float(v)
                        elif c == "11": pts[1][0] = float(v)
                        elif c == "21": pts[1][1] = float(v)
                        elif c == "31": pts[1][2] = float(v)
                        elif c == "12": pts[2][0] = float(v)
                        elif c == "22": pts[2][1] = float(v)
                        elif c == "32": pts[2][2] = float(v)
                        elif c == "13": pts[3][0] = float(v)
                        elif c == "23": pts[3][1] = float(v)
                        elif c == "33": pts[3][2] = float(v)
                        i += 2
                    faces_3d.append(pts)

        return {
            "lines": lines,
            "faces_3d": faces_3d,
            "total_lines": len(lines),
            "total_faces": len(faces_3d),
        }

    @classmethod
    def convert(
        cls,
        dxf_path: str,
        output_skp_path: str,
        template_skp_path: Optional[str] = None,
        scale_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """Converte um arquivo DXF diretamente para o formato binário .skp (Zero DLL)."""
        if not os.path.exists(dxf_path):
            raise FileNotFoundError(f"Arquivo DXF não encontrado: {dxf_path}")

        parsed = cls.parse_dxf(dxf_path)

        if template_skp_path is None or not os.path.exists(template_skp_path):
            template_skp_path = r"C:\Users\Fernando\Documents\Sem nome.skp"

        # Abre sessão baseada no template
        session = SkpBinaryWriter.open_session(template_skp_path)

        # Se houver faces 3D no DXF, cria a geometria correspondente
        created_elements = []
        for face_pts in parsed["faces_3d"]:
            # Calcula dimensões equivalentes para caixa ou face
            xs = [p[0] * scale_factor for p in face_pts]
            ys = [p[1] * scale_factor for p in face_pts]
            zs = [p[2] * scale_factor for p in face_pts]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            min_z, max_z = min(zs), max(zs)

            width_m = max(0.01, (max_x - min_x) / 100.0)
            length_m = max(0.01, (max_y - min_y) / 100.0)
            height_m = max(0.01, (max_z - min_z) / 100.0)

            if abs(max_z - min_z) < 0.001:
                # Face plana
                res = SkpBinaryWriter.add_rectangle(
                    width_m=width_m,
                    height_m=length_m,
                    offset_xyz_cm=[min_x, min_y, min_z]
                )
                created_elements.append(res)
            else:
                # Bloco sólido 3D
                res = SkpBinaryWriter.add_box(
                    width_m=width_m,
                    length_m=length_m,
                    height_m=height_m,
                    offset_xyz_cm=[min_x, min_y, min_z]
                )
                created_elements.append(res)

        saved_path = SkpBinaryWriter.save_session(output_skp_path, overwrite_confirmed=True)
        SkpBinaryWriter.close_session()

        return {
            "source_dxf": dxf_path,
            "output_skp": saved_path,
            "dxf_entities_read": parsed["total_faces"] + parsed["total_lines"],
            "converted_elements_count": len(created_elements),
            "status": "success",
        }
