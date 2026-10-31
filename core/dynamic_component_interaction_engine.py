"""
Motor de Interação com Componentes Dinâmicos do SketchUp (Trimble DC Click Engine - Zero DLL).

Implementa a engenharia reversa da ferramenta interativa de Componentes Dinâmicos (Interact Tool / Mãozinha):
1. Parser e interpretador sintático de fórmulas de clique oficiais da Trimble:
   - ANIMATE("prop", val1, val2, ...) -> Ciclo entre valores sucessivos de rotação, posição ou dimensão.
   - ANIMATEFAST("prop", val1, val2, ...) e ANIMATESLOW(...) -> Ciclos com velocidades predefinidas.
   - SET("prop", val) -> Atribuição direta de estado.
   - ALERT("mensagem") -> Disparo de alerta informativo ao usuário.
2. Atualização atômica do dicionário 'dynamic_attributes' da instância.
3. Recálculo analítico da matriz de transformação afim 4x4 (translação, rotação em X/Y/Z, escala).
4. Suporte a portas/gavetas abrindo, janelas correndo e peças dobráveis.
"""

import math
import re
from typing import Dict, Any, List, Optional, Tuple, Union


class DynamicComponentInteractionEngine:
    """Motor de execução de fórmulas interativas de Componentes Dinâmicos do SketchUp."""

    @classmethod
    def parse_onclick_formula(cls, formula: str) -> List[Dict[str, Any]]:
        """
        Interpreta a fórmula do atributo onClick.
        Ex: 'ANIMATE("roty", 0, 90); ALERT("Porta aberta!")'
        """
        actions = []
        if not formula or not formula.strip():
            return actions

        # Divide por ponto e vírgula se houver múltiplas instruções
        statements = [s.strip() for s in formula.split(";") if s.strip()]

        for stmt in statements:
            match = re.match(r'^([A-Z_]+)\s*\((.*)\)$', stmt, re.IGNORECASE)
            if not match:
                continue

            func_name = match.group(1).upper()
            raw_args = match.group(2).strip()

            # Quebra argumentos respeitando aspas
            args_tokens = []
            for token in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', raw_args):
                clean = token.strip().strip('"').strip("'")
                # Tenta converter para float se numérico
                try:
                    val = float(clean)
                    args_tokens.append(val)
                except ValueError:
                    args_tokens.append(clean)

            actions.append({
                "function": func_name,
                "arguments": args_tokens,
                "raw_statement": stmt
            })

        return actions

    @classmethod
    def execute_interaction(
        cls,
        instance_id: str,
        dynamic_attributes: Dict[str, Any],
        onclick_formula: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executa a interação na instância, avançando o estado e retornando
        a nova matriz de transformação 4x4 e alertas.
        """
        formula = onclick_formula or dynamic_attributes.get("onclick") or dynamic_attributes.get("onClick")
        if not formula:
            return {
                "instance_id": instance_id,
                "success": False,
                "message": "Nenhuma fórmula onClick definida nesta instância.",
                "updated_attributes": dynamic_attributes,
                "alerts": [],
                "target_transform": None
            }

        actions = cls.parse_onclick_formula(str(formula))
        updated_attrs = dict(dynamic_attributes)
        alerts = []
        animated_properties = {}

        for action in actions:
            func = action["function"]
            args = action["arguments"]

            if func in ["ANIMATE", "ANIMATEFAST", "ANIMATESLOW"]:
                if len(args) >= 2:
                    prop_name = str(args[0]).lower()
                    cycle_values = args[1:]

                    # Valor atual
                    current_val = updated_attrs.get(prop_name, cycle_values[0])
                    try:
                        current_num = float(current_val)
                    except (ValueError, TypeError):
                        current_num = cycle_values[0]

                    # Encontra o próximo valor do ciclo
                    next_val = cycle_values[0]
                    found_index = -1
                    for idx, val in enumerate(cycle_values):
                        if abs(float(val) - current_num) < 1e-3:
                            found_index = idx
                            break

                    if found_index != -1 and found_index + 1 < len(cycle_values):
                        next_val = cycle_values[found_index + 1]
                    else:
                        next_val = cycle_values[0]

                    updated_attrs[prop_name] = next_val
                    animated_properties[prop_name] = {
                        "from": current_num,
                        "to": next_val,
                        "speed": "fast" if func == "ANIMATEFAST" else ("slow" if func == "ANIMATESLOW" else "normal")
                    }

            elif func == "SET":
                if len(args) >= 2:
                    prop_name = str(args[0]).lower()
                    target_val = args[1]
                    updated_attrs[prop_name] = target_val
                    animated_properties[prop_name] = {"to": target_val, "speed": "instant"}

            elif func == "ALERT":
                if len(args) >= 1:
                    alerts.append(str(args[0]))

        # Monta matriz afim 4x4 baseada nos atributos atualizados (rotx, roty, rotz, x, y, z, lenx, leny, lenz)
        pos_x = float(updated_attrs.get("x", 0.0))
        pos_y = float(updated_attrs.get("y", 0.0))
        pos_z = float(updated_attrs.get("z", 0.0))

        rot_x_deg = float(updated_attrs.get("rotx", 0.0))
        rot_y_deg = float(updated_attrs.get("roty", 0.0))
        rot_z_deg = float(updated_attrs.get("rotz", 0.0))

        # Conversão de ângulos para matriz de rotação Euler ZYX
        rx = math.radians(rot_x_deg)
        ry = math.radians(rot_y_deg)
        rz = math.radians(rot_z_deg)

        cx, sx = math.cos(rx), math.sin(rx)
        cy, sy = math.cos(ry), math.sin(ry)
        cz, sz = math.cos(rz), math.sin(rz)

        # Matriz 4x4 no padrão column-major compatível com Three.js / SketchUp
        matrix = [
            cz * cy,
            sz * cy,
            -sy,
            0.0,

            cz * sy * sx - sz * cx,
            sz * sy * sx + cz * cx,
            cy * sx,
            0.0,

            cz * sy * cx + sz * sx,
            sz * sy * cx - cz * sx,
            cy * cx,
            0.0,

            pos_x,
            pos_y,
            pos_z,
            1.0
        ]

        return {
            "instance_id": instance_id,
            "success": True,
            "formula_executed": formula,
            "updated_attributes": updated_attrs,
            "animated_properties": animated_properties,
            "alerts": alerts,
            "target_transform": {
                "position": (round(pos_x, 4), round(pos_y, 4), round(pos_z, 4)),
                "rotation_deg": (round(rot_x_deg, 2), round(rot_y_deg, 2), round(rot_z_deg, 2)),
                "matrix4x4": [round(v, 6) for v in matrix]
            }
        }
