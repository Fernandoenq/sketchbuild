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

# SUEntityRef -- handle "base" generico (model/entity.h). Todo "Ref"
# especifico (SUComponentInstanceRef, SUFaceRef, ...) pode virar um
# SUEntityRef via uma funcao `SU<Tipo>ToEntity` -- confirmado via REA/
# Ghidra (27/10/2026, catalogacao do menu Editar, ver REVERSE_ENGINEERING_
# NOTES.md secao 26) que SUComponentInstanceToEntity (0x180008616) e um
# passthrough puro (`return param_1;`), ou seja, so reinterpreta o mesmo
# ponteiro -- os dois Refs tem byte-a-byte o mesmo layout, como todos os
# outros. Usado por SUEntitiesErase (exclusao real de instancia/entidade).
SUEntityRef = make_ref_struct("SUEntityRef")

# SUGeometryInputRef/SULoopInputRef -- handles de CRIACAO de geometria nova
# (model/geometry_input.h), diferentes dos Refs de leitura acima: sao
# "builders" temporarios (preenchidos em memoria, depois consumidos por
# SUEntitiesFill) -- nao apontam pra entidades ja existentes no modelo.
# Confirmado via REA/Ghidra (27/10/2026, menu Desenho > Formas > Retangulo,
# ver REVERSE_ENGINEERING_NOTES.md secao 28) que SUGeometryInputCreate/
# SUGeometryInputAddVertex/SULoopInputCreate/SULoopInputAddVertexIndex/
# SUGeometryInputAddFace/SUEntitiesFill sao exports publicos reais da DLL,
# com corpo nao-trivial (nao stubs) -- mesma familia documentada
# publicamente pelo SDK da Trimble.
SUGeometryInputRef = make_ref_struct("SUGeometryInputRef")
SULoopInputRef = make_ref_struct("SULoopInputRef")

# SUMaterialRef/SUDrawingElementRef -- material.h/drawing_element.h.
# Confirmado via REA/Ghidra (28/10/2026, Ferramentas > Pintura, ver
# REVERSE_ENGINEERING_NOTES.md secao 28) que SUMaterialCreate/
# SUMaterialSetColor/SUMaterialRelease/SUComponentInstanceToDrawingElement/
# SUDrawingElementSetMaterial sao exports publicos reais (pseudocodigo
# real batendo com o SDK publico documentado pela Trimble) -- permitem
# criar um material novo com cor RGBA customizada e aplica-lo numa
# instancia real do modelo. SUDrawingElementRef e outro "Ref generico"
# como SUEntityRef (mesmo layout binario, so reinterpretacao).
SUMaterialRef = make_ref_struct("SUMaterialRef")
SUDrawingElementRef = make_ref_struct("SUDrawingElementRef")

# SUGroupRef/SULayerRef -- model/group.h e model/layer.h. Confirmados via
# REA/Ghidra (28/10/2026, Grupos/Etiqueta, ver REVERSE_ENGINEERING_NOTES.md
# secao 28.17) como exports publicos reais da SketchUpAPI.dll (pseudocodigo
# real batendo com o SDK documentado pela Trimble) -- a UI chama "Etiqueta"
# o que a API interna ainda chama de "Layer" (nome legado da Trimble).
# SUGroupRef e um "ComponentInstance especial" por baixo (confirmado via
# RTTI dynamic_cast real no corpo de SUGroupCreate) -- SUGroupToComponentInstance
# converte (mesmo padrao passthrough de SUComponentInstanceToEntity/
# ToDrawingElement).
SUGroupRef = make_ref_struct("SUGroupRef")
SULayerRef = make_ref_struct("SULayerRef")

# SUSceneRef -- model/scene.h. Confirmado via REA/Ghidra (28/10/2026,
# menu Janela > Bandeja padrao > Cenas, ver REVERSE_ENGINEERING_NOTES.md
# secao 28.20) como export publico real: SUSceneCreate (alocador padrao),
# SUSceneSetName/SUSceneGetName, SUModelAddScenes (array, mesmo padrao de
# SUModelAddLayers), SUSceneActivate, SUModelGetScenes/SUModelGetNumScenes/
# SUModelGetActiveScene. A API Ruby do SketchUp chama o mesmo objeto de
# "Page" (Sketchup::Page) -- e o mesmo dado, dois nomes diferentes
# dependendo da API (C vs Ruby).
SUSceneRef = make_ref_struct("SUSceneRef")

# SUAxesRef -- model/axes.h. Confirmado via REA/Ghidra (28/10/2026, menu
# Ferramentas > Eixos, ver REVERSE_ENGINEERING_NOTES.md secao 28.21):
# SUAxesCreateCustom(SUAxesRef*, SUPoint3D* origin, SUVector3D* xaxis,
# SUVector3D* yaxis, SUVector3D* zaxis) -- pseudocodigo real confirmou os
# 5 parametros batendo com o SDK publico documentado pela Trimble, com
# validacao real de ortogonalidade entre os 3 eixos (retorna
# SU_ERROR_GENERIC=6 se nao-ortogonais -- por isso a base e sempre
# recomposta via Gram-Schmidt em core/mesh_extractor.py antes da chamada,
# nunca manda os vetores clicados crus). SUComponentDefinitionSetAxes
# aplica os eixos customizados na definicao de um Grupo/Componente (so
# ai existe um "set" no SDK publico -- nao ha SUModelSetAxes pra mudar
# os eixos do modelo raiz, so SUModelGetAxes de leitura).
SUAxesRef = make_ref_struct("SUAxesRef")

# SUCameraRef -- model/camera.h. Confirmado via REA/Ghidra (28/10/2026,
# câmera da Bandeja padrão errada ao abrir/criar modelo, ver
# REVERSE_ENGINEERING_NOTES.md seção 28.23): SUModelGetCamera devolve um
# ponteiro INTERNO pra dentro do SUModelRef (não precisa de release, mesmo
# padrão de "ref emprestada" já visto nesse SDK), SUCameraGetOrientation
# devolve eye/target/up (3x SUPoint3D/SUVector3D = 9 doubles, confirmado
# lendo os offsets reais da struct), SUCameraGetPerspective/
# GetPerspectiveFrustumFOV/GetFOVIsHeight/GetAspectRatio lêem os campos de
# projeção (FOV devolve SU_ERROR_NO_DATA=9 se a câmera não for perspectiva;
# aspect ratio devolve NO_DATA se for "automático", caso comum).
SUCameraRef = make_ref_struct("SUCameraRef")
SUSectionPlaneRef = make_ref_struct("SUSectionPlaneRef")
SUGuideLineRef = make_ref_struct("SUGuideLineRef")
SUGuidePointRef = make_ref_struct("SUGuidePointRef")


class SUColor(ctypes.Structure):
    """model/color.h -- RGBA, 1 byte por canal (0-255)."""

    _fields_ = [
        ("red", ctypes.c_ubyte),
        ("green", ctypes.c_ubyte),
        ("blue", ctypes.c_ubyte),
        ("alpha", ctypes.c_ubyte),
    ]


class SUPoint3D(ctypes.Structure):
    """model/geometry.h -- ponto 3D em coordenadas do modelo (metros, double)."""

    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]


class SUVector3D(ctypes.Structure):
    """model/geometry.h -- vetor 3D (ex.: normal de vertice)."""

    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]


class SUPlane3D(ctypes.Structure):
    """model/geometry.h -- plano 3D (equação analítica a*x + b*y + c*z + d = 0)."""

    _fields_ = [("a", ctypes.c_double), ("b", ctypes.c_double), ("c", ctypes.c_double), ("d", ctypes.c_double)]


class SUTransformation(ctypes.Structure):
    """model/transformation.h -- matriz 4x4 column-major (mesma convencao do
    Three.js `Matrix4.fromArray`, sem transposicao necessaria)."""

    _fields_ = [("values", ctypes.c_double * 16)]


class SUComponentBehavior(ctypes.Structure):
    """model/behavior.h -- layout de 16 bytes. offset 0 (component_type) e
    os 8 bytes finais (offset 8..15, NAO documentados no SDK publico)
    confirmados via REA/Ghidra (SUComponentDefinitionGetBehavior,
    27/10/2026). A ORDEM dos 3 bools (offset 4/5/6) foi inicialmente
    deduzida errado a partir so do pseudocodigo (component_cuts_opening e
    calculado via chamada de funcao, nao lido direto do objeto, o que
    sugeria erradamente ser o primeiro) -- CORRIGIDA e confirmada
    empiricamente comparando com `ComponentDefinition#behavior` via
    Console Ruby do SketchUp 2026 rodando de verdade (`[always_face_
    camera?, shadows_face_sun?, cuts_opening?] == [true, true, false]`
    pro componente "Sree" do template Simples/Metros)."""

    _fields_ = [
        ("component_type", ctypes.c_int32),  # enum SUComponentType (glue-to)
        ("component_cuts_opening", ctypes.c_bool),
        ("component_always_face_camera", ctypes.c_bool),
        ("component_shadows_face_sun", ctypes.c_bool),
        ("_padding", ctypes.c_uint8),
        ("_reserved", ctypes.c_int64),  # nao documentado no SDK publico
    ]
