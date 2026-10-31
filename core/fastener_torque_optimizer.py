"""
Otimizador de Parafusos, Fixadores e Torque de Aperto (NBR 7190 / ISO 898 - Zero DLL).

Dimensiona fixadores industriais e calcula o torque ótimo de aperto:
1. Mapeamento de espessuras de componentes de madeira e chapas metálicas conectadas.
2. Especificação de parafusos sextavados/franceses e porcas autotravantes Parlock DIN 985.
3. Arruelas de aba larga DIN 9021 para mitigação de esmagamento de fibras (NBR 7190).
4. Cálculo do torque recomendado (T = K * D * Fp) e tensão admissível de esmagamento.
"""

import math
from typing import List, Dict, Any, Tuple


class FastenerTorqueOptimizer:
    """Motor analítico de dimensionamento de fixadores e torque de montagem."""

    # Tensão admissível de esmagamento transversal do Eucalipto Citriodora tratado (NBR 7190)
    FC90_WOOD_MPA: float = 6.0  # N/mm²

    # Tabela padrão de fixadores usuais em playgrounds
    FASTENER_STANDARDS = {
        "M10": {"nominal_dia_mm": 10.0, "pitch_mm": 1.5, "washer_ext_dia_mm": 30.0, "washer_area_mm2": 628.0, "socket_size_mm": 17},
        "M12": {"nominal_dia_mm": 12.0, "pitch_mm": 1.75, "washer_ext_dia_mm": 37.0, "washer_area_mm2": 962.0, "socket_size_mm": 19},
        "M16": {"nominal_dia_mm": 16.0, "pitch_mm": 2.0, "washer_ext_dia_mm": 50.0, "washer_area_mm2": 1767.0, "socket_size_mm": 24},
        "1/2_POL": {"nominal_dia_mm": 12.7, "pitch_mm": 1.95, "washer_ext_dia_mm": 38.0, "washer_area_mm2": 1008.0, "socket_size_mm": 19},
        "5/8_POL": {"nominal_dia_mm": 15.88, "pitch_mm": 2.3, "washer_ext_dia_mm": 50.0, "washer_area_mm2": 1760.0, "socket_size_mm": 24},
    }

    @classmethod
    def calculate_connection_fasteners(
        cls,
        timber_thickness_mm: float = 160.0,
        steel_plate_thickness_mm: float = 4.75,
        bolt_standard: str = "1/2_POL",
        material_grade: str = "Inox_304",
        friction_factor_k: float = 0.18
    ) -> Dict[str, Any]:
        """
        Dimensiona o comprimento do parafuso e calcula o torque máximo sem danificar a madeira.
        """
        spec = cls.FASTENER_STANDARDS.get(bolt_standard, cls.FASTENER_STANDARDS["1/2_POL"])
        d_nom = spec["nominal_dia_mm"]
        washer_area = spec["washer_area_mm2"]

        # Espessura total do pacote:
        # Madeira + chapa + 2 arruelas (2 * 3mm) + porca autotravante (~1.2 * d) + sobra de rosca (min 3 fios ~ 6mm)
        washer_thickness_total = 6.0
        nut_thickness = d_nom * 1.2
        thread_protrusion = 6.0

        total_grip_length_mm = timber_thickness_mm + steel_plate_thickness_mm
        min_bolt_length_mm = total_grip_length_mm + washer_thickness_total + nut_thickness + thread_protrusion

        # Arredonda para o comprimento comercial superior mais próximo (múltiplo de 10mm ou 1/2 polegada)
        commercial_length_mm = math.ceil(min_bolt_length_mm / 10.0) * 10.0

        # Carga axial máxima de aperto antes de esmagar as fibras da madeira:
        # F_max = f_c90 * Area_arruela_aba_larga
        max_clamping_force_n = cls.FC90_WOOD_MPA * washer_area

        # Adota 75% da força de esmagamento como força de protensão segura Fp:
        pretension_force_n = max_clamping_force_n * 0.75

        # Torque de aperto normativo: T = K * D * Fp
        # T em N.m = K * (d_nom / 1000) * pretension_force_n
        torque_n_m = friction_factor_k * (d_nom / 1000.0) * pretension_force_n
        torque_kgf_m = torque_n_m / 9.80665

        return {
            "entity_type": "FastenerTorqueSpecification",
            "bolt_standard": bolt_standard,
            "material_grade": material_grade,
            "nominal_diameter_mm": d_nom,
            "grip_length_mm": total_grip_length_mm,
            "min_required_bolt_length_mm": round(min_bolt_length_mm, 1),
            "commercial_bolt_length_mm": commercial_length_mm,
            "recommended_washer": "Arruela Lisa de Aba Larga DIN 9021",
            "recommended_nut": "Porca Sextavada Autotravante com Inserto de Nylon DIN 985 (Parlock)",
            "socket_tool_size_mm": spec["socket_size_mm"],
            "max_wood_crushing_force_kn": round(max_clamping_force_n / 1000.0, 2),
            "pretension_force_kn": round(pretension_force_n / 1000.0, 2),
            "recommended_torque_n_m": round(torque_n_m, 1),
            "recommended_torque_kgf_m": round(torque_kgf_m, 2),
            "safe_clamping_status": "CONFORME NBR 7190 - PROTEÇÃO TOTAL CONTRA ESMAGAMENTO DE FIBRA"
        }
