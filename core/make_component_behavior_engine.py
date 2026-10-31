"""
Motor de Criação de Componentes e Comportamentos do SketchUp (Make Component - Zero DLL).

Implementa a engenharia reversa da caixa de diálogo 'Criar Componente' (Make Component - Atalho G):
(Editar -> Criar Componente / Edit -> Make Component)
1. Atributos Canônicos de Definição:
   - Nome da Definição (definition_name), Descrição (description).
   - Eixos locais do componente (Origem e orientação).
2. Comportamentos Oficiais de Alinhamento e Fixação (Glue to):
   - 'None' (Nenhum)
   - 'Any' (Qualquer face)
   - 'Horizontal' (Apenas pisos/tetos)
   - 'Vertical' (Apenas paredes verticais)
   - 'Sloped' (Apenas coberturas/planos inclinados)
3. Cortar Abertura (Cut Opening):
   - Recorta automaticamente um vão na face hospedeira onde o componente é colado (ex: janelas e portas).
4. Sempre Encarar a Câmera (Always Face Camera / Face-Me):
   - Rotaciona o componente para encarar o observador continuamente.
5. Sombras Voltadas para o Sol (Shadows Face Sun):
   - Projeta sombras orientadas pelo azimute do sol em componentes 2D Face-Me.
"""

from typing import List, Dict, Any, Tuple, Optional


class MakeComponentBehaviorEngine:
    """Motor analítico de definição e comportamentos de componentes oficiais do SketchUp."""

    VALID_GLUE_BEHAVIORS = ["NONE", "ANY", "HORIZONTAL", "VERTICAL", "SLOPED"]

    @classmethod
    def create_component_definition(
        cls,
        definition_name: str,
        description: str = "",
        glue_to: str = "NONE",
        cut_opening: bool = False,
        always_face_camera: bool = False,
        shadows_face_sun: bool = False,
        local_origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        opening_loop_2d: Optional[List[Tuple[float, float]]] = None
    ) -> Dict[str, Any]:
        """
        Gera a estrutura formal de definição de componente com comportamentos nativos.
        """
        if not definition_name or not definition_name.strip():
            raise ValueError("O nome do componente não pode estar vazio.")

        glue_clean = glue_to.upper().strip()
        if glue_clean not in cls.VALID_GLUE_BEHAVIORS:
            glue_clean = "NONE"

        # Se cortar abertura for ativado, valida se há um loop de corte definido
        if cut_opening and not opening_loop_2d:
            # Retângulo padrão de corte 1.0m x 2.10m (porta típica)
            opening_loop_2d = [(-0.5, 0.0), (0.5, 0.0), (0.5, 2.10), (-0.5, 2.10)]

        behavior = {
            "glue_to": glue_clean,
            "cut_opening": cut_opening,
            "always_face_camera": always_face_camera,
            "shadows_face_sun": shadows_face_sun,
            "local_origin": local_origin,
            "opening_loop": opening_loop_2d if cut_opening else None
        }

        return {
            "definition_name": definition_name.strip(),
            "description": description.strip(),
            "behavior": behavior,
            "is_dynamic": False,
            "instances_count": 0
        }

    @classmethod
    def test_glue_compatibility(
        cls,
        glue_behavior: str,
        target_face_normal: Tuple[float, float, float]
    ) -> bool:
        """
        Testa se o componente pode ser colado na face selecionada com base em sua normal.
        """
        glue = glue_behavior.upper().strip()
        if glue == "NONE":
            return False
        if glue == "ANY":
            return True

        nz = abs(target_face_normal[2])
        if glue == "HORIZONTAL":
            # Normal puramente vertical (Z = 1 ou -1)
            return nz > 0.95
        elif glue == "VERTICAL":
            # Normal puramente horizontal (Z = 0)
            return nz < 0.05
        elif glue == "SLOPED":
            # Normal inclinada (0.05 < Z < 0.95)
            return 0.05 <= nz <= 0.95

        return False
