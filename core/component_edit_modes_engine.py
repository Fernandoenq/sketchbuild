"""
Motor dos Modos de Exibição de Edição de Componentes do SketchUp (Zero DLL).

Implementa a engenharia reversa das opções clássicas de edição de componentes do SketchUp:
(Visualizar -> Edição de Componentes / View -> Component Edit)
1. Ocultar o Resto do Modelo (Hide Rest of Model):
   - Ao abrir um grupo ou componente para edição, oculta todas as outras instâncias da cena.
2. Ocultar Componentes Semelhantes (Hide Similar Components):
   - Oculta cópias adicionais da mesma definição para evitar poluição visual de edição.
3. Esmaecer o Resto do Modelo (Fade Rest of Model):
   - Aplica efeito 'fantasma' (ghosting) com opacidade atenuada (ex: 25%) nos objetos externos.
4. Esmaecer Componentes Semelhantes (Fade Similar Components):
   - Atenua a opacidade de outras instâncias da mesma definição.
5. Filtro de Visibilidade e Configuração de Materiais Three.js:
   - Determina quais instâncias ficam visíveis, invisíveis ou semitransparentes.
"""

from typing import List, Dict, Any, Optional


class ComponentEditModesEngine:
    """Motor analítico de visibilidade e foco de edição de componentes do SketchUp."""

    @classmethod
    def apply_component_edit_mode(
        cls,
        active_instance_id: Optional[str],
        active_definition_name: Optional[str],
        all_instances: List[Dict[str, Any]],
        hide_rest_of_model: bool = False,
        hide_similar_components: bool = False,
        fade_rest_of_model: bool = True,
        fade_similar_components: bool = True,
        fade_opacity: float = 0.25
    ) -> Dict[str, Any]:
        """
        Calcula o estado de visibilidade e opacidade de todas as instâncias da cena
        com base no componente atualmente em edição.
        """
        if not active_instance_id:
            # Nenhum componente em edição (modo normal de cena aberta)
            return {
                "is_editing": False,
                "active_instance_id": None,
                "active_definition_name": None,
                "instances_state": {
                    inst.get("instance_id", inst.get("id")): {
                        "visible": True,
                        "opacity": 1.0,
                        "is_active": False,
                        "mode": "normal"
                    }
                    for inst in all_instances
                }
            }

        instances_state = {}
        hidden_count = 0
        faded_count = 0

        for inst in all_instances:
            inst_id = inst.get("instance_id", inst.get("id"))
            def_name = inst.get("definition_name", inst.get("name"))

            if inst_id == active_instance_id:
                # O componente que está sendo ativamente editado
                instances_state[inst_id] = {
                    "visible": True,
                    "opacity": 1.0,
                    "is_active": True,
                    "mode": "active_editing"
                }
            elif def_name == active_definition_name:
                # Outra instância da mesma definição (componente semelhante)
                if hide_similar_components:
                    instances_state[inst_id] = {"visible": False, "opacity": 0.0, "is_active": False, "mode": "hidden"}
                    hidden_count += 1
                elif fade_similar_components:
                    instances_state[inst_id] = {"visible": True, "opacity": fade_opacity, "is_active": False, "mode": "faded"}
                    faded_count += 1
                else:
                    instances_state[inst_id] = {"visible": True, "opacity": 1.0, "is_active": False, "mode": "normal"}
            else:
                # Resto do modelo
                if hide_rest_of_model:
                    instances_state[inst_id] = {"visible": False, "opacity": 0.0, "is_active": False, "mode": "hidden"}
                    hidden_count += 1
                elif fade_rest_of_model:
                    instances_state[inst_id] = {"visible": True, "opacity": fade_opacity, "is_active": False, "mode": "faded"}
                    faded_count += 1
                else:
                    instances_state[inst_id] = {"visible": True, "opacity": 1.0, "is_active": False, "mode": "normal"}

        return {
            "is_editing": True,
            "active_instance_id": active_instance_id,
            "active_definition_name": active_definition_name,
            "hide_rest_of_model": hide_rest_of_model,
            "hide_similar_components": hide_similar_components,
            "fade_rest_of_model": fade_rest_of_model,
            "fade_opacity": fade_opacity,
            "total_instances": len(all_instances),
            "hidden_count": hidden_count,
            "faded_count": faded_count,
            "instances_state": instances_state
        }
