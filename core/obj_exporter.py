"""
Exportador OBJ standalone -- equivalente parcial do menu
"Arquivo > Exportar > Modelo 3D..." do SketchUp real (ver
REVERSE_ENGINEERING_NOTES.md secao 26).

A SketchUpAPI.dll (o SDK publico que o resto deste projeto usa via
core/su_api.py) NAO exporta nenhuma funcao `*Export*` -- confirmado via
REA/Ghidra (search_procedures "Export" contra o binario real devolveu
zero resultados). Os exportadores de OBJ/DAE/FBX/3DS/... do SketchUp real
sao implementados dentro do proprio SketchUp.exe (nao na DLL publica do
SDK), entao nao tem como reusar uma funcao nativa aqui -- escrevemos o
OBJ nos mesmos, a partir do DTO que ja extraimos (core/mesh_extractor.py).

So malha (vertices + normais + faces triangulares) -- sem UV/textura
(o pipeline atual nao extrai coordenadas de UV de nenhuma face ainda).
"""

from __future__ import annotations

INCHES_TO_METERS = 0.0254


def _transform_point(m: list[float], x: float, y: float, z: float) -> tuple[float, float, float]:
    """Aplica uma matriz 4x4 column-major (translacao inclusa) a um ponto."""
    return (
        m[0] * x + m[4] * y + m[8] * z + m[12],
        m[1] * x + m[5] * y + m[9] * z + m[13],
        m[2] * x + m[6] * y + m[10] * z + m[14],
    )


def _transform_normal(m: list[float], x: float, y: float, z: float) -> tuple[float, float, float]:
    """Aplica so o bloco linear 3x3 (sem translacao) -- suficiente pra
    rotacao+escala uniforme; nao usa a inversa-transposta porque os
    templates/instancias deste projeto nao tem escala nao-uniforme
    conhecida nas normais (mesma limitacao aceita no restante do app)."""
    nx = m[0] * x + m[4] * y + m[8] * z
    ny = m[1] * x + m[5] * y + m[9] * z
    nz = m[2] * x + m[6] * y + m[10] * z
    length = (nx * nx + ny * ny + nz * nz) ** 0.5
    if length < 1e-12:
        return (0.0, 0.0, 1.0)
    return (nx / length, ny / length, nz / length)


def write_obj(dto: dict, file_path: str) -> None:
    """Escreve um .obj combinando TODAS as instancias (malha ja expandida
    em espaco de mundo, convertida de polegadas pra metros -- mesma
    unidade usada pelo visualizador Three.js). Uma instancia sem
    geometria propria (ex.: "inst_root") e pulada."""
    definitions_by_id = {d["definition_id"]: d for d in dto["definitions"]}

    lines: list[str] = [
        "# Exportado pelo SketchBuild (sketchup_companion) -- ver",
        "# REVERSE_ENGINEERING_NOTES.md secao 26 (Arquivo > Exportar > Modelo 3D)",
        "# Unidade: metros",
    ]
    vertex_offset = 0

    for instance in dto["instances"]:
        definition = definitions_by_id.get(instance["definition_id"])
        if definition is None or not definition["vertices"]:
            continue

        transform = instance["transform"]
        vertices = definition["vertices"]
        normals = definition["normals"]
        indices = definition["indices"]
        num_vertices = len(vertices) // 3

        safe_name = (definition["name"] or "objeto").replace(" ", "_")
        lines.append(f"o {safe_name}_{instance['instance_id']}")

        for i in range(num_vertices):
            x, y, z = vertices[i * 3 : i * 3 + 3]
            wx, wy, wz = _transform_point(transform, x, y, z)
            lines.append(
                f"v {wx * INCHES_TO_METERS:.6f} {wy * INCHES_TO_METERS:.6f} {wz * INCHES_TO_METERS:.6f}"
            )

        has_normals = len(normals) == len(vertices)
        if has_normals:
            for i in range(num_vertices):
                nx, ny, nz = normals[i * 3 : i * 3 + 3]
                wnx, wny, wnz = _transform_normal(transform, nx, ny, nz)
                lines.append(f"vn {wnx:.6f} {wny:.6f} {wnz:.6f}")

        for i in range(0, len(indices), 3):
            a, b, c = (idx + vertex_offset + 1 for idx in indices[i : i + 3])
            if has_normals:
                lines.append(f"f {a}//{a} {b}//{b} {c}//{c}")
            else:
                lines.append(f"f {a} {b} {c}")

        vertex_offset += num_vertices

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
