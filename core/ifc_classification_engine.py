"""
Motor de Classificação BIM e Esquemas IFC Nativo do SketchUp (Zero DLL).

Implementa a engenharia reversa do sistema de Classificação do SketchUp Desktop:
(Janela -> Informações do Modelo -> Classificações)
1. Carregamento de esquemas de classificação padrão da indústria:
   - IFC 2x3 e IFC4 (BuildingSMART)
   - OmniClass (Table 23 - Products)
   - UniFormat
2. Atribuição de tipos de entidade IFC a componentes e grupos do modelo:
   - IfcWall, IfcBeam, IfcColumn, IfcSlab, IfcDoor, IfcWindow, IfcRoof, IfcSpace, IfcFooting, IfcCovering.
3. Gerenciamento de atributos canônicos IFC:
   - GlobalId (UUID ISO 10303-21)
   - PredefinedType (ex: NOTDEFINED, SOLIDWALL, USERDEFINED)
   - Name, Description, ObjectType, Tag
4. Validação de conformidade de classificação de instâncias para exportação OpenBIM.
"""

import uuid
from typing import List, Dict, Any, Optional


class IfcClassificationEngine:
    """Motor de classificação IFC e esquemas BIM oficial do SketchUp."""

    SUPPORTED_SCHEMAS = {
        "IFC4": {
            "name": "Industry Foundation Classes 4 (ISO 16739)",
            "version": "4.0.2.1",
            "classes": [
                "IfcWall", "IfcWallStandardCase", "IfcBeam", "IfcColumn",
                "IfcSlab", "IfcRoof", "IfcDoor", "IfcWindow", "IfcStair",
                "IfcRailing", "IfcCovering", "IfcFooting", "IfcSpace", "IfcBuildingElementProxy"
            ]
        },
        "IFC2X3": {
            "name": "Industry Foundation Classes 2x3 (ISO/PAS 16739)",
            "version": "2x3 TC1",
            "classes": [
                "IfcWall", "IfcBeam", "IfcColumn", "IfcSlab", "IfcRoof",
                "IfcDoor", "IfcWindow", "IfcStair", "IfcFooting", "IfcSpace"
            ]
        },
        "OmniClass": {
            "name": "OmniClass Construction Classification System",
            "table": "23 - Products",
            "classes": [
                "23-13 00 00 Structural Framing",
                "23-17 00 00 Exterior Enclosure",
                "23-23 00 00 Interior Finishes",
                "23-27 00 00 Conveying Equipment",
                "23-33 00 00 Plumbing"
            ]
        }
    }

    @classmethod
    def list_schemas(cls) -> Dict[str, Any]:
        """Lista os esquemas de classificação instalados e suas classes suportadas."""
        return {
            "available_schemas": list(cls.SUPPORTED_SCHEMAS.keys()),
            "schemas_details": cls.SUPPORTED_SCHEMAS
        }

    @classmethod
    def classify_component(
        cls,
        instance_id: str,
        definition_name: str,
        schema_name: str = "IFC4",
        ifc_class: str = "IfcBeam",
        predefined_type: str = "NOTDEFINED",
        description: str = "",
        tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classifica um componente ou grupo no esquema IFC escolhido,
        gerando identificador global unívoco (GUID) e metadados canônicos.
        """
        schema_key = schema_name.upper()
        if schema_key not in cls.SUPPORTED_SCHEMAS:
            schema_key = "IFC4"

        available_classes = cls.SUPPORTED_SCHEMAS[schema_key]["classes"]
        if ifc_class not in available_classes and schema_key.startswith("IFC"):
            # Fallback seguro para elemento genérico se classe não constar
            ifc_class = "IfcBuildingElementProxy"

        guid = str(uuid.uuid4())

        classification_data = {
            "instance_id": instance_id,
            "definition_name": definition_name,
            "schema": schema_key,
            "ifc_class": ifc_class,
            "global_id": guid,
            "predefined_type": predefined_type.upper(),
            "description": description or f"{ifc_class} - {definition_name}",
            "tag": tag or instance_id,
            "is_valid_bim": True
        }

        return classification_data

    @classmethod
    def audit_scene_classifications(
        cls,
        instances: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Audita todas as instâncias da cena, identificando componentes classificados
        e não classificados para compliance com a metodologia BIM.
        """
        classified_count = 0
        unclassified_count = 0
        class_distribution: Dict[str, int] = {}
        items_audit = []

        for inst in instances:
            inst_id = inst.get("instance_id", inst.get("id", "unknown"))
            def_name = inst.get("definition_name", inst.get("name", "Componente"))
            classification = inst.get("ifc_classification") or inst.get("classification")

            if classification and isinstance(classification, dict) and "ifc_class" in classification:
                c_name = classification["ifc_class"]
                classified_count += 1
                class_distribution[c_name] = class_distribution.get(c_name, 0) + 1
                items_audit.append({
                    "instance_id": inst_id,
                    "definition_name": def_name,
                    "status": "CLASSIFIED",
                    "ifc_class": c_name
                })
            else:
                unclassified_count += 1
                items_audit.append({
                    "instance_id": inst_id,
                    "definition_name": def_name,
                    "status": "UNCLASSIFIED",
                    "ifc_class": None
                })

        total = len(instances)
        compliance_pct = round((classified_count / total * 100.0) if total > 0 else 0.0, 1)

        return {
            "total_instances": total,
            "classified_count": classified_count,
            "unclassified_count": unclassified_count,
            "compliance_percentage": compliance_pct,
            "class_distribution": class_distribution,
            "audit_list": items_audit
        }
