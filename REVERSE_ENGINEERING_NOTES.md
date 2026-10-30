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
