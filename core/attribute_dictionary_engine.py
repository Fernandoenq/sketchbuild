"""
Motor de Dicionários de Atributos e Componentes Dinâmicos do SketchUp (Zero DLL).

Implementa a engenharia reversa de Attribute Dictionaries nativos do .SKP:
1. Estrutura hierárquica de pares chave-valor por entidade (instância/definição/modelo).
2. Suporte ao padrão oficial 'dynamic_attributes' da extensão Dynamic Components (Trimble).
3. Avaliação de fórmulas paramétricas de dimensões (_lenx_formula, _leny_formula, _lenz_formula).
4. Suporte a metadados IFC BIM e esquemas de classificação predial.
"""

import math
import re
from typing import Dict, Any, List, Optional, Union


class AttributeDictionaryEngine:
    """Motor analítico de attribute dictionaries e componentes dinâmicos do SketchUp."""

    @classmethod
    def create_dictionary(cls, name: str, attributes: Dict[str, Any] = None) -> Dict[str, Any]:
        """Cria um novo dicionário de atributos no padrão do SketchUp."""
        return {
            "name": name,
            "attributes": attributes or {},
            "count": len(attributes or {})
        }

    @classmethod
    def set_attribute(
        cls,
        dictionaries: Dict[str, Dict[str, Any]],
        dict_name: str,
        key: str,
        value: Union[str, int, float, bool, list]
    ) -> Dict[str, Any]:
        """Adiciona ou atualiza uma chave em um dicionário específico."""
        if dict_name not in dictionaries:
            dictionaries[dict_name] = cls.create_dictionary(dict_name)
        dictionaries[dict_name]["attributes"][key] = value
        dictionaries[dict_name]["count"] = len(dictionaries[dict_name]["attributes"])
        return dictionaries[dict_name]

    @classmethod
    def get_attribute(
        cls,
        dictionaries: Dict[str, Dict[str, Any]],
        dict_name: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Recupera o valor de um atributo em um dicionário."""
        if dict_name in dictionaries and key in dictionaries[dict_name]["attributes"]:
            return dictionaries[dict_name]["attributes"][key]
        return default

    @classmethod
    def configure_dynamic_component(
        cls,
        dictionaries: Dict[str, Dict[str, Any]],
        lenx_cm: float = 100.0,
        leny_cm: float = 100.0,
        lenz_cm: float = 100.0,
        formulas: Dict[str, str] = None,
        onclick_action: str = None,
        description: str = "Componente Dinâmico Paramétrico"
    ) -> Dict[str, Any]:
        """
        Configura atributos do padrão oficial Trimble 'dynamic_attributes'.
        """
        dict_name = "dynamic_attributes"
        if dict_name not in dictionaries:
            dictionaries[dict_name] = cls.create_dictionary(dict_name)

        attrs = dictionaries[dict_name]["attributes"]
        attrs["_formatversion"] = "1.0"
        attrs["_lengthunits"] = "CENTIMETERS"
        attrs["description"] = description
        attrs["lenx"] = float(lenx_cm)
        attrs["leny"] = float(leny_cm)
        attrs["lenz"] = float(lenz_cm)

        if formulas:
            for attr_name, formula in formulas.items():
                clean_key = f"_{attr_name.lower()}_formula"
                attrs[clean_key] = formula

        if onclick_action:
            attrs["onclick"] = onclick_action
            attrs["_onclick_formlabel"] = "OnClick"

        dictionaries[dict_name]["count"] = len(attrs)
        return dictionaries[dict_name]

    @classmethod
    def evaluate_dynamic_formula(
        cls,
        formula: str,
        context_vars: Dict[str, float]
    ) -> float:
        """
        Avalia fórmulas matemáticas simples de componentes dinâmicos do SketchUp.
        Ex: '=LenX * 2 + 10' ou '=Height * 1.5'
        """
        expr = formula.strip()
        if expr.startswith("="):
            expr = expr[1:].strip()

        # Substitui variáveis pelo valor
        for var_name, val in context_vars.items():
            # Match exato de palavra ignorando maiúsculas
            pattern = re.compile(rf'\b{re.escape(var_name)}\b', re.IGNORECASE)
            expr = pattern.sub(str(float(val)), expr)

        # Sanitiza permitindo apenas caracteres aritméticos
        allowed_chars = set("0123456789. +-/*()eE")
        if not set(expr).issubset(allowed_chars):
            raise ValueError(f"Fórmula contém caracteres inválidos ou não suportados: {formula}")

        try:
            return float(eval(expr, {"__builtins__": None}, {}))
        except Exception as e:
            raise ValueError(f"Erro ao avaliar fórmula {formula!r}: {e}")

    @classmethod
    def configure_ifc_classification(
        cls,
        dictionaries: Dict[str, Dict[str, Any]],
        ifc_class: str = "IfcFurnishingElement",
        predefined_type: str = "NOTDEFINED"
    ) -> Dict[str, Any]:
        """Configura o dicionário de classificação IFC BIM oficial do SketchUp."""
        schema_dict = "AppliedSchemaTypes"
        if schema_dict not in dictionaries:
            dictionaries[schema_dict] = cls.create_dictionary(schema_dict)

        dictionaries[schema_dict]["attributes"]["applied_schema"] = "IFC 4"
        dictionaries[schema_dict]["attributes"]["ifc_class"] = ifc_class
        dictionaries[schema_dict]["attributes"]["predefined_type"] = predefined_type
        dictionaries[schema_dict]["count"] = len(dictionaries[schema_dict]["attributes"])
        return dictionaries[schema_dict]
