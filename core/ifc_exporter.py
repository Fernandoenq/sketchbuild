import os
import uuid
import datetime
from typing import Dict, Any, List, Optional


class IfcExporter:
    """Compilador nativo IFC4 / IFC2X3 (STEP ISO 10303-21) a partir de modelos .skp (Zero DLL).
    
    Serializa a topologia B-Rep, hierarquia espacial BIM (IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey)
    e injeta dicionários de atributos e metadados analíticos como IfcPropertySet / IfcPropertySingleValue.
    """

    INCHES_TO_METERS = 0.0254

    @classmethod
    def _create_guid(cls) -> str:
        """Gera um GUID base64/alfanumérico de 22 caracteres no formato padrão do IFC."""
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
        u = uuid.uuid4().hex
        num = int(u, 16)
        res = []
        for _ in range(22):
            res.append(chars[num % 64])
            num //= 64
        return "".join(reversed(res))

    @classmethod
    def export_from_scene_data(cls, scene_data: Dict[str, Any], output_path: str, project_name: str = "Projeto SketchBuild") -> Dict[str, Any]:
        """Exporta a cena para um arquivo STEP ISO 10303-21 (.ifc)."""
        definitions = scene_data.get("definitions", [])
        instances = scene_data.get("instances", [])
        
        lines = []
        entity_id = 1

        def alloc_id() -> int:
            nonlocal entity_id
            curr = entity_id
            entity_id += 1
            return curr

        now_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # 1. Header do STEP
        header_text = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('{os.path.basename(output_path)}','{now_str}',('SketchBuild Architect'),('Fernando'),'SketchBuild Native IFC Engine 2.0 (Zero DLL)','SketchBuild','None');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;"""
        lines.append(header_text)

        # 2. Infraestrutura Básica (Unidades, Contextos, Origens)
        # OwnerHistory
        id_person = alloc_id()
        lines.append(f"#{id_person}=IFCPERSON($,'Fernando',$,$,$,$,$,$);")
        id_org = alloc_id()
        lines.append(f"#{id_org}=IFCORGANIZATION($,'SketchBuild',$,$,$);")
        id_person_org = alloc_id()
        lines.append(f"#{id_person_org}=IFCPERSONANDORGANIZATION(#{id_person},#{id_org},$);")
        id_app = alloc_id()
        lines.append(f"#{id_app}=IFCAPPLICATION(#{id_org},'2.0','SketchBuild Engine','SketchBuild');")
        id_history = alloc_id()
        lines.append(f"#{id_history}=IFCOWNERHISTORY(#{id_person_org},#{id_app},.READWRITE.,.NOTDEFINED.,$,$,$,{int(datetime.datetime.now().timestamp())});")

        # Unidades: Metros, Graus, Segundos
        id_length_unit = alloc_id()
        lines.append(f"#{id_length_unit}=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);")
        id_angle_unit = alloc_id()
        lines.append(f"#{id_angle_unit}=IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.);")
        id_units = alloc_id()
        lines.append(f"#{id_units}=IFCUNITASSIGNMENT((#{id_length_unit},#{id_angle_unit}));")

        # Origens e Direções
        id_origin_pt = alloc_id()
        lines.append(f"#{id_origin_pt}=IFCCARTESIANPOINT((0.,0.,0.));")
        id_dir_z = alloc_id()
        lines.append(f"#{id_dir_z}=IFCDIRECTION((0.,0.,1.));")
        id_dir_x = alloc_id()
        lines.append(f"#{id_dir_x}=IFCDIRECTION((1.,0.,0.));")
        id_placement_wcs = alloc_id()
        lines.append(f"#{id_placement_wcs}=IFCAXIS2PLACEMENT3D(#{id_origin_pt},#{id_dir_z},#{id_dir_x});")

        # Contexto Geométrico do Modelo
        id_context = alloc_id()
        lines.append(f"#{id_context}=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#{id_placement_wcs},$);")

        # Projeto, Site, Edifício, Pavimento
        guid_proj = cls._create_guid()
        id_project = alloc_id()
        lines.append(f"#{id_project}=IFCPROJECT('{guid_proj}',#{id_history},'{project_name}',$,$,$,$,(#{id_context}),#{id_units});")

        guid_site = cls._create_guid()
        id_site = alloc_id()
        id_site_placement = alloc_id()
        lines.append(f"#{id_site_placement}=IFCLOCALPLACEMENT($,#{id_placement_wcs});")
        lines.append(f"#{id_site}=IFCSITE('{guid_site}',#{id_history},'Terreno Principal',$,$,#{id_site_placement},$,$,.ELEMENT.,$,$,$,$,$);")

        guid_bldg = cls._create_guid()
        id_bldg = alloc_id()
        id_bldg_placement = alloc_id()
        lines.append(f"#{id_bldg_placement}=IFCLOCALPLACEMENT(#{id_site_placement},#{id_placement_wcs});")
        lines.append(f"#{id_bldg}=IFCBUILDING('{guid_bldg}',#{id_history},'Edificação Modelo',$,$,#{id_bldg_placement},$,$,.ELEMENT.,$,$,$);")

        guid_storey = cls._create_guid()
        id_storey = alloc_id()
        id_storey_placement = alloc_id()
        lines.append(f"#{id_storey_placement}=IFCLOCALPLACEMENT(#{id_bldg_placement},#{id_placement_wcs});")
        lines.append(f"#{id_storey}=IFCBUILDINGSTOREY('{guid_storey}',#{id_history},'Pavimento Térreo',$,$,#{id_storey_placement},$,$,.ELEMENT.,0.);")

        # Agregações: Project -> Site -> Building -> Storey
        id_rel_agg1 = alloc_id()
        lines.append(f"#{id_rel_agg1}=IFCRELAGGREGATES('{cls._create_guid()}',#{id_history},$,$,#{id_project},(#{id_site}));")
        id_rel_agg2 = alloc_id()
        lines.append(f"#{id_rel_agg2}=IFCRELAGGREGATES('{cls._create_guid()}',#{id_history},$,$,#{id_site},(#{id_bldg}));")
        id_rel_agg3 = alloc_id()
        lines.append(f"#{id_rel_agg3}=IFCRELAGGREGATES('{cls._create_guid()}',#{id_history},$,$,#{id_bldg},(#{id_storey}));")

        # 3. Processamento de Geometrias e Definições
        def_brep_map = {}
        for d in definitions:
            def_id = d.get("definition_id")
            raw_verts = d.get("vertices", [])
            indices = d.get("indices", [])
            if not raw_verts or not indices:
                continue

            num_verts = len(raw_verts) // 3
            # Cria pontos cartesianos IFCCARTESIANPOINT em metros (Z-up original do SketchUp)
            pt_ids = []
            for i in range(num_verts):
                vx = round(raw_verts[i * 3] * cls.INCHES_TO_METERS, 5)
                vy = round(raw_verts[i * 3 + 1] * cls.INCHES_TO_METERS, 5)
                vz = round(raw_verts[i * 3 + 2] * cls.INCHES_TO_METERS, 5)
                pid = alloc_id()
                lines.append(f"#{pid}=IFCCARTESIANPOINT(({vx},{vy},{vz}));")
                pt_ids.append(pid)

            # Faces e Loops (IFCFACE / IFCPOLYLOOP)
            face_ids = []
            for tri_i in range(0, len(indices), 3):
                if tri_i + 2 < len(indices):
                    i0, i1, i2 = indices[tri_i], indices[tri_i + 1], indices[tri_i + 2]
                    loop_id = alloc_id()
                    lines.append(f"#{loop_id}=IFCPOLYLOOP((#{pt_ids[i0]},#{pt_ids[i1]},#{pt_ids[i2]}));")
                    bound_id = alloc_id()
                    lines.append(f"#{bound_id}=IFCFACEOUTERBOUND(#{loop_id},.T.);")
                    face_id = alloc_id()
                    lines.append(f"#{face_id}=IFCFACE((#{bound_id}));")
                    face_ids.append(face_id)

            if face_ids:
                shell_id = alloc_id()
                face_refs_str = ",".join(f"#{fid}" for fid in face_ids)
                lines.append(f"#{shell_id}=IFCCLOSEDSHELL(({face_refs_str}));")
                brep_id = alloc_id()
                lines.append(f"#{brep_id}=IFCFACETEDBREP(#{shell_id});")
                def_brep_map[def_id] = brep_id

        # 4. Processamento de Instâncias e Elementos BIM (IfcBuildingElementProxy)
        element_ids = []
        if instances:
            for inst in instances:
                did = inst.get("definition_id")
                brep_id = def_brep_map.get(did)
                if brep_id is None:
                    continue

                m = inst.get("transform", [
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1,
                ])
                tx = round(m[12] * cls.INCHES_TO_METERS, 5)
                ty = round(m[13] * cls.INCHES_TO_METERS, 5)
                tz = round(m[14] * cls.INCHES_TO_METERS, 5)

                # Local Placement da instância
                p_origin = alloc_id()
                lines.append(f"#{p_origin}=IFCCARTESIANPOINT(({tx},{ty},{tz}));")
                p_axis = alloc_id()
                lines.append(f"#{p_axis}=IFCAXIS2PLACEMENT3D(#{p_origin},#{id_dir_z},#{id_dir_x});")
                inst_placement = alloc_id()
                lines.append(f"#{inst_placement}=IFCLOCALPLACEMENT(#{id_storey_placement},#{p_axis});")

                # Representação Geométrica
                shape_rep = alloc_id()
                lines.append(f"#{shape_rep}=IFCSHAPEREPRESENTATION(#{id_context},'Body','Brep',(#{brep_id}));")
                product_def_shape = alloc_id()
                lines.append(f"#{product_def_shape}=IFCPRODUCTDEFINITIONSHAPE($,$,(#{shape_rep}));")

                elem_name = inst.get("name") or "Componente BIM"
                elem_id = alloc_id()
                elem_guid = cls._create_guid()
                lines.append(f"#{elem_id}=IFCBUILDINGELEMENTPROXY('{elem_guid}',#{id_history},'{elem_name}',$,$,#{inst_placement},#{product_def_shape},$,$);")
                element_ids.append(elem_id)

                # Dicionários de Atributos BIM (Frente 12 -> IfcPropertySet)
                attrs = inst.get("attributes", {})
                for dict_name, dict_vals in attrs.items():
                    if isinstance(dict_vals, dict) and dict_vals:
                        prop_ids = []
                        for k, v in dict_vals.items():
                            val_str = str(v)
                            pr_id = alloc_id()
                            lines.append(f"#{pr_id}=IFCPROPERTYSINGLEVALUE('{k}',$,IFCTEXT('{val_str}'),$);")
                            prop_ids.append(pr_id)

                        pset_id = alloc_id()
                        pset_guid = cls._create_guid()
                        props_ref = ",".join(f"#{pid}" for pid in prop_ids)
                        lines.append(f"#{pset_id}=IFCPROPERTYSET('{pset_guid}',#{id_history},'{dict_name}',$,({props_ref}));")
                        rel_prop_id = alloc_id()
                        lines.append(f"#{rel_prop_id}=IFCRELDEFINESBYPROPERTIES('{cls._create_guid()}',#{id_history},$,$,(#{elem_id}),#{pset_id});")
        else:
            # Modelo sem instâncias explícitas: exporta cada definição diretamente
            for def_id, brep_id in def_brep_map.items():
                inst_placement = alloc_id()
                lines.append(f"#{inst_placement}=IFCLOCALPLACEMENT(#{id_storey_placement},#{id_placement_wcs});")
                shape_rep = alloc_id()
                lines.append(f"#{shape_rep}=IFCSHAPEREPRESENTATION(#{id_context},'Body','Brep',(#{brep_id}));")
                product_def_shape = alloc_id()
                lines.append(f"#{product_def_shape}=IFCPRODUCTDEFINITIONSHAPE($,$,(#{shape_rep}));")

                elem_id = alloc_id()
                elem_guid = cls._create_guid()
                lines.append(f"#{elem_id}=IFCBUILDINGELEMENTPROXY('{elem_guid}',#{id_history},'Entidade Geometria',$,$,#{inst_placement},#{product_def_shape},$,$);")
                element_ids.append(elem_id)

        # 5. Relacionamento Espacial: Containment em IfcBuildingStorey
        if element_ids:
            rel_contained = alloc_id()
            elems_str = ",".join(f"#{eid}" for eid in element_ids)
            lines.append(f"#{rel_contained}=IFCRELCONTAINEDINSPATIALSTRUCTURE('{cls._create_guid()}',#{id_history},'Spatial Containment',$,({elems_str}),#{id_storey});")

        lines.append("ENDSEC;")
        lines.append("END-ISO-10303-21;")

        content = "\n".join(lines) + "\n"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "output_path": output_path,
            "file_size_bytes": len(content.encode("utf-8")),
            "elements_count": len(element_ids),
            "format": "Industry Foundation Classes (IFC4 STEP)",
        }
