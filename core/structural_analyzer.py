"""
Analisador Estrutural e de Tensões em Vigas e Pilares (FEA / NBR 7190 - Zero DLL).

Implementa cálculos de resistência dos materiais e engenharia de estruturas:
1. Momento Fletor Máximo (M = q*L^2 / 8).
2. Tensão Normal de Flexão (sigma = M / W).
3. Flecha Elástica Máxima (delta = 5*q*L^4 / (384*E*I)).
4. Verificação de flecha admissível segundo a NBR 7190 (limite L/300).
5. Fator de Segurança Estrutural (FS = f_admissivel / sigma).
"""

import math
from typing import Dict, Any


class StructuralAnalyzer:
    """Motor analítico de cálculo estrutural de elementos de madeira."""

    # Propriedades do Eucalipto Tratado Citriodora (Classe C40 / D40 NBR 7190)
    E_MODULUS_MPA = 14500.0   # Módulo de Elasticidade (MPa = N/mm2)
    SIGMA_ADM_MPA = 18.0      # Tensão admissível à flexão com coeficientes de ponderação (MPa)

    @classmethod
    def analyze_beam(
        cls,
        span_length_m: float = 2.00,
        load_kn_per_m: float = 2.50,  # 250 kgf/m (crianças + piso)
        section_type: str = "circular",  # 'circular' ou 'rectangular'
        diameter_m: float = 0.16,      # Diâmetro se tora circular
        width_m: float = 0.08,         # Largura se retangular
        height_m: float = 0.16         # Altura se retangular
    ) -> Dict[str, Any]:
        """Calcula tensões, flecha e segurança de uma viga bi-apoiada."""
        L_mm = span_length_m * 1000.0
        q_n_per_mm = (load_kn_per_m * 1000.0) / 1000.0  # N/mm

        if section_type == "circular":
            D_mm = diameter_m * 1000.0
            I_mm4 = (math.pi * (D_mm ** 4)) / 64.0
            W_mm3 = (math.pi * (D_mm ** 3)) / 32.0
            area_cm2 = (math.pi * ((diameter_m * 100.0) ** 2)) / 4.0
        else:
            b_mm = width_m * 1000.0
            h_mm = height_m * 1000.0
            I_mm4 = (b_mm * (h_mm ** 3)) / 12.0
            W_mm3 = (b_mm * (h_mm ** 2)) / 6.0
            area_cm2 = (width_m * 100.0) * (height_m * 100.0)

        # Momento fletor máximo no meio do vão: M = q * L^2 / 8 (N*mm)
        M_max_n_mm = (q_n_per_mm * (L_mm ** 2)) / 8.0
        M_max_kn_m = M_max_n_mm / 1e6

        # Tensão normal de flexão máxima: sigma = M / W (MPa)
        sigma_mpa = M_max_n_mm / W_mm3

        # Flecha elástica no meio do vão: delta = (5 * q * L^4) / (384 * E * I) (mm)
        delta_mm = (5.0 * q_n_per_mm * (L_mm ** 4)) / (384.0 * cls.E_MODULUS_MPA * I_mm4)
        delta_limit_mm = L_mm / 300.0  # Limite NBR 7190 L/300

        # Fator de segurança
        fs = cls.SIGMA_ADM_MPA / sigma_mpa if sigma_mpa > 0 else 99.0
        deflection_compliant = delta_mm <= delta_limit_mm
        stress_compliant = sigma_mpa <= cls.SIGMA_ADM_MPA
        is_safe = deflection_compliant and stress_compliant

        return {
            "section_type": section_type,
            "span_length_m": span_length_m,
            "applied_load_kn_m": load_kn_per_m,
            "max_bending_moment_kn_m": round(M_max_kn_m, 3),
            "bending_stress_mpa": round(sigma_mpa, 2),
            "admissible_stress_mpa": cls.SIGMA_ADM_MPA,
            "max_deflection_mm": round(delta_mm, 2),
            "deflection_limit_mm": round(delta_limit_mm, 2),
            "safety_factor": round(fs, 2),
            "deflection_compliant": deflection_compliant,
            "stress_compliant": stress_compliant,
            "structural_status": "ESTRUTURA APROVADA (SEGURA)" if is_safe else "NECESSITA REFORÇO / SEÇÃO MAIOR",
        }
