"""
Motor do Modo 'Colorir por Etiqueta' do SketchUp (Color by Tag - Zero DLL).

Implementa a engenharia reversa do modo oficial 'Color by Tag / Color by Layer' do SketchUp:
(Bandeja Etiquetas -> Menu de Detalhes -> Colorir por Etiqueta)
1. Mapeamento de Cores Oficiais:
   - Cada Etiqueta/Tag possui uma cor sólida RGB/Hex associada.
   - Fornece paleta de contraste calibrada para tags criadas sem cor explícita.
2. Substituição de Materiais no Viewport:
   - Quando ativado, substitui as texturas e materiais visuais normais do Three.js pela cor da Etiqueta.
   - Permite auditoria visual imediata da organização em camadas e disciplinas BIM do modelo.
3. Toggle Dinâmico e Preservação de Estado:
   - Permite ligar/desligar sem perder as texturas e acabamentos originais das entidades.
"""

from typing import List, Dict, Any, Optional


class ColorByTagEngine:
    """Motor analítico do modo de exibição Color by Tag do SketchUp."""

    DEFAULT_PALETTE = [
        "#E53E3E", "#DD6B20", "#D69E2E", "#38A169", "#319795",
        "#3182CE", "#00B4D8", "#5A67D8", "#805AD5", "#D53F8C",
        "#718096", "#4A5568"
    ]

    @classmethod
    def apply_color_by_tag(
        cls,
        tags: List[Dict[str, Any]],
        instances: List[Dict[str, Any]],
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Calcula o mapa de substituição de cores por instância com base nas tags ativas.
        """
        # 1. Mapeia cor para cada tag
        tag_colors: Dict[str, str] = {}
        for idx, t in enumerate(tags):
            t_name = t.get("name", t.get("tag_name", "Layer0"))
            color = t.get("color")
            if not color or color == "default":
                color = cls.DEFAULT_PALETTE[idx % len(cls.DEFAULT_PALETTE)]
            tag_colors[t_name] = color

        # Tag padrão caso não encontrada
        if "Layer0" not in tag_colors and "Sem Etiqueta" not in tag_colors:
            tag_colors["Layer0"] = "#A0AEC0"

        # 2. Gera mapa de sobrescrita para cada instância da cena
        overrides: Dict[str, Dict[str, Any]] = {}
        for inst in instances:
            inst_id = inst.get("instance_id", inst.get("id"))
            inst_tag = inst.get("tag", inst.get("layer", "Layer0"))
            tag_color = tag_colors.get(inst_tag, "#A0AEC0")

            overrides[inst_id] = {
                "instance_id": inst_id,
                "tag": inst_tag,
                "color_by_tag_active": enabled,
                "override_color_hex": tag_color if enabled else None,
                "original_material": inst.get("material", "Padrão")
            }

        return {
            "color_by_tag_enabled": enabled,
            "total_tags_mapped": len(tag_colors),
            "tag_color_map": tag_colors,
            "instances_affected_count": len(overrides),
            "instance_color_overrides": overrides
        }
