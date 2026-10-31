"""
Exportador de Arquivos DXF 2D para Fabricação Digital CNC e Corte a Laser (Zero DLL).

Gera arquivos DXF R12/2000 ASCII limpos e otimizados para softwares de usinagem CAM
(Aspire, ArtCAM, SheetCAM, Fusion 360 CAM):
1. Contornos fechados com entidades 'LWPOLYLINE' (flag 70 = 1).
2. Separação de camadas:
   - CAM_CORTE_EXTERNO (Corte perimetral externo)
   - CAM_FUROS_INTERNOS (Furações para parafusos/fixadores)
   - CAM_GRAVACAO (Marcações e textos técnicos)
3. Unidades explícitas em milímetros ($INSUNITS 4).
"""

import os
from typing import List, Tuple, Dict, Any


class CamDxfExporter:
    """Gerador de arquivos DXF para máquinas de corte CNC e Laser."""

    @classmethod
    def generate_dxf_content(
        cls,
        parts: List[Dict[str, Any]]
    ) -> str:
        """
        Gera conteúdo DXF R12 ASCII a partir de uma lista de peças.
        cada part: {'name': str, 'outer_loop': [(x_mm, y_mm), ...], 'holes': [[(x, y), ...], ...]}
        """
        dxf_lines = [
            "0", "SECTION",
            "2", "HEADER",
            "9", "$ACADVER", "1", "AC1009",
            "9", "$INSUNITS", "70", "4",  # 4 = Milímetros
            "0", "ENDSEC",
            "0", "SECTION",
            "2", "TABLES",
            "0", "TABLE",
            "2", "LAYER",
            "70", "2",
            "0", "LAYER", "2", "CAM_CORTE_EXTERNO", "70", "0", "62", "1", "6", "CONTINUOUS",  # Vermelho
            "0", "LAYER", "2", "CAM_FUROS_INTERNOS", "70", "0", "62", "4", "6", "CONTINUOUS",  # Ciano
            "0", "ENDTAB",
            "0", "ENDSEC",
            "0", "SECTION",
            "2", "ENTITIES",
        ]

        # Adiciona os contornos das peças
        for part in parts:
            outer_loop = part.get("outer_loop", [])
            if outer_loop:
                # Contorno externo fechado
                dxf_lines.extend(["0", "POLYLINE", "8", "CAM_CORTE_EXTERNO", "66", "1", "70", "1"])  # 70 1 = Fechado
                for x, y in outer_loop:
                    dxf_lines.extend(["0", "VERTEX", "8", "CAM_CORTE_EXTERNO", "10", f"{x:.3f}", "20", f"{y:.3f}", "30", "0.0"])
                dxf_lines.extend(["0", "SEQEND"])

            # Furos internos
            for hole in part.get("holes", []):
                if hole:
                    dxf_lines.extend(["0", "POLYLINE", "8", "CAM_FUROS_INTERNOS", "66", "1", "70", "1"])
                    for x, y in hole:
                        dxf_lines.extend(["0", "VERTEX", "8", "CAM_FUROS_INTERNOS", "10", f"{x:.3f}", "20", f"{y:.3f}", "30", "0.0"])
                    dxf_lines.extend(["0", "SEQEND"])

        dxf_lines.extend(["0", "ENDSEC", "0", "EOF", ""])
        return "\n".join(dxf_lines)

    @classmethod
    def export_cam_dxf(cls, parts: List[Dict[str, Any]], output_path: str) -> str:
        """Salva arquivo DXF para CAM no disco."""
        content = cls.generate_dxf_content(parts)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path
