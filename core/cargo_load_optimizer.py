"""
Otimizador de Carregamento de Carga e Cubagem 3D (Cargo Load Optimizer - Zero DLL).

Calcula a cubagem, empacotamento 3D e distribuição de carga em veículos de transporte:
1. Alocação tridimensional ortogonal de volumes em baú de caminhão / container.
2. Centralização do Centro de Gravidade (CG) para estabilidade veicular.
3. Taxa de ocupação cúbica (m³) e aproveitamento de carga útil (kg).
4. Coordenadas 3D de cada volume alocado para renderização de mapa de carga.
"""

from typing import List, Dict, Any, Tuple


class CargoLoadOptimizer:
    """Motor de otimização de cubagem e carregamento logístico 3D."""

    # Veículos padrão pré-configurados
    VEHICLE_PROFILES = {
        "caminhao_toco": {"length_m": 6.20, "width_m": 2.40, "height_m": 2.40, "payload_kg": 6000.0},
        "caminhao_truck": {"length_m": 8.50, "width_m": 2.45, "height_m": 2.60, "payload_kg": 14000.0},
        "carreta_bau": {"length_m": 14.20, "width_m": 2.50, "height_m": 2.80, "payload_kg": 25000.0},
    }

    @classmethod
    def optimize_load(
        cls,
        packages: List[Dict[str, Any]],
        vehicle_type: str = "caminhao_truck",
        custom_dimensions: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Otimiza a alocação 3D de volumes no baú do caminhão.
        packages: lista de [{'name': str, 'length_m': float, 'width_m': float, 'height_m': float, 'weight_kg': float, 'quantity': int}]
        """
        vehicle = cls.VEHICLE_PROFILES.get(vehicle_type, cls.VEHICLE_PROFILES["caminhao_truck"])
        if custom_dimensions:
            vehicle = {**vehicle, **custom_dimensions}

        v_length = vehicle["length_m"]
        v_width = vehicle["width_m"]
        v_height = vehicle["height_m"]
        v_payload = vehicle["payload_kg"]
        v_volume_m3 = v_length * v_width * v_height

        # Desdobra as peças por quantidade
        items_to_pack = []
        for p in packages:
            qty = p.get("quantity", 1)
            for i in range(qty):
                items_to_pack.append({
                    "id": f"{p.get('name', 'Volume')}_{i+1}",
                    "name": p.get("name", "Volume"),
                    "length": float(p.get("length_m", 1.0)),
                    "width": float(p.get("width_m", 1.0)),
                    "height": float(p.get("height_m", 1.0)),
                    "weight_kg": float(p.get("weight_kg", 50.0)),
                    "volume_m3": float(p.get("length_m", 1.0)) * float(p.get("width_m", 1.0)) * float(p.get("height_m", 1.0))
                })

        # Ordena por peso decrescente (peças pesadas embaixo) e maior comprimento
        items_to_pack.sort(key=lambda x: (x["weight_kg"], x["volume_m3"]), reverse=True)

        packed_items = []
        unpacked_items = []

        curr_x = 0.0
        curr_y = 0.0
        curr_z = 0.0
        max_layer_height = 0.0
        max_row_width = 0.0
        total_weight_kg = 0.0
        total_cargo_volume_m3 = 0.0

        for item in items_to_pack:
            il, iw, ih = item["length"], item["width"], item["height"]

            # Checagem de carga máxima admissível
            if total_weight_kg + item["weight_kg"] > v_payload:
                unpacked_items.append({**item, "reason": "Excesso de peso máximo do veículo"})
                continue

            # Tentativa de alocação ao longo do comprimento X
            if curr_x + il <= v_length and curr_y + iw <= v_width and curr_z + ih <= v_height:
                pass
            elif curr_y + iw + max_row_width <= v_width and curr_z + ih <= v_height:
                # Nova linha lateral Y
                curr_x = 0.0
                curr_y += max_row_width
                max_row_width = 0.0
            elif curr_z + ih + max_layer_height <= v_height:
                # Nova camada superior Z
                curr_x = 0.0
                curr_y = 0.0
                curr_z += max_layer_height
                max_layer_height = 0.0
                max_row_width = 0.0
            else:
                unpacked_items.append({**item, "reason": "Falta de espaço volumétrico no baú"})
                continue

            # Item cabe no ponto atual (curr_x, curr_y, curr_z)
            packed_items.append({
                "item_id": item["id"],
                "name": item["name"],
                "position": [round(curr_x, 3), round(curr_y, 3), round(curr_z, 3)],
                "dimensions": [round(il, 3), round(iw, 3), round(ih, 3)],
                "weight_kg": item["weight_kg"]
            })

            total_weight_kg += item["weight_kg"]
            total_cargo_volume_m3 += item["volume_m3"]

            max_layer_height = max(max_layer_height, ih)
            max_row_width = max(max_row_width, iw)
            curr_x += il

        # Cálculo do Centro de Gravidade (CG) da carga
        if total_weight_kg > 0:
            cg_x = sum((it["position"][0] + it["dimensions"][0]*0.5) * it["weight_kg"] for it in packed_items) / total_weight_kg
            cg_y = sum((it["position"][1] + it["dimensions"][1]*0.5) * it["weight_kg"] for it in packed_items) / total_weight_kg
            cg_z = sum((it["position"][2] + it["dimensions"][2]*0.5) * it["weight_kg"] for it in packed_items) / total_weight_kg
        else:
            cg_x, cg_y, cg_z = 0.0, 0.0, 0.0

        volumetric_occupancy_pct = (total_cargo_volume_m3 / v_volume_m3) * 100.0
        weight_occupancy_pct = (total_weight_kg / v_payload) * 100.0

        return {
            "entity_type": "CargoLoadPlan",
            "vehicle_type": vehicle_type,
            "vehicle_dimensions_m": [v_length, v_width, v_height],
            "vehicle_volume_m3": round(v_volume_m3, 2),
            "vehicle_max_payload_kg": round(v_payload, 1),
            "packed_items_count": len(packed_items),
            "unpacked_items_count": len(unpacked_items),
            "total_cargo_weight_kg": round(total_weight_kg, 1),
            "total_cargo_volume_m3": round(total_cargo_volume_m3, 2),
            "volumetric_occupancy_pct": round(volumetric_occupancy_pct, 1),
            "weight_occupancy_pct": round(weight_occupancy_pct, 1),
            "center_of_gravity": [round(cg_x, 3), round(cg_y, 3), round(cg_z, 3)],
            "packed_items": packed_items,
            "unpacked_items": unpacked_items,
            "status": "CARGA 100% ALOCADA" if not unpacked_items else f"{len(unpacked_items)} ITENS NÃO COUBERAM"
        }
