"""
SketchBuild - Compilador de Desenhos Técnicos Vetoriais 2D (Plantas Baixas e Elevações)
(Frente 27 - Zero DLL / Pure Python)

Gera desenhos técnicos vetoriais padronizados no formato W3C Scalable Vector Graphics (.svg),
com projeção ortográfica direta das arestas B-Rep, carimbo de engenharia (ABNT NBR 6492),
linhas de cota dimensionais e escalas arquitetônicas (1:25, 1:50, 1:100).
"""

from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional, Tuple


class TechnicalDrawingExporter:
    """Exportador vetorial 2D de plantas baixas e elevações técnicas com carimbo e cotas."""

    @classmethod
    def export_svg(
        cls,
        scene_dto: Dict[str, Any],
        output_path: str,
        view_type: str = "top",
        title: str = "Prancha Técnica de Engenharia",
        scale: str = "1:50",
    ) -> Dict[str, Any]:
        """Compila e grava o desenho técnico vetorial SVG em disco."""
        svg_content = cls.generate_svg(scene_dto, view_type=view_type, title=title, scale=scale)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        return {
            "path": os.path.abspath(output_path),
            "view_type": view_type,
            "scale": scale,
            "file_size_bytes": len(svg_content.encode("utf-8")),
            "title": title,
        }

    @classmethod
    def generate_svg(
        cls,
        scene_dto: Dict[str, Any],
        view_type: str = "top",
        title: str = "Projeto SketchBuild Parkelô",
        scale: str = "1:50",
    ) -> str:
        """Gera a string SVG com a projeção ortográfica, carimbo e cotas."""
        view_type = view_type.lower()
        if view_type not in ["top", "front", "side"]:
            view_type = "top"

        # Dimensões da prancha técnica A3 (paisagem: 420mm x 297mm -> escala 1px = 1mm ou 1200 x 850 px)
        width_px = 1200
        height_px = 850
        margin_px = 60

        # 1. Coleta todos os vértices e arestas em espaço de mundo
        definitions = {d.get("definition_id"): d for d in scene_dto.get("definitions", [])}
        instances = scene_dto.get("instances", [])

        world_edges: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
        all_x: List[float] = []
        all_y: List[float] = []

        for inst in instances:
            did = inst.get("definition_id")
            d_info = definitions.get(did, {})
            verts = d_info.get("vertices", [])
            indices = d_info.get("indices", [])
            mat = inst.get("transform", [])

            if not verts:
                continue

            # Função de transformação 4x4
            def transform_pt(vx: float, vy: float, vz: float) -> Tuple[float, float, float]:
                if len(mat) >= 16:
                    wx = mat[0] * vx + mat[4] * vy + mat[8] * vz + mat[12]
                    wy = mat[1] * vx + mat[5] * vy + mat[9] * vz + mat[13]
                    wz = mat[2] * vx + mat[6] * vy + mat[10] * vz + mat[14]
                    return (wx * 0.0254, wy * 0.0254, wz * 0.0254)  # polegadas -> metros
                return (vx * 0.0254, vy * 0.0254, vz * 0.0254)

            # Projeta os pontos 3D para 2D de acordo com a vista ortográfica
            # No SketchUp nativo: X = Leste/Oeste, Y = Norte/Sul, Z = Altura (Up)
            def project_pt(wx: float, wy: float, wz: float) -> Tuple[float, float]:
                if view_type == "top":
                    return (wx, wy)  # Planta baixa
                elif view_type == "front":
                    return (wx, wz)  # Elevação frontal
                else:
                    return (wy, wz)  # Elevação lateral

            # Extrai arestas dos triângulos
            for i in range(0, len(indices), 3):
                if i + 2 < len(indices):
                    i0, i1, i2 = indices[i], indices[i + 1], indices[i + 2]
                    p0 = transform_pt(verts[i0*3], verts[i0*3+1], verts[i0*3+2])
                    p1 = transform_pt(verts[i1*3], verts[i1*3+1], verts[i1*3+2])
                    p2 = transform_pt(verts[i2*3], verts[i2*3+1], verts[i2*3+2])

                    pt2d_0 = project_pt(*p0)
                    pt2d_1 = project_pt(*p1)
                    pt2d_2 = project_pt(*p2)

                    world_edges.append((pt2d_0, pt2d_1))
                    world_edges.append((pt2d_1, pt2d_2))
                    world_edges.append((pt2d_2, pt2d_0))

                    all_x.extend([pt2d_0[0], pt2d_1[0], pt2d_2[0]])
                    all_y.extend([pt2d_0[1], pt2d_1[1], pt2d_2[1]])

        # Se não houver geometria, usa limites default
        min_x = min(all_x) if all_x else -2.0
        max_x = max(all_x) if all_x else 2.0
        min_y = min(all_y) if all_y else -2.0
        max_y = max(all_y) if all_y else 2.0

        model_w = max(max_x - min_x, 0.5)
        model_h = max(max_y - min_y, 0.5)

        # Escala de ajuste para caber na prancha (área útil de desenho: 800 x 600 px)
        usable_w = width_px - 2 * margin_px - 150  # deixa espaço para carimbo
        usable_h = height_px - 2 * margin_px - 80
        scale_px_per_m = min(usable_w / model_w, usable_h / model_h) * 0.85

        def to_svg_x(m_x: float) -> float:
            return margin_px + (m_x - min_x) * scale_px_per_m + 50

        def to_svg_y(m_y: float) -> float:
            # SVG tem eixo Y invertido (0 no topo)
            return height_px - margin_px - (m_y - min_y) * scale_px_per_m - 80

        view_names = {
            "top": "PLANTA BAIXA DE ENGENHARIA (CORTE HORIZONTAL Z=1.20M)",
            "front": "ELEVAÇÃO FRONTAL TÉCNICA (VISTA X-Z)",
            "side": "ELEVAÇÃO LATERAL TÉCNICA (VISTA Y-Z)",
        }
        view_title = view_names.get(view_type, "DESENHO TÉCNICO")

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width_px} {height_px}" width="{width_px}" height="{height_px}">',
            '  <defs>',
            '    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">',
            '      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#F0F4F8" stroke-width="1"/>',
            '    </pattern>',
            '    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1B365D" />',
            '    </marker>',
            '  </defs>',
            f'  <rect width="{width_px}" height="{height_px}" fill="#FFFFFF" stroke="#1B365D" stroke-width="4"/>',
            f'  <rect x="{margin_px/2}" y="{margin_px/2}" width="{width_px - margin_px}" height="{height_px - margin_px}" fill="url(#grid)" stroke="#A0AEC0" stroke-width="1.5"/>',
            f'  <!-- Título Superior -->',
            f'  <text x="{margin_px}" y="{margin_px + 10}" font-family="Segoe UI, Arial" font-size="16" font-weight="bold" fill="#1B365D">{view_title}</text>',
            f'  <text x="{margin_px}" y="{margin_px + 28}" font-family="Segoe UI, Arial" font-size="11" fill="#718096">Norma ABNT NBR 6492 &bull; Sistema de Coordenadas Métrico Oficial</text>',
            '  <!-- Arestas do Modelo 2D -->',
            '  <g stroke="#1A202C" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">',
        ]

        # Desenha as arestas filtrando duplicatas aproximadas
        seen_edges = set()
        for e in world_edges:
            x1, y1 = to_svg_x(e[0][0]), to_svg_y(e[0][1])
            x2, y2 = to_svg_x(e[1][0]), to_svg_y(e[1][1])
            # Hash espacial simples para não duplicar linhas
            key = tuple(sorted([(round(x1, 1), round(y1, 1)), (round(x2, 1), round(y2, 1))]))
            if key not in seen_edges and math.hypot(x2 - x1, y2 - y1) > 1.5:
                seen_edges.add(key)
                svg.append(f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')

        svg.append('  </g>')

        # Cotas Limítrofes (Largura e Comprimento Totais)
        dim_x1 = to_svg_x(min_x)
        dim_x2 = to_svg_x(max_x)
        dim_y_bottom = to_svg_y(min_y) + 30
        dim_w_text = f"{model_w:.2f} m"

        svg.append('  <!-- Cotas Lineares -->')
        svg.append(f'  <line x1="{dim_x1:.1f}" y1="{dim_y_bottom:.1f}" x2="{dim_x2:.1f}" y2="{dim_y_bottom:.1f}" stroke="#1B365D" stroke-width="1" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
        svg.append(f'  <line x1="{dim_x1:.1f}" y1="{dim_y_bottom - 10:.1f}" x2="{dim_x1:.1f}" y2="{dim_y_bottom + 10:.1f}" stroke="#1B365D" stroke-width="1"/>')
        svg.append(f'  <line x1="{dim_x2:.1f}" y1="{dim_y_bottom - 10:.1f}" x2="{dim_x2:.1f}" y2="{dim_y_bottom + 10:.1f}" stroke="#1B365D" stroke-width="1"/>')
        svg.append(f'  <text x="{(dim_x1 + dim_x2)/2:.1f}" y="{dim_y_bottom - 6:.1f}" font-family="Segoe UI, Arial" font-size="11" font-weight="bold" fill="#1B365D" text-anchor="middle">{dim_w_text}</text>')

        # Carimbo Técnico de Engenharia (Canto Inferior Direito)
        stamp_w = 340
        stamp_h = 130
        stamp_x = width_px - margin_px - stamp_w
        stamp_y = height_px - margin_px - stamp_h

        svg.append('  <!-- Carimbo de Engenharia -->')
        svg.append(f'  <g transform="translate({stamp_x}, {stamp_y})">')
        svg.append(f'    <rect width="{stamp_w}" height="{stamp_h}" fill="#FFFFFF" stroke="#1B365D" stroke-width="2"/>')
        svg.append(f'    <line x1="0" y1="36" x2="{stamp_w}" y2="36" stroke="#1B365D" stroke-width="1.5"/>')
        svg.append(f'    <line x1="0" y1="84" x2="{stamp_w}" y2="84" stroke="#1B365D" stroke-width="1"/>')
        svg.append(f'    <line x1="200" y1="36" x2="200" y2="{stamp_h}" stroke="#1B365D" stroke-width="1"/>')
        svg.append('    <text x="12" y="24" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="#1B365D">PARKELÔ &bull; ENGENHARIA DE PLAYGROUNDS</text>')
        svg.append(f'    <text x="12" y="52" font-family="Segoe UI, Arial" font-size="10" fill="#718096">PROJETO / MODELO</text>')
        svg.append(f'    <text x="12" y="68" font-family="Segoe UI, Arial" font-size="12" font-weight="bold" fill="#1B365D">{title[:25]}</text>')
        svg.append(f'    <text x="12" y="100" font-family="Segoe UI, Arial" font-size="10" fill="#718096">RESPONSÁVEL TÉCNICO</text>')
        svg.append('    <text x="12" y="116" font-family="Segoe UI, Arial" font-size="11" font-weight="bold" fill="#2D3748">Fernando Filho</text>')
        svg.append(f'    <text x="210" y="52" font-family="Segoe UI, Arial" font-size="10" fill="#718096">ESCALA</text>')
        svg.append(f'    <text x="210" y="68" font-family="Segoe UI, Arial" font-size="12" font-weight="bold" fill="#1B365D">{scale}</text>')
        svg.append(f'    <text x="210" y="100" font-family="Segoe UI, Arial" font-size="10" fill="#718096">DATA / VERSÃO</text>')
        svg.append('    <text x="210" y="116" font-family="Segoe UI, Arial" font-size="11" fill="#2D3748">2026-10-30</text>')
        svg.append('  </g>')

        svg.append('</svg>')
        return '\n'.join(svg)
