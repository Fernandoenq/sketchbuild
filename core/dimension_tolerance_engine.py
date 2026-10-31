"""
SketchBuild - Motor de Cotas com Tolerâncias e Desvios Dimensionais (Zero DLL / Pure Python)
Frente 84: Engenharia Reversa do SketchUp - Dimension Tolerances (ISO 2768 & NBR 6492)

Calcula e formata cotas técnicas com tolerâncias bilaterais (+-), desvios assimétricos,
limites máximos/mínimos e classes de precisão da norma ISO 2768-1.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple


class DimensionToleranceEngine:
    """Motor de cálculo e formatação de tolerâncias dimensionais para cotas."""

    # Tabela ISO 2768-1 (faixa_min, faixa_max, {classe: delta_mm})
    ISO_2768_LINEAR = [
        (0.5, 3.0, {"f": 0.05, "m": 0.1, "c": 0.2, "v": 0.5}),
        (3.0, 6.0, {"f": 0.05, "m": 0.1, "c": 0.3, "v": 0.5}),
        (6.0, 30.0, {"f": 0.1, "m": 0.2, "c": 0.5, "v": 1.0}),
        (30.0, 120.0, {"f": 0.15, "m": 0.3, "c": 0.8, "v": 1.5}),
        (120.0, 400.0, {"f": 0.2, "m": 0.5, "c": 1.2, "v": 2.5}),
        (400.0, 1000.0, {"f": 0.3, "m": 0.8, "c": 2.0, "v": 4.0}),
        (1000.0, 2000.0, {"f": 0.5, "m": 1.2, "c": 3.0, "v": 6.0}),
        (2000.0, 4000.0, {"f": 1.0, "m": 2.0, "c": 4.0, "v": 8.0}),
    ]

    @classmethod
    def calculate_tolerance(
        cls,
        nominal_val: float,
        unit: str = "mm",
        tolerance_type: str = "BILATERAL",  # BILATERAL, LIMITS, DEVIATION, ISO_CLASS
        upper_tol: float = 0.1,
        lower_tol: float = 0.1,
        iso_class: str = "m",  # f (fina), m (média), c (grossa), v (muito grossa)
        precision: int = 2,
    ) -> Dict[str, Any]:
        """
        Calcula os limites dimensionais e gera o texto formatado para a cota.
        """
        nom = float(nominal_val)
        # Se nominal for em metros, converter para mm para lookup na norma ISO
        nom_mm = nom * 1000.0 if unit == "m" else nom

        up = abs(upper_tol)
        low = abs(lower_tol)

        if tolerance_type.upper() == "ISO_CLASS":
            c_key = iso_class.lower()
            delta_mm = 0.2
            for min_d, max_d, classes in cls.ISO_2768_LINEAR:
                if min_d <= nom_mm <= max_d:
                    delta_mm = classes.get(c_key, 0.2)
                    break
            up = delta_mm if unit == "mm" else (delta_mm / 1000.0)
            low = up
            formatted_text = f"{nom:.{precision}f} ± {up:.{precision}f} {unit} (ISO 2768-{c_key})"

        elif tolerance_type.upper() == "BILATERAL":
            low = up
            formatted_text = f"{nom:.{precision}f} ± {up:.{precision}f} {unit}"

        elif tolerance_type.upper() == "LIMITS":
            max_val = nom + up
            min_val = nom - low
            formatted_text = f"MAX {max_val:.{precision}f} / MIN {min_val:.{precision}f} {unit}"

        else:  # DEVIATION
            formatted_text = f"{nom:.{precision}f} +{up:.{precision}f}/-{low:.{precision}f} {unit}"

        max_limit = nom + up
        min_limit = nom - low

        return {
            "entity_type": "DimensionTolerance",
            "nominal_value": round(nom, 4),
            "unit": unit,
            "tolerance_type": tolerance_type.upper(),
            "upper_tolerance": round(up, 4),
            "lower_tolerance": round(low, 4),
            "max_limit": round(max_limit, 4),
            "min_limit": round(min_limit, 4),
            "total_span": round(max_limit - min_limit, 4),
            "formatted_text": formatted_text,
            "status": "TOLERÂNCIA DIMENSIONAL CALCULADA COM SUCESSO",
        }
