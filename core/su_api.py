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
    SUPoint3D,
    SUVector3D,
    SUTransformation,
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

    def save(self, file_path: str) -> None:
        """Grava o modelo em disco via SUModelSaveToFile. Pode sobrescrever
        o arquivo original (mesmo path usado em open_model) ou salvar em
        outro caminho."""
        path_bytes = os.fspath(file_path).encode("utf-8")
        su_check(
            self._dll.SUModelSaveToFile(self._model, path_bytes),
            "SUModelSaveToFile",
        )

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
