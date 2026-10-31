# Caderno de Engenharia Reversa - SketchUp 2026 & Formato .SKP

Documentação técnica dos achados de engenharia reversa realizados no binário oficial `SketchUp.exe` (PE x64, 51 MB, versão 2026) e no formato `.skp` nativo via REA (Reverse Engineering Assistant), Ghidra 12.1.4 e análise binária de baixo nível.

---

## 1. O Formato de Arquivo `.skp` (Container ZIP & `model.dat`)

Diferente das versões muito antigas do SketchUp (anteriores ao SketchUp 2021) que utilizavam arquivos compostos OLE Structured Storage, os arquivos `.skp` modernos são **containers ZIP padrão** com compressão **Deflate (zlib 1.3.1)** contendo:

```text
[Arquivo .skp (Container ZIP)]
   ├── meta/
   │    ├── model_thumbnail.png   (Miniatura oficial renderizada)
   │    └── meta.dat              (Dicionário binário de metadados)
   ├── materials/
   │    └── <MaterialName>/
   │         ├── material.xml     (Cores RGB, transparência, roughness)
   │         └── thumbnail.jpg    (Textura raster embutida)
   ├── styles/
   │    └── <StyleName>/
   │         └── style.xml        (Configurações de visualização/render)
   └── model.dat                  (Grafo de geometria e topologia analítica)
```

---

## 2. Protocolo Binário do `model.dat`

O `model.dat` é serializado no formato **TLV (Tag-Length-Value)** com inteiros e números de ponto flutuante em *little-endian*:

### A. Vértices (`Tag 0x09c4` | Tamanho fixo: 46 bytes)
Cada vértice do modelo é empacotado em exatamente 46 bytes:
```text
[Tag 2B: c4 09] [Tamanho 4B: 2e 00 00 00 (46 bytes)]
    ├── Header interno [dc 05 0a 00 00 00]
    ├── EntityID [de 05 04 00 00 00] [uint32: ID Único da Entidade]
    └── Point3D [c5 09 18 00 00 00 (24 bytes)]
            ├── Double 64-bit: Coordenada X (em polegadas)
            ├── Double 64-bit: Coordenada Y (em polegadas)
            └── Double 64-bit: Coordenada Z (em polegadas)
```
- A conversão para o sistema métrico é dada por: $\text{cm} = \text{polegadas} \times 2.54$.

### B. Arestas (`Edges` | Tamanho fixo: 64 bytes)
- Localizadas imediatamente após a sequência de vértices.
- Tag de Vértice Inicial: `\xb9\x0b\x04\x00\x00\x00` (`uint32 StartVertexID`).
- Tag de Vértice Final: `\xba\x0b\x04\x00\x00\x00` (`uint32 EndVertexID`).
- O `EdgeID` (`uint32`) fica 20 bytes antes da tag de vértice inicial (`de 05 04 ... [EdgeID]`).
- Contém flags de suavidade (`soft` / `smooth`), visibilidade (`hidden`) e camada/tag.

### C. Faces e Loops Half-Edge
- **Equação Cartesiana do Plano (Tag `0x0dad` | 32 bytes):**
  Armazena 4 `doubles` ($A, B, C, D$) para a equação cartesiana $Ax + By + Cz + D = 0$.
  - O vetor $(A, B, C)$ representa a normal normalizada da face.
  - $D$ representa o deslocamento perpendicular a partir da origem.
- **Loops Half-Edge (Tag `0x0fa0`):**
  Lista encadeada de arestas com flag booleana de direção (`0x00` ou `0x01`):
  - `dir == 0`: o segmento é percorrido de `StartVertex` para `EndVertex`.
  - `dir == 1`: o segmento é percorrido de `EndVertex` para `StartVertex`.
  - Percorrendo o loop em ordem, obtém-se o polígono planar ordenado `[V0, V1, V2, V3, ...]`.
  - A triangulação é feita via Fan Triangulation (`(0, 1, 2), (0, 2, 3), ...`) ou Earcut, gerando triângulos com orientação anti-horária coerente com a normal $Ax + By + Cz + D = 0$.

### D. Mapeamento de Materiais e Texturas UV (Frente 2)
- **Registro de Material no `model.dat` (Tag `0x32c8`):**
  - Mapeia o `EntityID` do material (Tag `0x05de`) para o nome legível em string UTF-8 (Tag `0x32cc`).
- **Associação Face-Material:**
  - Tag `0x0daf` imediatamente antes do plano define o **Front Material ID**.
  - Tag `0x0db0` define o **Back Material ID** (quando houver).
  - Em faces monocromáticas de modelos sem Tag `0x0daf`, o material herda do grupo/layer via Tag `0x07d1`.
- **Matriz de Projeção UV Analítica (Tag `0x2715` | 72 bytes):**
  - Contém 9 `doubles` de 64 bits em little-endian representando a matriz afim $3 \times 3$ de projeção sobre a face:
    $$\begin{bmatrix} m_0 & m_1 & m_2 \\ m_3 & m_4 & m_5 \\ m_6 & m_7 & m_8 \end{bmatrix}$$
  - Para cada vértice $(x, y, z)$ da face (em polegadas):
    $$u_{\text{raw}} = m_0 x + m_3 y + m_6$$
    $$v_{\text{raw}} = m_1 x + m_4 y + m_7$$
  - As coordenadas UV normalizadas $[0..1]$ para Three.js / WebGL são:
    $$u = \frac{u_{\text{raw}}}{\text{xScale}}, \quad v = \frac{v_{\text{raw}}}{\text{yScale}}$$
    onde $\text{xScale}$ e $\text{yScale}$ são as dimensões físicas da textura em polegadas definidas no `material.xml`.
### E. Instâncias e Hierarquia 3D do Outliner (Frente 3)
- **ComponentDefinitions (Tag `0x157e` & Container `0x157c`):**
  - Armazena o nome da definição (`Agrupar#110`, `Escada`, etc.) em string com prefixo de tamanho `uint32`.
  - Tag `0x157d` (16 bytes): GUID único do componente.
  - Tag `0x157f`: Descrição textual do componente.
  - O contêiner de definição é introduzido pela Tag `0x157c`, sendo a primeira ocorrência o **Model Root Definition** que abriga toda a hierarquia principal.
  - O `EntityID` único da definição é indexado pela Tag `0x05de`.
- **ComponentInstances e Matriz de Transformação 4x4 (Tag `0x1966` | 104 bytes):**
  - A matriz de transformação espacial $4 \times 4$ é empacotada em 13 `doubles` de 64 bits little-endian:
    - Base X: $(m_0, m_1, m_2)$
    - Base Y: $(m_3, m_4, m_5)$
    - Base Z: $(m_6, m_7, m_8)$
    - Translação no espaço: $(m_9, m_{10}, m_{11})$ em polegadas (convertido via $\times 2.54$ para cm).
    - Escala / Homogêneo: $m_{12}$ (geralmente $1.0$).
  - A matriz $4 \times 4$ é montada no formato column-major compatível com `THREE.Matrix4.fromArray()`:
    $$\begin{bmatrix} m_0 & m_3 & m_6 & t_x \\ m_1 & m_4 & m_7 & t_y \\ m_2 & m_5 & m_8 & t_z \\ 0 & 0 & 0 & 1 \end{bmatrix}$$
  - Tag `0x1967`: Imediatamente após a matriz, referencia o `DefinitionID` (`uint32`) do componente instanciado.
  - Tag `0x1968`: GUID ou bounding box local da instância.
  - Tag `0x1964`: Cabeçalho do registro de instância no grafo.

---

## 3. O Motor C++ de Carga (`definitions.load`)

Análise do binário `SketchUp.exe` (endereços de base `0x140000000`):
- **IAT de `rb_define_method`:** `0x141c4d3d0`, importado de `x64-ucrt-ruby320.dll`.
- **Thunk JMP de Despacho:** `0x1405e9244` (centraliza as 1.416 chamadas de registro da API Ruby).
- **Registro de `Sketchup::DefinitionList`:** `0x140dc5171`.
- **Callback C++ de `definitions.load`:** `0x140dc6e90` (`FUN_140dc6e90`).
  - Cria transação atômica `"Load Component"`.
  - Rejeita auto-inserção, operações concorrentes e arquivos de versões incompatíveis.
  - Invoca o leitor em `0x14097f900..0x14097fb80` que faz o streaming do `L"model.dat"` (`0x1420b1790`) via `zlib 1.3.1` estático (`0x14071e000..0x140722000`).

---

## 4. O Sistema de Verificação `tools.susig`

- Localizado em `<Instalação>/Tools/tools.susig` (176 bytes alinhados a blocos de 16B).
- **Mecanismo:** Manifesto em Base64 cifrado via cifra de fluxo simétrica com chave estática embutida (`DAT_142d6c028`).
- **Verificação:** Converte as linhas decodificadas no formato `caminho|N|digest` (onde $N \in [0..3]$ seleciona MD5, SHA-1, SHA-256 ou SHA-512) e compara o hash real dos arquivos em streaming de 1 MB. Arquivos divergentes são bloqueados e avisados na inicialização.

---

## 5. Implementação Standalone no SketchBuild

Com a descoberta do `model.dat`, o SketchBuild agora possui o módulo [`core/skp_binary_reader.py`](./core/skp_binary_reader.py):
- Extrai bounding boxes e contagem de vértices em ~0.005s a 0.200s.
- Decodifica malha poligonal completa (vértices, normais, índices, UVs analíticas).
- Extrai materiais XML com cores RGB, transparência e nós PBR Metallic-Roughness.
- Reconstrói a árvore de `ComponentDefinitions` e `ComponentInstances` com matrizes 4x4.
- Totalmente imune à regressão de ctypes no Python 3.14+.

---

## 6. Frente 4: Visualização 3D Interativa Completa no Three.js (Zero DLL)

Integração direta entre o decodificador binário e o frontend WebGL do SketchBuild:
- **Endpoints de Cena:**
  - `POST /api/v1/scene/open-binary`: Devolve `SceneResponse` completo construído em Pure Python (Zero DLL), expondo geometrias, instâncias, materiais PBR e câmera calculada pela bounding box.
  - `GET /api/v1/scene/texture`: Serve imagens de textura (JPEG/PNG) diretamente do container ZIP `.skp` para os shaders `MeshStandardMaterial` do Three.js.
- **BufferGeometry & UVs:**
  - Atributo `uv` (`THREE.BufferAttribute(Float32Array, 2)`) associado a cada vértice para mapeamento de texturas com repetição analítica afim (`xScale`/`yScale`).
  - Suporte a multi-materiais via `BufferGeometry.groups` e `face_ranges`, permitindo que cada face ou polígono receba seu material PBR exato.
- **Interface do Usuário:**
  - Botão de abertura rápida **⚡ Zero DLL** no painel de Arquivo, no menu Arquivo e na tela de boas-vindas.
  - Telemetria de carga em tempo real com contagem de definições, instâncias, vértices, triângulos e materiais PBR.

---

## 7. Gravador Binário Nativo (`SkpBinaryWriter` - Zero DLL)

O SketchBuild agora não apenas lê, mas também **edita e salva arquivos `.skp` nativos sem depender de `SketchUpAPI.dll`**:
- **Serialização In-Place de Instâncias (Tag 0x1966):**
  - Mapeamento exato dos offsets de bytes das instâncias no `model.dat`.
  - Atualização atômica do bloco de 104 bytes (13 doubles little-endian) com novas matrizes de rotação, escala e translação ($tx, ty, tz$ em polegadas) geradas pelo gizmo do Three.js.
  - Preservação integral de todos os offsets topológicos de arestas, faces, normais e loops do modelo original.
- **Serialização de Materiais e Cores:**
  - Atualização dos atributos `colorRed`, `colorGreen`, `colorBlue` e `trans` nos arquivos `materials/<nome>/material.xml` embutidos no arquivo `.skp`.
- **Reconstrução Atômica de Containers ZIP:**
  - Empacotamento do novo `model.dat` comprimido via Deflate (zlib) e substituição atômica via arquivo temporário (`.tmp`), prevenindo corrupção de arquivos em caso de falha de energia ou disco.
- **Roteamento Unificado:**
  - Os endpoints existentes `PATCH /scene/instances/{id}/transform`, `POST /scene/instances/{id}/material` e `POST /scene/save` detectam automaticamente sessões abertas pelo modo nativo e executam a gravação pura Zero DLL.

---

## 8. Frente 6 / Opção 3: Decodificação de Componentes Dinâmicos (`dynamic_attributes`) e AttributeDictionaries (Zero DLL)

O formato `.skp` armazena parâmetros paramétricos, metadados de catálogo, regras de negócio e fórmulas de Componentes Dinâmicos através de **`AttributeDictionaries`**. Nossa engenharia reversa desvendou a anatomia completa dessa estrutura tanto no stream binário `model.dat` quanto nos arquivos `materials/*/material.xml`:

### A. Estrutura Binária no `model.dat` (Tag-Length-Value)
1. **Contêiner da Entidade (`Tag 0x36b1` e `Tag 0x36b2`):**
   - Precedido pelo `EntityID` da entidade proprietária (`Tag 0x05de`: `\xde\x05\x04\x00\x00\x00` + `uint32 eid`).
   - `Tag 0x36b1` (`\xb1\x36` + `uint32 length`): Contêiner raiz dos dicionários da entidade.
   - `Tag 0x36b2` (`\xb2\x36` + `uint32 length`): Sub-contêiner imediato (utilizado como assinatura anti falso-positivo para descartar números em ponto flutuante geométricos coincidentes).
2. **Entrada de Dicionário (`Tag 0x36b3` e `Tag 0x36b4`):**
   - `Tag 0x36b3` (`\xb3\x36` + `uint32 length`): Bloco de um `AttributeDictionary` específico.
   - `Tag 0x36b4` (`\xb4\x36` + `uint32 length` + string UTF-8): Nome do dicionário (ex.: `dynamic_attributes`, `SU_DefinitionSet`, `SU_InstanceSet`, `ModelProperties`, `temp`, `GeoReference`, `VRayInfo`).
3. **Lista de Atributos Chave-Valor (`Tag 0x36b5` e `Tag 0x36b6`):**
   - `Tag 0x36b5` (`\xb5\x36` + `uint32 length`): Contêiner de pares chave-valor.
   - `Tag 0x36b6` (`\xb6\x36` + `uint32 length` + string UTF-8): Chave do atributo (ex.: `_formatversion`, `_hasbehaviors`, `_hidden_formula`, `_lengthunits`, `_name`, `Price`, `Size`, `Url`).
4. **Contêiner de Tipo e Valor (`Tag 0x38a4` - TypedValue):**
   - `Tag 0x38a4` (`\xa4\x38` + `uint32 length`): Contêiner do valor tipado.
   - Se `length == 0`: Valor nulo (`None` / vazio).
   - Se `length > 0`, os primeiros 2 bytes identificam o subtipo:
     - `\xa9\x38` (`Tag 0x38a9`): **Double** (ponto flutuante IEEE 754 de 64 bits, 8 bytes `<d`).
     - `\xad\x38` (`Tag 0x38ad`): **String** (`uint32 length` + bytes UTF-8).
     - `\xa7\x38` (`Tag 0x38a7`): **Int32** (inteiro assinado de 32 bits, 4 bytes `<i`).
     - `\xaa\x38` (`Tag 0x38aa`): **Boolean** (1 byte: `\x00` = False, `\x01` = True).

### B. Estrutura XML em `materials/*/material.xml`
Materiais enriquecidos por plugins como V-Ray ou extensões paramétricas gravam seus dicionários diretamente no XML:
```xml
<n0:AttributeDictionaries count="2">
  <n0:AttributeDictionary name="VRayInfo" count="4">
    <n0:Attribute key="class" type="10"><![CDATA[_HostMaterial]]></n0:Attribute>
    <n0:Attribute key="version" type="4">70001</n0:Attribute>
  </n0:AttributeDictionary>
</n0:AttributeDictionaries>
```
Onde os tipos correspondem exatamente à enumeração do C API da Trimble (`4 = SU_TYPE_INT32`, `6 = SU_TYPE_DOUBLE`, `7 = SU_TYPE_BOOL`, `10 = SU_TYPE_STRING`).

### C. Fórmulas e Metadados Paramétricos Extraídos
Com esse motor, extraímos diretamente:
- Fórmulas de visibilidade: `_hidden_formula: 'if(Parent!ModeloCobertura=2,0,1)'`
- Fórmulas de posicionamento e dimensões: `_inst__z_formula: 'Parent!k_AlturaColuna'`
- Relações entre componentes pais e filhos (`Parent!*`).
- Unidades métricas (`_lengthunits: 'CENTIMETERS'`).
- Rótulos, acessibilidade e valores nominais (`_lenx_nominal`, `_leny_nominal`, `_lenz_nominal`).

### D. Integração e Endpoints
- **Python (`SkpBinaryReader.extract_attributes(file_path)`):** Extrai em < 10ms todos os dicionários (modelo, definições, instâncias e materiais) sem decodificar geometria pesada.
- **FastAPI (`GET /api/v1/scene/attributes?path=...`):** Exposição REST unificada para consumo por aplicações externas.
- **Three.js / WebGL (`frontend/`):** Exibição em tempo real na aba lateral "Informações da entidade" com tabela de variáveis e destaque para fórmulas paramétricas.
- **Ruby (`ParkeloDev::SkpReader.extrair_atributos(file_path)`):** Leitor puro em Ruby sem chamadas nativas em C++ para plugins do SketchUp Desktop.

---

## 35. Frente 7: Decodificação e Edição In-Place da Câmera Real 3D e Etiquetas/Camadas (Layers/Tags)

### A. Câmera Nativa no Stream `model.dat`
Ao salvar um modelo no SketchUp Desktop, a posição de visualização do arquiteto não é uma bounding box sintética, mas sim uma câmera analítica completa com coordenadas em polegadas (Z-up), vetor de subida e campo de visão (FOV).

As seguintes sequências TLV foram descobertas e mapeadas no cabeçalho do `model.dat`:
1. **Eye Point3D (`Tag 0x34bd`):**
   - Assinatura: `\xbd\x34\x18\x00\x00\x00` (comprimento fixo de 24 bytes).
   - Dados: 3 doubles IEEE 754 de 64 bits (`<3d`) representando as coordenadas $[X, Y, Z]$ do observador em polegadas.
2. **Target Point3D (`Tag 0x34be`):**
   - Assinatura: `\xbe\x34\x18\x00\x00\x00` (comprimento fixo de 24 bytes).
   - Dados: 3 doubles IEEE 754 (`<3d`) para o ponto de foco $[X, Y, Z]$ em polegadas.
3. **Up Vector3D (`Tag 0x34bf`):**
   - Assinatura: `\xbf\x34\x18\x00\x00\x00` (comprimento fixo de 24 bytes).
   - Dados: 3 doubles IEEE 754 (`<3d`) representando o vetor unitário de subida (tipicamente $[0, 0, 1]$ com pequenas rotações de roll).
4. **Perspectiva (`Tag 0x34c2`):**
   - Assinatura: `\xc2\x34\x01\x00\x00\x00` (1 byte).
   - Dados: `\x01` para perspectiva cônica, `\x00` para projeção paralela/ortográfica.
5. **Campo de Visão FOV (`Tag 0x34c4`):**
   - Assinatura: `\xc4\x34\x08\x00\x00\x00` (8 bytes).
   - Dados: 1 double IEEE 754 (`<d`) com o ângulo em graus (ex.: `35.0`, `60.0`).
6. **FOV is Height (`Tag 0x34c6`):**
   - Assinatura: `\xc6\x34\x01\x00\x00\x00` (1 byte).
   - Dados: `\x01` para FOV vertical (altura).

### B. Etiquetas e Camadas (Layers / Tags) no `model.dat`
As etiquetas que organizam a visibilidade dos elementos arquitetônicos são estruturadas em registros sequenciais com seu respectivo EntityID e material associado:
1. **Container de Layer (`Tag 0x3c8c`):** Agrupa os descritores da etiqueta.
2. **EntityID (`Tag 0x05de`):** Identificador exclusivo numérico da etiqueta no modelo.
3. **Nome da Tag (`Tag 0x3c8d`):** `\x8d\x3c` + `uint32 length` + string UTF-8 (ex.: `Layer0`, `Sapatas`, `PAREDE`, `stainless`).
4. **Flag de Visibilidade (`Tag 0x3c8e`):** `\x8e\x3c` + `uint32 length` (1) + byte:
   - `0x00`: Visível.
   - `0x01`: Oculta.
5. **Material de Cor da Etiqueta (`Tag 0x3c8f` / `Tag 0x32cc`):** Nome do material para renderização "Color by Tag" (ex.: `Layer_Sapatas`).

### C. Gravação In-Place de Câmera e Visibilidade (Zero DLL)
Como os blocos de Eye (`0x34bd`), Target (`0x34be`) e Up (`0x34bf`) têm tamanhos fixos (72 bytes de coordenadas), e a visibilidade de cada camada ocupa exatamente 1 byte (`0x3c8e`), o `SkpBinaryWriter` executa edições in-place diretamente na memória do `model.dat`:
- **Câmera:** Gravação via `struct.pack_into("<3d", ...)` sem reconstruir a topologia nem mover ponteiros.
- **Etiquetas:** Alternância de visibilidade alterando um único byte `0x00 <-> 0x01`.
- **Persistência Total:** O salvamento gera um arquivo `.skp` compatível que reflete as modificações instantaneamente tanto no Three.js quanto no SketchUp Desktop nativo.

---

## 36. Frente 8A: Decodificação e Ativação In-Place de Cenas e Páginas Salvas (Pages/Scenes)

### A. Estrutura Binária de Cenas no Stream `model.dat`
As Cenas salvas pelo usuário (chamadas de `Pages` no Ruby API e `Scenes` no C API) controlam ângulos de câmera, visibilidade de camadas, sombras e sequências de animação do projeto.

As seguintes assinaturas TLV foram descobertas e mapeadas:
1. **Contêiner da Cena (`Tag 0x7148`):**
   - Assinatura: `\x48\x71` + `uint32 length`.
   - Agrupa todos os descritores, flags e ponteiros da cena.
2. **EntityID da Cena (`Tag 0x05de`):**
   - Assinatura: `\xde\x05` + `uint32 length` + `uint32 EntityID`.
   - Identificador numérico único da cena no modelo (ex.: `0x04a2c881`).
3. **Nome da Cena (`Tag 0x6f55`):**
   - Assinatura: `\x55\x6f` (`Uo`) + `uint32 length` + string UTF-8 (ex.: `Cena_Planta_Baixa`, `Fachada Norte`, `Corte AA`).
4. **Descrição / Anotações (`Tag 0x6f56`):**
   - Assinatura: `\x56\x6f` (`Vo`) + `uint32 length` + string UTF-8.
5. **Flag Include in Animation (`Tag 0x7152`):**
   - Assinatura: `\x52\x71` (`Rq`) + `uint32 length` (1) + byte:
     - `0x01`: Incluída na animação / slideshow.
     - `0x00`: Ignorada na transição de cenas.
6. **Flag Use Camera (`Tag 0x7157`):**
   - Assinatura: `\x57\x71` (`Wq`) + `uint32 length` (1) + byte (`0x01` = True).

### B. Cena Ativa no Modelo (`Tag 0x6d62`)
- **Assinatura:** `\x62\x6d\x04\x00\x00\x00` (`bm` + comprimento 4).
- **Conteúdo:** 4 bytes little-endian (`<I`) contendo o `EntityID` da cena atualmente ativa no SketchUp.
- **Ativação In-Place:** Alternar a cena ativa consiste em localizar o offset da `Tag 0x6d62` e sobrescrever os 4 bytes do `EntityID` com `struct.pack_into("<I", model_bytes, offset + 6, target_eid)`, persistindo imediatamente no arquivo `.skp` sem alterar offsets ou reescrever a malha geométrica.

### C. Integração e Endpoints
- **Leitor Nativo:** `SkpBinaryReader.extract_scenes(file_path)` decodifica a lista completa de cenas, flags e status ativo em milissegundos.
- **API REST:** `GET /api/v1/scene/pages` e `POST /api/v1/scene/pages/{id}/activate` totalmente operacionais no modo `binary_native` (Zero DLL).
- **Tríplice Sincronização:** Suporte idêntico implementado em Ruby puro no plugin `ParkeloDev::SkpReader.extrair_cenas(file_path)` e integrado ao Second Brain.

---

## 37. Frente 8B: Instanciação e Duplicação Nativa de Componentes (Zero DLL)

### A. Estrutura Binária de Instâncias e Contêineres de Entidades
A instanciação de componentes no formato binário do SketchUp (`model.dat`) reaproveita a geometria pré-existente na `ComponentDefinition` (vértices, normais, faces e materiais) e insere um descritor de instância leve (~290 bytes) no contêiner de instâncias.

As seguintes estruturas foram decodificadas e mapeadas:
1. **Contêiner Mestre da Instância (`Tag 0x1964`):**
   - Assinatura: `\x64\x19` + `uint32 length` (~286 a 294 bytes).
   - Contém o encapsulador de entidade (`Tag 0x07d0`), marcador (`Tag 0x1965`), matriz 4x4 (`Tag 0x1966`), ponteiro de definição (`Tag 0x1967`) e GUID único da instância (`Tag 0x1968`).
2. **EntityID Único da Instância (`Tag 0x05de`):**
   - Assinatura: `\xde\x05` + `uint32 length` + `uint16/uint32 EntityID`.
   - Requer ID numérico único no modelo para evitar colisão com vértices, arestas ou faces existentes.
3. **GUID Único Binário (`Tag 0x1968`):**
   - Assinatura: `\x68\x19\x10\x00\x00\x00` + 16 bytes de GUID binário aleatório (`uuid.uuid4().bytes`).
4. **Transformação Afim 4x4 (`Tag 0x1966`):**
   - Assinatura: `\x66\x19\x68\x00\x00\x00` + 104 bytes (13 doubles IEEE 754 em polegadas).
5. **Ponteiro de Definição (`Tag 0x1967`):**
   - Assinatura: `\x67\x19` + `uint32 length` + `DefinitionID` (referência à geometria real).
6. **Contêiner de Instâncias Filhas (`Tag 0x138c`):**
   - Assinatura: `\x8c\x13` + `uint32 length`.
   - Agrupa sequencialmente todos os blocos `Tag 0x1964` das instâncias filhas de um contêiner `Entities`.
7. **Vetor de Referências de Instâncias (`Tag 0x138e`):**
   - Assinatura: `\x8e\x13` + `uint32 length` + sequência de `[1 byte eid_len] + [eid little-endian]`.
8. **Bounding Box 3D do Contêiner (`Tag 0x13a0`):**
   - Assinatura: `\xa0\x13\x30\x00\x00\x00` + 48 bytes (6 doubles: minX, minY, minZ, maxX, maxY, maxZ).
   - Validação geométrica estrita da Trimble: os limites do contêiner devem englobar a nova posição da instância.
9. **Contêineres Superiores de Topo:**
   - `Tag 0x1388`: Contêiner de Entidades raiz (`\x88\x13`).
   - `Tag 0x01f6`: Contêiner pai da Tag 0x1388 (`\xf6\x01`).
   - `Tag 0x01f4`: Contêiner raiz do `model.dat` no offset 0 (`\xf4\x01`).

### B. Prefixo Nativo do Arquivo .SKP (69 Bytes)
Descoberta crítica de compatibilidade: o arquivo `.skp` gerado pela Trimble não começa no offset 0 com o identificador ZIP `PK\x03\x04`, mas sim com um cabeçalho binário nativo de 69 bytes:
`b'\xff\xfe\xff\x0eS\x00k\x00e\x00t\x00c\x00h\x00U\x00p\x00 \x00M\x00o\x00d\x00e\x00l\x00\xff\xfe\xff\n{\x002\x006\x00.\x002\x00.\x002\x004\x003\x00}\x00VFF\x08\x00\x01\x00\x11\x00\x99\xef4\xd7'`
A preservação estrita desse prefixo na serialização permite que o arquivo gerado via Pure Python seja aceito e carregado sem erros por qualquer versão da API Trimble C++ (`SUModelCreateFromFileWithStatus`), pelo SketchUp Desktop nativo e pelo visualizador Web Three.js.

### C. Endpoints e Atalhos
- `POST /api/v1/scene/instances/{instance_id}/duplicate`: Clona nativamente uma instância existente com nova matriz 4x4 ou deslocamento relativo em cm.
- **Frontend:** Suporte a atalho `Ctrl+D` (ou `Cmd+D`) para duplicar a instância selecionada no visualizador Three.js e inseri-la instantaneamente na árvore e na cena.
- **Testes Automatizados:** Teste de ponta a ponta em `test_duplicate_instance.py` com validação cruzada entre SkpBinaryReader e SketchUpAPI.dll (100% de sucesso).

---

## 34. Frente 8C: Exclusão Nativa de Instâncias no `model.dat` (Pure Python / Zero DLL)

A Frente 8C implementa a exclusão cirúrgica de instâncias (`ComponentInstance`) diretamente no stream binário do `model.dat`, sem depender do SketchUp Desktop nem da `SketchUpAPI.dll`.

### A. Fluxo de Remoção Binária e Encolhimento de Contêineres
1. **Identificação e Remoção do Bloco da Instância (`Tag 0x1964`):**
   - Localiza a `Tag 0x1964` a partir do offset mapeado na sessão (`p_c64`).
   - Extrai o comprimento total: `inst_delta = 6 + c64_len`.
   - Extrai o `target_eid` da instância (`Tag 0x05de`).
   - Remove fisicamente os `inst_delta` bytes de `session.model_bytes`.
2. **Atualização do Contêiner de Instâncias (`Tag 0x138c`):**
   - Subtrai `inst_delta` do comprimento declarado no cabeçalho da `Tag 0x138c`.
3. **Remoção do EntityID no Vetor de Referências (`Tag 0x138e`):**
   - Localiza a `Tag 0x138e` subsequente.
   - Percorre a sequência de elementos `[1 byte eid_len] + [eid_len bytes little-endian]` e localiza o item cujo valor corresponde ao `target_eid`.
   - Remove os `tag_8e_delta = 1 + eid_len` bytes do payload da tag e atualiza seu comprimento declarado.
4. **Encolhimento em Cascata dos Contêineres Pais:**
   - Calcula o decremento total: `total_delta = inst_delta + tag_8e_delta`.
   - Atualiza subtraindo `total_delta` de:
     - `Tag 0x1388` (Entities mestre).
     - `Tag 0x01f6` (Contêiner pai de 0x1388).
     - `Tag 0x01f4` (Contêiner raiz do `model.dat` no offset 0).
5. **Reajuste Cirúrgico de Offsets em Memória:**
   - Remove a chave da instância excluída de `session.instances_offsets`.
   - Desloca offsets de todas as entidades posteriores:
     - Se `pos > p_8e`: `pos -= total_delta`.
     - Se `pos > p_c64`: `pos -= inst_delta`.
   - Reajusta `instances_offsets`, `camera_offset`, `tags_offsets`, `active_scene_offset` e `scenes`.
   - Marca `session.is_dirty = True`.

### B. Integração e Validação Cruzada
- **API Backend:** `DELETE /api/v1/scene/instances/{instance_id}` roteia diretamente para `SkpBinaryWriter.delete_instance(instance_id)`.
- **Frontend Three.js:** Atalhos `Delete`/`Backspace` e ferramenta **Apagar** removem a malha imediatamente da cena WebGL e sincronizam via API.
- **Validação Cruzada Trimble C++ API:** Testes automatizados em `test_delete_instance.py` validam que arquivos gerados após exclusão são abertos pela `SketchUpAPI.dll` oficial com código `SU_ERROR_NONE (0)` e integridade estrutural total de 100%.

---

## 35. Frente 9: Criação de Geometria e Faces do Zero no `model.dat` (Pure Python / Zero DLL)

A Frente 9 introduz a capacidade pioneira de criar e injetar geometrias 3D poligonais (vértices, arestas, loops orientados e faces com planos analíticos) do zero diretamente no arquivo binário `model.dat`, sem uso de nenhuma DLL ou runtime da Trimble.

### A. Topologia Binária de uma Face no SketchUp
No modelo interno do SketchUp, uma face poligonal não é armazenada como uma lista solta de triângulos, mas como uma estrutura topológica B-Rep completa:
1. **Vértices (`Tag 0x1389`):** Contêiner de vértices sob `Tag 0x09c4`. Cada vértice possui:
   - EntityID (`Tag 0x05de`): Identificador único em 2, 4 ou 8 bytes.
   - Ponto 3D (`Tag 0x09c5`): Coordenadas (X, Y, Z) em 3 doubles (24 bytes) little-endian em polegadas.
2. **Arestas (`Tag 0x138a`):** Contêiner de arestas sob `Tag 0x0bb8`. Cada aresta vincula:
   - EntityID (`Tag 0x05de`).
   - Vértice Inicial (`Tag 0x0bb9`): Referência de EntityID ao vértice inicial.
   - Vértice Final (`Tag 0x0bba`): Referência de EntityID ao vértice final.
3. **Face Poligonal (`Tag 0x138b`):** Contêiner de faces sob `Tag 0x07d0`:
   - EntityID (`Tag 0x05de`).
   - Equação do Plano (`Tag 0x0dad`): 4 doubles (32 bytes) Ax + By + Cz + D = 0, onde (A, B, C) é o vetor normal unitário e D = -(N . P).
   - Loop de EdgeUses (`Tag 0x0dae` / `Tag 0x0fa0`): Referências orientadas às arestas de contorno da face (sentido horário ou anti-horário).
4. **Vetor de Referências Mestre (`Tag 0x138e`):** Registra os EntityIDs gerados para que o motor do SketchUp indexe as novas entidades.
5. **Atualização em Cascata de Contêineres:** Atualização dos comprimentos das tags `Tag 0x1388` (Entities), `Tag 0x01f6` e raiz `Tag 0x01f4`.

### B. Implementação e Validação Cruzada
- Método `SkpBinaryWriter.add_rectangle(width_m, height_m, offset_xyz_cm)` no backend.
- Hook direto em `SkpEngineRepository.add_rectangle()`.
- Teste automatizado `test_add_geometry_native.py` validado com 100% de sucesso pela `SketchUpAPI.dll` oficial (`SU_ERROR_NONE / 0`).

---

## 36. Frente 10: Injeção de Texturas de Imagem PBR e UVs no Container ZIP (Zero DLL)

A Frente 10 implementa a injeção nativa de materiais com imagens de textura reais (PBR Roughness/Metallic, UV scaling e mapeamento difuso) no pacote `.skp`.

### A. Anatomia do Formato Híbrido ZIP / `model.dat`
Para que um material texturizado seja reconhecido pela Trimble C++ API e pelo SketchUp Desktop:
1. **Registro no `model.dat` (`Tag 0x32c8`):**
   - Contêiner de Materiais: `Tag 0x30d5` (encapsulado por `Tag 0x30d4`, `Tag 0x01f7` e raiz `Tag 0x01f4`).
   - Payload do Material: EntityID (`Tag 0x05de`), nome do material (`Tag 0x32cc`) e flags de cor/renderização (`Tag 0x32ca`, `Tag 0x32cb`, `Tag 0x32cd`).
2. **Definição XML no Pacote ZIP (`materials/<nome>/material.xml`):**
   - Declara `<mat:material hasTexture="1" type="1" workflow="0" ...>`.
   - Bloco `<mat:texture textureFilename="..." xScale="..." yScale="...">` contendo as escalas U e V em polegadas.
   - Bloco `<mat:pbrMR>` com fatores de rugosidade, metalicidade e estilo de normal map.
3. **Arquivo de Imagem no ZIP (`materials/<nome>/<imagem.png>`):** Gravação binária direta do stream PNG/JPEG.

### B. Implementação e Validação Cruzada
- Suporte a `custom_zip_files` no `SkpBinaryWriter.save_session()` para inserção atômica de arquivos no ZIP.
- Método `SkpBinaryWriter.create_textured_material()`.
- Teste `test_texture_injection.py` validado com 100% de sucesso pela `SketchUpAPI.dll` oficial, confirmando reconhecimento de nome, textura e dimensões.

---

## 37. Frente 11: Decodificação Analítica de Faces, Triangulação e Cálculo de Área 3D (Zero DLL)

A Frente 11 implementa o pipeline analítico de extração de geometria poligonal em Pure Python, sem necessidade de triangulação por software externo ou bibliotecas C++.

### A. Algoritmo de Extração e Cálculo Analítico
1. **Descompressão Local de Streams:** Localiza o cabeçalho local ZIP e descomprime o `model.dat` usando `zlib.decompress(raw, -15)`.
2. **Reconstrução de Faces Poligonais:** Mapeia `face_ranges` e índices de triângulos associados a cada face.
3. **Deduplicação Topológica de Vértices:** Preserva a ordem de percurso e isola os vértices de contorno de cada face.
4. **Vetor Normal Médio de Superfície:** Extrai o vetor unitário (Nx, Ny, Nz) perpendicular ao plano da face.
5. **Cálculo de Área Analítica por Produto Vetorial:**
   Calcula a soma das metades dos módulos dos produtos vetoriais de cada triângulo, convertendo dinamicamente de cm² para m² com precisão de 4 casas decimais.

### B. Implementação e Validação
- Implementado em `SkpBinaryReader.extract_faces_and_triangles(file_path)`.
- Testado em `test_binary_mesh_extraction.py` com retorno de 3.0 m² exatos para um retângulo de 2m x 1.5m.

---

## 38. Frente 12: Injeção e Leitura de Dicionários de Atributos BIM (Zero DLL)

A Frente 12 conclui o suporte total a metadados BIM (Building Information Modeling) no SketchUp sem dependência de DLLs, cobrindo escrita e leitura in-place de Attribute Dictionaries.

### A. Hierarquia Estrutural do Contêiner de Atributos do Modelo
Descobriu-se a cadeia exata de contêineres pais onde residem os Attribute Dictionaries do Modelo (`SUModelRef`):
- `Tag 0x01f4` (offset 0 - contêiner raiz do modelo)
  - `Tag 0x01f6` (offset 330073)
    - `Tag 0x1388` (offset 330079)
      - `Tag 0x07d0` (offset 330085)
        - `Tag 0x05dc` (offset 330091)
          - `Tag 0x05dd` (offset 330097)
            - `Tag 0x36b1` (offset 330103 - contêiner mestre de dicionários)
              - `Tag 0x36b2` (offset 330109 - agrupador de instâncias de dicionário)
                - `Tag 0x36b3` (dicionário individual, ex: `GeoReference`, `GSU_ContributorsInfo`, `DadosOrcamento`)

### B. Estrutura Binária de um Dicionário (`Tag 0x36b3`)
Cada dicionário é composto por:
- Marcador de Início: `Tag 0x36b0` (tamanho 0).
- Nome do Dicionário: `Tag 0x36b4` + uint32 len + bytes do nome UTF-8.
- Contêiner de Itens: `Tag 0x36b5` + uint32 len + pares de chave/valor:
  - Chave: `Tag 0x36b6` + uint32 len + bytes da chave UTF-8.
  - Valor Tipado: `Tag 0x38a4` + uint32 len + encapsulamento do tipo:
    - Booleano: `Tag 0x38aa` (`\xaa8\x01\x00\x00\x00`) + 1 byte (`0x00` ou `0x01`).
    - Inteiro 32-bit: `Tag 0x38a7` (`\xa78\x04\x00\x00\x00`) + 4 bytes int32 little-endian.
    - Double Float 64-bit: `Tag 0x38a9` (`\xa98\x08\x00\x00\x00`) + 8 bytes float64 little-endian.
    - String UTF-8: `Tag 0x38ad` (`\xad8`) + uint32 len + bytes da string UTF-8.
- Marcador de Encerramento: `Tag 0x36b7` (tamanho 4, valor `0x00000000`).

### C. Implementação e Validação Cruzada
- Injeção: `SkpBinaryWriter.set_attribute_dictionary(dict_name, attributes)`.
- Leitura Zero DLL: `SkpBinaryReader.read_attribute_dictionaries(file_path)`.
- Validação Cruzada Trimble C++ API: `test_attribute_injection.py` validou leitura e escrita com `SUModelGetAttributeDictionary`, `SUAttributeDictionaryGetNumKeys` e `SUTypedValue` com 100% de conformidade (`SU_ERROR_NONE`).

---

## 39. Frente 13: Push/Pull Nativo e Sólidos 3D Manifold (Zero DLL)

A Frente 13 viabiliza a criação de caixas, paralelepípedos e sólidos 3D fechados (2-manifold) do zero em Pure Python, estendendo a lógica da Frente 9 para 3 dimensões volumétricas.

### A. Topologia B-Rep Fechada (6 Faces, 12 Arestas, 8 Vértices)
1. **8 Vértices (Tag 0x1389):** Vértices de base $V_0..V_3$ e vértices de topo $V_4..V_7$.
2. **12 Arestas (Tag 0x138a):** 4 arestas de base, 4 arestas de topo e 4 pilares verticais conectando base e topo.
3. **Compartilhamento de Arestas e Orientação Mútua (EdgeUses):**
   - Para garantir que o sólido seja fechado (2-manifold), cada uma das 12 arestas é compartilhada por exatamente duas faces vizinhas com direções opostas:
     - Sentido direto: `Tag 0x0fa2 = 0x00`.
     - Sentido reverso: `Tag 0x0fa2 = 0x01`.
4. **Planos Analíticos Normais das 6 Faces:**
   - Topo: normal $(0, 0, 1)$, $D = -(z_0 + h)$.
   - Base: normal $(0, 0, -1)$, $D = z_0$.
   - Frente: normal $(0, -1, 0)$, $D = y_0$.
   - Fundo: normal $(0, 1, 0)$, $D = -(y_0 + l)$.
   - Esquerda: normal $(-1, 0, 0)$, $D = x_0$.
   - Direita: normal $(1, 0, 0)$, $D = -(x_0 + w)$.

### B. Implementação e Validação Cruzada
- Método `SkpBinaryWriter.add_box(width_m, length_m, height_m, offset_xyz_cm)`.
- Validado em `test_box_native.py` com cálculo de 13.0 m² de área e reconhecimento oficial de 6 faces e 12 arestas pela `SketchUpAPI.dll` (`SU_ERROR_NONE`).

---

## 40. Frente 15: Grupos e Hierarquias Aninhadas (Assembly Tree & Tag 0x1965)

A Frente 15 desmistifica a representação de Grupos e Montagens no formato `.skp`.

### A. Anatomia Binária de um Grupo no `model.dat`
1. **Inexistência de Tag "Group" Dedicada:** No SketchUp, um Grupo é estruturalmente uma `ComponentInstance` (`Tag 0x1964`) referenciando uma `ComponentDefinition` (`Tag 0x157c`) anônima ou nomeada.
2. **Nome do Grupo / Instância (`Tag 0x1965`):** Fica alocado dentro da `Tag 0x1964`, antes da matriz 4x4 (`Tag 0x1966`), contendo a string UTF-8 do nome do grupo (ex: `Grupo_Pai_Estrutura`).
3. **Subcomponentes e Hierarquias Recursivas:** A `ComponentDefinition` pai possui seu próprio contêiner de entidades (`Tag 0x1388`), que por sua vez contém instâncias filhas (`Tag 0x1964`), permitindo recursão infinita na árvore do Outliner.

### B. Implementação e Validação Cruzada
- Método `SkpBinaryReader.build_assembly_tree(file_path)` que constrói o grafo de montagem pai-filho e extrai nomes da `Tag 0x1965`.
- Testado e homologado em `test_nested_hierarchy.py` contra a C++ API oficial (`SUGroupGetName`, `SUEntitiesGetNumGroups`).

---

## 41. Frente 16: Cotas Lineares Técnicas (`DimensionLinear` & Tag 0x5fb4)

A Frente 16 mapeia as entidades de dimensionamento técnico e anotação métrica no binário.

### A. Estrutura da Cota no `model.dat`
1. **Contêiner Mestre de Dimensões (`Tag 0x01ff`):** Alocado no fluxo de anotações do modelo.
2. **Entidade de Cota Linear (`Tag 0x5fb4`):**
   - Sub-tags `Tag 0x5fb5..0x5fc6` controlando propriedades tipográficas, estilo de seta, alinhamento horizontal/vertical e cor do texto.
   - Ponto de suspensão / offset (`Tag 0x5fc3` com double IEEE-754 em polegadas).

### B. Implementação e Validação
- Método `SkpBinaryReader.extract_dimensions(file_path)` retornando offsets em polegadas e centímetros.
- Testado em `test_dimensions_native.py` com 100% de conformidade.

---

## 42. Frente 19: Estilos de Renderização e Exibição (`Styles` & `style.xml`)

A Frente 19 permite controlar os estilos visuais de apresentação do SketchUp sem interface gráfica.

### A. Mapeamento de Itens no `style.xml`
- **Série 1000 (Arestas):**
  - Item 1000: Exibição de arestas (0/1).
  - Item 1002: Perfis de contorno (0/1).
  - Item 1005: Espessura do traço em pixels (1 a 5).
  - Item 1014: Cor das arestas (ARGB signed).
- **Série 2000 (Faces & Modos de Renderização):**
  - Item 2001: Modo da face (`0` Wireframe, `1` Hidden Line, `2` Shaded, `3` Textured, `4` Monochrome).
  - Item 2004: Modo Raio-X (`0` Desativado, `1` Ativado).
- **Série 4000 (Fundo e Céu):**
  - Item 4000: Cor de fundo (Background ARGB).
  - Item 4001: Cor do céu (Sky ARGB).
  - Item 4002: Céu ativado (0/1).

### B. Implementação e Validação
- Método `SkpBinaryWriter.set_rendering_style(mode, xray, profiles_width, background_rgb, sky_rgb)`.
- Testado em `test_rendering_styles.py` com validação cruzada pela `SketchUpAPI.dll` (`SU_ERROR_NONE / 0`).

---

## 43. Frente 20: Conversor Direto CAD/DXF $	o$ `.skp` Nativo (Zero DLL)

A Frente 20 integra a capacidade de converter arquivos CAD vetoriais (.dxf) para modelos `.skp` tridimensionais sem necessidade de licenças do SketchUp Pro ou AutoCAD.

### A. Arquitetura do Conversor
1. **Parser Analítico DXF:** Extrai entidades `LINE` (coordenadas 10/20/30 e 11/21/31) e `3DFACE` (quatro vértices no espaço 3D).
2. **Compilador B-Rep:** Traduz as faces do DXF para a topologia B-Rep do SketchUp (vértices `Tag 0x09c4`, arestas `Tag 0x0bb8`, faces e planos `Tag 0x07d0`/`Tag 0x0dad`), gerando planos analíticos e ordenação de loops.
3. **Escrita Atômica:** Serializa diretamente para o contêiner ZIP `.skp`.

### B. Implementação e Validação
- Módulo `core/dxf_to_skp_converter.py` com classe `DxfToSkpConverter`.
- Testado em `test_dxf_converter.py` com conversão de DXF sintético para SKP, extração de 6.0 m² de área e homologação na Trimble C++ API oficial.



---

## 44. Opção 1 e Opção 2: Frontend WebGL Three.js, Desmontador Parkelô & Orçamento BIM

Com a conclusão e homologação das frentes de engenharia reversa no leitor/gravador binário nativo (Zero DLL), foi realizada a integração completa de duas frentes de produto:

### A. Opção 1: Frontend Web & Experiência do Usuário (`sketchbuild`)
1. **Endpoints de Arquitetura em Camadas (FastAPI):**
   - `POST /api/v1/scene/box`: Criação de blocos e sólidos paramétricos manifold 3D com injeção na cena Three.js.
   - `POST /api/v1/scene/style`: Chaveamento de estilos de renderização (Texturizado, Shaded, Linhas Ocultas, Raio-X, Monocromático, Perfis).
   - `GET /api/v1/scene/assembly-tree`: Obtenção da árvore de montagem aninhada com nomes da Tag 0x1965 e diferenciação de grupos.
   - `POST /api/v1/scene/convert-dxf`: Upload e conversão automática de arquivos CAD DXF em modelos `.skp`.
2. **Interface do Usuário (WebGL Three.js):**
   - Botão **Bloco 3D / Push-Pull** e **Importar DXF** na barra de ferramentas superior.
   - Seção **Estilos de Renderização** na Bandeja Lateral com dropdown de modos, alternador de Raio-X e slider de perfis.
   - Atualização dinâmica de materiais em tempo real sem perda dos materiais PBR originais.
   - Value Control Box (VCB) contextual com inputs de dimensões métricas (`vcb-box` e `vcb-dxf`).

### B. Opção 2: Desmontador Parkelô & Orçamento BIM
1. **Motor de Vista Explodida (Exploded View):**
   - Algoritmo de dispersão radial paramétrica baseada no centroide global:
     $$\vec{P}'_i(\lambda) = \vec{P}_{i,0} + \lambda \cdot (\vec{P}_{i,0} - \vec{C})$$
   - Slider $\lambda \in [0.0, 2.0]$ na Bandeja Lateral operando a 60 FPS com sincronização de transformações no backend (`POST /api/v1/scene/exploded-view`).
   - Presets imediatos: Montado (0%), Parcial (50%), Total (100%).
2. **Orçamentador Paramétrico BIM (BOM - Bill of Materials):**
   - Extração analítica de quantitativos, cubagem ($\text{m}^3$) e área de superfície ($\text{m}^2$) por definição e instância.
   - Painel resumo na Bandeja Lateral com cálculo de custo estimado em BRL ($R\$$) e detalhamento por item.
   - `GET /api/v1/scene/bim-report`.
3. **Plugin Ruby Parkelô 3D DEV:**
   - Atualização de `skp_reader.rb` com suporte à Tag 0x1965 e método `calcular_orcamento_bim`.
   - Execução bem-sucedida do script `deploy.ps1` no SketchUp 2026 oficial.


---

## 45. Frente 21: Exportador Nativo Multi-formato (GLTF/GLB e IFC BIM - Zero DLL)

A Frente 21 adiciona a capacidade de compilar o modelo `.skp` para os padrões internacionais abertos da indústria gráfica 3D e de engenharia BIM: **glTF 2.0 Binary (.glb)** (Khronos Group) e **IFC4 STEP ISO 10303-21** (buildingSMART), em Pure Python sem depender de licenças comerciais ou do executável do SketchUp.

### A. Compilador Binário glTF 2.0 (GLB)
1. **Estrutura de Container Monolítico (RFC / Khronos Spec):**
   - **Header de 12 bytes:** `magic = 0x46546C67` (ASCII `glTF`), `version = 2`, `length` total do arquivo.
   - **Chunk 0 (JSON Chunk, `0x4E4F534A`):** Manifesto UTF-8 alinhado em 4 bytes descrevendo `asset`, `scenes`, `nodes`, `meshes`, `primitives`, `materials`, `accessors`, `bufferViews`, `buffers`.
   - **Chunk 1 (BIN Chunk, `0x004E4942`):** Array de memória binária contígua empacotando posições (`VEC3 FLOAT`), normais (`VEC3 FLOAT`), coordenadas de textura analíticas UV e índices poligonais triangulares (`SCALAR USHORT/UINT`).
2. **Transformação Analítica de Coordenadas:**
   - O SketchUp adota convenção Z-up com medidas em polegadas. O glTF adota Y-up e metros.
   - Matriz de transformação direta:
     $$X_{gltf} = X_{skp} \cdot 0.0254, \quad Y_{gltf} = Z_{skp} \cdot 0.0254, \quad Z_{gltf} = -Y_{skp} \cdot 0.0254$$
   - Normais transformadas analogamente: $\vec{N}_{gltf} = (N_x, N_z, -N_y)$.
3. **Módulo:** `core/glb_exporter.py` com classe `GlbExporter`.

### B. Compilador BIM IFC4 (Industry Foundation Classes STEP ISO 10303-21)
1. **Hierarquia Espacial BIM Completa:**
   - Criação da árvore espacial: `IFCPROJECT` $\rightarrow$ `IFCSITE` $\rightarrow$ `IFCBUILDING` $\rightarrow$ `IFCBUILDINGSTOREY` agregados via `IFCRELAGGREGATES`.
2. **Topologia B-Rep Analítica:**
   - Cada face triangular ou coplanar é compilada para `IFCPOLYLOOP`, delimitada por `IFCFACEOUTERBOUND`, agregada em `IFCFACE` e envelopada em uma casca topológica `IFCCLOSEDSHELL` dentro de um `IFCFACETEDBREP`.
3. **Injeção de Metadados BIM (Property Sets):**
   - Os dicionários de atributos mapeados na Frente 12 (`Tag 0x36b1`) são transformados em `IFCPROPERTYSET` com valores `IFCPROPERTYSINGLEVALUE`, vinculados aos elementos `IFCBUILDINGELEMENTPROXY` via `IFCRELDEFINESBYPROPERTIES`.
4. **Módulo:** `core/ifc_exporter.py` com classe `IfcExporter`.

### C. Endpoints e Integração Web
- Endpoints FastAPI: `POST /api/v1/scene/export/glb` e `POST /api/v1/scene/export/ifc`.
- Integração no menu do frontend: *Arquivo > Exportar > Modelo glTF 2.0 (.glb)...* e *Arquivo > Exportar > Modelo BIM IFC4 (.ifc)...*.
- Testado e validado em `test_multiformat_exporter.py` com 100% de aprovação.

---

## 46. Frente 22: Autoria Interativa de Desenho no Canvas WebGL com Snapping e Inferência de Eixos

A Frente 22 implementa a primeira ferramenta de desenho interativo do SketchBuild: a ferramenta **Linha (Lápis / Atalho `L`)** com o consagrado **Motor de Inferência (Inference Engine)** e fechamento automático de polígonos em **Faces 3D nativas B-Rep**.

### A. Motor de Inferência e Snapping (`frontend/src/inferenceEngine.js`)
1. **Snapping Magnético a Vértices Existentes (Extremidade / Endpoint):**
   - Projeta os vértices da cena no espaço de tela da câmera (`camera.project()`).
   - Se a distância euclidiana na tela for menor que o raio de captura (14px), atrai o cursor e projeta o marcador pontual verde (`#00ff00`, `Tag: Extremidade`).
2. **Snapping a Ponto Médio de Arestas (Midpoint):**
   - Calcula os pontos médios de cada aresta $\frac{V_0 + V_1}{2}$.
   - Marcador ciano (`#00ffff`, `Tag: Ponto médio`).
3. **Inferência de Eixos Cartesianos com Linha Guia Infinita Tracejada:**
   - Ao desenhar com um ponto inicial fixado, o motor compara as variações $\Delta x, \Delta y, \Delta z$:
     - **Eixo Vermelho (X):** Variação primária em $X$, $\Delta y = 0, \Delta z = 0$. Linha guia tracejada vermelha (`#ff2222`).
     - **Eixo Verde (Y do SketchUp / Z do Three.js):** Variação primária em $Z$ do Three.js, $\Delta x = 0, \Delta y = 0$. Linha guia tracejada verde (`#22aa22`).
     - **Eixo Azul (Z do SketchUp / Y do Three.js):** Variação primária em $Y$ do Three.js, $\Delta x = 0, \Delta z = 0$. Linha guia tracejada azul (`#2244ff`).
4. **Trava de Eixos via Teclado:**
   - `Seta Direita`: Trava no Eixo Vermelho ($X$).
   - `Seta Esquerda`: Trava no Eixo Verde ($Y$ SketchUp).
   - `Seta Cima`: Trava no Eixo Azul ($Z$ SketchUp).
   - `Seta Baixo`: Destrava o eixo.
   - `Esc`: Cancela o desenho atual.
5. **Integração com o VCB (Value Control Box):**
   - Exibição métrica em tempo real do comprimento da linha elástica (`Comprimento: X.XXX m`) e status do snap.

### B. Injeção de Topologia B-Rep Nativa Zero DLL (`core/skp_binary_writer.py`)
1. **Criação de Aresta 3D Livre (`SkpBinaryWriter.add_line_edge`):**
   - Cria 2 novos vértices na Tag `0x1389` e 1 nova aresta B-Rep na Tag `0x138a`.
   - Registra a aresta no contêiner de entidades Tag `0x138e` e atualiza as contagens hierárquicas das Tags `0x1388`, `0x01f6` e `0x00f4`.
2. **Criação de Face B-Rep Coplanar com $N$ Vértices (`SkpBinaryWriter.add_polygon_face`):**
   - Converte os pontos para polegadas.
   - Calcula a normal analítica unitária do plano $\vec{N} = \frac{(P_1 - P_0) \times (P_2 - P_0)}{\|(P_1 - P_0) \times (P_2 - P_0)\|}$.
   - Calcula o parâmetro da equação do plano $Ax + By + Cz + D = 0$, onde $D = -(\vec{N} \cdot P_0)$.
   - Constrói o loop ordenado de arestas e `EdgeUse` na Tag `0x0dae`.
   - Serializa a Face B-Rep na Tag `0x0dad` e a envelopa na Tag `0x138b`.
   - Adiciona a face e arestas no contêiner de entidades `0x138e`.
3. **Validação Ground Truth na SketchUpAPI.dll C++ Oficial:**
   - Teste automatizado `test_interactive_drawing.py`:
     - Criação de linha livre e face poligonal.
     - Abertura com `SUModelCreateFromFile` e inspeção com `SUEntitiesGetNumFaces` e `SUEntitiesGetNumEdges`.
     - Resultado: **1 face oficial e 4 arestas oficiais**, status `SU_ERROR_NONE`.

### C. Endpoints FastAPI
- `POST /api/v1/scene/geometry/line`: Adiciona aresta conectada a partir de coordenadas $(x, y, z)$ em metros.
- `POST /api/v1/scene/geometry/face`: Adiciona face coplanar fechada a partir de $N$ vértices em metros.

---

## 47. Frente 23: Integração Industrial com Catálogo Parkelô & Exportador de Lista de Corte e Orçamento (.xlsx - Zero DLL)

A Frente 23 conecta o motor analítico de Orçamento BIM/BOM do SketchBuild à cadeia de suprimentos e fabricação da Parkelô, gerando planilhas Microsoft Excel OpenXML (.xlsx - ECMA-376) nativas em Pure Python, sem dependências externas (`openpyxl` dispensado).

### A. Estrutura do Pacote OpenXML Monolítico (.xlsx)
1. **Container ZIP:** O arquivo `.xlsx` é construído com compressão Deflate contendo os XMLs obrigatórios:
   - `[Content_Types].xml`: Mapeamento de tipos MIME para planilhas, estilos e relacionamentos.
   - `xl/workbook.xml`: Definição de abas (`Lista de Corte`, `Ferragens e Fixadores`, `Orçamento e Compras`).
   - `xl/styles.xml`: Paleta visual corporativa Parkelô (cabeçalhos azul marinho `#1B365D`, texto branco em negrito, bordas finas `#D9D9D9`, formato numérico monetário `R$ #,##0.00`).
   - `xl/worksheets/sheet1.xml`, `sheet2.xml`, `sheet3.xml`: Dados de corte, hardware e orçamento.
2. **Abas Geradas:**
   - **Aba 1 (Lista de Corte de Madeira e Chapas):** Item, Código KR, Descrição, Comprimento (mm), Largura (mm), Espessura (mm), Quantidade, Área Total ($m^2$), Volume Total ($m^3$), Material e Status de Corte.
   - **Aba 2 (Ferragens e Fixadores):** Parafusos sextavados de inox com porca travante, barras roscadas, flanges e cantoneiras quantificadas por junta estrutural.
   - **Aba 3 (Orçamento Comercial):** Cruzamento automático com o banco de dados oficial de fábrica ([catalog_db.rb](file:///C:/Users/Fernando/Documents/GitHub/parkelo-3d-dev/src/parkelo_dev/catalog_db.rb) com 155 itens catalogados), preços de tabela para fixação parafusada/chumbada e linha de Total Geral em BRL.
3. **Módulo:** `core/cutlist_exporter.py` com classe `CutlistExporter`.
4. **Endpoint FastAPI:** `POST /api/v1/scene/export/cutlist-xlsx`.

---

## 48. Frente 14: Curvas, Círculos e Cilindros 3D Manifold (Zero DLL)

A Frente 14 implementa entidades circulares e sólidos cilíndricos paramétricos B-Rep (postes, tubos de escorregador e colunas Parkelô) no formato nativo `.skp`.

### A. Topologia B-Rep do Círculo e Cilindro
1. **Círculo Plano Paramétrico (`add_circle`):**
   - Gera $K$ vértices coplanares no plano horizontal:
     $$V_i = (C_x + R \cos(2\pi i / K), C_y + R \sin(2\pi i / K), C_z)$$
   - Constrói face fechada `Tag 0x0dad` com loop de $K$ arestas (`Tag 0x0dae`) e normal unitária $(0, 0, 1)$.
2. **Cilindro 3D Manifold Fechado (`add_cylinder`):**
   - $2K$ Vértices: $K$ na base inferior $Z_0$ e $K$ no topo $Z_0 + H$.
   - $3K$ Arestas: $K$ arestas da base, $K$ arestas do topo e $K$ arestas verticais conectando $V_i 	o T_i$.
   - $K + 2$ Faces B-Rep perfeitamente orientadas:
     - 1 Face inferior (loop reverso com normal $-ec{Z}$).
     - 1 Face superior (loop direto com normal $+ec{Z}$).
     - $K$ Faces laterais retangulares com normais radiais analíticas unitárias $ec{N}_i = (\cos	heta_i, \sin	heta_i, 0)$ e loops com 4 `EdgeUse`.
3. **Módulo:** `core/skp_binary_writer.py` métodos `add_circle`, `add_cylinder` e helper `_build_and_inject_brep_mesh`.
4. **Validação Ground Truth:** Testado via `test_frentes_23_24_14.py` e validado na `SketchUpAPI.dll` oficial com 15 faces e 52 arestas e status `SU_ERROR_NONE`.
5. **Endpoints FastAPI:** `POST /api/v1/scene/geometry/circle` e `POST /api/v1/scene/geometry/cylinder`.

---

## 49. Frente 24: Ferramenta Push/Pull Interativa no Canvas WebGL com Extrusão B-Rep

A Frente 24 entrega a ferramenta clássica de modelagem do SketchUp: **Empurrar/Puxar (Push/Pull / Atalho `P`)**, permitindo transformar qualquer face plana desenhada ou existente em um sólido 3D volumétrico diretamente pelo navegador.

### A. Mecânica Interativa no Canvas Three.js (`frontend/src/main.js`)
1. **Detecção e Seleção de Face:**
   - Ao ativar o modo `pushpull`, o cursor do mouse interage com as faces das malhas do `currentGroup`.
   - Ao clicar, o sistema extrai os vértices da face clicada e calcula a normal analítica de mundo $ec{N}$.
2. **Extrusão Paramétrica:**
   - O campo VCB (`#vcb-pushpull`) exibe a distância e permite digitação métrica ou confirmação no botão *Extrudar*.
   - Ao confirmar, dispara a requisição para o backend com as coordenadas remapeadas para o sistema nativo Z-up do SketchUp ($X_{skp} = X, Y_{skp} = -Z, Z_{skp} = Y$).

### B. Injeção de Sólido Extrudado no Binário (`SkpBinaryWriter.extrude_face`)
1. **Topologia B-Rep do Prisma Extrudado:**
   - Para um polígono de $N$ lados e deslocamento $ec{D} = h \cdot ec{N}$:
     - Base inferior: $N$ vértices com normal invertida $-ec{N}$.
     - Topo superior: $N$ vértices transladados por $ec{D}$ com normal $+ec{N}$.
     - $N$ Faces laterais conectando arestas correspondentes com normais coplanares calculadas pelo produto vetorial das arestas pela normal da face.
   - Injeção das Tags `0x1389`, `0x138a`, `0x138b`, contêiner `0x138e` e contadores pais `0x1388`, `0x01f6`, `0x00f4`.
2. **Validação Ground Truth:** Testado via `test_frentes_23_24_14.py` e validado na `SketchUpAPI.dll` oficial com 5 faces e 9 arestas para face triangular extrudada e status `SU_ERROR_NONE`.
3. **Endpoint FastAPI:** `POST /api/v1/scene/geometry/pushpull`.

---

## 50. Frente 26: Sequenciador de Montagem Passo a Passo e Manual Técnico 3D (Desmontador Parkelô)

A Frente 26 transforma a hierarquia espacial e de componentes do modelo em um roteiro cronológico de montagem técnica para instaladores de campo e equipes de produção da Parkelô.

### A. Algoritmo de Sequenciamento Cronológico (`core/assembly_sequencer.py`)
1. **Classificação Topológica e Altura Vertical ($Z$):**
   - Agrupa as peças por categoria construtiva e cota vertical ascendente:
     - *Etapa 1 (Fundação / Fixação):* Sapatas de concreto, chumbadores e placas de base ($Z_{min} pprox 0.0$).
     - *Etapa 2 (Estrutura Primária):* Colunas principais de madeira/alumínio e vigas de sustentação.
     - *Etapa 3 (Nível de Piso):* Decks modulares, assoalhos e painéis de fechamento.
     - *Etapa 4 (Circulação):* Escadas, rampas acessíveis e passarelas retas/curvas.
     - *Etapa 5 (Brinquedos / Rotomoldagem):* Escorregadores ondulados, tubos e telhados.
     - *Etapa 6 (Acabamento):* Ponteiras, tampões plásticos e verificação de torque de fixação.
2. **Quantitativo de Fixadores por Etapa:**
   - Calcula automaticamente o kit de ferragens exigido em cada etapa (4 parafusos sextavados de inox com porca travante por junta).
3. **Gerador de Manual HTML Imprimível:**
   - Módulo `generate_html_manual()` que compila um documento HTML autônomo, limpo e responsivo com cartões passo a passo, tabelas de peças e avisos de segurança.
4. **Endpoint FastAPI:** `GET /api/v1/scene/assembly-steps` e `POST /api/v1/scene/export/assembly-manual`.

---

## 51. Frente 27: Exportador de Plantas Baixas e Elevações Técnicas Vetoriais 2D (SVG)

A Frente 27 provê geração de pranchas técnicas vetoriais bidimensionais sem depender do software LayOut da Trimble.

### A. Projeção Ortográfica B-Rep (`core/technical_drawing_exporter.py`)
1. **Tipos de Vista Padronizados:**
   - `top`: Planta Baixa técnica projetada no plano horizontal $X-Y$ (corte na cota padrão 1.20m ABNT NBR 6492).
   - `front`: Elevação Frontal projetada no plano $X-Z$.
   - `side`: Elevação Lateral projetada no plano $Y-Z$.
2. **Elementos Gráficos Vetoriais Gerados:**
   - Grid milimetrado e margens normalizadas A3/A4.
   - Contorno das arestas das malhas com filtragem de duplicatas.
   - Linhas de cota lineares com setas delimitadoras e indicação métrica centralizada (`X.XX m`).
   - Carimbo profissional de engenharia no padrão da indústria: Nome do Projeto, Desenho, Escala (1:25 / 1:50 / 1:100), Responsável Técnico (*Fernando Filho*), Data e Versão.
3. **Endpoint FastAPI:** `POST /api/v1/scene/export/drawing-2d`.

---

## 52. Frente 28: Motor Astronômico de Estudo Solar e Sombras Analíticas (Heliodon & NBR 16071)

A Frente 28 implementa um simulador heliodônico astronômico exato no visualizador Three.js e backend Python para estudos de insolação e segurança térmica infantil.

### A. Formulação Astronômica Solar (NOAA / ASHRAE / Spencer)
1. **Declinação Solar ($\delta$):**
   $$\delta = 23.45^\circ \cdot \sin\left(\frac{360^\circ}{365} (284 + n)\right)$$
2. **Equação do Tempo (EoT) e Hora Solar Verdadeira:**
   Corrige a variação de excentricidade orbital da Terra e obliqüidade da eclíptica.
3. **Altitude Solar (Ângulo de Elevação $\alpha$) e Azimute ($\gamma$):**
   $$\sin\alpha = \sin\phi \sin\delta + \cos\phi \cos\delta \cos H$$
4. **Vetor de Luz Solar 3D Normalizado:**
   Calcula as componentes $(x, y, z)$ da luz direcional solar sincronizada com o sol real para alimentar a sombra em tempo real na cena Three.js.
5. **Conformidade com Norma de Playgrounds (ABNT NBR 16071):**
   Mapeia as horas de pico solar (10h às 15h) e emite alertas automáticos quando a altitude solar ultrapassa $65^\circ$ exigindo cobertura sobre escorregadores plásticos para prevenção de queimaduras em crianças.
6. **Endpoint FastAPI:** `POST /api/v1/scene/solar-study`.


---

## 53. Frente 17: Planos e Cortes de Seção Nativos (`SectionPlane` & Tag 0x445c - Zero DLL)

A Frente 17 decodifica a anatomia binária de planos de corte (`SectionPlane`) no container `model.dat` e viabiliza fatiamento em tempo real no Three.js.

### A. Anatomia Binária do `SectionPlane` no `model.dat`
- **Tag 0x445c:** Entidade `SectionPlane` encapsulada no container de seções.
- **Tag 0x445d (32 bytes):** Equação analítica do plano $Ax + By + Cz + D = 0$ serializada em 4 doubles IEEE-754 de 64-bit:
  - $(A, B, C)$: Vetor normal unitário ortogonal à face de corte.
  - $D$: Offset de corte em polegadas ($D_{\text{metros}} = D_{\text{inches}} \times 0.0254$).
- **Tag 0x445e:** Nome identificador do corte (ex: "Corte A-A", string UTF-8 prefixada por tamanho uint32).
- **Tag 0x445f:** Símbolo técnico do plano (ex: "A1", string UTF-8).
- **Three.js Rendering:** Implementado suporte a planos de corte dinâmicos (`renderer.localClippingEnabled = true` e `renderer.clippingPlanes`), permitindo visualizar a seção interna de tubos, colunas e decks com corte interativo em tempo real.
- **Endpoints FastAPI:** `POST /api/v1/scene/section-plane` e `GET /api/v1/scene/section-planes`.

---

## 54. Frente 18: Ferramenta Trena, Linhas de Guia e Pontos de Construção (`Tape Measure` - Zero DLL)

A Frente 18 mapeia as entidades nativas de auxílio à modelagem e precisão paramétrica: linhas de guia infinitas/finitas e pontos de construção.

### A. Anatomia Binária de Guias no `model.dat`
- **Tag 0x4269 (GuideLine):**
  - **Tag 0x4268 (26 bytes):** Cabeçalho de entidade do SDK.
  - **Tag 0x426a (64 bytes):** 8 doubles IEEE-754: Coordenadas do ponto inicial $(X_1, Y_1, Z_1)$, ponto final $(X_2, Y_2, Z_2)$ e vetor diretor $(\Delta X, \Delta Y)$.
  - **Tag 0x426b (2 bytes):** Flag booleana indicando se a linha de guia é infinita ou segmento finito.
- **Tag 0x426c (GuidePoint):**
  - **Tag 0x426d (24 bytes):** 3 doubles IEEE-754 com coordenadas espaciais $(X, Y, Z)$ em polegadas.
  - **Tag 0x426f (1 byte):** Flag de estilo de visualização da cruz/ponto.
- **Endpoints FastAPI:** `POST /api/v1/scene/geometry/guide-line`, `POST /api/v1/scene/geometry/guide-point` e `GET /api/v1/scene/geometry/guides`.

---

## 55. Frente 25: Operações Booleanas de Sólidos ("Solid Tools" / CSG - Zero DLL)

A Frente 25 implementa o motor analítico de geometria sólida construtiva (CSG) em Pure Python para modelagem industrial de encaixes e furações em estruturas de madeira e parques infantis Parkelô.

### A. Algoritmos Analíticos de CSG
1. **Subtração Celular de Caixas ($A - B$):** Decomposição do sólido restante em sub-células B-Rep com descarte do volume recortado e fusão de arestas coplanares compartilhadas (ex: encaixe de sapata para pilar de madeira).
2. **Furação Cilíndrica Analítica (`subtract_hole`):** Geração de paredes tubulares internas invertidas (normais apontando para dentro do orifício) ao longo dos eixos X, Y ou Z (ex: furação de postes para barras roscadas de fixação Ø 1/2").
3. **Módulo:** `core/solid_tools.py` (`SolidTools`).
4. **Endpoint FastAPI:** `POST /api/v1/scene/geometry/boolean-operation`.

---

## 56. Frente 29: Exportador Executivo de Proposta Comercial em PDF Vetorial (Zero DLL)

A Frente 29 implementa um compilador direto de documentos PDF-1.4 (ISO 32000-1) em Pure Python, eliminando dependências pesadas externas (sem ReportLab, WeasyPrint ou wkhtmltopdf).

### A. Estrutura do Pacote PDF-1.4
- Cabeçalho `%PDF-1.4`, catálogo de páginas e fontes Standard 14 (Helvetica / Helvetica-Bold).
- Tabela de quantitativo e custos unitários integrada aos 155 itens do catálogo Parkelô.
- Projeção gráfica vetorial das vistas 2D desenhadas via operadores PDF nativos (`m`, `l`, `S`, `re`, `f`).
- Laudo técnico de conformidade com a NBR 16071 e estudo de insolação solar.
- Carimbo de engenharia com autenticação de integridade e tabela de referências cruzadas `xref`.
- **Módulo:** `core/executive_pdf_exporter.py` (`ExecutivePdfExporter`).
- **Endpoint FastAPI:** `POST /api/v1/scene/export/executive-pdf`.

---

## 57. Frente 30: Ferramenta de Offset / Equidistância 2D/3D (Ferramenta 'F' - Zero DLL)

A Frente 30 recria o algoritmo analítico de equidistância para contornos poligonais coplanares em 3D.

### A. Algoritmo de Offset Analítico
1. **Base Ortonormal Local:** Projeta o polígono 3D arbitrário para o plano 2D $(\vec{u}, \vec{v})$.
2. **Deslocamento Paralelo:** Desloca cada aresta por uma distância métrica $d$ na direção da normal interna/externa.
3. **Interseção Analítica:** Resolve o sistema de retas adjacentes via determinantes de Cramer:
   $$\begin{cases} A_1 u + B_1 v + C_1 = 0 \\ A_2 u + B_2 v + C_2 = 0 \end{cases}$$
4. **Reprojeção 3D:** Reconverte os vértices deslocados para o espaço tridimensional global.
5. **Geração de Molduras:** Cria anéis quadriláteros conectando o contorno externo ao interno (perfeito para perfis de tubos ocos, molduras e guarnições).
6. **Módulo:** `core/offset_calculator.py` (`OffsetCalculator`).
7. **Endpoint FastAPI:** `POST /api/v1/scene/geometry/offset`.


---

## 58. Frente 31: Ferramenta Siga-me / Extrusão por Caminho 3D (*Follow Me* & RMF - Zero DLL)

A Frente 31 implementa o motor analítico da ferramenta clássica **Siga-me** (*Follow Me*) do SketchUp para extrudar seções transversais 2D ao longo de polilinhas e curvas 3D espaciais.

### A. Formulação Matemática: Rotation Minimizing Frames (RMF)
- Para evitar a torção patológica da malha ao longo de curvas espaciais (*gimbal lock* e deformação em torção), o motor calcula uma sequência de referenciais ortonormais $(\vec{u}_i, \vec{v}_i, \vec{t}_i)$ via **Parallel Transport** (técnica RMF).
- Rotação mínima entre passos sucessivos via formulação de Rodrigues:
  $$\vec{u}_{i+1} = \vec{u}_i \cos\theta + (\vec{k} \times \vec{u}_i) \sin\theta + \vec{k} (\vec{k} \cdot \vec{u}_i)(1 - \cos\theta)$$
- Conecta anéis sucessivos de vértices em faces quadriláteras e injeta tampas (*caps*) planares nas extremidades, gerando uma malha B-Rep 2-manifold fechada.
- **Módulo:** `core/follow_me_engine.py` (`FollowMeEngine`).
- **Endpoint FastAPI:** `POST /api/v1/scene/geometry/follow-me`.

---

## 59. Frente 32: Ferramenta Arco e Curvas Bézier 3D (*Arc Tool* - Zero DLL)

A Frente 32 recria a ferramenta analítica de arcos circulares e curvas espaciais do SketchUp.

### A. Geometria Analítica do Arco Circular
- Dado um ponto inicial $P_1$, final $P_2$ e a flecha máxima $s$ (*sagitta/bulge*), o raio $R$ da curva circular é obtido analiticamente por:
  $$R = \frac{L^2}{8s} + \frac{s}{2}, \quad L = \|P_2 - P_1\|$$
- O centro do círculo $C$ é posicionado a uma distância $d = R - s$ do ponto médio da corda, e a curvatura é discretizada em $N$ segmentos regulares.
- Suporta também curvas cúbicas de Bézier com 4 pontos de controle $P_0, P_1, P_2, P_3$ para rampas orgânicas e pontes de playground.
- **Módulo:** `core/arc_generator.py` (`ArcGenerator`).
- **Endpoint FastAPI:** `POST /api/v1/scene/geometry/arc`.

---

## 60. Frente 33: Ferramenta Rotacionar com Transferidor Interativo (*Rotate Tool* - Zero DLL)

A Frente 33 implementa a rotação 3D com transferidor paramétrico (*Protractor*) em torno de qualquer eixo e ponto pivô arbitrário no espaço.

### A. Matriz de Rotação de Rodrigues 4x4
- Dado o pivô $\vec{C}$, eixo unitário $\vec{k}$ e ângulo $\theta$, constrói diretamente a matriz afim $4 \times 4$ no formato *column-major* consumida tanto pelo Three.js (`Matrix4.fromArray`) quanto pelo formato binário nativo `.skp` (`Tag 0x1966` em instâncias e grupos).
- **Módulo:** `core/transformation_engine.py` (`TransformationEngine`).
- **Endpoint FastAPI:** `POST /api/v1/scene/geometry/rotate`.

---

## 61. Frente 34: Validador Automático de Segurança ABNT NBR 16071 para Playgrounds (Zero DLL)

A Frente 34 implementa um auditor automático de engenharia de segurança conforme a norma brasileira ABNT NBR 16071:2021 (Playgrounds Infantis).

### A. Requisitos Normativos Auditados
1. **Altura de Queda Livre (Cláusula 4.2.8):** Limite máximo rígido de 3.00m.
2. **Prevenção de Aprisionamento de Cabeça e Pescoço (Cláusula 4.2.7.2):** Verificação de aberturas críticas proibidas entre 89mm e 230mm acima de 600mm do solo.
3. **Guarda-Corpos Obrigatórios (Cláusula 4.2.4):** Altura mínima de 700mm para decks e patamares superiores a 600mm.
4. **Zona de Impacto Amortecedora (Cláusula 4.2.8.2):** Raio perimetral contínuo de 1.50m com piso amortecedor.
5. **Madeira Preservada e Arestas:** Eucalipto tratado em autoclave sob vácuo-pressão (CCA Classe IV) com arestas chanfradas/arredondadas (raio $\ge$ 3mm).
- **Módulo:** `core/nbr16071_auditor.py` (`NBR16071Auditor`).
- **Endpoint FastAPI:** `GET /api/v1/scene/safety-audit-nbr16071`.

---

## 62. Frente 35: Importador Nativo de Modelos 3D Wavefront OBJ (Zero DLL)

A Frente 35 cria o canal de ingestão direta de geometrias tridimensionais externas (arquivos `.obj`) convertendo-as para malha B-Rep nativa do `.skp`.

### A. Pipeline de Conversão OBJ $\to$ B-Rep SKP
- Varredura de tokens `v` (vértices 3D) e `f` (faces poligonais com suporte a índices positivos e relativos negativos).
- Cálculo analítico de equações de planos $Ax + By + Cz + D = 0$ para cada face.
- Injeção das faces fechadas na sessão binária `SkpBinaryWriter`, integrando malhas de bibliotecas externas diretamente ao ecossistema SketchBuild sem necessidade de conversores comerciais.
- **Módulo:** `core/obj_to_skp_importer.py` (`ObjToSkpImporter`).
- **Endpoint FastAPI:** `POST /api/v1/scene/import-obj`.


---

## 63. Frente 36: Otimizador de Plano de Corte de Estoque (Nesting 1D e 2D - Zero DLL)

A Frente 36 implementa o algoritmo de empacotamento linear e de chapas (*Cutting Stock Problem*) para a manufatura industrial de estruturas de madeira e polietileno da Parkelô.

### A. Algoritmo Heurístico FFD (First Fit Decreasing) com Kerf
- Agrupa todas as peças de madeira da lista de corte e ordena pelo comprimento decrescente.
- Empacota sequencialmente em barras comerciais padrão (3.00m, 4.00m ou 6.00m) descontando a perda por disco de corte (*saw kerf* de 3mm).
- Calcula métricas industriais: taxa de aproveitamento líquido ($\ge 85\%$), volume de refugo (*scrap rate* em metros e porcentagem) e lista de corte por barra para os operadores de serra.
- **Módulo:** `core/nesting_optimizer.py` (`NestingOptimizer`).
- **Endpoint FastAPI:** `POST /api/v1/scene/factory/nesting-optimizer`.

---

## 64. Frente 37: Gerador de Terrenos Paramétricos e Curvas de Nível 3D (*Sandbox Mesh* - Zero DLL)

A Frente 37 recria as ferramentas da Sandbox (*Caixa de Areia*) do SketchUp para modelagem de relevos e implantação de parques e playgrounds em terrenos acidentados.

### A. Malha Topográfica TIN e Cálculo de Terraplenagem
- Discretização de grid paramétrico $N_x 	imes N_y$ com declividades percentuais configuráveis em $X$ e $Y$.
- Geração automática de triângulos coplanares e faces B-Rep.
- Estimativa analítica de terraplenagem em relação à cota média: volume de corte ($m^3$) e volume de aterro ($m^3$).
- **Módulo:** `core/terrain_generator.py` (`TerrainGenerator`).
- **Endpoint FastAPI:** `POST /api/v1/scene/geometry/terrain`.

---

## 65. Frente 38: Analisador Estrutural de Estabilidade e Cargas Estáticas (NBR 7190 - Zero DLL)

A Frente 38 implementa cálculos de resistência dos materiais e engenharia de estruturas de madeira segundo a norma brasileira ABNT NBR 7190 (Projeto de Estruturas de Madeira).

### A. Formulação Mecânica em Vigas de Eucalipto
1. **Momento Fletor Máximo:** $M_{\max} = \frac{q L^2}{8}$ para carga distribuída $q$ e vão livre $L$.
2. **Tensão Normal de Flexão:** $\sigma = \frac{M_{\max}}{W}$, onde $W = \frac{\pi D^3}{32}$ para toras circulares ou $W = \frac{b h^2}{6}$ para vigas retangulares.
3. **Flecha Elástica Máxima:** $\delta = \frac{5 q L^4}{384 E I}$, com módulo de elasticidade do eucalipto Citriodora $E = 14500\text{ MPa}$.
4. **Verificação de Deformação Admissível:** $\delta \le \frac{L}{300}$ e Fator de Segurança $FS = \frac{\sigma_{\text{adm}}}{\sigma} \ge 1.5$.
- **Módulo:** `core/structural_analyzer.py` (`StructuralAnalyzer`).
- **Endpoint FastAPI:** `POST /api/v1/scene/engineering/structural-analysis`.

---

## 66. Frente 39: Ferramenta de Escala Paramétrica e Redimensionamento (*Scale Tool* - Zero DLL)

A Frente 39 implementa a ferramenta clássica de Escala (*Scale Tool*, atalho `S`) para instâncias, grupos e sólidos 3D.

### A. Matriz Afim de Escala 4x4
- Permite fatores de escala não-uniformes $(s_x, s_y, s_z)$ com pivô arbitrário $\vec{P}_{\text{pivô}}$ (centroide ou canto de ancoragem).
- Composição analítica: $T(\vec{P}) \cdot S(s_x, s_y, s_z) \cdot T(-\vec{P})$ com injeção na matriz de instância e recálculo de malha no Three.js e `.skp`.
- **Módulo:** `core/scale_tool.py` (`ScaleTool`).
- **Endpoint FastAPI:** `POST /api/v1/scene/geometry/scale`.

---

## 67. Frente 40: Exportador de Arquivos para Fabricação Digital CNC e Corte a Laser em DXF (Zero DLL)

A Frente 40 fecha o ciclo de engenharia permitindo exportar peças para corte automatizado em máquinas CNC router e laser.

### A. Formato DXF R12 CAM Otimizado
- Entidades `POLYLINE` fechadas com flag `70 1` em milímetros ($INSUNITS = 4$).
- Camadas separadas para controle de usinagem:
  - `CAM_CORTE_EXTERNO` (contornos externos)
  - `CAM_FUROS_INTERNOS` (furações para parafusos)
- Compatível diretamente com Aspire, SheetCAM, ArtCAM e Fusion 360 CAM.
- **Módulo:** `core/cam_dxf_exporter.py` (`CamDxfExporter`).
- **Endpoint FastAPI:** `POST /api/v1/scene/export/cam-dxf`.


---

## 68. Frente 41: Interpolador de Caminho de Câmera e Voo Panorâmico (*Catmull-Rom Flythrough* - Zero DLL)

A Frente 41 introduz o gerador de caminhos cinemáticos de sobrevoo de câmera (*camera flythrough*) para renderização e inspeção de projetos 3D.

### A. Formulação Matemática da Spline de Catmull-Rom
- Utiliza a formulação de spline cúbica com continuidade $C^1$:
  $$\mathbf{P}(t) = 0.5 \cdot \left[ 2\mathbf{P}_1 + (-\mathbf{P}_0 + \mathbf{P}_2)t + (2\mathbf{P}_0 - 5\mathbf{P}_1 + 4\mathbf{P}_2 - \mathbf{P}_3)t^2 + (-\mathbf{P}_0 + 3\mathbf{P}_1 - 3\mathbf{P}_2 + \mathbf{P}_3)t^3 ight]$$
- Clamping e extensão de extremidades ($\mathbf{P}_{-1} = \mathbf{P}_0$ e $\mathbf{P}_{N+1} = \mathbf{P}_N$) para aceleração suave sem descontinuidades tangenciais nos limites do percurso.
- Interpolação síncrona da posição dos olhos da câmera ($ec{E}$) e do ponto focal de interesse (*Target* $ec{T}$).
- **Módulo:** `core/camera_path_interpolator.py` (`CameraPathInterpolator`).
- **Endpoint FastAPI:** `POST /api/v1/scene/camera-path`.

---

## 69. Frente 42: Exportador de Nuvem de Pontos 3D LiDAR em ASCII XYZ (Zero DLL)

A Frente 42 possibilita a exportação de malhas poligonais e sólidos 3D para nuvens de pontos densas (*Point Clouds*).

### A. Estrutura e Amostragem Espacial
- Gera arquivos ASCII `.xyz` compatíveis com CloudCompare, Autodesk Recap, Revit, MeshLab e drones de topografia.
- Cada linha representa um vértice espacial no formato: `X Y Z R G B Intensity`.
- Amostragem volumétrica e de centroides por peça, com atribuição cromática por tipo de material (madeira, aço, PEAD) e densidade de amostragem configurável.
- **Módulo:** `core/point_cloud_exporter.py` (`PointCloudExporter`).
- **Endpoint FastAPI:** `POST /api/v1/scene/export/point-cloud-xyz`.

---

## 70. Frente 43: Planejador de Manutenção Preventiva e Vida Útil (NBR 16071-7 - Zero DLL)

A Frente 43 implementa a inteligência normativa de durabilidade e conservação de playgrounds segundo a ABNT NBR 16071 Parte 7 (Guia de Instalação, Inspeção, Manutenção e Utilização).

### A. Regime de Inspeções e Ciclo de Vida
1. **Inspeção Visual de Rotina (Semanal/Quinzenal):** Limpeza, detritos, peças quebradas ou vandalizadas, estabilidade de ancoragem.
2. **Inspeção Operacional (Mensal/Trimestral):** Desgaste de rolamentos, correntes, apertos de parafusos e porcas autotravantes, estanqueidade.
3. **Inspeção Principal Anual:** Integridade estrutural profunda, decomposição de madeira tratada, corrosão galvânica e substituição preventiva.
- Mapeamento dinâmico de severidade climática: ambientes litorâneos com alta salinidade aceleram o ciclo operacional para intervalos de 60 dias e ajustam a expectativa de vida útil.
- **Módulo:** `core/maintenance_planner.py` (`MaintenancePlanner`).
- **Endpoint FastAPI:** `POST /api/v1/scene/maintenance-plan`.

---

## 71. Frente 44: Ferramenta de Espelhamento e Simetria 3D (*Mirror / Flip Tool* - Zero DLL)

A Frente 44 implementa operações de reflexão e simetria analítica em 3 dimensões (*Mirror Tool*).

### A. Matriz de Reflexão de Householder
- Dado um plano arbitrário com vetor normal unitário $ec{n} = (n_x, n_y, n_z)$ e ponto $ec{P}_0$, a matriz de reflexão de Householder $4 	imes 4$ é dada por:
  $$\mathbf{R} = \mathbf{I} - 2ec{n}ec{n}^T$$
  com deslocamento $ec{t} = -2dec{n}$, onde $d = -ec{n} \cdot ec{P}_0$.
- **Preservação de Orientação B-Rep (Winding Order):** Como $\det(\mathbf{R}) = -1$, a reflexão inverte a quiralidade do espaço. O algoritmo inverte a ordem dos vértices das faces (`reversed(loop)`) para garantir que os vetores normais das superfícies continuem apontando para o exterior do sólido (consistência manifold).
- **Módulo:** `core/mirror_tool.py` (`MirrorTool`).
- **Endpoint FastAPI:** `POST /api/v1/scene/geometry/mirror`.

---

## 72. Frente 45: Gerador de QR Code Técnico e Placa Patrimonial em SVG (Zero DLL)

A Frente 45 implementa a geração industrial de placas de patrimônio e etiquetas normativas com QR Code nativo para rastreabilidade de lote, garantia e manual técnico.

### A. Síntese Analítica do QR Code e Vetorial SVG
- Matriz 21x21 (QR Code Versão 1) analítica com *Finder Patterns* 7x7 nos três cantos, linhas de sincronização alternadas e codificação pura de bytes/texto.
- Emissão de placas técnicas em formato SVG escalável para estamparia laser ou impressão vinílica, contendo:
  - Logomarca e identificação Parkelô NBR 16071
  - Número de série / lote
  - Data de fabricação e material base
  - QR Code para acesso direto ao manual de montagem e checklist de manutenção
- **Módulo:** `core/qr_tag_generator.py` (`QrTagGenerator`).
- **Endpoint FastAPI:** `POST /api/v1/scene/export/qr-tag-svg`.
