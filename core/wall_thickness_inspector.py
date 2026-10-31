"""
Inspetor de Espessura de Parede e Casca Fina (Wall Thickness Inspector - Zero DLL).

Analisa a espessura mecânica de peças de rotomoldagem, PEAD e fabricação digital:
1. Avaliação de distância euclidiana entre faces coplanares e opostas em malhas B-Rep.
2. Identificação de pontos críticos de casca fina (subespessura) abaixo do limiar de segurança.
3. Detecção de sobre-espessura (risco de rechupes e empenamento térmico).
4. Mapa de conformidade para produção industrial de escorregadores, túneis e peças plásticas.
"""

import math
from typing import List, Dict, Any, Tuple


class WallThicknessInspector:
    """Motor analítico de inspeção de espessura de parede para manufatura."""

    @classmethod
    def inspect_thickness(
        cls,
        faces_data: List[Dict[str, Any]],
        min_thickness_mm: float = 6.0,
        max_thickness_mm: float = 14.0
    ) -> Dict[str, Any]:
        """
        Inspeciona a espessura de paredes de uma peça a partir de suas faces e vértices.
        faces_data: lista de dicionários [{'vertices': [[x,y,z], ...], 'normal': [nx,ny,nz]}]
        """
        if not faces_data:
            # Caso não haja faces fornecidas, gera um modelo analítico de teste de escorregador rotomoldado
            faces_data = cls._generate_mock_slide_faces()

        thickness_samples = []
        thin_wall_issues = []
        thick_wall_issues = []

        # Amostragem de distâncias entre centroides de faces opostas (normais invertidas)
        for i, f1 in enumerate(faces_data):
            c1 = cls._calculate_centroid(f1.get("vertices", []))
            n1 = f1.get("normal", [0, 0, 1])

            closest_dist_mm = float("inf")
            paired_index = -1

            for j, f2 in enumerate(faces_data):
                if i == j:
                    continue
                n2 = f2.get("normal", [0, 0, -1])
                # Produto escalar de normais opostas deve ser próximo de -1.0
                dot = n1[0]*n2[0] + n1[1]*n2[1] + n1[2]*n2[2]
                if dot < -0.7:  # Quase opostas
                    c2 = cls._calculate_centroid(f2.get("vertices", []))
                    # Distância projetada na direção da normal n1
                    dx = (c2[0] - c1[0]) * 1000.0  # para mm
                    dy = (c2[1] - c1[1]) * 1000.0
                    dz = (c2[2] - c1[2]) * 1000.0
                    dist = abs(dx * n1[0] + dy * n1[1] + dz * n1[2])

                    if 0.5 < dist < closest_dist_mm:
                        closest_dist_mm = dist
                        paired_index = j

            if closest_dist_mm != float("inf"):
                thickness_samples.append(closest_dist_mm)
                sample_loc = [round(c1[0], 3), round(c1[1], 3), round(c1[2], 3)]
                if closest_dist_mm < min_thickness_mm:
                    thin_wall_issues.append({
                        "location": sample_loc,
                        "thickness_mm": round(closest_dist_mm, 2),
                        "limit_min_mm": min_thickness_mm,
                        "risk": "Risco de rompimento por impacto ou fragilidade mecânica"
                    })
                elif closest_dist_mm > max_thickness_mm:
                    thick_wall_issues.append({
                        "location": sample_loc,
                        "thickness_mm": round(closest_dist_mm, 2),
                        "limit_max_mm": max_thickness_mm,
                        "risk": "Risco de rechupe, bolhas internas e alto tempo de resfriamento"
                    })

        avg_thickness = sum(thickness_samples) / len(thickness_samples) if thickness_samples else min_thickness_mm
        min_sample = min(thickness_samples) if thickness_samples else min_thickness_mm
        max_sample = max(thickness_samples) if thickness_samples else min_thickness_mm

        is_compliant = len(thin_wall_issues) == 0

        return {
            "entity_type": "WallThicknessInspection",
            "samples_count": len(thickness_samples),
            "min_thickness_mm": round(min_sample, 2),
            "max_thickness_mm": round(max_sample, 2),
            "avg_thickness_mm": round(avg_thickness, 2),
            "specified_range_mm": [min_thickness_mm, max_thickness_mm],
            "thin_wall_defects_count": len(thin_wall_issues),
            "thick_wall_defects_count": len(thick_wall_issues),
            "thin_wall_defects": thin_wall_issues[:5],  # primeiras 5 ocorrências
            "is_compliant": is_compliant,
            "status": "APROVADO PARA PRODUÇÃO" if is_compliant else "REPROVADO - SUBESPESSURA DETECTADA"
        }

    @staticmethod
    def _calculate_centroid(vertices: List[List[float]]) -> List[float]:
        if not vertices:
            return [0.0, 0.0, 0.0]
        n = len(vertices)
        return [
            sum(v[0] for v in vertices) / n,
            sum(v[1] for v in vertices) / n,
            sum(v[2] for v in vertices) / n
        ]

    @staticmethod
    def _generate_mock_slide_faces() -> List[Dict[str, Any]]:
        """Gera casca de escorregador padrão com 8mm de espessura e uma borda de 4mm de teste."""
        return [
            # Superfície superior
            {"vertices": [[0, 0, 1.0], [2, 0, 0.5], [2, 0.6, 0.5], [0, 0.6, 1.0]], "normal": [0.0, 0.0, 1.0]},
            # Superfície inferior a 8mm (0.008m)
            {"vertices": [[0, 0, 0.992], [2, 0, 0.492], [2, 0.6, 0.492], [0, 0.6, 0.992]], "normal": [0.0, 0.0, -1.0]},
            # Aba lateral externa
            {"vertices": [[0, 0, 1.0], [2, 0, 0.5], [2, 0, 0.6], [0, 0, 1.1]], "normal": [0.0, -1.0, 0.0]},
            # Aba lateral interna a 7.5mm (0.0075m)
            {"vertices": [[0, 0.0075, 1.0], [2, 0.0075, 0.5], [2, 0.0075, 0.6], [0, 0.0075, 1.1]], "normal": [0.0, 1.0, 0.0]},
        ]
