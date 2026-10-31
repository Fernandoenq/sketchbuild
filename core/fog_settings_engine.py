"""Engine de Engenharia Reversa da Caixa de Dialogo de Nevoa (Fog Settings Dialog).

Controla a ativacao, atenuacao atmosferica, distancias de inicio/fim (Near/Far)
e vinculo de cor da nevoa com o plano de fundo para renderizacao no SketchUp e Three.js.
"""

from __future__ import annotations
from typing import Any


class FogSettingsEngine:
    """Implementa o gerenciamento analitico de nevoa parametrica (Fog Settings) do SketchUp."""

    @classmethod
    def configure_fog(
        cls,
        enabled: bool = True,
        use_background_color: bool = True,
        fog_color_hex: str = "#E0E8F0",
        background_color_hex: str = "#FFFFFF",
        near_distance_m: float = 10.0,
        far_distance_m: float = 100.0,
        camera_far_limit_m: float = 1000.0
    ) -> dict[str, Any]:
        """Calcula os parametros analiticos de nevoa linear para WebGL / Three.js."""
        near = max(0.1, float(near_distance_m))
        far = max(near + 1.0, float(far_distance_m))

        final_color = background_color_hex.upper() if use_background_color else fog_color_hex.upper()
        if not final_color.startswith("#"):
            final_color = f"#{final_color}"

        # Conversao para Three.js Fog payload
        # THREE.Fog(colorHexInt, nearDistance, farDistance)
        color_int = int(final_color.lstrip("#"), 16) if len(final_color) == 7 else 0xE0E8F0

        three_payload = {
            "type": "Fog",
            "enabled": enabled,
            "color_hex": final_color,
            "color_int": color_int,
            "near": round(near, 2),
            "far": round(far, 2),
        }

        return {
            "success": True,
            "enabled": enabled,
            "use_background_color": use_background_color,
            "resolved_fog_color_hex": final_color,
            "near_distance_m": round(near, 2),
            "far_distance_m": round(far, 2),
            "fog_span_m": round(far - near, 2),
            "three_fog_payload": three_payload,
        }
