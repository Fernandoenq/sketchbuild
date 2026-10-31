"""
Motor de Geometria Oculta e Objetos Ocultos do SketchUp (Zero DLL).

Implementa a engenharia reversa das opções oficiais do menu Visualizar do SketchUp:
(Visualizar -> Geometria Oculta / Visualizar -> Objetos Ocultos)
1. Distinção Canônica Oficial (SketchUp 2020+):
   - Geometria Oculta (Hidden Geometry): Arestas ocultas/suavizadas em superfícies curvas e faces individuais ocultas,
     renderizadas como linhas pontilhadas/tracejadas.
   - Objetos Ocultos (Hidden Objects): Grupos e componentes inteiros que foram ocultados pelo usuário,
     renderizados como malha fantasma/caixa tracejada sem bloquear cliques.
2. Controle de Visibilidade para Three.js:
   - Configura flags de renderização tracejada (LineDashedMaterial) para arestas ocultas reveladas.
   - Restaura visibilidade normal ou oculta conforme comandos 'Exibir' (Unhide).
"""

from typing import List, Dict, Any, Optional


class HiddenGeometryEngine:
    """Motor analítico de controle de geometria oculta e objetos ocultos do SketchUp."""

    @classmethod
    def configure_hidden_display(
        cls,
        show_hidden_geometry: bool = False,
        show_hidden_objects: bool = False,
        instances: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calcula o estado de exibição de instâncias e arestas com base nas flags ativas.
        """
        instances_display = {}
        if instances:
            for inst in instances:
                inst_id = inst.get("instance_id", inst.get("id"))
                is_hidden = inst.get("is_hidden", False) or inst.get("hidden", False)

                if is_hidden:
                    if show_hidden_objects:
                        instances_display[inst_id] = {
                            "visible": True,
                            "display_mode": "ghost_dashed",
                            "opacity": 0.35,
                            "wireframe": True
                        }
                    else:
                        instances_display[inst_id] = {
                            "visible": False,
                            "display_mode": "hidden",
                            "opacity": 0.0,
                            "wireframe": False
                        }
                else:
                    instances_display[inst_id] = {
                        "visible": True,
                        "display_mode": "normal",
                        "opacity": 1.0,
                        "wireframe": False
                    }

        edges_display = {}
        if edges:
            for idx, edge in enumerate(edges):
                e_id = edge.get("id", f"edge_{idx}")
                is_soft_or_hidden = edge.get("is_hidden", False) or edge.get("is_soft", False) or edge.get("is_smooth", False)

                if is_soft_or_hidden:
                    edges_display[e_id] = {
                        "visible": show_hidden_geometry,
                        "style": "dashed" if show_hidden_geometry else "hidden",
                        "dash_size": 0.05,
                        "gap_size": 0.02
                    }
                else:
                    edges_display[e_id] = {
                        "visible": True,
                        "style": "solid",
                        "dash_size": 0.0,
                        "gap_size": 0.0
                    }

        return {
            "show_hidden_geometry": show_hidden_geometry,
            "show_hidden_objects": show_hidden_objects,
            "instances_display_state": instances_display,
            "edges_display_state": edges_display
        }
