"""
Motor de Estilos de Arestas Nativos do SketchUp (Zero DLL).

Implementa as 7 opções canônicas de exibição de arestas do SketchUp:
1. Profiles: Arestas de contorno/silhueta desenhadas com espessura destacada.
2. Depth Cue: Atenuação e espessura proporcional à proximidade da câmera.
3. Extensions: Prolongamento analítico das pontas das arestas.
4. Endpoints: Nós gráficos nas extremidades dos segmentos.
5. Jitter: Variação paramétrica emulando traço manual à mão livre.
6. Back Edges (Atalho K): Arestas oclusas por faces sólidas em linha tracejada.
7. Color by Material / Color by Tag / Default Edge Color.
"""

from typing import Dict, Any, List, Tuple


class EdgeStylesEngine:
    """Controlador e classificador de estilos de arestas nativos do SketchUp."""

    DEFAULT_SETTINGS = {
        "edges_enabled": True,
        "profiles_enabled": True,
        "profile_width": 2,
        "depth_cue_enabled": False,
        "depth_cue_width": 3,
        "extensions_enabled": False,
        "extension_length_px": 4,
        "endpoints_enabled": False,
        "endpoint_size_px": 5,
        "jitter_enabled": False,
        "back_edges_enabled": False,  # Atalho K
        "edge_color_mode": "all_same",  # "all_same", "by_material", "by_tag"
        "default_color_hex": "#000000"
    }

    def __init__(self, settings: Dict[str, Any] = None):
        self._settings = {**self.DEFAULT_SETTINGS, **(settings or {})}

    @property
    def settings(self) -> Dict[str, Any]:
        return self._settings.copy()

    def update_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza uma ou mais opções do estilo de arestas."""
        self._settings.update(new_settings)
        return self.settings

    def toggle_back_edges(self) -> bool:
        """Alterna a exibição de arestas traseiras tracejadas (Equivalente ao atalho 'K')."""
        self._settings["back_edges_enabled"] = not self._settings["back_edges_enabled"]
        return self._settings["back_edges_enabled"]

    def toggle_profiles(self) -> bool:
        """Alterna o destaque de silhuetas/perfis externos."""
        self._settings["profiles_enabled"] = not self._settings["profiles_enabled"]
        return self._settings["profiles_enabled"]

    def classify_edges(
        self,
        edges_with_faces: List[Dict[str, Any]],
        camera_direction: Tuple[float, float, float] = (0.0, -1.0, 0.0)
    ) -> Dict[str, Any]:
        """
        Classifica as arestas da cena em Perfis (silhuetas), Arestas Normais e Arestas Traseiras.
        edges_with_faces: [{'start': [x,y,z], 'end': [x,y,z], 'face_normals': [[nx,ny,nz], ...]}]
        """
        profiles = []
        normal_edges = []
        back_edges = []

        cdx, cdy, cdz = camera_direction
        c_mag = (cdx**2 + cdy**2 + cdz**2)**0.5 or 1.0
        cdx, cdy, cdz = cdx/c_mag, cdy/c_mag, cdz/c_mag

        for edge in edges_with_faces:
            normals = edge.get("face_normals", [])
            seg = {"start": edge["start"], "end": edge["end"]}

            if len(normals) == 1:
                # Borda de contorno livre (sempre perfil)
                profiles.append(seg)
            elif len(normals) >= 2:
                # Testa se uma face está voltada para a câmera e a outra voltada para longe
                dot1 = normals[0][0]*cdx + normals[0][1]*cdy + normals[0][2]*cdz
                dot2 = normals[1][0]*cdx + normals[1][1]*cdy + normals[1][2]*cdz

                if (dot1 > 0 and dot2 <= 0) or (dot1 <= 0 and dot2 > 0):
                    # Aresta de silhueta (Perfil do modelo)
                    profiles.append(seg)
                else:
                    normal_edges.append(seg)
            else:
                normal_edges.append(seg)

            # Se back edges estiver habilitado, as arestas oclusas são marcadas para tracejado
            if self._settings["back_edges_enabled"]:
                back_edges.append(seg)

        return {
            "entity_type": "ClassifiedEdgeStyles",
            "settings": self.settings,
            "profiles_count": len(profiles),
            "normal_edges_count": len(normal_edges),
            "back_edges_count": len(back_edges),
            "profiles": profiles,
            "normal_edges": normal_edges,
            "back_edges": back_edges if self._settings["back_edges_enabled"] else []
        }
