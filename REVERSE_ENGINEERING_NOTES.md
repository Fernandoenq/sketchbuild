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
- Não depende de `ctypes` nem da `SketchUpAPI.dll`.
- Totalmente imune à regressão de ctypes no Python 3.14+.
