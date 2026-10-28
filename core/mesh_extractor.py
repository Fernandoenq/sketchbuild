"""
Percorre a arvore Model -> Entities -> {Faces, ComponentInstances} de um
.skp ja aberto (via core.su_api.SketchUpAPI/SketchUpModel) e monta o DTO
consumido pelo visualizador 3D (Three.js):

    {
        "definitions": [{"definition_id", "name", "vertices", "normals", "indices"}, ...],
        "instances":   [{"instance_id", "definition_id", "transform", "parent_instance_id"}, ...],
    }

"definitions" tem a geometria uma unica vez por definicao (deduplicada --
uma definicao pode aparecer em N instancias). "instances" tem uma entrada
por ocorrencia real na arvore (nao deduplicado), com a matriz 4x4 ja
composta em espaco de mundo (coluna-major, consumivel direto por
`Matrix4.fromArray()` no Three.js, sem transposicao).

"parent_instance_id" preserva a hierarquia da arvore original (quem esta
aninhado dentro de quem) mesmo com a lista sendo plana -- usado pelo
Outliner do frontend (Fase 4) pra remontar a arvore client-side sem mudar
o formato que o sceneBuilder.js ja consome. "inst_root" (pseudo-instancia
sintetica que representa o Entities raiz do Model) tem
`parent_instance_id: null`; os filhos diretos do modelo tem
`parent_instance_id: "inst_root"`.

`extract_scene_with_registry()` tambem devolve um "registry" -- mapa
instance_id -> {"ref": SUComponentInstanceRef, "parent_world": [16 floats]}
-- usado pela edicao (seção 17/18 das notas): pra reescrever a transformacao
de uma instancia de volta na SketchUpAPI.dll, a chamada
SUComponentInstanceSetTransform espera a transformacao LOCAL (relativa ao
pai imediato), nao a mundial usada pro DTO -- por isso guardamos o
parent_world de cada instancia pra poder recalcular local = inverse(
parent_world) @ novo_world (ver invert_affine4()).

REQUER Python 3.12 (mesma regressao do ctypes do Python 3.14 -- ver
REVERSE_ENGINEERING_NOTES.md secao 15).
"""

from __future__ import annotations

IDENTITY_4X4 = [
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
]


def matmul4(a: list[float], b: list[float]) -> list[float]:
    """Multiplica duas matrizes 4x4 column-major: resultado = a @ b
    (world = parent_world @ local, convencao padrao de scene graph)."""
    c = [0.0] * 16
    for col in range(4):
        for row in range(4):
            c[col * 4 + row] = sum(a[k * 4 + row] * b[col * 4 + k] for k in range(4))
    return c


def invert_affine4(m: list[float]) -> list[float]:
    """Inverte uma matriz 4x4 afim column-major (ultima linha [0,0,0,1]
    implicita -- nao checada). Usa a formula fechada do cofator/adjugate
    pra inverter so o bloco linear 3x3 (rotacao+escala), e
    inversa_translacao = -InvL @ t -- evita puxar numpy so por isso."""
    a, d, g = m[0], m[1], m[2]
    b, e, h = m[4], m[5], m[6]
    c, f, i = m[8], m[9], m[10]
    tx, ty, tz = m[12], m[13], m[14]

    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        raise ValueError("matriz nao inversivel (determinante ~0)")
    inv_det = 1.0 / det

    inv00 = (e * i - f * h) * inv_det
    inv01 = (c * h - b * i) * inv_det
    inv02 = (b * f - c * e) * inv_det
    inv10 = (f * g - d * i) * inv_det
    inv11 = (a * i - c * g) * inv_det
    inv12 = (c * d - a * f) * inv_det
    inv20 = (d * h - e * g) * inv_det
    inv21 = (b * g - a * h) * inv_det
    inv22 = (a * e - b * d) * inv_det

    inv_tx = -(inv00 * tx + inv01 * ty + inv02 * tz)
    inv_ty = -(inv10 * tx + inv11 * ty + inv12 * tz)
    inv_tz = -(inv20 * tx + inv21 * ty + inv22 * tz)

    return [
        inv00, inv10, inv20, 0.0,
        inv01, inv11, inv21, 0.0,
        inv02, inv12, inv22, 0.0,
        inv_tx, inv_ty, inv_tz, 1.0,
    ]


def _build_definition_mesh(api, entities, faces_registry: dict) -> dict:
    """Acumula vertices/normals/indices de todas as faces diretas de um
    Entities, ajustando o offset dos indices por face. Tambem monta
    `face_ranges` (lista de {face_id, triangle_start, triangle_count},
    em unidade de TRIANGULO -- 3 indices cada) e preenche
    `faces_registry` (face_id -> SUFaceRef) por referencia, usado pra
    "Ferramentas > Pintura" por face (ver app/repositories/
    skp_engine_repository.py paint_face() e REVERSE_ENGINEERING_NOTES.md
    secao 28.19). `face_id` usa o mesmo padrao de `def_id`/`instance_id`
    ja usados neste arquivo: ponteiro bruto do Ref em hex, estavel
    enquanto o SUModelRef continuar aberto na sessao."""
    vertices: list[float] = []
    normals: list[float] = []
    indices: list[int] = []
    face_ranges: list[dict] = []

    for face in api.get_faces(entities):
        face_mesh = api.build_face_mesh(face)
        base = len(vertices) // 3
        triangle_start = len(indices) // 3
        vertices.extend(face_mesh["vertices"])
        normals.extend(face_mesh["normals"])
        indices.extend(i + base for i in face_mesh["indices"])
        triangle_count = len(face_mesh["indices"]) // 3
        if triangle_count:
            face_id = f"face_{face.ptr or 0:x}"
            face_ranges.append(
                {
                    "face_id": face_id,
                    "triangle_start": triangle_start,
                    "triangle_count": triangle_count,
                }
            )
            faces_registry[face_id] = face

    return {
        "vertices": vertices,
        "normals": normals,
        "indices": indices,
        "face_ranges": face_ranges,
    }


def _collect_definition(
    api, entities, definition_ref, def_id: str, name: str, definitions: dict, faces_registry: dict
) -> None:
    """`definition_ref` e o SUComponentDefinitionRef (None so pro pseudo-
    "root", que nao e um componente de verdade e portanto nunca "sempre
    de frente para a camera")."""
    if def_id in definitions:
        return
    mesh = _build_definition_mesh(api, entities, faces_registry)
    always_faces_camera = (
        api.get_definition_always_faces_camera(definition_ref)
        if definition_ref is not None
        else False
    )
    definitions[def_id] = {
        "definition_id": def_id,
        "name": name,
        "always_faces_camera": always_faces_camera,
        **mesh,
    }


def _walk_instances(
    api,
    entities,
    parent_world: list[float],
    definitions: dict,
    instances: list,
    seen_defs: set,
    registry: dict,
    faces_registry: dict,
    parent_instance_id: str | None = None,
) -> None:
    # Grupos sao uma colecao SEPARADA de ComponentInstances no SDK
    # (SUEntitiesGetGroups, nunca aparecem em SUEntitiesGetInstances) --
    # convertidos aqui via group_to_instance() (passthrough real,
    # confirmado via REA, ver REVERSE_ENGINEERING_NOTES.md secao 28.17)
    # pra reaproveitar o MESMO caminho de extracao/edicao ja existente,
    # sem duplicar logica -- um Grupo tem definicao/transform/entities
    # proprios, exatamente como uma instancia de componente comum.
    all_instances = list(api.get_instances(entities)) + [
        api.group_to_instance(group) for group in api.get_groups(entities)
    ]

    for instance in all_instances:
        definition = api.get_instance_definition(instance)
        def_id = f"def_{definition.ptr or 0:x}"
        local = api.get_instance_transform(instance)
        world = matmul4(parent_world, local)

        instance_id = f"inst_{len(instances)}"
        instances.append(
            {
                "instance_id": instance_id,
                "definition_id": def_id,
                "transform": world,
                "parent_instance_id": parent_instance_id,
            }
        )
        # `entities` aqui e o Entities DIRETO (pai) onde essa instancia
        # vive -- guardado pra permitir exclusao real via SUEntitiesErase
        # (precisa do Entities pai exato, nao qualquer um -- ver
        # core/su_api.py erase_instance() e REVERSE_ENGINEERING_NOTES.md
        # secao 26).
        registry[instance_id] = {
            "ref": instance,
            "parent_world": list(parent_world),
            "parent_entities": entities,
        }

        def_entities = api.get_definition_entities(definition)
        if def_id not in seen_defs:
            seen_defs.add(def_id)
            name = api.get_definition_name(definition) or def_id
            _collect_definition(
                api, def_entities, definition, def_id, name, definitions, faces_registry
            )

        _walk_instances(
            api,
            def_entities,
            world,
            definitions,
            instances,
            seen_defs,
            registry,
            faces_registry,
            instance_id,
        )


def extract_scene_with_registry(api, model) -> tuple[dict, dict, dict]:
    """Devolve (dto, registry, faces_registry). `registry`/`faces_registry`
    so sao uteis enquanto o `model` continuar aberto (os Refs guardados
    neles apontam pra objetos vivos dentro do SUModelRef aberto) -- ver
    app/repositories/skp_engine_repository.py / SceneSession.
    `faces_registry` mapeia face_id -> SUFaceRef (usado por
    paint_face(), ver REVERSE_ENGINEERING_NOTES.md secao 28.19)."""
    root_entities = model.get_entities()

    definitions: dict[str, dict] = {}
    instances: list[dict] = []
    registry: dict[str, dict] = {}
    faces_registry: dict[str, object] = {}

    _collect_definition(api, root_entities, None, "root", "root", definitions, faces_registry)
    instances.append(
        {
            "instance_id": "inst_root",
            "definition_id": "root",
            "transform": list(IDENTITY_4X4),
            "parent_instance_id": None,
        }
    )
    registry["inst_root"] = {
        "ref": None,
        "parent_world": list(IDENTITY_4X4),
        "parent_entities": None,
    }

    _walk_instances(
        api,
        root_entities,
        list(IDENTITY_4X4),
        definitions,
        instances,
        {"root"},
        registry,
        faces_registry,
        parent_instance_id="inst_root",
    )

    dto = {"definitions": list(definitions.values()), "instances": instances}
    return dto, registry, faces_registry


def extract_scene(api, model) -> dict:
    """Devolve so o DTO {"definitions": [...], "instances": [...]} --
    atalho pra quando o registry de edicao nao e necessario (ex.: CLI
    standalone em main.py)."""
    dto, _registry, _faces_registry = extract_scene_with_registry(api, model)
    return dto
