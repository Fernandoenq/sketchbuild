"""
Tipos base da C API pública da Trimble (SketchUpAPI.dll).

Referência: SDK público da Trimble (slapi / SketchUp C API), headers
`SketchUpAPI/common.h`, `SketchUpAPI/model/model.h`. Esta API é
documentada oficialmente pela Trimble para desenvolvedores de extensão
-- não é uma API privada nem protegida pelo `tools.susig`.

Todos os "Ref" da API são handles opacos: uma struct com um único
ponteiro `void*` interno (`ptr`). O SDK C real usa macros para gerar um
tipo por entidade (SUModelRef, SUEntitiesRef, ...), mas em ctypes todos
têm o mesmo layout binário, então definimos uma fábrica genérica.
"""

import ctypes


# SU_RESULT: enum C (int de 4 bytes). 0 = SU_ERROR_NONE (sucesso).
SU_RESULT = ctypes.c_int

SU_ERROR_NONE = 0
# Demais códigos de erro do SDK público (common.h) — mapeados conforme
# necessário à medida que os testamos; não decodificados via Ghidra,
# vêm da documentação pública do SDK.
SU_ERRORS = {
    0: "SU_ERROR_NONE",
    1: "SU_ERROR_NULL_POINTER_INPUT",
    2: "SU_ERROR_INVALID_INPUT",
    3: "SU_ERROR_NULL_POINTER_OUTPUT",
    4: "SU_ERROR_INVALID_OUTPUT",
    5: "SU_ERROR_OVERWRITE_VALID",
    6: "SU_ERROR_GENERIC",
    7: "SU_ERROR_SERIALIZATION",
    8: "SU_ERROR_OUT_OF_RANGE",
    9: "SU_ERROR_NO_DATA",
    10: "SU_ERROR_INSUFFICIENT_SIZE",
    11: "SU_ERROR_UNKNOWN_EXCEPTION",
    12: "SU_ERROR_MODEL_INVALID",
    13: "SU_ERROR_MODEL_VERSION",
    14: "SU_ERROR_LAYER_LOCKED",
    15: "SU_ERROR_DUPLICATE",
    16: "SU_ERROR_PARTIAL_SUCCESS",
    17: "SU_ERROR_UNSUPPORTED",
    18: "SU_ERROR_INVALID_ARGUMENT",
}


def su_check(result: int, call_name: str) -> None:
    """Levanta exceção se o SU_RESULT não for SU_ERROR_NONE."""
    if result != SU_ERROR_NONE:
        nome = SU_ERRORS.get(result, f"codigo_desconhecido_{result}")
        raise RuntimeError(f"{call_name} falhou: {nome} ({result})")


def make_ref_struct(nome: str):
    """Cria uma struct ctypes opaca equivalente a um `SU<Entidade>Ref`."""
    return type(nome, (ctypes.Structure,), {"_fields_": [("ptr", ctypes.c_void_p)]})


SUModelRef = make_ref_struct("SUModelRef")
SUEntitiesRef = make_ref_struct("SUEntitiesRef")
SUComponentDefinitionRef = make_ref_struct("SUComponentDefinitionRef")
SUFaceRef = make_ref_struct("SUFaceRef")
SUComponentInstanceRef = make_ref_struct("SUComponentInstanceRef")
SUMeshHelperRef = make_ref_struct("SUMeshHelperRef")
SUStringRef = make_ref_struct("SUStringRef")


class SUPoint3D(ctypes.Structure):
    """model/geometry.h -- ponto 3D em coordenadas do modelo (metros, double)."""

    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]


class SUVector3D(ctypes.Structure):
    """model/geometry.h -- vetor 3D (ex.: normal de vertice)."""

    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]


class SUTransformation(ctypes.Structure):
    """model/transformation.h -- matriz 4x4 column-major (mesma convencao do
    Three.js `Matrix4.fromArray`, sem transposicao necessaria)."""

    _fields_ = [("values", ctypes.c_double * 16)]
