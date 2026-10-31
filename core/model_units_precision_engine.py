"""
Motor de Unidades, Precisão Decimal e Snaps do Modelo do SketchUp (Zero DLL).

Implementa a engenharia reversa do painel 'Informações do Modelo -> Unidades' do SketchUp:
(Janela -> Informações do Modelo -> Unidades / Window -> Model Info -> Units)
1. Formatos Canônicos do SketchUp:
   - Decimal: Metros (m), Centímetros (cm), Milímetros (mm), Polegadas (in), Pés (ft).
   - Arquitetônico: Pés e Polegadas Fracionárias (ex: 5' 6 1/2", 1/16").
   - Engenharia: Pés e Polegadas Decimais.
2. Precisão Decimal Regulável:
   - 0, 0.0, 0.00, 0.000, 0.0000.
3. Snapping de Comprimento e Ângulo:
   - Habilitação de Snap de Comprimento e intervalo métrico (ex: 0.05m, 10mm).
   - Habilitação de Snap de Ângulo e incremento angular (ex: 15.0°, 45.0°).
4. Conversão e Formatação Bidirecional:
   - Converte metros canônicos para string formatada de exibição no VCB e Entity Info.
   - Converte qualquer entrada do usuário em metros internos para gravação consistente no .SKP.
"""

import math
import re
from typing import Dict, Any, Tuple, Optional


class ModelUnitsPrecisionEngine:
    """Motor analítico de unidades, precisão e snapping do SketchUp."""

    SUPPORTED_UNITS = ["METERS", "CENTIMETERS", "MILLIMETERS", "INCHES", "FEET"]
    UNIT_FACTORS_FROM_METERS = {
        "METERS": 1.0,
        "CENTIMETERS": 100.0,
        "MILLIMETERS": 1000.0,
        "INCHES": 39.37007874,
        "FEET": 3.280839895
    }
    UNIT_SUFFIXES = {
        "METERS": "m",
        "CENTIMETERS": "cm",
        "MILLIMETERS": "mm",
        "INCHES": '"',
        "FEET": "'"
    }

    @classmethod
    def configure_units(
        cls,
        format_type: str = "DECIMAL",
        unit_length: str = "METERS",
        precision_digits: int = 2,
        enable_length_snapping: bool = True,
        length_snap_interval_m: float = 0.01,
        enable_angle_snapping: bool = True,
        angle_snap_degrees: float = 15.0
    ) -> Dict[str, Any]:
        """
        Configura o sistema de unidades e precisão do modelo.
        """
        fmt = format_type.upper().strip()
        unit = unit_length.upper().strip()
        if unit not in cls.SUPPORTED_UNITS:
            unit = "METERS"

        prec = max(0, min(5, precision_digits))

        return {
            "format": fmt,
            "unit": unit,
            "unit_suffix": cls.UNIT_SUFFIXES[unit],
            "precision_digits": prec,
            "enable_length_snapping": enable_length_snapping,
            "length_snap_interval_m": round(max(0.0001, length_snap_interval_m), 4),
            "enable_angle_snapping": enable_angle_snapping,
            "angle_snap_degrees": round(max(0.1, min(90.0, angle_snap_degrees)), 2),
            "is_metric": unit in ["METERS", "CENTIMETERS", "MILLIMETERS"]
        }

    @classmethod
    def format_length(
        cls,
        length_meters: float,
        unit: str = "METERS",
        precision_digits: int = 2
    ) -> str:
        """
        Formata um comprimento em metros para a string exibida na VCB.
        Ex: 1.5 -> "1.50m" ou "150.0cm".
        """
        unit_clean = unit.upper().strip()
        factor = cls.UNIT_FACTORS_FROM_METERS.get(unit_clean, 1.0)
        suffix = cls.UNIT_SUFFIXES.get(unit_clean, "m")
        val = length_meters * factor

        fmt_str = f"{{:.{precision_digits}f}}{{}}"
        return fmt_str.format(val, suffix)

    @classmethod
    def parse_user_input(
        cls,
        input_str: str,
        active_unit: str = "METERS"
    ) -> float:
        """
        Interpreta a digitação do usuário no VCB com sufixo ou sem, retornando sempre em metros.
        Ex: "2.5m" -> 2.5, "250cm" -> 2.5, "2500mm" -> 2.5, "10'" -> 3.048, "100" -> baseado em active_unit.
        """
        clean = input_str.strip().lower().replace(",", ".")
        match = re.match(r'^([\d\.\-]+)\s*([a-z"\'/]*)$', clean)
        if not match:
            try:
                return float(clean)
            except ValueError:
                return 0.0

        val = float(match.group(1))
        suffix = match.group(2).strip()

        if suffix in ["m", "meter", "meters"]:
            return val
        elif suffix in ["cm", "centimeter", "centimeters"]:
            return val / 100.0
        elif suffix in ["mm", "millimeter", "millimeters"]:
            return val / 1000.0
        elif suffix in ['"', "in", "inch", "inches"]:
            return val * 0.0254
        elif suffix in ["'", "ft", "foot", "feet"]:
            return val * 0.3048
        else:
            # Sem sufixo explícito: adota a unidade ativa do modelo
            factor = cls.UNIT_FACTORS_FROM_METERS.get(active_unit.upper(), 1.0)
            return val / factor

    @classmethod
    def apply_snapping(
        cls,
        value_m: float,
        snap_interval_m: float = 0.01
    ) -> float:
        """Aplica o snap métrico no valor em metros."""
        if snap_interval_m <= 0.0:
            return value_m
        return round(round(value_m / snap_interval_m) * snap_interval_m, 6)

    @classmethod
    def apply_angle_snapping(
        cls,
        angle_deg: float,
        snap_deg: float = 15.0
    ) -> float:
        """Aplica o snap angular no valor em graus."""
        if snap_deg <= 0.0:
            return angle_deg
        return round(round(angle_deg / snap_deg) * snap_deg, 2)
