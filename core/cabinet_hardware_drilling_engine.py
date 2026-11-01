"""
SketchBuild - Motor de Furação Industrial e Ferragens para Marcenaria (Zero DLL / Pure Python)
Frente Marcenaria Avançada: Furação Normativa Sistema 32 (DIN 68858), Caneco 35mm e Minifix

Implementa:
1. Padrão Universal Sistema 32 para laterais de armários e prateleiras reguláveis:
   - Passo vertical padronizado de 32mm.
   - Recuo padrão de 37mm da borda frontal (e traseira).
   - Diâmetro de 5mm para suportes de prateleira e pinos.
2. Furação de Dobradiças Caneco 35mm (Concealed Hinges):
   - Caneco na porta: diâmetro 35mm a 22mm da borda, profundidade 12mm.
   - Calço na lateral: furos duplos espaçados em 32mm na vertical, recuo de 37mm da borda.
   - Distribuição de quantidade automática conforme altura da porta (2 a 5 dobradiças).
3. Furação de Dispositivos de Montagem Minifix / Rafix e Cavilhas:
   - Tambor Minifix 15mm: centro a 34mm (ou 24mm) da borda, profundidade 13mm.
   - Furo passante de topo para o parafuso/pino: diâmetro 8mm.
   - Furos de cavilha de madeira 8x30mm para travamento estrutural.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


class CabinetHardwareDrillingEngine:
    """Motor analítico de cálculo e mapeamento de coordenadas de furação CNC e marcenaria."""

    SYSTEM_32_PITCH_MM: float = 32.0
    DEFAULT_FRONT_SETBACK_MM: float = 37.0

    @classmethod
    def calculate_system_32_shelf_holes(
        cls,
        side_height_mm: float,
        side_depth_mm: float,
        front_setback_mm: float = DEFAULT_FRONT_SETBACK_MM,
        rear_setback_mm: float = DEFAULT_FRONT_SETBACK_MM,
        margin_top_mm: float = 120.0,
        margin_bottom_mm: float = 120.0,
        hole_diameter_mm: float = 5.0,
        hole_depth_mm: float = 11.5,
    ) -> Dict[str, Any]:
        """
        Calcula os furos da cremalheira Sistema 32 em uma lateral de móvel.
        Gera duas colunas verticais (frontal e traseira) com passo de 32mm.
        """
        holes: List[Dict[str, Any]] = []

        usable_height = side_height_mm - margin_top_mm - margin_bottom_mm
        if usable_height <= 0:
            return {
                "status": "warning",
                "message": "Altura útil insuficiente para linha de furação Sistema 32",
                "hole_count": 0,
                "holes": [],
            }

        num_pitches = int(usable_height // cls.SYSTEM_32_PITCH_MM)
        start_y = margin_bottom_mm + (usable_height - (num_pitches * cls.SYSTEM_32_PITCH_MM)) / 2.0

        front_x = front_setback_mm
        rear_x = side_depth_mm - rear_setback_mm

        for i in range(num_pitches + 1):
            y_pos = round(start_y + (i * cls.SYSTEM_32_PITCH_MM), 2)
            # Furo frontal
            holes.append({
                "id": f"SYS32_F_{i+1:02d}",
                "type": "SYSTEM_32_SHELF",
                "column": "front",
                "x_mm": round(front_x, 2),
                "y_mm": y_pos,
                "diameter_mm": hole_diameter_mm,
                "depth_mm": hole_depth_mm,
            })
            # Furo traseiro
            holes.append({
                "id": f"SYS32_R_{i+1:02d}",
                "type": "SYSTEM_32_SHELF",
                "column": "rear",
                "x_mm": round(rear_x, 2),
                "y_mm": y_pos,
                "diameter_mm": hole_diameter_mm,
                "depth_mm": hole_depth_mm,
            })

        return {
            "status": "success",
            "side_height_mm": side_height_mm,
            "side_depth_mm": side_depth_mm,
            "hole_count": len(holes),
            "step_mm": cls.SYSTEM_32_PITCH_MM,
            "front_setback_mm": front_setback_mm,
            "rear_setback_mm": rear_setback_mm,
            "holes": holes,
        }

    @classmethod
    def calculate_door_hinge_drillings(
        cls,
        door_height_mm: float,
        door_width_mm: float,
        hinge_margin_end_mm: float = 90.0,
        cup_diameter_mm: float = 35.0,
        cup_depth_mm: float = 12.0,
        cup_center_to_edge_mm: float = 22.5,  # K=5mm + 17.5mm
    ) -> Dict[str, Any]:
        """
        Calcula a furação de dobradiças de caneco 35mm para a porta e seus respectivos
        calços para a lateral do gabinete. Quantidade calculada conforme a altura normativa.
        """
        # Regra empírica de quantidade de dobradiças por altura
        if door_height_mm <= 900.0:
            hinge_count = 2
        elif door_height_mm <= 1600.0:
            hinge_count = 3
        elif door_height_mm <= 2000.0:
            hinge_count = 4
        else:
            hinge_count = 5

        door_cup_holes: List[Dict[str, Any]] = []
        cabinet_plate_holes: List[Dict[str, Any]] = []

        # Determina posições Y
        y_positions: List[float] = []
        if hinge_count == 2:
            y_positions = [hinge_margin_end_mm, door_height_mm - hinge_margin_end_mm]
        else:
            y_positions.append(hinge_margin_end_mm)
            step = (door_height_mm - 2 * hinge_margin_end_mm) / (hinge_count - 1)
            for i in range(1, hinge_count - 1):
                y_positions.append(hinge_margin_end_mm + i * step)
            y_positions.append(door_height_mm - hinge_margin_end_mm)

        for idx, y in enumerate(y_positions):
            h_id = f"HINGE_{idx+1}"
            # 1. Furo de caneco na porta
            door_cup_holes.append({
                "hinge_id": h_id,
                "type": "HINGE_CUP_35",
                "target": "door",
                "x_mm": round(cup_center_to_edge_mm, 2),
                "y_mm": round(y, 2),
                "diameter_mm": cup_diameter_mm,
                "depth_mm": cup_depth_mm,
            })
            # 2. Dois furos para parafusos do caneco (45mm ou 48mm entre centros, a 9.5mm do centro)
            door_cup_holes.append({
                "hinge_id": f"{h_id}_SCREW_1",
                "type": "HINGE_CUP_SCREW",
                "target": "door",
                "x_mm": round(cup_center_to_edge_mm + 9.5, 2),
                "y_mm": round(y - 22.5, 2),
                "diameter_mm": 2.5,
                "depth_mm": 10.0,
            })
            door_cup_holes.append({
                "hinge_id": f"{h_id}_SCREW_2",
                "type": "HINGE_CUP_SCREW",
                "target": "door",
                "x_mm": round(cup_center_to_edge_mm + 9.5, 2),
                "y_mm": round(y + 22.5, 2),
                "diameter_mm": 2.5,
                "depth_mm": 10.0,
            })
            # 3. Dois furos do calço na lateral do armário (32mm entre eles verticalmente, recuo 37mm)
            cabinet_plate_holes.append({
                "hinge_id": f"{h_id}_PLATE_TOP",
                "type": "HINGE_PLATE_37",
                "target": "side_panel",
                "x_mm": round(cls.DEFAULT_FRONT_SETBACK_MM, 2),
                "y_mm": round(y + 16.0, 2),
                "diameter_mm": 5.0,
                "depth_mm": 11.5,
            })
            cabinet_plate_holes.append({
                "hinge_id": f"{h_id}_PLATE_BOTTOM",
                "type": "HINGE_PLATE_37",
                "target": "side_panel",
                "x_mm": round(cls.DEFAULT_FRONT_SETBACK_MM, 2),
                "y_mm": round(y - 16.0, 2),
                "diameter_mm": 5.0,
                "depth_mm": 11.5,
            })

        return {
            "status": "success",
            "door_height_mm": door_height_mm,
            "door_width_mm": door_width_mm,
            "recommended_hinge_count": hinge_count,
            "door_cup_drillings": door_cup_holes,
            "cabinet_mounting_plates": cabinet_plate_holes,
        }

    @classmethod
    def calculate_minifix_joint(
        cls,
        joint_width_mm: float,
        panel_thickness_mm: float = 18.0,
        drum_setback_mm: float = 34.0,
        margin_ends_mm: float = 50.0,
        include_wooden_dowels: bool = True,
    ) -> Dict[str, Any]:
        """
        Calcula a furação de travamento com tambor excêntrico Minifix 15mm e cavilhas 8x30mm.
        Utilizado na união de base, topo e prateleiras fixas com as laterais.
        """
        if joint_width_mm < (margin_ends_mm * 2 + 32):
            joint_count = 1
            x_offsets = [joint_width_mm / 2.0]
        elif joint_width_mm <= 600.0:
            joint_count = 2
            x_offsets = [margin_ends_mm, joint_width_mm - margin_ends_mm]
        else:
            joint_count = 3
            x_offsets = [
                margin_ends_mm,
                joint_width_mm / 2.0,
                joint_width_mm - margin_ends_mm,
            ]

        face_drillings: List[Dict[str, Any]] = []
        edge_drillings: List[Dict[str, Any]] = []

        for idx, x_pos in enumerate(x_offsets):
            j_id = f"MINIFIX_{idx+1}"
            # Furo do tambor na face do painel horizontal (prateleira/base)
            face_drillings.append({
                "id": f"{j_id}_DRUM",
                "type": "MINIFIX_DRUM_15",
                "x_mm": round(x_pos, 2),
                "y_mm": round(drum_setback_mm, 2),
                "diameter_mm": 15.0,
                "depth_mm": 13.5,
            })
            # Furo de topo do pino (conecta a borda ao tambor)
            edge_drillings.append({
                "id": f"{j_id}_BOLT_HOLE",
                "type": "MINIFIX_BOLT_PASSAGE",
                "x_mm": round(x_pos, 2),
                "z_mm": round(panel_thickness_mm / 2.0, 2),
                "diameter_mm": 8.0,
                "depth_mm": round(drum_setback_mm + 5.0, 2),
            })
            # Furo da cavilha de madeira 8x30mm a 32mm do minifix
            if include_wooden_dowels:
                dowel_x = x_pos + (32.0 if x_pos < joint_width_mm / 2.0 else -32.0)
                edge_drillings.append({
                    "id": f"{j_id}_DOWEL",
                    "type": "WOODEN_DOWEL_8",
                    "x_mm": round(dowel_x, 2),
                    "z_mm": round(panel_thickness_mm / 2.0, 2),
                    "diameter_mm": 8.0,
                    "depth_mm": 25.0,
                })

        return {
            "status": "success",
            "joint_width_mm": joint_width_mm,
            "panel_thickness_mm": panel_thickness_mm,
            "joint_count": joint_count,
            "face_drillings": face_drillings,
            "edge_drillings": edge_drillings,
            "total_holes": len(face_drillings) + len(edge_drillings),
        }
