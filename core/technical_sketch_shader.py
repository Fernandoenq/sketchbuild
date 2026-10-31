"""
Renderizador e Filtro Estilizado de Linha Oculta e Esboço Técnico (Zero DLL).

Emula estilos visuais clássicos de desenho técnico e arquitetônico do SketchUp:
1. Extração analítica de silhuetas e arestas vivas com ângulo diédrico > limiar (Crease Edges).
2. Remoção de arestas coplanares suaves para redução de ruído visual.
3. Extensão estilizada de arestas nos cruzamentos (Overshoot / Overhang em nanquim).
4. Exportação vetorial de pranchas estilizadas em SVG com traço arquitetônico.
"""

import math
from typing import List, Dict, Any, Tuple


class TechnicalSketchShader:
    """Motor analítico de renderização e estilização de linhas técnicas."""

    @classmethod
    def filter_sharp_edges(
        cls,
        faces_data: List[Dict[str, Any]],
        dihedral_angle_threshold_deg: float = 25.0
    ) -> List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
        """
        Filtra arestas vivas entre faces com ângulo diédrico maior que o limiar.
        faces_data: lista de [{'vertices': [(x,y,z), ...], 'normal': (nx,ny,nz)}]
        """
        edge_to_faces: Dict[Tuple[Tuple[float, float, float], Tuple[float, float, float]], List[Tuple[float, float, float]]] = {}

        for face in faces_data:
            verts = [tuple(v) for v in face.get("vertices", [])]
            normal = tuple(face.get("normal", (0.0, 0.0, 1.0)))
            num_v = len(verts)
            for i in range(num_v):
                p1 = verts[i]
                p2 = verts[(i + 1) % num_v]
                # Normaliza sentido da aresta para chave de dicionário
                edge_key = (min(p1, p2), max(p1, p2))
                if edge_key not in edge_to_faces:
                    edge_to_faces[edge_key] = []
                edge_to_faces[edge_key].append(normal)

        cos_threshold = math.cos(math.radians(dihedral_angle_threshold_deg))
        sharp_edges = []

        for edge, normals in edge_to_faces.items():
            if len(normals) == 1:
                # Aresta de contorno livre (borda aberta)
                sharp_edges.append(edge)
            elif len(normals) >= 2:
                n1, n2 = normals[0], normals[1]
                dot = n1[0]*n2[0] + n1[1]*n2[1] + n1[2]*n2[2]
                if dot < cos_threshold:
                    sharp_edges.append(edge)

        return sharp_edges

    @classmethod
    def generate_sketch_svg(
        cls,
        edges: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]],
        overshoot_mm: float = 8.0,
        view_scale: float = 100.0,
        canvas_width: int = 800,
        canvas_height: int = 600,
        output_path: str = None
    ) -> str:
        """
        Gera prancha vetorial SVG com traço estilizado de arquiteto (nanquim / overshoot).
        """
        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}">',
            f'  <rect width="{canvas_width}" height="{canvas_height}" fill="#FCFAF2" />',  # Papel vegetal texturizado
            '  <defs>',
            '    <filter id="hand-drawn-filter">',
            '      <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" result="noise" />',
            '      <feDisplacementMap in="SourceGraphic" in2="noise" scale="1.5" />',
            '    </filter>',
            '  </defs>',
            '  <g id="architectural-lines" stroke="#1A202C" stroke-width="1.8" stroke-linecap="round" filter="url(#hand-drawn-filter)">'
        ]

        overshoot_m = overshoot_mm / 1000.0

        for (x1, y1, z1), (x2, y2, z2) in edges:
            # Projeção ortográfica frontal (X, Z) mapeada para o centro do canvas
            dx = x2 - x1
            dz = z2 - z1
            length = math.sqrt(dx**2 + dz**2)
            if length < 1e-6:
                continue

            # Extensão das pontas (overshoot)
            ux, uz = dx / length, dz / length
            ex1 = x1 - ux * overshoot_m
            ez1 = z1 - uz * overshoot_m
            ex2 = x2 + ux * overshoot_m
            ez2 = z2 + uz * overshoot_m

            # Coordenadas em pixels na tela
            sx1 = canvas_width * 0.5 + ex1 * view_scale
            sy1 = canvas_height * 0.8 - ez1 * view_scale
            sx2 = canvas_width * 0.5 + ex2 * view_scale
            sy2 = canvas_height * 0.8 - ez2 * view_scale

            svg_lines.append(f'    <line x1="{sx1:.1f}" y1="{sy1:.1f}" x2="{sx2:.1f}" y2="{sy2:.1f}" />')

        svg_lines.append('  </g>')
        # Carimbo técnico de rodapé
        svg_lines.append(f'  <text x="30" y="{canvas_height - 25}" font-family="Courier, monospace" font-size="12" fill="#4A5568">ESBOÇO TÉCNICO ARQUITETÔNICO - SKETCHBUILD NPR ENGINE (OVERSHOOT {overshoot_mm}mm)</text>')
        svg_lines.append('</svg>')

        svg_content = "\n".join(svg_lines)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(svg_content)

        return svg_content
