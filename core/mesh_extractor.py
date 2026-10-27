"""
Percorre a arvore Model -> Entities -> {Faces, ComponentInstances} de um
.skp ja aberto (via core.su_api.SketchUpAPI/SketchUpModel) e monta o DTO
consumido pelo visualizador 3D (Three.js):

    {
        "definitions": [{"definition_id", "name", "vertices", "normals", "indices"}, ...],
        "instances":   [{"instance_id", "definition_id", "transform"}, ...],
    }

"definitions" tem a geometria uma unica vez por definicao (deduplicada --
uma definicao pode aparecer em N instancias). "instances" tem uma entrada
por ocorrencia real na arvore (nao deduplicado), com a matriz 4x4 ja
composta em espaco de mundo (coluna-major, consumivel direto por
`Matrix4.fromArray()` no Three.js, sem transposicao).

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


def _build_definition_mesh(api, entities) -> dict:
    """Acumula vertices/normals/indices de todas as faces diretas de um
    Entities, ajustando o offset dos indices por face."""
    vertices: list[float] = []
    normals: list[float] = []
    indices: list[int] = []

    for face in api.get_faces(entities):
        face_mesh = api.build_face_mesh(face)
        base = len(vertices) // 3
        vertices.extend(face_mesh["vertices"])
        normals.extend(face_mesh["normals"])
        indices.extend(i + base for i in face_mesh["indices"])

    return {"vertices": vertices, "normals": normals, "indices": indices}


def _collect_definition(api, entities, def_id: str, name: str, definitions: dict) -> None:
    if def_id in definitions:
        return
    mesh = _build_definition_mesh(api, entities)
    definitions[def_id] = {"definition_id": def_id, "name": name, **mesh}


def _walk_instances(
    api,
    entities,
    parent_world: list[float],
    definitions: dict,
    instances: list,
    seen_defs: set,
    registry: dict,
) -> None:
    for instance in api.get_instances(entities):
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
            }
        )
        registry[instance_id] = {"ref": instance, "parent_world": list(parent_world)}

        def_entities = api.get_definition_entities(definition)
        if def_id not in seen_defs:
            seen_defs.add(def_id)
            name = api.get_definition_name(definition) or def_id
            _collect_definition(api, def_entities, def_id, name, definitions)

        _walk_instances(api, def_entities, world, definitions, instances, seen_defs, registry)


def extract_scene_with_registry(api, model) -> tuple[dict, dict]:
    """Devolve (dto, registry). `registry` so e util enquanto o `model`
    continuar aberto (os SUComponentInstanceRef guardados nele apontam
    pra objetos vivos dentro do SUModelRef aberto) -- ver
    app/repositories/skp_engine_repository.py / SceneSession."""
    root_entities = model.get_entities()

    definitions: dict[str, dict] = {}
    instances: list[dict] = []
    registry: dict[str, dict] = {}

    _collect_definition(api, root_entities, "root", "root", definitions)
    instances.append(
        {"instance_id": "inst_root", "definition_id": "root", "transform": list(IDENTITY_4X4)}
    )
    registry["inst_root"] = {"ref": None, "parent_world": list(IDENTITY_4X4)}

    _walk_instances(
        api, root_entities, list(IDENTITY_4X4), definitions, instances, {"root"}, registry
    )

    dto = {"definitions": list(definitions.values()), "instances": instances}
    return dto, registry


def extract_scene(api, model) -> dict:
    """Devolve so o DTO {"definitions": [...], "instances": [...]} --
    atalho pra quando o registry de edicao nao e necessario (ex.: CLI
    standalone em main.py)."""
    dto, _registry = extract_scene_with_registry(api, model)
    return dto
