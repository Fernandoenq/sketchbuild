"""
Binding ctypes para a C API pública da Trimble (SketchUpAPI.dll).

Carrega a DLL oficial do SDK (instalada junto com o SketchUp Desktop,
não precisa do SketchUp.exe aberto) e expõe um subconjunto inicial de
funções com `argtypes`/`restype` configurados, para chamadas seguras.

Caminho padrão de instalação no Windows:
    C:\\Program Files\\SketchUp\\SketchUp 2026\\SketchUp\\SketchUpAPI.dll

Todas as funções `SU*` retornam `SU_RESULT` (c_int); usamos `su_check`
para converter falha em excecao Python.

REQUISITO DE RUNTIME -- Python 3.12 (ver REVERSE_ENGINEERING_NOTES.md
secao 15): o Python 3.14.3 tem uma regressao confirmada no modulo
`ctypes` (`_ctypes`/`python314.dll`) que crasha o processo
(STATUS_ACCESS_VIOLATION, dentro de `PyObject_IsInstance`, nunca
chegando a executar a chamada nativa) ao chamar
`SUModelCreateFromFileWithStatus`/`SUModelCreateFromBufferWithStatus`.
Confirmado via analise de crash dump (WinDbg) e reproducao ao vivo
(cdb.exe) contra a DLL real. O mesmo codigo, com os mesmos argumentos,
contra a mesma DLL, funciona perfeitamente no Python 3.12 -- a
SketchUpAPI.dll nunca teve nenhuma limitacao real.
"""

import sys
import warnings

import ctypes
import os

from core.su_types import (
    SUModelRef,
    SUEntitiesRef,
    SUComponentDefinitionRef,
    SUFaceRef,
    SUComponentInstanceRef,
    SUMeshHelperRef,
    SUStringRef,
    SUEntityRef,
    SUGeometryInputRef,
    SULoopInputRef,
    SUMaterialRef,
    SUDrawingElementRef,
    SUGroupRef,
    SULayerRef,
    SUSceneRef,
    SUAxesRef,
    SUCameraRef,
    SUColor,
    SUPoint3D,
    SUVector3D,
    SUTransformation,
    SUComponentBehavior,
    su_check,
)

DEFAULT_DLL_PATH = (
    r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\SketchUpAPI.dll"
)

if sys.version_info[:2] != (3, 12):
    warnings.warn(
        "sketchbuild foi validado com Python 3.12. O Python 3.14.3 "
        "tem uma regressao conhecida no ctypes que crasha o processo ao "
        "chamar SUModelCreateFromFileWithStatus/SUModelCreateFromBufferWithStatus "
        "(ver REVERSE_ENGINEERING_NOTES.md secao 15). Rode com `py -3.12`.",
        RuntimeWarning,
        stacklevel=2,
    )


class SketchUpAPI:
    """Wrapper fino sobre SketchUpAPI.dll via ctypes."""

    def __init__(self, dll_path: str = DEFAULT_DLL_PATH):
        if not os.path.isfile(dll_path):
            raise FileNotFoundError(
                f"SketchUpAPI.dll nao encontrada em: {dll_path}"
            )
        # Usa WinDLL (sem necessidade de stdcall explicito no x64, mas
        # mantem explicito o carregamento via API do Windows/CRT).
        self._dll = ctypes.WinDLL(dll_path)
        self._bind_prototypes()
        self._initialized = False

    def _bind_prototypes(self) -> None:
        dll = self._dll

        # void SUInitialize(void);
        # [Observado via REA/Ghidra em SketchUpAPI.dll, 27/10/2026] O
        # assembly real (endereco 0x180065b10, atras do thunk do export)
        # nao escreve nenhum SU_RESULT em EAX/RAX antes do RET -- a
        # funcao e um guard de contador de referencia (so inicializa de
        # fato quando o contador global passa de 0 para 1) e nao segue o
        # contrato documentado publicamente de "retorna SU_RESULT". O
        # valor que ctypes le em EAX e lixo de uma chamada interna
        # anterior, por isso restype=None (nao tratamos como SU_RESULT).
        dll.SUInitialize.argtypes = []
        dll.SUInitialize.restype = None

        # void SUTerminate(void); -- mesma logica de SUInitialize, nao
        # confirmada via assembly ainda, mas tratada da mesma forma por
        # seguranca (ver pendencia no REVERSE_ENGINEERING_NOTES.md).
        dll.SUTerminate.argtypes = []
        dll.SUTerminate.restype = None

        # void SUGetAPIVersion(size_t* major, size_t* minor);
        # [Observado via REA/Ghidra, 27/10/2026] Assembly real escreve
        # direto em *major/*minor (checando NULL antes) e nunca toca
        # EAX/RAX para um status -- tambem void, mesmo padrao de
        # SUInitialize. Nesta build: *major=14, *minor=2 (API 14.2).
        dll.SUGetAPIVersion.argtypes = [
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUGetAPIVersion.restype = None

        # void SUModelCreateFromFile(SUModelRef* model, const char* file_path);
        # [Observado via REA/Ghidra, 27/10/2026] E um wrapper void que
        # so chama SUModelCreateFromFileWithStatus(model, path, &status)
        # e DESCARTA o status -- nao serve pra detectar erro de arquivo.
        # Nao usamos esta funcao; mantida so para referencia/registro.
        dll.SUModelCreateFromFile.argtypes = [
            ctypes.POINTER(SUModelRef),
            ctypes.c_char_p,
        ]
        dll.SUModelCreateFromFile.restype = None

        # SU_RESULT SUModelCreateFromFileWithStatus(
        #     SUModelRef* model, const char* file_path, SUModelLoadStatus* status);
        # [Observado via REA/Ghidra, 27/10/2026] Esta sim retorna um
        # SU_RESULT de verdade em EAX (confirmado: path==NULL -> 1
        # SU_ERROR_NULL_POINTER_INPUT; status==NULL -> 3
        # SU_ERROR_NULL_POINTER_OUTPUT; arquivo invalido/corrompido -> 7
        # SU_ERROR_SERIALIZATION). Usamos esta no open_model().
        dll.SUModelCreateFromFileWithStatus.argtypes = [
            ctypes.POINTER(SUModelRef),
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_int),
        ]
        dll.SUModelCreateFromFileWithStatus.restype = ctypes.c_int

        # SU_RESULT SUModelCreateFromBufferWithStatus(
        #     SUModelRef* model, const void* buffer, size_t buffer_length,
        #     SUModelLoadStatus* status);
        # [Observado via REA/Ghidra, 27/10/2026] Export direto (sem
        # thunk), confirmado por pseudocodigo: buffer==NULL -> 1,
        # status==NULL -> 3, buffer_length==0 -> 7. Candidato alternativo
        # a SUModelCreateFromFileWithStatus -- ver REVERSE_ENGINEERING_
        # NOTES.md secao 9.6. Mesmo padrao interno (fat pointer tipo
        # std::function construido dentro da propria DLL), so que sem
        # I/O de arquivo -- nos lemos o .skp em bytes no Python e
        # passamos o buffer direto.
        dll.SUModelCreateFromBufferWithStatus.argtypes = [
            ctypes.POINTER(SUModelRef),
            ctypes.c_char_p,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int),
        ]
        dll.SUModelCreateFromBufferWithStatus.restype = ctypes.c_int

        # SU_RESULT SUModelRelease(SUModelRef* model);
        dll.SUModelRelease.argtypes = [ctypes.POINTER(SUModelRef)]
        dll.SUModelRelease.restype = ctypes.c_int

        # SU_RESULT SUModelGetEntities(SUModelRef model, SUEntitiesRef* entities);
        dll.SUModelGetEntities.argtypes = [
            SUModelRef,
            ctypes.POINTER(SUEntitiesRef),
        ]
        dll.SUModelGetEntities.restype = ctypes.c_int

        # SU_RESULT SUEntitiesGetNumFaces(SUEntitiesRef entities, size_t* count);
        dll.SUEntitiesGetNumFaces.argtypes = [
            SUEntitiesRef,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUEntitiesGetNumFaces.restype = ctypes.c_int

        # SU_RESULT SUEntitiesGetNumEdges(SUEntitiesRef entities, size_t* count);
        dll.SUEntitiesGetNumEdges.argtypes = [
            SUEntitiesRef,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUEntitiesGetNumEdges.restype = ctypes.c_int

        # SU_RESULT SUEntitiesGetNumInstances(SUEntitiesRef entities, size_t* count);
        dll.SUEntitiesGetNumInstances.argtypes = [
            SUEntitiesRef,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUEntitiesGetNumInstances.restype = ctypes.c_int

        # -- extracao de malha/arvore de componentes [Observado via REA/
        # Ghidra, 27/10/2026 -- assinaturas confirmadas por assembly real
        # (nao por pseudocodigo), uma a uma, apos resolvida a regressao
        # do ctypes (secao 15). Todas seguem o mesmo padrao ja validado:
        # Ref por valor, ponteiros de saida, len/count* para arrays.]

        # SU_RESULT SUEntitiesGetFaces(SUEntitiesRef entities, size_t len,
        #     SUFaceRef faces[], size_t* count);
        dll.SUEntitiesGetFaces.argtypes = [
            SUEntitiesRef,
            ctypes.c_size_t,
            ctypes.POINTER(SUFaceRef),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUEntitiesGetFaces.restype = ctypes.c_int

        # SU_RESULT SUEntitiesGetInstances(SUEntitiesRef entities, size_t len,
        #     SUComponentInstanceRef instances[], size_t* count);
        dll.SUEntitiesGetInstances.argtypes = [
            SUEntitiesRef,
            ctypes.c_size_t,
            ctypes.POINTER(SUComponentInstanceRef),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUEntitiesGetInstances.restype = ctypes.c_int

        # SU_RESULT SUComponentInstanceGetDefinition(SUComponentInstanceRef
        #     instance, SUComponentDefinitionRef* definition);
        dll.SUComponentInstanceGetDefinition.argtypes = [
            SUComponentInstanceRef,
            ctypes.POINTER(SUComponentDefinitionRef),
        ]
        dll.SUComponentInstanceGetDefinition.restype = ctypes.c_int

        # SU_RESULT SUComponentInstanceGetTransform(SUComponentInstanceRef
        #     instance, SUTransformation* transform);
        dll.SUComponentInstanceGetTransform.argtypes = [
            SUComponentInstanceRef,
            ctypes.POINTER(SUTransformation),
        ]
        dll.SUComponentInstanceGetTransform.restype = ctypes.c_int

        # SU_RESULT SUComponentDefinitionGetEntities(SUComponentDefinitionRef
        #     definition, SUEntitiesRef* entities);
        dll.SUComponentDefinitionGetEntities.argtypes = [
            SUComponentDefinitionRef,
            ctypes.POINTER(SUEntitiesRef),
        ]
        dll.SUComponentDefinitionGetEntities.restype = ctypes.c_int

        # SU_RESULT SUComponentDefinitionGetName(SUComponentDefinitionRef
        #     definition, SUStringRef* name); -- `name` precisa ser criado
        # antes via SUStringCreate (confirmado por assembly: a funcao
        # verifica *name != NULL e falha com SU_ERROR_INVALID_OUTPUT senao).
        dll.SUComponentDefinitionGetName.argtypes = [
            SUComponentDefinitionRef,
            ctypes.POINTER(SUStringRef),
        ]
        dll.SUComponentDefinitionGetName.restype = ctypes.c_int

        # SU_RESULT SUComponentDefinitionGetBehavior(SUComponentDefinitionRef
        #     comp_def, struct SUComponentBehavior* behavior);
        # [Observado via REA/Ghidra, 27/10/2026] Corpo real (atras do thunk
        # do export) valida comp_def==NULL (-> 2) e behavior==NULL (-> 3),
        # depois preenche uma struct de 16 bytes via uma funcao auxiliar
        # (FUN_1800b9a70): component_type:int32 @0, component_cuts_opening:
        # bool @4 (calculado via chamada de funcao), component_always_face_
        # camera:bool @5, component_shadows_face_sun:bool @6 (esses dois
        # lidos direto do objeto da definicao) -- ORDEM dos 3 bools
        # confirmada empiricamente via Console Ruby real (nao só pelo
        # pseudocodigo, que por si só sugeria ordem errada -- ver nota em
        # SUComponentBehavior, core/su_types.py). Os 8 bytes finais
        # (offset 8..15) sao um campo NAO documentado no SDK publico.
        dll.SUComponentDefinitionGetBehavior.argtypes = [
            SUComponentDefinitionRef,
            ctypes.POINTER(SUComponentBehavior),
        ]
        dll.SUComponentDefinitionGetBehavior.restype = ctypes.c_int

        # SU_RESULT SUStringCreate(SUStringRef* string);
        dll.SUStringCreate.argtypes = [ctypes.POINTER(SUStringRef)]
        dll.SUStringCreate.restype = ctypes.c_int

        # SU_RESULT SUStringRelease(SUStringRef* string);
        dll.SUStringRelease.argtypes = [ctypes.POINTER(SUStringRef)]
        dll.SUStringRelease.restype = ctypes.c_int

        # SU_RESULT SUStringGetUTF8Length(SUStringRef string, size_t* length);
        dll.SUStringGetUTF8Length.argtypes = [
            SUStringRef,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUStringGetUTF8Length.restype = ctypes.c_int

        # SU_RESULT SUStringGetUTF8(SUStringRef string, size_t len,
        #     char* utf8, size_t* count);
        dll.SUStringGetUTF8.argtypes = [
            SUStringRef,
            ctypes.c_size_t,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUStringGetUTF8.restype = ctypes.c_int

        # SU_RESULT SUMeshHelperCreate(SUMeshHelperRef* mesh_ref, SUFaceRef face);
        dll.SUMeshHelperCreate.argtypes = [
            ctypes.POINTER(SUMeshHelperRef),
            SUFaceRef,
        ]
        dll.SUMeshHelperCreate.restype = ctypes.c_int

        # SU_RESULT SUMeshHelperRelease(SUMeshHelperRef* mesh_ref);
        dll.SUMeshHelperRelease.argtypes = [ctypes.POINTER(SUMeshHelperRef)]
        dll.SUMeshHelperRelease.restype = ctypes.c_int

        # SU_RESULT SUMeshHelperGetNumVertices(SUMeshHelperRef mesh, size_t* count);
        dll.SUMeshHelperGetNumVertices.argtypes = [
            SUMeshHelperRef,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUMeshHelperGetNumVertices.restype = ctypes.c_int

        # SU_RESULT SUMeshHelperGetNumTriangles(SUMeshHelperRef mesh, size_t* count);
        dll.SUMeshHelperGetNumTriangles.argtypes = [
            SUMeshHelperRef,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUMeshHelperGetNumTriangles.restype = ctypes.c_int

        # SU_RESULT SUMeshHelperGetVertices(SUMeshHelperRef mesh, size_t len,
        #     SUPoint3D vertices[], size_t* count);
        dll.SUMeshHelperGetVertices.argtypes = [
            SUMeshHelperRef,
            ctypes.c_size_t,
            ctypes.POINTER(SUPoint3D),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUMeshHelperGetVertices.restype = ctypes.c_int

        # SU_RESULT SUMeshHelperGetNormals(SUMeshHelperRef mesh, size_t len,
        #     SUVector3D normals[], size_t* count);
        dll.SUMeshHelperGetNormals.argtypes = [
            SUMeshHelperRef,
            ctypes.c_size_t,
            ctypes.POINTER(SUVector3D),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUMeshHelperGetNormals.restype = ctypes.c_int

        # SU_RESULT SUMeshHelperGetVertexIndices(SUMeshHelperRef mesh, size_t len,
        #     size_t indices[], size_t* count); -- indices ja vem 0-based
        # (confirmado por assembly: a DLL faz abs(valor_interno)-1 antes
        # de escrever no array, entao nao subtraimos 1 de novo no Python).
        dll.SUMeshHelperGetVertexIndices.argtypes = [
            SUMeshHelperRef,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUMeshHelperGetVertexIndices.restype = ctypes.c_int

        # -- edicao/persistencia [Observado via REA/Ghidra, 27/10/2026 --
        # assinaturas confirmadas por assembly real, seguindo os thunks
        # dos exports ate o corpo de validacao/implementacao de fato]

        # SU_RESULT SUComponentInstanceSetTransform(SUComponentInstanceRef
        #     instance, const SUTransformation* transform);
        # [Confirmado via assembly] instance por valor (RCX), transform
        # por ponteiro (RDX, checado contra NULL antes de delegar pro
        # setter generico validado da DLL) -- bate com a assinatura
        # publica do SDK.
        dll.SUComponentInstanceSetTransform.argtypes = [
            SUComponentInstanceRef,
            ctypes.POINTER(SUTransformation),
        ]
        dll.SUComponentInstanceSetTransform.restype = ctypes.c_int

        # SU_RESULT SUModelSaveToFile(SUModelRef model, const char* file_path);
        # [Confirmado via assembly] model por valor (RCX), file_path por
        # ponteiro (RDX) -- a funcao e um wrapper fino que delega pro
        # helper interno de save-com-versao (R8D=0xe), sem alterar os
        # dois primeiros argumentos. Bate com a assinatura publica do SDK.
        dll.SUModelSaveToFile.argtypes = [
            SUModelRef,
            ctypes.c_char_p,
        ]
        dll.SUModelSaveToFile.restype = ctypes.c_int

        # SU_RESULT SUModelGetUnits(SUModelRef model, SUModelUnits* units);
        # [Observado via REA/Ghidra, 27/10/2026 -- assinatura confirmada
        # por pseudocodigo real, nao assumida do SDK publico] Valida
        # model==NULL (-> 2 SU_ERROR_INVALID_INPUT) e units==NULL (-> 3
        # SU_ERROR_NULL_POINTER_OUTPUT). Internamente chama
        # SUModelGetOptionsManager -> SUOptionsManagerGetOptionsProviderByName
        # ("UnitsOptions") -> SUOptionsProviderGetValue("LengthUnit") e
        # ("LengthFormat"). *units recebe o valor de "LengthUnit" como
        # passthrough direto (0..4), EXCETO quando "LengthFormat" indica
        # formato pes-e-polegadas (==2 -> forca *units=1) ou
        # polegadas fracionarias/decimais (==1 ou 3 -> forca *units=0).
        # Esse override nao aparece no header publico do SDK; so afeta
        # os casos de Polegadas/Pes, nao Milimetros/Centimetros/Metros.
        dll.SUModelGetUnits.argtypes = [
            SUModelRef,
            ctypes.POINTER(ctypes.c_int),
        ]
        dll.SUModelGetUnits.restype = ctypes.c_int

        # -- exclusao de entidade (menu Editar > Excluir) [Observado via
        # REA/Ghidra, 27/10/2026 -- catalogacao do menu Editar, ver
        # REVERSE_ENGINEERING_NOTES.md secao 26]

        # SUEntityRef SUComponentInstanceToEntity(SUComponentInstanceRef instance);
        # [Confirmado por pseudocodigo] passthrough puro (`return param_1;`)
        # -- so reinterpreta o mesmo ponteiro como SUEntityRef (ver nota em
        # core/su_types.py). Passado/retornado por valor (struct de 1
        # ponteiro cabe em registrador, igual aos demais Refs).
        dll.SUComponentInstanceToEntity.argtypes = [SUComponentInstanceRef]
        dll.SUComponentInstanceToEntity.restype = SUEntityRef

        # SU_RESULT SUEntitiesErase(SUEntitiesRef entities, size_t len,
        #     const SUEntityRef entities_arr[]);
        # [Confirmado via assembly] entities==NULL -> 2
        # SU_ERROR_INVALID_INPUT; entities_arr==NULL -> 1
        # SU_ERROR_NULL_POINTER_INPUT. Remove de verdade os `len` entities
        # do array de `entities` (a Entities PAI onde a instancia vive --
        # nao da pra passar qualquer Entities, precisa ser a direta).
        # Equivalente nativo do "Editar > Excluir" / tecla Del do SketchUp
        # real.
        dll.SUEntitiesErase.argtypes = [
            SUEntitiesRef,
            ctypes.c_size_t,
            ctypes.POINTER(SUEntityRef),
        ]
        dll.SUEntitiesErase.restype = ctypes.c_int

        # -- criacao de geometria nova (menu Desenho > Formas > Retangulo)
        # [Confirmado via REA/Ghidra, 27/10/2026 -- catalogacao do menu
        # Desenho, ver REVERSE_ENGINEERING_NOTES.md secao 28] Familia
        # inteira de funcoes confirmadas como exports publicos reais da
        # DLL (pseudocodigo com corpo nao-trivial, nao stub) -- mesma
        # familia documentada publicamente pelo SDK da Trimble
        # (model/geometry_input.h). Fluxo: GeometryInputCreate -> N x
        # AddVertex -> LoopInputCreate -> N x LoopInputAddVertexIndex ->
        # GeometryInputAddFace (consome o loop, zera o ponteiro do
        # chamador -- ownership transfer, mesmo padrao do SDK publico) ->
        # EntitiesFill (processa tudo e cria as SUFaceRef/SUEdgeRef de
        # verdade dentro da Entities) -> GeometryInputRelease.

        # SU_RESULT SUGeometryInputCreate(SUGeometryInputRef* geometry_input);
        dll.SUGeometryInputCreate.argtypes = [ctypes.POINTER(SUGeometryInputRef)]
        dll.SUGeometryInputCreate.restype = ctypes.c_int

        # SU_RESULT SUGeometryInputRelease(SUGeometryInputRef* geometry_input);
        dll.SUGeometryInputRelease.argtypes = [ctypes.POINTER(SUGeometryInputRef)]
        dll.SUGeometryInputRelease.restype = ctypes.c_int

        # SU_RESULT SUGeometryInputAddVertex(SUGeometryInputRef geometry_input,
        #     const SUPoint3D* vertex);
        dll.SUGeometryInputAddVertex.argtypes = [
            SUGeometryInputRef,
            ctypes.POINTER(SUPoint3D),
        ]
        dll.SUGeometryInputAddVertex.restype = ctypes.c_int

        # SU_RESULT SULoopInputCreate(SULoopInputRef* loop_input);
        dll.SULoopInputCreate.argtypes = [ctypes.POINTER(SULoopInputRef)]
        dll.SULoopInputCreate.restype = ctypes.c_int

        # SU_RESULT SULoopInputRelease(SULoopInputRef* loop_input); -- so
        # usada se AddFace nao for chamada (erro no meio do caminho); em
        # fluxo normal a posse do loop passa pra AddFace, que libera.
        dll.SULoopInputRelease.argtypes = [ctypes.POINTER(SULoopInputRef)]
        dll.SULoopInputRelease.restype = ctypes.c_int

        # SU_RESULT SULoopInputAddVertexIndex(SULoopInputRef loop_input,
        #     size_t vertex_index);
        dll.SULoopInputAddVertexIndex.argtypes = [SULoopInputRef, ctypes.c_size_t]
        dll.SULoopInputAddVertexIndex.restype = ctypes.c_int

        # SU_RESULT SUGeometryInputAddFace(SUGeometryInputRef geometry_input,
        #     SULoopInputRef* loop_input); -- consome e zera *loop_input.
        dll.SUGeometryInputAddFace.argtypes = [
            SUGeometryInputRef,
            ctypes.POINTER(SULoopInputRef),
        ]
        dll.SUGeometryInputAddFace.restype = ctypes.c_int

        # SU_RESULT SUEntitiesFill(SUEntitiesRef entities,
        #     SUGeometryInputRef geometry_input, bool weld_vertices);
        dll.SUEntitiesFill.argtypes = [
            SUEntitiesRef,
            SUGeometryInputRef,
            ctypes.c_bool,
        ]
        dll.SUEntitiesFill.restype = ctypes.c_int

        # -- material/cor (menu Ferramentas > Pintura) [Confirmado via
        # REA/Ghidra, 28/10/2026 -- ver REVERSE_ENGINEERING_NOTES.md
        # secao 28] Familia completa de exports publicos reais
        # (pseudocodigo real batendo com o SDK publico documentado,
        # model/material.h e model/drawing_element.h): cria um
        # SUMaterialRef novo, define a cor RGBA, converte a instancia
        # pra SUDrawingElementRef (mesmo "Ref generico" de
        # SUComponentInstanceToEntity, so reinterpretacao de ponteiro) e
        # aplica o material nela.

        # SU_RESULT SUMaterialCreate(SUMaterialRef* material);
        dll.SUMaterialCreate.argtypes = [ctypes.POINTER(SUMaterialRef)]
        dll.SUMaterialCreate.restype = ctypes.c_int

        # SU_RESULT SUMaterialRelease(SUMaterialRef* material);
        dll.SUMaterialRelease.argtypes = [ctypes.POINTER(SUMaterialRef)]
        dll.SUMaterialRelease.restype = ctypes.c_int

        # SU_RESULT SUMaterialSetColor(SUMaterialRef material, const SUColor* color);
        dll.SUMaterialSetColor.argtypes = [SUMaterialRef, ctypes.POINTER(SUColor)]
        dll.SUMaterialSetColor.restype = ctypes.c_int

        # SUDrawingElementRef SUComponentInstanceToDrawingElement(
        #     SUComponentInstanceRef instance); -- passthrough puro
        # (`return param_1;`, confirmado via pseudocodigo real), mesmo
        # padrao de SUComponentInstanceToEntity (secao 26): retorna o
        # Ref por VALOR, nao via ponteiro de saida, e nao tem SU_RESULT
        # pra checar.
        dll.SUComponentInstanceToDrawingElement.argtypes = [SUComponentInstanceRef]
        dll.SUComponentInstanceToDrawingElement.restype = SUDrawingElementRef

        # SU_RESULT SUDrawingElementSetMaterial(SUDrawingElementRef drawing_elem,
        #     SUMaterialRef material);
        dll.SUDrawingElementSetMaterial.argtypes = [SUDrawingElementRef, SUMaterialRef]
        dll.SUDrawingElementSetMaterial.restype = ctypes.c_int

        # -- Grupos (menu Editar > Criar grupo) e Etiqueta/Tag (menu
        # Ferramentas > Etiqueta) [Confirmado via REA/Ghidra, 28/10/2026 --
        # ver REVERSE_ENGINEERING_NOTES.md secao 28.17] Familia inteira
        # confirmada por pseudocodigo real batendo com o SDK publico
        # documentado pela Trimble (model/group.h, model/layer.h). A UI
        # chama "Etiqueta" o que a API interna ainda chama "Layer" (nome
        # legado da Trimble).

        # SU_RESULT SUGroupCreate(SUGroupRef* group);
        dll.SUGroupCreate.argtypes = [ctypes.POINTER(SUGroupRef)]
        dll.SUGroupCreate.restype = ctypes.c_int

        # SU_RESULT SUEntitiesAddGroup(SUEntitiesRef entities, SUGroupRef group);
        dll.SUEntitiesAddGroup.argtypes = [SUEntitiesRef, SUGroupRef]
        dll.SUEntitiesAddGroup.restype = ctypes.c_int

        # SU_RESULT SUGroupGetEntities(SUGroupRef group, SUEntitiesRef* entities);
        dll.SUGroupGetEntities.argtypes = [SUGroupRef, ctypes.POINTER(SUEntitiesRef)]
        dll.SUGroupGetEntities.restype = ctypes.c_int

        # SU_RESULT SUGroupSetName(SUGroupRef group, const char* name);
        dll.SUGroupSetName.argtypes = [SUGroupRef, ctypes.c_char_p]
        dll.SUGroupSetName.restype = ctypes.c_int

        # SUComponentInstanceRef SUGroupToComponentInstance(SUGroupRef group);
        # [Confirmado por pseudocodigo] passthrough puro (`return param_1;`),
        # mesmo padrao de SUComponentInstanceToEntity/ToDrawingElement -- um
        # Grupo E um ComponentInstance especial por baixo (confirmado via
        # dynamic_cast real no corpo de SUGroupCreate).
        dll.SUGroupToComponentInstance.argtypes = [SUGroupRef]
        dll.SUGroupToComponentInstance.restype = SUComponentInstanceRef

        # SU_RESULT SUEntitiesGetGroups(SUEntitiesRef entities, size_t len,
        #     SUGroupRef groups[], size_t* count);
        dll.SUEntitiesGetGroups.argtypes = [
            SUEntitiesRef,
            ctypes.c_size_t,
            ctypes.POINTER(SUGroupRef),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUEntitiesGetGroups.restype = ctypes.c_int

        # SU_RESULT SUEntitiesGetNumGroups(SUEntitiesRef entities, size_t* count);
        dll.SUEntitiesGetNumGroups.argtypes = [
            SUEntitiesRef,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUEntitiesGetNumGroups.restype = ctypes.c_int

        # SU_RESULT SULayerCreate(SULayerRef* layer);
        dll.SULayerCreate.argtypes = [ctypes.POINTER(SULayerRef)]
        dll.SULayerCreate.restype = ctypes.c_int

        # SU_RESULT SULayerSetName(SULayerRef layer, const char* name);
        dll.SULayerSetName.argtypes = [SULayerRef, ctypes.c_char_p]
        dll.SULayerSetName.restype = ctypes.c_int

        # SU_RESULT SUModelAddLayers(SUModelRef model, size_t len,
        #     const SULayerRef layers[]);
        dll.SUModelAddLayers.argtypes = [
            SUModelRef,
            ctypes.c_size_t,
            ctypes.POINTER(SULayerRef),
        ]
        dll.SUModelAddLayers.restype = ctypes.c_int

        # SU_RESULT SUDrawingElementSetLayer(SUDrawingElementRef drawing_elem,
        #     SULayerRef layer);
        dll.SUDrawingElementSetLayer.argtypes = [SUDrawingElementRef, SULayerRef]
        dll.SUDrawingElementSetLayer.restype = ctypes.c_int

        # -- Pintura por face (menu Ferramentas > Pintura, modo "face")
        # [Confirmado via REA/Ghidra, 28/10/2026 -- ver
        # REVERSE_ENGINEERING_NOTES.md secao 28.19]. SUFaceSetFrontMaterial/
        # SUFaceSetBackMaterial sao exports publicos reais, e o pseudocodigo
        # real confirmou que SUFaceSetFrontMaterial e um thin wrapper que so
        # chama SUFaceToDrawingElement(face) (passthrough puro, `return
        # param_1;`, mesmo layout binario de todo "Ref" do SDK) seguido de
        # SUDrawingElementSetMaterial -- por isso usamos o mesmo caminho
        # direto aqui (ver paint_face() abaixo), igual ja feito em
        # paint_instance().

        # SUDrawingElementRef SUFaceToDrawingElement(SUFaceRef face);
        dll.SUFaceToDrawingElement.argtypes = [SUFaceRef]
        dll.SUFaceToDrawingElement.restype = SUDrawingElementRef

        # -- Cenas (menu Janela > Bandeja padrao > Cenas) [Confirmado via
        # REA/Ghidra, 28/10/2026 -- ver REVERSE_ENGINEERING_NOTES.md secao
        # 28.20]. Familia inteira confirmada por pseudocodigo real batendo
        # com o SDK publico documentado pela Trimble (model/scene.h). A API
        # Ruby chama o mesmo objeto de "Page" -- mesmo dado, nome diferente.

        # SU_RESULT SUSceneCreate(SUSceneRef* scene); -- alocador padrao
        # (pseudocodigo real: 1=NULL_POINTER_INPUT se param_1==0, mesmo
        # padrao de SUGroupCreate/SULayerCreate).
        dll.SUSceneCreate.argtypes = [ctypes.POINTER(SUSceneRef)]
        dll.SUSceneCreate.restype = ctypes.c_int

        # SU_RESULT SUSceneSetName(SUSceneRef scene, const char* name);
        # [Confirmado por pseudocodigo: 1=NULL_POINTER_INPUT se name nulo,
        # mesmo padrao de SUGroupSetName/SULayerSetName.]
        dll.SUSceneSetName.argtypes = [SUSceneRef, ctypes.c_char_p]
        dll.SUSceneSetName.restype = ctypes.c_int

        # SU_RESULT SUSceneGetName(SUSceneRef scene, SUStringRef* name);
        dll.SUSceneGetName.argtypes = [SUSceneRef, ctypes.POINTER(SUStringRef)]
        dll.SUSceneGetName.restype = ctypes.c_int

        # SU_RESULT SUModelAddScenes(SUModelRef model, size_t len,
        #     const SUSceneRef scenes[]); -- [Confirmado por pseudocodigo:
        # mesmo padrao array de SUModelAddLayers, usado aqui em vez do
        # SUModelAddScene singular pra reaproveitar a mesma convencao ja
        # validada neste projeto.]
        dll.SUModelAddScenes.argtypes = [
            SUModelRef,
            ctypes.c_size_t,
            ctypes.POINTER(SUSceneRef),
        ]
        dll.SUModelAddScenes.restype = ctypes.c_int

        # SU_RESULT SUModelSetActiveScene(SUModelRef model, SUSceneRef scene);
        # -- TROCADO em 28/10/2026: `SUSceneActivate` (1 ou 2 parametros,
        # ambas as tentativas testadas isoladamente) sempre retornava
        # sucesso (0) mas `SUModelGetActiveScene` continuava devolvendo
        # NO_DATA depois -- ou seja, nao e essa a funcao que o SDK usa pra
        # setar o estado que `SUModelGetActiveScene` le. Busca nova via REA
        # (`search_procedures("ActiveScene")`) achou `SUModelSetActiveScene`
        # (endereco 0x180004507), funcao SEPARADA de `SUSceneActivate`.
        # Pseudocodigo real confirma 2 parametros (model, scene), ambos
        # validados contra null (retorna 2=INVALID_INPUT), retorna 6 se a
        # chamada interna falhar, 0 em sucesso -- exatamente o padrao
        # esperado pelo par get/set. Testado isoladamente (fora do HTTP)
        # antes de aplicar aqui: `SUModelGetActiveScene` passou a refletir
        # a cena ativada.
        dll.SUModelSetActiveScene.argtypes = [SUModelRef, SUSceneRef]
        dll.SUModelSetActiveScene.restype = ctypes.c_int

        # SU_RESULT SUModelGetNumScenes(SUModelRef model, size_t* count);
        dll.SUModelGetNumScenes.argtypes = [
            SUModelRef,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUModelGetNumScenes.restype = ctypes.c_int

        # SU_RESULT SUModelGetScenes(SUModelRef model, size_t len,
        #     SUSceneRef scenes[], size_t* count);
        dll.SUModelGetScenes.argtypes = [
            SUModelRef,
            ctypes.c_size_t,
            ctypes.POINTER(SUSceneRef),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUModelGetScenes.restype = ctypes.c_int

        # SU_RESULT SUModelGetActiveScene(SUModelRef model, SUSceneRef* scene);
        # [Confirmado por pseudocodigo: 2=INVALID_INPUT se model nulo,
        # 3=NULL_POINTER_OUTPUT se scene nulo, 9=NO_DATA se nao houver cena
        # ativa -- tratado especialmente em get_active_scene() abaixo, nao
        # como erro generico.]
        dll.SUModelGetActiveScene.argtypes = [
            SUModelRef,
            ctypes.POINTER(SUSceneRef),
        ]
        dll.SUModelGetActiveScene.restype = ctypes.c_int

        # -- Etiquetas reais (Janela > Bandeja padrao > Etiquetas)
        # [Confirmado via REA/Ghidra, 28/10/2026 -- ver
        # REVERSE_ENGINEERING_NOTES.md secao 28.22]. Antes deste projeto so
        # sabia CRIAR/ATRIBUIR uma Etiqueta (SULayerCreate/SetLayer, secao
        # 28.18) -- nunca LISTAR as reais do modelo nem ler/alterar
        # visibilidade. Pseudocodigo real confirmado pra todas as funcoes
        # abaixo (nenhuma e thin wrapper nem passthrough).

        # SU_RESULT SUModelGetNumLayers(SUModelRef model, size_t* count);
        # model==NULL -> 2; count==NULL -> 3; se a colecao interna de
        # layers do modelo nao existir -> 6 (tratado como lista vazia aqui).
        dll.SUModelGetNumLayers.argtypes = [
            SUModelRef,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUModelGetNumLayers.restype = ctypes.c_int

        # SU_RESULT SUModelGetLayers(SUModelRef model, size_t len,
        #     SULayerRef layers[], size_t* count); -- mesmo padrao de
        # SUModelGetScenes (len clampado ao total real, *count = escrito).
        dll.SUModelGetLayers.argtypes = [
            SUModelRef,
            ctypes.c_size_t,
            ctypes.POINTER(SULayerRef),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        dll.SUModelGetLayers.restype = ctypes.c_int

        # SU_RESULT SULayerGetName(SULayerRef layer, SUStringRef* name);
        # Achado especifico (pseudocodigo real): existe um branch interno
        # que devolve uma string CONSTANTE fixa em vez do nome real quando
        # um bool-check interno da true -- bate com o comportamento visto
        # na Bandeja padrao real (a Etiqueta padrao/sem-etiqueta aparece
        # como "Sem etiquetas", nunca com nome vazio).
        dll.SULayerGetName.argtypes = [SULayerRef, ctypes.POINTER(SUStringRef)]
        dll.SULayerGetName.restype = ctypes.c_int

        # SU_RESULT SULayerGetVisibility(SULayerRef layer, bool* visible);
        # SU_RESULT SULayerSetVisibility(SULayerRef layer, bool visible);
        # Achado especifico (pseudocodigo real): a DLL guarda internamente
        # uma flag "hidden" (invertida) e inverte na leitura/escrita pra
        # expor "visible" -- transparente pro binding ctypes, documentado
        # aqui so pra explicar a semantica caso o comportamento pareca
        # "ao contrario" num teste isolado futuro.
        dll.SULayerGetVisibility.argtypes = [SULayerRef, ctypes.POINTER(ctypes.c_bool)]
        dll.SULayerGetVisibility.restype = ctypes.c_int
        dll.SULayerSetVisibility.argtypes = [SULayerRef, ctypes.c_bool]
        dll.SULayerSetVisibility.restype = ctypes.c_int

        # SU_RESULT SUDrawingElementGetLayer(SUDrawingElementRef drawing_elem,
        #     SULayerRef* layer); -- Achado especifico (pseudocodigo real):
        # se o elemento nao tiver layer associado, devolve 9=NO_DATA (nao
        # sucesso com *layer vazio) -- tratado como None aqui, mesmo padrao
        # ja usado em get_active_scene().
        dll.SUDrawingElementGetLayer.argtypes = [
            SUDrawingElementRef,
            ctypes.POINTER(SULayerRef),
        ]
        dll.SUDrawingElementGetLayer.restype = ctypes.c_int

        # SU_RESULT SUModelGetDefaultLayer(SUModelRef model, SULayerRef* layer);
        dll.SUModelGetDefaultLayer.argtypes = [
            SUModelRef,
            ctypes.POINTER(SULayerRef),
        ]
        dll.SUModelGetDefaultLayer.restype = ctypes.c_int

        # -- Eixos customizados (menu Ferramentas > Eixos) [Confirmado via
        # REA/Ghidra, 28/10/2026 -- ver REVERSE_ENGINEERING_NOTES.md secao
        # 28.21]. model/axes.h.

        # SU_RESULT SUAxesCreateCustom(SUAxesRef* axes, const SUPoint3D* origin,
        #     const SUVector3D* xaxis, const SUVector3D* yaxis,
        #     const SUVector3D* zaxis); -- pseudocodigo real confirmou os 5
        # parametros batendo com o SDK publico; valida que os 3 eixos sao
        # realmente ortogonais entre si (retorna 6=GENERIC se nao forem --
        # por isso a base e sempre recomposta via Gram-Schmidt antes de
        # chegar aqui, ver orthonormal_axes_from_points() em
        # core/mesh_extractor.py).
        dll.SUAxesCreateCustom.argtypes = [
            ctypes.POINTER(SUAxesRef),
            ctypes.POINTER(SUPoint3D),
            ctypes.POINTER(SUVector3D),
            ctypes.POINTER(SUVector3D),
            ctypes.POINTER(SUVector3D),
        ]
        dll.SUAxesCreateCustom.restype = ctypes.c_int

        # SU_RESULT SUComponentDefinitionSetAxes(SUComponentDefinitionRef
        #     definition, SUAxesRef axes); -- unico "set" de eixos que o SDK
        # publico expoe (so em definicao de Grupo/Componente -- nao ha
        # SUModelSetAxes pra mudar os eixos do modelo raiz, so leitura via
        # SUModelGetAxes).
        dll.SUComponentDefinitionSetAxes.argtypes = [
            SUComponentDefinitionRef,
            SUAxesRef,
        ]
        dll.SUComponentDefinitionSetAxes.restype = ctypes.c_int

        # SU_RESULT SUAxesRelease(SUAxesRef* axes); -- mesmo padrao de
        # release de todo objeto alocado por SUAxesCreateCustom (nao e
        # consumido/possuido por SetAxes, que so LE os valores -- precisa
        # ser liberado por quem criou).
        dll.SUAxesRelease.argtypes = [ctypes.POINTER(SUAxesRef)]
        dll.SUAxesRelease.restype = ctypes.c_int

        # -- Camera real do modelo (bandeja padrao -- posicao/angulo
        # errados ao abrir/criar modelo) [Confirmado via REA/Ghidra,
        # 28/10/2026 -- ver REVERSE_ENGINEERING_NOTES.md secao 28.23].
        # model/camera.h.

        # SU_RESULT SUModelGetCamera(SUModelRef model, SUCameraRef* camera);
        # Achado especifico (pseudocodigo real): devolve um ponteiro
        # INTERNO pra dentro do proprio SUModelRef (offset fixo) -- "ref
        # emprestada", nao precisa (e nao deve) ser liberada com um
        # release, mesmo padrao ja visto noutros *GetX deste SDK que
        # devolvem sub-objetos do model em vez de alocar algo novo.
        dll.SUModelGetCamera.argtypes = [SUModelRef, ctypes.POINTER(SUCameraRef)]
        dll.SUModelGetCamera.restype = ctypes.c_int

        # SU_RESULT SUCameraGetOrientation(SUCameraRef camera,
        #     SUPoint3D* position, SUPoint3D* target, SUVector3D* up_vector);
        # Pseudocodigo real confirmou os 3 parametros de saida (9 doubles
        # no total) lendo direto dos offsets da struct da camera -- mesma
        # convencao de unidade/eixo (polegadas, Z-up) da geometria e das
        # transforms de instancia, conversao pra metros/Y-up fica a cargo
        # do frontend (mesmo padrao ja usado pro resto do DTO).
        dll.SUCameraGetOrientation.argtypes = [
            SUCameraRef,
            ctypes.POINTER(SUPoint3D),
            ctypes.POINTER(SUPoint3D),
            ctypes.POINTER(SUVector3D),
        ]
        dll.SUCameraGetOrientation.restype = ctypes.c_int

        # SU_RESULT SUCameraGetPerspective(SUCameraRef camera, bool* is_perspective);
        dll.SUCameraGetPerspective.argtypes = [SUCameraRef, ctypes.POINTER(ctypes.c_bool)]
        dll.SUCameraGetPerspective.restype = ctypes.c_int

        # SU_RESULT SUCameraGetPerspectiveFrustumFOV(SUCameraRef camera,
        #     double* fov); -- Achado especifico (pseudocodigo real): devolve
        # 9=NO_DATA se a camera nao estiver em modo perspectiva (campo
        # interno de flag zerado), nunca sucesso com valor invalido.
        dll.SUCameraGetPerspectiveFrustumFOV.argtypes = [
            SUCameraRef,
            ctypes.POINTER(ctypes.c_double),
        ]
        dll.SUCameraGetPerspectiveFrustumFOV.restype = ctypes.c_int

        # SU_RESULT SUCameraGetFOVIsHeight(SUCameraRef camera, bool* fov_is_height);
        dll.SUCameraGetFOVIsHeight.argtypes = [SUCameraRef, ctypes.POINTER(ctypes.c_bool)]
        dll.SUCameraGetFOVIsHeight.restype = ctypes.c_int

    # -- ciclo de vida da API -------------------------------------------------

    def initialize(self) -> None:
        """Chama SUInitialize(). Obrigatorio antes de qualquer outra chamada.

        Nao valida retorno: a funcao real e void (ver nota em
        _bind_prototypes). Nao ha SU_RESULT para checar aqui.
        """
        self._dll.SUInitialize()
        self._initialized = True

    def terminate(self) -> None:
        """Chama SUTerminate(). Libera recursos globais do SDK. Void (idem SUInitialize)."""
        if self._initialized:
            self._dll.SUTerminate()
            self._initialized = False

    def __enter__(self) -> "SketchUpAPI":
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.terminate()

    # -- versao ----------------------------------------------------------------

    def get_api_version(self) -> tuple[int, int]:
        """SUGetAPIVersion e void: le os valores escritos nos ponteiros, sem SU_RESULT."""
        major = ctypes.c_size_t()
        minor = ctypes.c_size_t()
        self._dll.SUGetAPIVersion(ctypes.byref(major), ctypes.byref(minor))
        return (major.value, minor.value)

    # -- arvore de entidades / malha ----------------------------------------
    # Usado pelo core/mesh_extractor.py para montar o DTO do visualizador 3D.

    def get_faces(self, entities: SUEntitiesRef) -> list[SUFaceRef]:
        count = ctypes.c_size_t()
        su_check(
            self._dll.SUEntitiesGetNumFaces(entities, ctypes.byref(count)),
            "SUEntitiesGetNumFaces",
        )
        n = count.value
        if n == 0:
            return []
        arr = (SUFaceRef * n)()
        actual = ctypes.c_size_t()
        su_check(
            self._dll.SUEntitiesGetFaces(entities, n, arr, ctypes.byref(actual)),
            "SUEntitiesGetFaces",
        )
        return list(arr)[: actual.value]

    def get_instances(self, entities: SUEntitiesRef) -> list[SUComponentInstanceRef]:
        count = ctypes.c_size_t()
        su_check(
            self._dll.SUEntitiesGetNumInstances(entities, ctypes.byref(count)),
            "SUEntitiesGetNumInstances",
        )
        n = count.value
        if n == 0:
            return []
        arr = (SUComponentInstanceRef * n)()
        actual = ctypes.c_size_t()
        su_check(
            self._dll.SUEntitiesGetInstances(entities, n, arr, ctypes.byref(actual)),
            "SUEntitiesGetInstances",
        )
        return list(arr)[: actual.value]

    def get_instance_definition(
        self, instance: SUComponentInstanceRef
    ) -> SUComponentDefinitionRef:
        definition = SUComponentDefinitionRef()
        su_check(
            self._dll.SUComponentInstanceGetDefinition(
                instance, ctypes.byref(definition)
            ),
            "SUComponentInstanceGetDefinition",
        )
        return definition

    def get_instance_transform(self, instance: SUComponentInstanceRef) -> list[float]:
        """Matriz 4x4 column-major (ver SUTransformation) -- mesma convencao
        consumida direto por `Matrix4.fromArray()` no Three.js."""
        transform = SUTransformation()
        su_check(
            self._dll.SUComponentInstanceGetTransform(
                instance, ctypes.byref(transform)
            ),
            "SUComponentInstanceGetTransform",
        )
        return list(transform.values)

    def set_instance_transform(
        self, instance: SUComponentInstanceRef, transform: list[float]
    ) -> None:
        """Grava a transformacao LOCAL (relativa ao pai imediato) de uma
        instancia -- NAO a matriz mundial usada no DTO do visualizador.
        Conversao mundo->local e responsabilidade de quem chama (ver
        core/mesh_extractor.invert_affine4 e app/repositories/
        skp_engine_repository.py)."""
        su_transform = SUTransformation(values=(ctypes.c_double * 16)(*transform))
        su_check(
            self._dll.SUComponentInstanceSetTransform(
                instance, ctypes.byref(su_transform)
            ),
            "SUComponentInstanceSetTransform",
        )

    def erase_instance(
        self, parent_entities: SUEntitiesRef, instance: SUComponentInstanceRef
    ) -> None:
        """Remove de verdade uma SUComponentInstanceRef do seu Entities pai,
        via SUComponentInstanceToEntity + SUEntitiesErase (equivalente
        nativo do "Editar > Excluir"/Del). `parent_entities` precisa ser o
        Entities DIRETO onde a instancia vive (ver registry["parent_entities"]
        em core/mesh_extractor.py)."""
        entity = self._dll.SUComponentInstanceToEntity(instance)
        arr = (SUEntityRef * 1)(entity)
        su_check(
            self._dll.SUEntitiesErase(parent_entities, 1, arr),
            "SUEntitiesErase",
        )

    def add_face(self, entities: SUEntitiesRef, points: list[tuple[float, float, float]]) -> None:
        """Cria uma face plana nova dentro de `entities` a partir de uma
        lista ordenada de vertices coplanares (polegadas, unidade nativa
        da SDK -- ver conversao em sceneBuilder.js) -- equivalente real
        de "Desenho > Formas > Retangulo"/"Círculo"/"Polígono" (aqui só o
        caso retangular/poligonal simples é usado, ver
        app/repositories/skp_engine_repository.py). Fluxo documentado em
        _bind_prototypes() (criacao de geometria nova, REVERSE_ENGINEERING_
        NOTES.md secao 28): GeometryInput -> N vertices -> 1 loop com
        todos os indices -> 1 face -> EntitiesFill grava de verdade."""
        dll = self._dll
        geometry_input = SUGeometryInputRef()
        su_check(dll.SUGeometryInputCreate(ctypes.byref(geometry_input)), "SUGeometryInputCreate")
        try:
            for x, y, z in points:
                vertex = SUPoint3D(x=x, y=y, z=z)
                su_check(
                    dll.SUGeometryInputAddVertex(geometry_input, ctypes.byref(vertex)),
                    "SUGeometryInputAddVertex",
                )

            loop_input = SULoopInputRef()
            su_check(dll.SULoopInputCreate(ctypes.byref(loop_input)), "SULoopInputCreate")
            for index in range(len(points)):
                su_check(
                    dll.SULoopInputAddVertexIndex(loop_input, ctypes.c_size_t(index)),
                    "SULoopInputAddVertexIndex",
                )
            su_check(
                dll.SUGeometryInputAddFace(geometry_input, ctypes.byref(loop_input)),
                "SUGeometryInputAddFace",
            )  # a partir daqui o loop_input foi consumido (ownership transfer)

            su_check(
                dll.SUEntitiesFill(entities, geometry_input, ctypes.c_bool(True)),
                "SUEntitiesFill",
            )
        finally:
            su_check(dll.SUGeometryInputRelease(ctypes.byref(geometry_input)), "SUGeometryInputRelease")

    def paint_instance(
        self, instance: SUComponentInstanceRef, r: int, g: int, b: int, a: int = 255
    ) -> None:
        """Aplica uma cor RGBA nova (0-255 por canal) de verdade numa
        instancia real do modelo -- equivalente real de "Ferramentas >
        Pintura" (ver REVERSE_ENGINEERING_NOTES.md secao 28). Fluxo
        confirmado via REA/Ghidra (pseudocodigo real, familia completa
        de exports publicos): MaterialCreate -> MaterialSetColor ->
        ComponentInstanceToDrawingElement (passthrough) ->
        DrawingElementSetMaterial. O material fica "dono" da cena (nao
        e liberado aqui -- `SUMaterialRelease` destruiria o material
        que acabou de ser atribuido; o SDK transfere a posse pro
        modelo quando o material e aplicado, mesmo padrao do
        GeometryInput em add_face)."""
        dll = self._dll
        material = SUMaterialRef()
        su_check(dll.SUMaterialCreate(ctypes.byref(material)), "SUMaterialCreate")
        color = SUColor(red=r, green=g, blue=b, alpha=a)
        su_check(dll.SUMaterialSetColor(material, ctypes.byref(color)), "SUMaterialSetColor")
        drawing_elem = dll.SUComponentInstanceToDrawingElement(instance)
        su_check(
            dll.SUDrawingElementSetMaterial(drawing_elem, material),
            "SUDrawingElementSetMaterial",
        )

    def paint_face(self, face: SUFaceRef, r: int, g: int, b: int, a: int = 255) -> None:
        """Aplica uma cor RGBA nova de verdade numa FACE especifica (nao
        na instancia inteira) -- equivalente real de pintar por face no
        SketchUp (ver REVERSE_ENGINEERING_NOTES.md secao 28.19). Como a
        face pertence a geometria da DEFINICAO (nao da instancia), a
        mudanca fica gravada no .skp pra TODAS as instancias que
        compartilham essa definicao -- mesmo comportamento do SketchUp
        real (diferente de paint_instance(), que so afeta UMA
        instancia). Mesmo fluxo confirmado via REA pra
        SUFaceSetFrontMaterial: MaterialCreate -> MaterialSetColor ->
        SUFaceToDrawingElement (passthrough) -> DrawingElementSetMaterial."""
        dll = self._dll
        material = SUMaterialRef()
        su_check(dll.SUMaterialCreate(ctypes.byref(material)), "SUMaterialCreate")
        color = SUColor(red=r, green=g, blue=b, alpha=a)
        su_check(dll.SUMaterialSetColor(material, ctypes.byref(color)), "SUMaterialSetColor")
        drawing_elem = dll.SUFaceToDrawingElement(face)
        su_check(
            dll.SUDrawingElementSetMaterial(drawing_elem, material),
            "SUDrawingElementSetMaterial",
        )

    def create_group(self, parent_entities: SUEntitiesRef, name: str) -> SUGroupRef:
        """Cria um Grupo real dentro de `parent_entities` -- equivalente
        real de "Editar > Criar grupo" (ver REVERSE_ENGINEERING_NOTES.md
        secao 28.17). Fluxo confirmado via REA/Ghidra (pseudocodigo real):
        GroupCreate -> SetName -> EntitiesAddGroup. Devolve o SUGroupRef
        pra o chamador preencher geometria via get_group_entities() (o
        grupo nasce vazio, igual um Entities novo)."""
        dll = self._dll
        group = SUGroupRef()
        su_check(dll.SUGroupCreate(ctypes.byref(group)), "SUGroupCreate")
        su_check(
            dll.SUGroupSetName(group, name.encode("utf-8")), "SUGroupSetName"
        )
        su_check(
            dll.SUEntitiesAddGroup(parent_entities, group), "SUEntitiesAddGroup"
        )
        return group

    def get_group_entities(self, group: SUGroupRef) -> SUEntitiesRef:
        entities = SUEntitiesRef()
        su_check(
            self._dll.SUGroupGetEntities(group, ctypes.byref(entities)),
            "SUGroupGetEntities",
        )
        return entities

    def get_groups(self, entities: SUEntitiesRef) -> list[SUGroupRef]:
        """Grupos sao uma colecao SEPARADA de ComponentInstances no SDK
        (SUEntitiesGetGroups, nao aparecem em SUEntitiesGetInstances) --
        ver core/mesh_extractor.py, que converte cada um via
        group_to_instance() pra reaproveitar o mesmo caminho de
        extracao/edicao ja existente pra instancias."""
        count = ctypes.c_size_t()
        su_check(
            self._dll.SUEntitiesGetNumGroups(entities, ctypes.byref(count)),
            "SUEntitiesGetNumGroups",
        )
        n = count.value
        if n == 0:
            return []
        arr = (SUGroupRef * n)()
        actual = ctypes.c_size_t()
        su_check(
            self._dll.SUEntitiesGetGroups(entities, n, arr, ctypes.byref(actual)),
            "SUEntitiesGetGroups",
        )
        return list(arr)[: actual.value]

    def group_to_instance(self, group: SUGroupRef) -> SUComponentInstanceRef:
        """Um SUGroupRef E um SUComponentInstanceRef especial por baixo
        (confirmado via dynamic_cast real no corpo de SUGroupCreate) --
        passthrough puro, mesmo padrao de SUComponentInstanceToEntity."""
        return self._dll.SUGroupToComponentInstance(group)

    def create_tag(self, model: SUModelRef, name: str) -> SULayerRef:
        """Cria uma Etiqueta (Tag) real e a registra no modelo --
        equivalente real de "Ferramentas > Etiqueta" (ver
        REVERSE_ENGINEERING_NOTES.md secao 28.17). A UI chama "Etiqueta"
        o que a API interna ainda chama "Layer" (nome legado da Trimble).
        Fluxo: LayerCreate -> SetName -> ModelAddLayers (array de 1)."""
        dll = self._dll
        layer = SULayerRef()
        su_check(dll.SULayerCreate(ctypes.byref(layer)), "SULayerCreate")
        su_check(
            dll.SULayerSetName(layer, name.encode("utf-8")), "SULayerSetName"
        )
        arr = (SULayerRef * 1)(layer)
        su_check(dll.SUModelAddLayers(model, 1, arr), "SUModelAddLayers")
        return layer

    def set_instance_tag(self, instance: SUComponentInstanceRef, layer: SULayerRef) -> None:
        """Aplica uma Etiqueta (Tag/Layer) real numa instancia -- mesmo
        padrao de paint_instance() (ComponentInstanceToDrawingElement +
        setter), so trocando Material por Layer."""
        dll = self._dll
        drawing_elem = dll.SUComponentInstanceToDrawingElement(instance)
        su_check(
            dll.SUDrawingElementSetLayer(drawing_elem, layer),
            "SUDrawingElementSetLayer",
        )

    def create_scene(self, model: SUModelRef, name: str) -> SUSceneRef:
        """Cria uma Cena real e a registra no modelo -- equivalente real
        de "Janela > Bandeja padrao > Cenas" (ver REVERSE_ENGINEERING_
        NOTES.md secao 28.20). A API Ruby chama o mesmo objeto de "Page".
        Fluxo: SceneCreate -> SetName -> ModelAddScenes (array de 1, mesmo
        padrao de create_tag()). NAO captura camera/estilo visual -- este
        projeto nao tem binding de SUCameraRef ainda (limitacao
        documentada, nao escondida)."""
        dll = self._dll
        scene = SUSceneRef()
        su_check(dll.SUSceneCreate(ctypes.byref(scene)), "SUSceneCreate")
        su_check(
            dll.SUSceneSetName(scene, name.encode("utf-8")), "SUSceneSetName"
        )
        arr = (SUSceneRef * 1)(scene)
        su_check(dll.SUModelAddScenes(model, 1, arr), "SUModelAddScenes")
        return scene

    def activate_scene(self, model: SUModelRef, scene: SUSceneRef) -> None:
        """Ativa uma Cena real (SUModelSetActiveScene) -- vira a "cena
        ativa" do modelo, persistida ao salvar o .skp. Nao move a camera
        do viewer nesta sessao (este projeto nao le/escreve SUCameraRef
        ainda -- limitacao documentada, ver REVERSE_ENGINEERING_NOTES.md
        secao 28.20)."""
        su_check(
            self._dll.SUModelSetActiveScene(model, scene), "SUModelSetActiveScene"
        )

    def get_scenes(self, model: SUModelRef) -> list[SUSceneRef]:
        count = ctypes.c_size_t()
        su_check(
            self._dll.SUModelGetNumScenes(model, ctypes.byref(count)),
            "SUModelGetNumScenes",
        )
        n = count.value
        if n == 0:
            return []
        arr = (SUSceneRef * n)()
        actual = ctypes.c_size_t()
        su_check(
            self._dll.SUModelGetScenes(model, n, arr, ctypes.byref(actual)),
            "SUModelGetScenes",
        )
        return list(arr)[: actual.value]

    def get_scene_name(self, scene: SUSceneRef) -> str:
        """Mesmo padrao de leitura de SUStringRef ja usado em
        get_definition_name()."""
        dll = self._dll
        name_ref = SUStringRef()
        su_check(dll.SUStringCreate(ctypes.byref(name_ref)), "SUStringCreate")
        try:
            su_check(dll.SUSceneGetName(scene, ctypes.byref(name_ref)), "SUSceneGetName")
            length = ctypes.c_size_t()
            su_check(
                dll.SUStringGetUTF8Length(name_ref, ctypes.byref(length)),
                "SUStringGetUTF8Length",
            )
            buf = ctypes.create_string_buffer(length.value + 1)
            actual = ctypes.c_size_t()
            su_check(
                dll.SUStringGetUTF8(name_ref, length.value + 1, buf, ctypes.byref(actual)),
                "SUStringGetUTF8",
            )
            return buf.value.decode("utf-8")
        finally:
            dll.SUStringRelease(ctypes.byref(name_ref))

    def get_active_scene(self, model: SUModelRef) -> SUSceneRef | None:
        """SUModelGetActiveScene devolve SU_ERROR_NO_DATA (codigo 9, ver
        SU_ERRORS em core/su_types.py) quando nao ha cena ativa -- tratado
        aqui como `None`, nao como excecao (diferente de todo outro
        binding deste arquivo, que usa su_check genérico)."""
        scene = SUSceneRef()
        result = self._dll.SUModelGetActiveScene(model, ctypes.byref(scene))
        if result == 9:  # SU_ERROR_NO_DATA
            return None
        su_check(result, "SUModelGetActiveScene")
        return scene

    def list_layers(self, model: SUModelRef) -> list[SULayerRef]:
        """Lista TODAS as Etiquetas (Tags/Layers) reais ja existentes no
        modelo (SUModelGetNumLayers + SUModelGetLayers) -- diferente de
        create_tag() (28.18), que so CRIA uma nova. Se a colecao interna
        de layers nao existir (SU_ERROR_GENERIC=6, achado de pseudocodigo
        real), trata como lista vazia em vez de lancar excecao."""
        dll = self._dll
        n = ctypes.c_size_t()
        result = dll.SUModelGetNumLayers(model, ctypes.byref(n))
        if result == 6:  # SU_ERROR_GENERIC (colecao de layers ausente)
            return []
        su_check(result, "SUModelGetNumLayers")
        if n.value == 0:
            return []
        arr = (SULayerRef * n.value)()
        actual = ctypes.c_size_t()
        su_check(
            dll.SUModelGetLayers(model, n.value, arr, ctypes.byref(actual)),
            "SUModelGetLayers",
        )
        return list(arr)[: actual.value]

    def get_layer_name(self, layer: SULayerRef) -> str:
        """Mesmo padrao de leitura de SUStringRef ja usado em
        get_scene_name()/get_definition_name(). A propria DLL devolve
        "Sem etiquetas" (nome fixo interno) pra Etiqueta padrao -- nao
        precisa de fallback manual aqui (achado de pseudocodigo real)."""
        dll = self._dll
        name_ref = SUStringRef()
        su_check(dll.SUStringCreate(ctypes.byref(name_ref)), "SUStringCreate")
        try:
            su_check(dll.SULayerGetName(layer, ctypes.byref(name_ref)), "SULayerGetName")
            length = ctypes.c_size_t()
            su_check(
                dll.SUStringGetUTF8Length(name_ref, ctypes.byref(length)),
                "SUStringGetUTF8Length",
            )
            buf = ctypes.create_string_buffer(length.value + 1)
            actual = ctypes.c_size_t()
            su_check(
                dll.SUStringGetUTF8(name_ref, length.value + 1, buf, ctypes.byref(actual)),
                "SUStringGetUTF8",
            )
            return buf.value.decode("utf-8")
        finally:
            dll.SUStringRelease(ctypes.byref(name_ref))

    def get_layer_visibility(self, layer: SULayerRef) -> bool:
        """SULayerGetVisibility -- a DLL inverte uma flag "hidden" interna
        antes de devolver (achado de pseudocodigo real), ja transparente
        aqui: devolve visibilidade real, nao a flag crua."""
        visible = ctypes.c_bool()
        su_check(
            self._dll.SULayerGetVisibility(layer, ctypes.byref(visible)),
            "SULayerGetVisibility",
        )
        return bool(visible.value)

    def set_layer_visibility(self, layer: SULayerRef, visible: bool) -> None:
        """SULayerSetVisibility -- equivalente real do olho (toggle de
        visibilidade) ao lado de cada Etiqueta na Bandeja padrao real."""
        su_check(
            self._dll.SULayerSetVisibility(layer, ctypes.c_bool(visible)),
            "SULayerSetVisibility",
        )

    def get_drawing_element_layer(
        self, drawing_elem: SUDrawingElementRef
    ) -> SULayerRef | None:
        """SUDrawingElementGetLayer devolve SU_ERROR_NO_DATA (9) quando o
        elemento nao tem layer associado (achado de pseudocodigo real) --
        tratado como None, mesmo padrao de get_active_scene()."""
        layer = SULayerRef()
        result = self._dll.SUDrawingElementGetLayer(drawing_elem, ctypes.byref(layer))
        if result == 9:  # SU_ERROR_NO_DATA
            return None
        su_check(result, "SUDrawingElementGetLayer")
        return layer

    def get_default_layer(self, model: SUModelRef) -> SULayerRef:
        """SUModelGetDefaultLayer -- a Etiqueta padrao/"Sem etiquetas" real
        do modelo (toda instancia sem Etiqueta explicita pertence a ela)."""
        layer = SULayerRef()
        su_check(
            self._dll.SUModelGetDefaultLayer(model, ctypes.byref(layer)),
            "SUModelGetDefaultLayer",
        )
        return layer

    def get_instance_tag_name(
        self, model: SUModelRef, instance: SUComponentInstanceRef
    ) -> str:
        """Nome real da Etiqueta da instancia (ComponentInstanceToDrawingElement
        -> SUDrawingElementGetLayer -> SULayerGetName) -- usado pra expor o
        campo `tag` no InstanceDTO (core/mesh_extractor.py), ate entao
        write-only (dava pra atribuir via Ferramentas > Etiqueta mas nunca
        aparecia em lugar nenhum da UI). Instancia sem layer associado
        (None, achado de pseudocodigo real) usa a Etiqueta padrao do
        `model` passado (mesmo padrao de create_tag(model, name))."""
        dll = self._dll
        drawing_elem = dll.SUComponentInstanceToDrawingElement(instance)
        layer = self.get_drawing_element_layer(drawing_elem)
        if layer is None:
            layer = self.get_default_layer(model)
        return self.get_layer_name(layer)

    def create_custom_axes(
        self,
        origin: tuple[float, float, float],
        xaxis: tuple[float, float, float],
        yaxis: tuple[float, float, float],
        zaxis: tuple[float, float, float],
    ) -> SUAxesRef:
        """SUAxesCreateCustom -- `origin`/`xaxis`/`yaxis`/`zaxis` ja devem
        chegar como uma base ORTONORMAL (ver
        core.mesh_extractor.orthonormal_axes_from_points()), senao a DLL
        rejeita com SU_ERROR_GENERIC (6). Coordenadas em POLEGADAS (mesma
        unidade nativa do .skp -- ver core/su_api.py topo do arquivo)."""
        axes = SUAxesRef()
        su_check(
            self._dll.SUAxesCreateCustom(
                ctypes.byref(axes),
                ctypes.byref(SUPoint3D(*origin)),
                ctypes.byref(SUVector3D(*xaxis)),
                ctypes.byref(SUVector3D(*yaxis)),
                ctypes.byref(SUVector3D(*zaxis)),
            ),
            "SUAxesCreateCustom",
        )
        return axes

    def set_definition_axes(
        self, definition: SUComponentDefinitionRef, axes: SUAxesRef
    ) -> None:
        """SUComponentDefinitionSetAxes -- redefine o sistema de eixos
        LOCAL da definicao de um Grupo/Componente (equivalente real de
        "Ferramentas > Eixos"). So LE os valores de `axes` (nao assume
        posse do Ref) -- quem chamou continua responsavel por liberar
        via release_axes()."""
        su_check(
            self._dll.SUComponentDefinitionSetAxes(definition, axes),
            "SUComponentDefinitionSetAxes",
        )

    def release_axes(self, axes: SUAxesRef) -> None:
        su_check(self._dll.SUAxesRelease(ctypes.byref(axes)), "SUAxesRelease")

    def get_model_camera(self, model: SUModelRef) -> dict:
        """Devolve a camera REAL "atual" do modelo (eye/target/up, FOV --
        a mesma que o SketchUp real mostra ao abrir um arquivo ou criar
        um modelo novo a partir de um template, ver REVERSE_ENGINEERING_NOTES.md
        secao 28.23) em vez de so enquadrar pela bounding box como o
        frontend fazia antes. Posicao/alvo/up saem em polegadas, Z-up
        (mesma convencao bruta do resto do DTO) -- conversao pra
        metros/Y-up fica a cargo do frontend.

        `fov_deg`/`fov_is_height` ficam `None` quando a camera nao esta em
        modo perspectiva (SUCameraGetPerspectiveFrustumFOV devolve
        SU_ERROR_NO_DATA=9 nesse caso) -- o frontend cai pro enquadramento
        automatico por bounding box como limitacao aceita (este projeto
        nao implementa projecao paralela "de verdade" vinda do arquivo,
        so a aproximacao ja existente de Camera > Projecao paralela)."""
        camera = SUCameraRef()
        su_check(
            self._dll.SUModelGetCamera(model, ctypes.byref(camera)),
            "SUModelGetCamera",
        )

        eye = SUPoint3D()
        target = SUPoint3D()
        up = SUVector3D()
        su_check(
            self._dll.SUCameraGetOrientation(
                camera, ctypes.byref(eye), ctypes.byref(target), ctypes.byref(up)
            ),
            "SUCameraGetOrientation",
        )

        is_perspective = ctypes.c_bool()
        su_check(
            self._dll.SUCameraGetPerspective(camera, ctypes.byref(is_perspective)),
            "SUCameraGetPerspective",
        )

        fov_deg = None
        fov_is_height = True
        if is_perspective.value:
            fov = ctypes.c_double()
            fov_result = self._dll.SUCameraGetPerspectiveFrustumFOV(
                camera, ctypes.byref(fov)
            )
            if fov_result == 0:
                fov_deg = fov.value
                fov_is_height_c = ctypes.c_bool()
                su_check(
                    self._dll.SUCameraGetFOVIsHeight(
                        camera, ctypes.byref(fov_is_height_c)
                    ),
                    "SUCameraGetFOVIsHeight",
                )
                fov_is_height = fov_is_height_c.value
            elif fov_result != 9:
                su_check(fov_result, "SUCameraGetPerspectiveFrustumFOV")

        return {
            "eye": [eye.x, eye.y, eye.z],
            "target": [target.x, target.y, target.z],
            "up": [up.x, up.y, up.z],
            "perspective": is_perspective.value,
            "fov_deg": fov_deg,
            "fov_is_height": fov_is_height,
        }

    def get_definition_entities(
        self, definition: SUComponentDefinitionRef
    ) -> SUEntitiesRef:
        entities = SUEntitiesRef()
        su_check(
            self._dll.SUComponentDefinitionGetEntities(
                definition, ctypes.byref(entities)
            ),
            "SUComponentDefinitionGetEntities",
        )
        return entities

    def get_definition_always_faces_camera(
        self, definition: SUComponentDefinitionRef
    ) -> bool:
        """True quando o componente tem a opcao "Sempre de frente para a
        camera" ligada (ex.: o personagem de escala dos templates) -- ver
        SUComponentBehavior em core/su_types.py. So expomos esse campo por
        enquanto; os outros 3 (glue-to/shadows/cuts_opening) nao sao
        usados pelo visualizador ainda."""
        behavior = SUComponentBehavior()
        su_check(
            self._dll.SUComponentDefinitionGetBehavior(
                definition, ctypes.byref(behavior)
            ),
            "SUComponentDefinitionGetBehavior",
        )
        return bool(behavior.component_always_face_camera)

    def get_definition_name(self, definition: SUComponentDefinitionRef) -> str:
        name_ref = SUStringRef()
        su_check(self._dll.SUStringCreate(ctypes.byref(name_ref)), "SUStringCreate")
        try:
            su_check(
                self._dll.SUComponentDefinitionGetName(
                    definition, ctypes.byref(name_ref)
                ),
                "SUComponentDefinitionGetName",
            )
            length = ctypes.c_size_t()
            su_check(
                self._dll.SUStringGetUTF8Length(name_ref, ctypes.byref(length)),
                "SUStringGetUTF8Length",
            )
            buf = ctypes.create_string_buffer(length.value + 1)
            actual = ctypes.c_size_t()
            su_check(
                self._dll.SUStringGetUTF8(
                    name_ref, length.value + 1, buf, ctypes.byref(actual)
                ),
                "SUStringGetUTF8",
            )
            return buf.value.decode("utf-8")
        finally:
            self._dll.SUStringRelease(ctypes.byref(name_ref))

    def build_face_mesh(self, face: SUFaceRef) -> dict:
        """Triangula uma face via SUMeshHelper. Devolve vertices/normals
        (arrays planos, 3 floats por vertice) e indices (3 por triangulo,
        0-based -- ver nota em SUMeshHelperGetVertexIndices)."""
        mesh_ref = SUMeshHelperRef()
        su_check(
            self._dll.SUMeshHelperCreate(ctypes.byref(mesh_ref), face),
            "SUMeshHelperCreate",
        )
        try:
            num_vertices = ctypes.c_size_t()
            su_check(
                self._dll.SUMeshHelperGetNumVertices(
                    mesh_ref, ctypes.byref(num_vertices)
                ),
                "SUMeshHelperGetNumVertices",
            )
            num_triangles = ctypes.c_size_t()
            su_check(
                self._dll.SUMeshHelperGetNumTriangles(
                    mesh_ref, ctypes.byref(num_triangles)
                ),
                "SUMeshHelperGetNumTriangles",
            )

            nv = num_vertices.value
            nt = num_triangles.value
            if nv == 0 or nt == 0:
                return {"vertices": [], "normals": [], "indices": []}

            vtx_arr = (SUPoint3D * nv)()
            actual = ctypes.c_size_t()
            su_check(
                self._dll.SUMeshHelperGetVertices(
                    mesh_ref, nv, vtx_arr, ctypes.byref(actual)
                ),
                "SUMeshHelperGetVertices",
            )

            nrm_arr = (SUVector3D * nv)()
            su_check(
                self._dll.SUMeshHelperGetNormals(
                    mesh_ref, nv, nrm_arr, ctypes.byref(actual)
                ),
                "SUMeshHelperGetNormals",
            )

            num_indices = nt * 3
            idx_arr = (ctypes.c_size_t * num_indices)()
            su_check(
                self._dll.SUMeshHelperGetVertexIndices(
                    mesh_ref, num_indices, idx_arr, ctypes.byref(actual)
                ),
                "SUMeshHelperGetVertexIndices",
            )

            vertices: list[float] = []
            for p in vtx_arr:
                vertices.extend((p.x, p.y, p.z))
            normals: list[float] = []
            for v in nrm_arr:
                normals.extend((v.x, v.y, v.z))
            indices = list(idx_arr)[: actual.value]

            return {"vertices": vertices, "normals": normals, "indices": indices}
        finally:
            self._dll.SUMeshHelperRelease(ctypes.byref(mesh_ref))

    # -- modelo ------------------------------------------------------------

    def open_model(self, file_path: str) -> "SketchUpModel":
        """Abre um .skp a partir de um caminho de arquivo, via
        SUModelCreateFromFileWithStatus.

        Validado com um .skp real em Python 3.12 (ver
        REVERSE_ENGINEERING_NOTES.md secao 15): carrega o modelo sem
        precisar do SketchUp instalado/aberto. REQUER Python 3.12 -- em
        Python 3.14.3 esta chamada crasha o processo por uma regressao
        confirmada no ctypes do proprio CPython (nao e um problema da
        SketchUpAPI.dll nem do formato .skp).
        """
        model = SUModelRef()
        path_bytes = os.fspath(file_path).encode("utf-8")
        status = ctypes.c_int(-1)
        su_check(
            self._dll.SUModelCreateFromFileWithStatus(
                ctypes.byref(model), path_bytes, ctypes.byref(status)
            ),
            "SUModelCreateFromFileWithStatus",
        )
        return SketchUpModel(self._dll, model)

    def open_model_from_buffer(self, file_path: str) -> "SketchUpModel":
        """Abre um .skp a partir de um buffer de bytes em memoria, via
        SUModelCreateFromBufferWithStatus -- evita qualquer I/O de
        arquivo dentro da DLL (le o .skp inteiro em bytes no Python e
        passa o buffer direto).

        Validado com um .skp real em Python 3.12 (ver
        REVERSE_ENGINEERING_NOTES.md secao 15). REQUER Python 3.12 --
        mesma regressao do ctypes descrita em open_model().
        """
        with open(file_path, "rb") as f:
            data = f.read()
        return self.open_model_from_bytes(data)

    def open_model_from_bytes(self, data: bytes) -> "SketchUpModel":
        """Abre um .skp a partir de bytes que ja estao em memoria -- usado
        pelo upload via <input type="file"> do navegador (ver
        app/repositories/skp_engine_repository.py open_from_upload()): o
        navegador nunca expoe o caminho real em disco de um arquivo
        escolhido assim, so o conteudo, entao nao ha path pra ler aqui.
        Mesma chamada SUModelCreateFromBufferWithStatus de
        open_model_from_buffer(), que delega pra este metodo depois de ler
        o arquivo do disco."""
        model = SUModelRef()
        status = ctypes.c_int(-1)
        su_check(
            self._dll.SUModelCreateFromBufferWithStatus(
                ctypes.byref(model), data, len(data), ctypes.byref(status)
            ),
            "SUModelCreateFromBufferWithStatus",
        )
        return SketchUpModel(self._dll, model)


class SketchUpModel:
    """Representa um SUModelRef aberto; libera no __exit__/close()."""

    def __init__(self, dll: ctypes.WinDLL, model_ref: SUModelRef):
        self._dll = dll
        self._model = model_ref
        self._closed = False

    def close(self) -> None:
        if not self._closed:
            su_check(self._dll.SUModelRelease(ctypes.byref(self._model)), "SUModelRelease")
            self._closed = True

    def __enter__(self) -> "SketchUpModel":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def get_entities(self) -> SUEntitiesRef:
        entities = SUEntitiesRef()
        su_check(
            self._dll.SUModelGetEntities(self._model, ctypes.byref(entities)),
            "SUModelGetEntities",
        )
        return entities

    @property
    def raw_ref(self) -> SUModelRef:
        """SUModelRef cru -- usado por chamadas que operam no nivel do
        Model, nao de Entities (ex.: SUModelAddLayers em create_tag())."""
        return self._model

    def save(self, file_path: str) -> None:
        """Grava o modelo em disco via SUModelSaveToFile. Pode sobrescrever
        o arquivo original (mesmo path usado em open_model) ou salvar em
        outro caminho."""
        path_bytes = os.fspath(file_path).encode("utf-8")
        su_check(
            self._dll.SUModelSaveToFile(self._model, path_bytes),
            "SUModelSaveToFile",
        )

    def get_units(self) -> int:
        """Retorna o SUModelUnits (int) do modelo via SUModelGetUnits.

        Valores confirmados por assembly real (ver _bind_prototypes):
        0=Polegadas, 1=Pes, 2=Milimetros, 3=Centimetros, 4=Metros -- essa
        ordem segue o SDK publico (model.h) e os dois primeiros valores
        (0 e 1) foram confirmados empiricamente pelo override de
        LengthFormat observado no pseudocodigo real. Usado para
        identificar a unidade real de cada template .skp (ver
        REVERSE_ENGINEERING_NOTES.md secao 24)."""
        units = ctypes.c_int(-1)
        su_check(
            self._dll.SUModelGetUnits(self._model, ctypes.byref(units)),
            "SUModelGetUnits",
        )
        return units.value

    def count_summary(self) -> dict:
        """Retorna contagens básicas (faces/arestas/instâncias) do modelo raiz."""
        entities = self.get_entities()

        num_faces = ctypes.c_size_t()
        su_check(
            self._dll.SUEntitiesGetNumFaces(entities, ctypes.byref(num_faces)),
            "SUEntitiesGetNumFaces",
        )

        num_edges = ctypes.c_size_t()
        su_check(
            self._dll.SUEntitiesGetNumEdges(entities, ctypes.byref(num_edges)),
            "SUEntitiesGetNumEdges",
        )

        num_instances = ctypes.c_size_t()
        su_check(
            self._dll.SUEntitiesGetNumInstances(entities, ctypes.byref(num_instances)),
            "SUEntitiesGetNumInstances",
        )

        return {
            "faces": num_faces.value,
            "edges": num_edges.value,
            "instances": num_instances.value,
        }
