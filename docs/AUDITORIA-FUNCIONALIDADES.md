# Auditoria de funcionalidades (gerada por `tools/auditar_frentes.py`)

Arquivo gerado. Não editar à mão: rode `python tools/auditar_frentes.py`. Regra dos selos no cabeçalho do script.

## Resumo

| Selo | Módulos | Significado |
|---|---|---|
| VALIDADO | 13 | conferido contra o SketchUp real, a SketchUpAPI.dll ou golden |
| TESTADO | 164 | teste automatizado cita o módulo, mas só confere consistência interna (sem oráculo) |
| SEM TESTE | 20 | usado pelo app ou por outro módulo, nenhum teste o cita |
| ORFAO | 1 | nem o app, nem outros módulos, nem testes o usam |

Total: 198 módulos em `core/`, 33167 linhas. Módulos com palavra de alerta (simul, mock, placeholder, etc.): 38.

Rigor dos testes das frentes (`test_frentes_*.py`): 389 asserts frouxos (limite mínimo, tipo de entidade, presença) contra 311 de valor exato.

**Leitura honesta:** só VALIDADO tem prova de fidelidade ao SketchUp. TESTADO significa que o código faz o que o
próprio teste espera, o que não prova que o resultado bate com o SketchUp ou com a norma citada.

## ORFAO (1)

| Módulo | Linhas | Descrição | Testes | App/rotas | DLL | Alertas |
|---|---|---|---|---|---|---|
| `core/unhide_entities_engine.py` | 114 | SketchBuild - Motor de Reexibição de Entidades Ocultas (Zero DLL / Pure Python) | - | - | - | - |

## SEM TESTE (20)

| Módulo | Linhas | Descrição | Testes | App/rotas | DLL | Alertas |
|---|---|---|---|---|---|---|
| `core/technical_drawing_exporter.py` | 215 | SketchBuild - Compilador de Desenhos Técnicos Vetoriais 2D (Plantas Baixas e Elevações) | - | 1 | - | aproxima |
| `core/art_report_generator.py` | 153 | Gerador de Minuta Técnica de ART / RRT em PDF Vetorial (Zero DLL / Pure Python). | - | 1 | - | simul |
| `core/spiral_tube_generator.py` | 150 | Gerador de Tubos e Tobogãs Espirais Paramétricos 3D (Zero DLL). | - | 1 | - | aproxima |
| `core/zebra_label_exporter.py` | 142 | Exportador de Etiquetas Térmicas Zebra ZPL II para Fábrica (Zero DLL). | - | 1 | - | simul |
| `core/hic_simulator.py` | 126 | Simulador de Impacto e Altura Crítica de Queda HIC (NBR 16071-3 / EN 1177 - Zero DLL). | - | 1 | - | simul |
| `core/wall_thickness_inspector.py` | 125 | Inspetor de Espessura de Parede e Casca Fina (Wall Thickness Inspector - Zero DLL). | - | 1 | - | mock |
| `core/swing_kinematics_simulator.py` | 95 | Simulador de Cinemática e Envelope de Segurança para Balanços (NBR 16071 - Zero DLL). | - | 1 | - | simul |
| `core/field_inspection_exporter.py` | 383 | Exportador de Ficha de Inspeção e Checklist de Campo Offline (NBR 16071-7 - Zero DLL). | - | 1 | - | - |
| `core/assembly_sequencer.py` | 211 | SketchBuild - Sequenciador de Montagem Passo a Passo e Manual Técnico 3D | - | 1 | - | - |
| `core/cargo_load_optimizer.py` | 145 | Otimizador de Carregamento de Carga e Cubagem 3D (Cargo Load Optimizer - Zero DLL). | - | 1 | - | - |
| `core/solar_calculator.py` | 141 | SketchBuild - Motor Astronômico de Estudo Solar e Sombras Analíticas | - | 1 | - | - |
| `core/technical_sketch_shader.py` | 119 | Renderizador e Filtro Estilizado de Linha Oculta e Esboço Técnico (Zero DLL). | - | 1 | - | - |
| `core/hip_roof_generator.py` | 112 | Gerador de Telhados de Quatro Águas e Piramidais Paramétricos (Zero DLL). | - | 1 | - | - |
| `core/angle_dimension_tool.py` | 110 | Ferramenta de Cota Angular e Medição de Transferidor 3D (Angle Dimension - Zero DLL). | - | 1 | - | - |
| `core/overturn_stability_calculator.py` | 110 | Calculador de Centro de Gravidade e Estabilidade ao Tombamento (NBR 16071 / NBR 6123 - Zero DLL). | - | 1 | - | - |
| `core/obj_exporter.py` | 99 | Exportador OBJ standalone -- equivalente parcial do menu | - | 1 | sim | - |
| `core/cache_malhas.py` | 93 | Cache em disco da malha (triangulos) de cada definicao grande (04/11/2026, | - | - | - | - |
| `core/exploded_view_trail_tool.py` | 93 | Ferramenta de Linhas de Trajetória para Vista Explodida (Zero DLL). | - | 1 | - | - |
| `core/fastener_torque_optimizer.py` | 87 | Otimizador de Parafusos, Fixadores e Torque de Aperto (NBR 7190 / ISO 898 - Zero DLL). | - | 1 | - | - |
| `core/carbon_footprint_calculator.py` | 74 | Calculador de Pegada de Carbono e Sustentabilidade de Madeira (Zero DLL). | - | 1 | - | - |

## TESTADO (164)

| Módulo | Linhas | Descrição | Testes | App/rotas | DLL | Alertas |
|---|---|---|---|---|---|---|
| `core/mini_wind_cfd_2d_engine.py` | 114 | Motor de Túnel de Vento Numérico CFD 2D em Python Puro (Mini Wind CFD 2D - Zero DLL). | test_frentes_116_a_145.py | 1 | - | aproxima, simul |
| `core/cutlist_exporter.py` | 401 | SketchBuild - Compilador Nativo de Lista de Corte e Orçamento Industrial em Excel .xlsx | test_cutlist_exporter.py, test_frentes_23_24_14.py | 1 | - | aproxima |
| `core/sheet_nesting_2d_engine.py` | 242 | SketchBuild - Motor de Plano de Corte e Nesting 2D Guilhotinado para Marcenaria (Zero DLL / Pure Python) | test_frentes_layout_e_marcenaria_avancada.py | 1 | - | simul |
| `core/su_types.py` | 212 | Tipos base da C API pública da Trimble (SketchUpAPI.dll). | test_attribute_injection.py, test_box_native.py, test_cylinder_and_extrusion.py... | 1 | sim | stub |
| `core/construction_guide_engine.py` | 198 | SketchBuild - Motor de Linhas Guia e Auxiliares de Construção (Zero DLL / Pure Python) | test_opcao_a_parte_8_sketchup_native.py | 1 | - | simul |
| `core/freehand_curve_engine.py` | 171 | Motor da Ferramenta Mão Livre do SketchUp (Freehand Tool - Zero DLL). | test_opcao_a_parte_4_sketchup_native.py | 1 | - | aproxima |
| `core/from_contours_sandbox_engine.py` | 169 | SketchBuild - Motor de Caixa de Areia a Partir de Contornos (Zero DLL / Pure Python) | test_opcao_a_parte_8_sketchup_native.py | 1 | - | aproxima |
| `core/infinite_guide_engine.py` | 165 | SketchBuild - Motor de Linhas e Pontos de Construção Infinitos (Zero DLL / Pure Python) | test_frentes_71_a_75.py | 1 | - | simul |
| `core/shadow_heliodon_engine.py` | 163 | SketchBuild - Motor de Sombras e Heliodon Integrado (Zero DLL / Pure Python) | test_frentes_66_a_70.py | 1 | - | aproxima |
| `core/slicing_3d_print_engine.py` | 159 | Motor de Fatiamento e Exportação para Impressão 3D (3D Slicing & G-Code / STL & 3MF - Zero DLL). | test_frentes_106_a_115.py | 1 | - | aproxima |
| `core/match_photo_engine.py` | 148 | Motor de Adequar Fotografia do SketchUp (Match Photo Engine - Zero DLL). | test_opcao_a_sketchup_native.py | 1 | - | aproxima |
| `core/dolly_fov_lens_engine.py` | 145 | Motor de Dolly de Câmera, Campo de Visão (FOV) e Lente Fotográfica do SketchUp (Zero DLL). | test_opcao_a_parte_4_sketchup_native.py | 1 | - | aproxima |
| `core/steel_profile_engine.py` | 144 | Motor de Perfis Estruturais Metálicos Paramétricos NBR 8800 (Structural Steel Profiles - Zero DLL). | test_frentes_106_a_115.py | 1 | - | aproxima |
| `core/hydraulic_piping_engine.py` | 134 | Motor de Tubulações Hidráulicas, Conexões e Perda de Carga NBR 5626 (Hydraulic Piping - Zero DLL). | test_frentes_106_a_115.py | 1 | - | aproxima |
| `core/reinforced_concrete_beam_engine.py` | 133 | Motor de Vigas de Concreto Armado no Estado Limite Último ABNT NBR 6118 (RC Beam ELU - Zero DLL). | test_frentes_116_a_145.py | 1 | - | aproxima |
| `core/rigid_body_physics_engine.py` | 125 | Motor de Simulação de Cinemática e Corpos Rígidos (Rigid Body Physics - Zero DLL). | test_frentes_106_a_115.py | 1 | - | simul |
| `core/add_detail_sandbox_engine.py` | 124 | Engine de Engenharia Reversa da Ferramenta Adicionar Detalhe (Add Detail Tool) da Caixa de Areia. | test_opcao_a_parte_6_sketchup_native.py | 1 | - | aproxima |
| `core/nbr16071_auditor.py` | 124 | Auditor Automático de Segurança e Conformidade ABNT NBR 16071 (Zero DLL). | test_frentes_31_a_35.py | 1 | - | simul |
| `core/photometric_spot_light_engine.py` | 120 | SketchBuild - Lâmpadas Fotométricas e Holofotes Spot (Zero DLL / Pure Python) | test_frentes_91_a_95.py | 1 | - | aproxima |
| `core/voronoi_fracture_engine.py` | 119 | SketchBuild - Padrões Voronoi e Painéis Vazados Paramétricos 3D (Zero DLL / Pure Python) | test_frentes_101_a_105.py | 1 | - | aproxima |
| `core/walk_camera_gravity_engine.py` | 116 | Engine de Engenharia Reversa da Ferramenta Percorrer (Walk Tool) com Gravidade e Colisao. | test_opcao_a_parte_6_sketchup_native.py | 1 | - | simul |
| `core/thermal_comfort_engine.py` | 111 | Motor de Conforto Térmico e Transmitância Térmica NBR 15220 (Thermal Transmittance - Zero DLL). | test_frentes_106_a_115.py | 1 | - | aproxima |
| `core/solar_photovoltaic_array_engine.py` | 103 | Motor de Usinas Solares Fotovoltaicas e Geração Distribuída (Solar PV Array - Zero DLL). | test_frentes_116_a_145.py | 1 | - | aproxima |
| `core/stormwater_drainage_engine.py` | 103 | Motor de Drenagem Pluvial, Calhas e Condutores ABNT NBR 10844 (Stormwater Drainage - Zero DLL). | test_frentes_116_a_145.py | 1 | - | aproxima |
| `core/sewer_network_gravity_engine.py` | 101 | Motor de Redes Coletoras de Esgoto Sanitário por Gravidade ABNT NBR 9649 (Sewer Network - Zero DLL). | test_frentes_116_a_145.py | 1 | - | aproxima |
| `core/bim_4d_gantt_schedule_engine.py` | 99 | Motor de Planejamento BIM 4D e Cronograma Físico-Financeiro Gantt (BIM 4D Schedule - Zero DLL). | test_frentes_116_a_145.py | 1 | - | simul |
| `core/ventilated_facade_engine.py` | 96 | Motor de Fachadas Ventiladas e Câmara Convectiva de Ar (Ventilated Facade - Zero DLL). | test_frentes_116_a_145.py | 1 | - | simul |
| `core/wind_pressure_engine.py` | 96 | SketchBuild - Simulação de Vento e Pressão Dinâmica NBR 6123 (Zero DLL / Pure Python) | test_frentes_101_a_105.py | 1 | - | simul |
| `core/construction_site_logistics_engine.py` | 92 | Motor de Logística de Canteiro e Interferência de Gruas NR-18 (Site Logistics - Zero DLL). | test_frentes_116_a_145.py | 1 | - | simul |
| `core/skp_binary_writer.py` | 2395 | SketchBuild - Gravador Binário Nativo de Arquivos .SKP (Pure Python / Zero DLL) | test_add_geometry_native.py, test_attribute_injection.py, test_binary_mesh_extraction.py... | 2 | sim | - |
| `core/glb_exporter.py` | 317 | - | test_multiformat_exporter.py | 1 | - | - |
| `core/executive_pdf_exporter.py` | 299 | Exportador de Proposta Executiva e Prancha Técnica em PDF Nativo (Zero DLL). | test_frentes_17_18_25_29_30.py | 1 | - | - |
| `core/cabinet_hardware_drilling_engine.py` | 268 | SketchBuild - Motor de Furação Industrial e Ferragens para Marcenaria (Zero DLL / Pure Python) | test_frentes_layout_e_marcenaria_avancada.py | 1 | - | - |
| `core/curve_engine.py` | 255 | SketchBuild - Motor de Curvas e Polilinhas Soldadas (Zero DLL / Pure Python) | test_frentes_66_a_70.py | 1 | - | - |
| `core/solid_tools.py` | 254 | Solid Tools - Operações Booleanas de Sólidos (CSG) em Pure Python (Zero DLL). | test_frentes_17_18_25_29_30.py | 1 | - | - |
| `core/ifc_exporter.py` | 253 | - | test_multiformat_exporter.py | 1 | - | - |
| `core/section_plane_engine.py` | 229 | SketchBuild - Motor de Planos de Corte Múltiplos, Aninhamento e Inversão (Zero DLL / Pure Python) | test_frentes_66_a_70.py | 1 | - | - |
| `core/sandbox_tools_engine.py` | 228 | Motor Completo da Caixa de Areia Nativa do SketchUp (Sandbox Tools - Zero DLL). | test_opcao_a_sketchup_native.py | 1 | - | - |
| `core/polymesh_loop_engine.py` | 223 | SketchBuild - Decodificador de Malhas com Furos e Hierarquia de Loops (Zero DLL / Pure Python) | test_frentes_81_a_85.py | 1 | - | - |
| `core/architectural_wall_engine.py` | 222 | SketchBuild - Paredes Arquitetônicas com Aberturas Automáticas de Vãos (Zero DLL / Pure Python) | test_frentes_96_a_100.py | 1 | - | - |
| `core/abnt_drawing_sheet_engine.py` | 214 | SketchBuild - Motor de Pranchas Técnicas ABNT e Viewports com Escala (Zero DLL / Pure Python) | test_frentes_layout_e_marcenaria_avancada.py | 1 | - | - |
| `core/intersect_faces_engine.py` | 210 | Motor de Interseção de Faces do SketchUp (Intersect Faces with Model / Selection - Zero DLL). | test_opcao_a_parte_4_sketchup_native.py | 1 | - | - |
| `core/walk_look_around_engine.py` | 203 | Motor das Ferramentas Nativas Caminhar, Olhar em Volta e Posicionar Câmera do SketchUp (Zero DLL). | test_opcao_a_sketchup_native.py | 1 | - | - |
| `core/quad_mesh_subd_engine.py` | 200 | SketchBuild - Decodificador e Subdivisão de Superfície SubD / QuadMesh (Zero DLL / Pure Python) | test_frentes_86_a_90.py | 1 | - | - |
| `core/furniture_edge_banding_engine.py` | 199 | SketchBuild - Motor de Fita de Borda para Marcenaria Sob Medida (Zero DLL / Pure Python) | test_frentes_layout_e_marcenaria_avancada.py | 1 | - | - |
| `core/dynamic_component_interaction_engine.py` | 191 | Motor de Interação com Componentes Dinâmicos do SketchUp (Trimble DC Click Engine - Zero DLL). | test_opcao_a_sketchup_native.py | 1 | - | - |
| `core/offset_calculator.py` | 189 | Calculador de Offset / Equidistância Analítica 2D e 3D em Pure Python (Zero DLL). | test_frentes_17_18_25_29_30.py | 1 | - | - |
| `core/entity_metrics_inspector_engine.py` | 188 | Motor do Inspetor de Informações da Entidade do SketchUp (Entity Info Inspector - Zero DLL). | test_opcao_a_parte_2_sketchup_native.py | 1 | - | - |
| `core/trimble_solid_tools_engine.py` | 181 | Motor das Ferramentas de Sólidos Nativas do SketchUp (Trimble Solid Tools - Zero DLL). | test_opcao_a_sketchup_native.py | 1 | - | - |
| `core/three_d_text_engine.py` | 176 | Motor da Ferramenta Texto 3D Nativo do SketchUp (3D Text Tool - Zero DLL). | test_opcao_a_parte_2_sketchup_native.py | 1 | - | - |
| `core/arc_generator.py` | 169 | Gerador de Arcos Circulares e Curvas 3D (Arc Tool - Zero DLL). | test_frentes_31_a_35.py | 1 | - | - |
| `core/follow_me_engine.py` | 169 | Motor Follow Me / Siga-me - Extrusão 3D ao Longo de Caminho (Zero DLL). | test_frentes_31_a_35.py | 1 | - | - |
| `core/piping_ductwork_engine.py` | 166 | SketchBuild - Tubulações e Dutos Paramétricos 3D com Conexões (Zero DLL / Pure Python) | test_frentes_91_a_95.py | 1 | - | - |
| `core/reverse_orient_faces_engine.py` | 165 | Motor de Inversão e Orientação de Faces do SketchUp (Reverse Faces & Orient Faces - Zero DLL). | test_opcao_a_parte_4_sketchup_native.py | 1 | - | - |
| `core/dimension_radial_engine.py` | 163 | SketchBuild - Motor de Cotas Radiais e Diamétricas (Zero DLL / Pure Python) | test_frentes_76_a_80.py | 1 | - | - |
| `core/radial_arc_dimension_engine.py` | 163 | SketchBuild - Motor de Cotas Radiais, Diamétricas e de Arcos (Zero DLL / Pure Python) | test_opcao_a_parte_8_sketchup_native.py | 1 | - | - |
| `core/scenes_animation_engine.py` | 163 | SketchBuild - Gerenciador de Cenas e Interpolação de Animação de Câmera (Zero DLL / Pure Python) | test_frentes_66_a_70.py | 1 | - | - |
| `core/nested_instance_hierarchy_engine.py` | 161 | SketchBuild - Decodificador de Grupos Aninhados e Matrizes Globais de Instância (Zero DLL / Pure Python) | test_frentes_71_a_75.py | 1 | - | - |
| `core/dimension_linear_engine.py` | 157 | SketchBuild - Motor de Cotas Lineares e Alinhadas (Zero DLL / Pure Python) | test_frentes_71_a_75.py | 1 | - | - |
| `core/section_hatch_engine.py` | 157 | SketchBuild - Motor de Hachuras Gráficas para Cortes de Seção (Zero DLL / Pure Python) | test_frentes_76_a_80.py | 1 | - | - |
| `core/bim_5d_sinapi_cost_engine.py` | 154 | Motor de Orçamento Paramétrico e Composição de Custos SINAPI (BIM 5D / SINAPI - Zero DLL). | test_frentes_106_a_115.py | 1 | - | - |
| `core/face_styles_engine.py` | 154 | SketchBuild - Motor de Estilos de Faces e Transparência Estilo Vidro (Zero DLL / Pure Python) | test_frentes_66_a_70.py | 1 | - | - |
| `core/ifc_classification_engine.py` | 154 | Motor de Classificação BIM e Esquemas IFC Nativo do SketchUp (Zero DLL). | test_opcao_a_parte_2_sketchup_native.py | 1 | - | - |
| `core/soft_smooth_angle_engine.py` | 154 | SketchBuild - Motor de Suavização Angular de Arestas e Normais de Phong (Zero DLL / Pure Python) | test_opcao_a_parte_8_sketchup_native.py | 1 | - | - |
| `core/aligned_dimension_engine.py` | 153 | SketchBuild - Motor de Cotas Lineares Alinhadas e Rotacionadas (Zero DLL / Pure Python) | test_opcao_a_parte_8_sketchup_native.py | 1 | - | - |
| `core/model_units_precision_engine.py` | 153 | Motor de Unidades, Precisão Decimal e Snaps do Modelo do SketchUp (Zero DLL). | test_opcao_a_parte_2_sketchup_native.py | 1 | - | - |
| `core/axes_system_engine.py` | 151 | Motor do Sistema de Eixos do Modelo do SketchUp (Axes Tool - Zero DLL). | test_opcao_a_parte_2_sketchup_native.py | 1 | - | - |
| `core/retaining_wall_engine.py` | 151 | Motor de Muros de Arrimo e Estabilidade Geotécnica NBR 11682 (Retaining Walls - Zero DLL). | test_frentes_106_a_115.py | 1 | - | - |
| `core/generate_report_engine.py` | 150 | Motor Oficial de Geração de Relatórios do SketchUp (Generate Report - Zero DLL). | test_opcao_a_parte_2_sketchup_native.py | 1 | - | - |
| `core/weld_edges_engine.py` | 149 | Motor de Soldagem de Arestas do SketchUp (Weld Edges Tool - Zero DLL / Pure Python). | test_opcao_a_parte_7_sketchup_native.py | - | - | - |
| `core/shell_solid_offset_engine.py` | 148 | SketchBuild - Motor de Espessura e Offset de Casca Sólida B-Rep (Zero DLL / Pure Python) | test_frentes_91_a_95.py | 1 | - | - |
| `core/skp_lod_optimizer_engine.py` | 148 | SketchBuild - Otimizador e Compactador de Geometria LOD para Baixa Latência Web (Zero DLL / Pure Python) | test_frentes_96_a_100.py | 1 | - | - |
| `core/tag_folder_engine.py` | 148 | Motor de Pastas de Tags e Árvore de Camadas do SketchUp (Zero DLL). | test_opcao_a_parte_7_sketchup_native.py | 1 | - | - |
| `core/dxf_to_skp_converter.py` | 147 | - | test_dxf_converter.py | 1 | - | - |
| `core/leader_text_callout_engine.py` | 147 | SketchBuild - Motor de Chamadas de Texto 3D e Rótulo de Área de Face (Zero DLL / Pure Python) | test_opcao_a_parte_8_sketchup_native.py | 1 | - | - |
| `core/slope_stability_bishop_engine.py` | 145 | Motor de Estabilidade de Taludes e Encostas Método de Bishop Simplificado (Slope Stability - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/space_truss_engine.py` | 143 | Motor de Estruturas Espaciais e Treliças Tubulares 3D (Space Truss - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/attribute_dictionary_engine.py` | 141 | Motor de Dicionários de Atributos e Componentes Dinâmicos do SketchUp (Zero DLL). | test_opcao_a_parte_7_sketchup_native.py | 1 | - | - |
| `core/flip_along_axes_engine.py` | 139 | Motor de Inversão ao Longo dos Eixos do SketchUp (Flip Along Tool - Zero DLL / Pure Python). | test_opcao_a_parte_7_sketchup_native.py | 1 | - | - |
| `core/ifc4_bim_export_engine.py` | 138 | SketchBuild - Exportador Canônico de IFC4 BIM LOI/LOD 350 (Zero DLL / Pure Python) | test_frentes_101_a_105.py | 1 | - | - |
| `core/orbit_flythrough_path_engine.py` | 137 | SketchBuild - Animação de Câmera em Percurso Orbit e Flythrough (Zero DLL / Pure Python) | test_frentes_91_a_95.py | 1 | - | - |
| `core/section_dimension_engine.py` | 136 | SketchBuild - Motor de Cortes com Cota Automática de Seção (Zero DLL / Pure Python) | test_frentes_86_a_90.py | 1 | - | - |
| `core/mass_properties_engine.py` | 135 | SketchBuild - Propriedades Físicas, Centro de Gravidade e Inércia B-Rep (Zero DLL / Pure Python) | test_frentes_86_a_90.py | 1 | - | - |
| `core/axis_lock_inference_engine.py` | 133 | Motor de Bloqueio de Eixos e Inferência do SketchUp (Axis Lock & Inference Engine - Zero DLL). | test_opcao_a_parte_4_sketchup_native.py | 1 | - | - |
| `core/smooth_soft_edges_engine.py` | 129 | SketchBuild - Decodificador de Malhas com Suavização de Arestas (Zero DLL / Pure Python) | test_frentes_76_a_80.py | 1 | - | - |
| `core/geo_reference_engine.py` | 128 | SketchBuild - Gerenciador de Georreferenciamento e Coordenadas Globais (Zero DLL / Pure Python) | test_frentes_76_a_80.py | 1 | - | - |
| `core/clash_collision_engine.py` | 127 | SketchBuild - Detecção de Colisão e Interferência entre Componentes (Zero DLL / Pure Python) | test_frentes_86_a_90.py | 1 | - | - |
| `core/gabion_retaining_wall_engine.py` | 125 | Motor de Muros de Gabião e Contenções Gravíticas Drenantes ABNT NBR 10328 (Gabion Wall - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/soft_smooth_edges_engine.py` | 124 | Engine de Engenharia Reversa da Caixa de Dialogo Suavizar Arestas (Soften / Smooth Edges). | test_opcao_a_parte_5_sketchup_native.py | 1 | - | - |
| `core/alpha_texture_engine.py` | 123 | SketchBuild - Motor de Materiais com Canal Alfa e Componentes Face-Me (Zero DLL / Pure Python) | test_frentes_71_a_75.py | 1 | - | - |
| `core/architectural_hatching_engine.py` | 123 | SketchBuild - Motor de Hachuras Técnicas Arquitetônicas (Zero DLL / Pure Python) | test_frentes_layout_e_marcenaria_avancada.py | 1 | - | - |
| `core/undo_redo_engine.py` | 123 | SketchBuild - Histórico de Operações Atômicas e Undo/Redo (Zero DLL / Pure Python) | test_frentes_81_a_85.py | 1 | - | - |
| `core/texture_pin_mapping_engine.py` | 122 | Motor de Posicionamento e Mapeamento de Texturas por Pinos do SketchUp (Zero DLL). | test_opcao_a_parte_3_sketchup_native.py | 1 | - | - |
| `core/watermark_style_engine.py` | 122 | Motor de Estilos de Marca d'Água do SketchUp (Watermark Style Engine - Zero DLL). | test_opcao_a_sketchup_native.py | 1 | - | - |
| `core/stamp_terrain_engine.py` | 121 | Engine de Engenharia Reversa da Ferramenta Carimbo (Stamp Tool) da Caixa de Areia (Sandbox). | test_opcao_a_parte_5_sketchup_native.py | 1 | - | - |
| `core/solid_inspector_engine.py` | 120 | SketchBuild - Inspetor de Sólidos e Validação 2-Manifold (Zero DLL / Pure Python) | test_opcao_a_parte_8_sketchup_native.py | 1 | - | - |
| `core/stair_generator_engine.py` | 120 | SketchBuild - Gerador Paramétrico de Escadas (Zero DLL / Pure Python) | test_frentes_101_a_105.py | 1 | - | - |
| `core/sheet_metal_unfold_engine.py` | 119 | SketchBuild - Planificação e Desdobramento de Chapa Metálica (Zero DLL / Pure Python) | test_frentes_96_a_100.py | 1 | - | - |
| `core/regular_polygon_engine.py` | 118 | Motor da Ferramenta Polígono Regular Paramétrico do SketchUp (Polygon Tool - Zero DLL). | test_opcao_a_parte_4_sketchup_native.py | 1 | - | - |
| `core/glulam_clt_timber_engine.py` | 117 | Motor de Madeira Laminada Colada (Glulam) e CLT ABNT NBR 7190 / Eurocode 5 (Engineered Timber - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/nesting_optimizer.py` | 116 | Otimizador de Plano de Corte de Estoque (Nesting 1D e 2D - Zero DLL). | test_frentes_36_a_40.py | 1 | - | - |
| `core/room_acoustics_engine.py` | 116 | Motor de Acústica Arquitetônica e Tempo de Reverberação NBR 10152 (Room Acoustics - Zero DLL). | test_frentes_106_a_115.py | 1 | - | - |
| `core/cam_cutlist_fabrication_engine.py` | 114 | SketchBuild - Tabela de Cutlist Otimizada para Fabricação CNC (Zero DLL / Pure Python) | test_frentes_91_a_95.py | 1 | - | - |
| `core/prestressed_concrete_engine.py` | 114 | Motor de Concreto Protendido e Perdas de Protensão ABNT NBR 6118 (Prestressed Concrete - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/deep_foundations_piles_engine.py` | 113 | Motor de Estacas e Fundações Profundas ABNT NBR 6122 (Deep Foundations - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/drape_contour_engine.py` | 113 | Engine de Engenharia Reversa da Ferramenta Projetar (Drape Tool) da Caixa de Areia (Sandbox). | test_opcao_a_parte_5_sketchup_native.py | 1 | - | - |
| `core/qr_tag_generator.py` | 113 | Gerador de Etiquetas Técnicas de Patrimônio com QR Code Analítico (Zero DLL). | test_frentes_41_a_45.py | 1 | - | - |
| `core/bim_ifc_property_set_engine.py` | 111 | Engine de Engenharia Reversa para Conjuntos de Propriedades BIM (IFC Property Sets - Psets). | test_opcao_a_parte_5_sketchup_native.py | 1 | - | - |
| `core/shallow_footings_engine.py` | 111 | Motor de Sapatas Isoladas e Fundações Rasas ABNT NBR 6122 / NBR 6118 (Shallow Footings - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/align_view_engine.py` | 110 | SketchBuild - Motor de Alinhamento de Câmera à Face (Zero DLL / Pure Python) | test_frentes_81_a_85.py | 1 | - | - |
| `core/section_cut_fill_engine.py` | 110 | Engine de Engenharia Reversa para Inversao de Plano de Corte e Preenchimento de Secao (Section Cut Fill). | test_opcao_a_parte_5_sketchup_native.py | 1 | - | - |
| `core/detention_basin_hydrology_engine.py` | 109 | Motor de Bacias de Detenção e Amortecimento Hidrológico de Cheias (Detention Basin - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/edge_styles_engine.py` | 109 | Motor de Estilos de Arestas Nativos do SketchUp (Zero DLL). | test_opcao_a_parte_7_sketchup_native.py | 1 | - | - |
| `core/fuel_gas_piping_engine.py` | 108 | Motor de Instalações de Gás Canalizado GLP/GN ABNT NBR 15526 / NBR 15358 (Fuel Gas Piping - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/waffle_slab_engine.py` | 108 | Motor de Lajes Nervuradas Bidirecionais com Cubetas Plásticas (Waffle Slab - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/component_edit_modes_engine.py` | 107 | Motor dos Modos de Exibição de Edição de Componentes do SketchUp (Zero DLL). | test_opcao_a_parte_2_sketchup_native.py | 1 | - | - |
| `core/push_pull_create_face_engine.py` | 107 | Engine de Engenharia Reversa do Push/Pull com Nova Face (Ctrl + Push/Pull Tool). | test_opcao_a_parte_5_sketchup_native.py | 1 | - | - |
| `core/ground_sky_style_engine.py` | 105 | Motor de Configurações de Fundo, Solo e Céu dos Estilos do SketchUp (Ground & Sky Style Engine - Zero DLL). | test_opcao_a_parte_4_sketchup_native.py | 1 | - | - |
| `core/electrical_conduit_engine.py` | 104 | Motor de Dimensionamento de Eletrodutos e Fiação Elétrica NBR 5410 (Electrical Conduits - Zero DLL). | test_frentes_106_a_115.py | 1 | - | - |
| `core/photometric_lumen_design_engine.py` | 103 | Motor de Iluminação Artificial de Interiores e Método dos Lúmens ABNT NBR ISO/CIE 8995-1 (Photometric Lumen -  | test_frentes_116_a_145.py | 1 | - | - |
| `core/texture_projection_engine.py` | 103 | Motor de Projeção de Texturas e Coordenadas UV do SketchUp (Zero DLL). | test_opcao_a_parte_7_sketchup_native.py | 1 | - | - |
| `core/bim_7d_asset_management_cobie_engine.py` | 102 | Motor de Gestão de Ativos BIM 7D e Exportação COBie (BIM 7D Facility Management - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/make_component_behavior_engine.py` | 102 | Motor de Criação de Componentes e Comportamentos do SketchUp (Make Component - Zero DLL). | test_opcao_a_parte_3_sketchup_native.py | 1 | - | - |
| `core/concrete_formwork_shoring_engine.py` | 100 | Motor de Fôrmas e Escoramento de Estruturas de Concreto ABNT NBR 15696 / DIN 18218 (Formwork & Shoring - Zero  | test_frentes_116_a_145.py | 1 | - | - |
| `core/panorama_spherical_engine.py` | 100 | SketchBuild - Decodificador de Projeção Esférica e Panorama 360° (Zero DLL / Pure Python) | test_frentes_86_a_90.py | 1 | - | - |
| `core/advanced_selection_engine.py` | 99 | Motor de Seleção Avançada do SketchUp (Advanced Selection - Zero DLL). | test_opcao_a_parte_3_sketchup_native.py | 1 | - | - |
| `core/hvac_thermal_load_engine.py` | 98 | Motor de Carga Térmica de Climatização HVAC ASHRAE / ABNT NBR 16401 (HVAC Thermal Load - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/life_cycle_assessment_engine.py` | 98 | Motor de Avaliação do Ciclo de Vida (ACV / LCA) e Energia Embutida ISO 14040 (Life Cycle Assessment - Zero DLL | test_frentes_116_a_145.py | 1 | - | - |
| `core/transformation_engine.py` | 98 | Motor de Transformações Geométricas 3D e Ferramenta Rotacionar (Rotate Tool - Zero DLL). | test_frentes_31_a_35.py | 1 | - | - |
| `core/glazing_fenestration_engine.py` | 97 | Motor de Esquadrias Paramétricas e Fachadas Pele de Vidro (Glazing & Fenestration - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/obj_to_skp_importer.py` | 97 | Importador de Modelos 3D Wavefront OBJ para .SKP Nativo (Zero DLL). | test_frentes_31_a_35.py | 1 | - | - |
| `core/two_point_perspective_engine.py` | 97 | Motor de Câmera de Perspectiva de Dois Pontos do SketchUp (Zero DLL). | test_opcao_a_parte_7_sketchup_native.py | 1 | - | - |
| `core/lightning_protection_spda_engine.py` | 96 | Motor de Proteção contra Descargas Atmosféricas SPDA ABNT NBR 5419 (Lightning Protection - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/purge_unused_engine.py` | 96 | Motor de Eliminação de Elementos Não Utilizados do SketchUp (Purge Unused - Zero DLL). | test_opcao_a_parte_3_sketchup_native.py | 1 | - | - |
| `core/daylight_factor_engine.py` | 95 | Motor de Iluminação Natural e Fator de Luz Diurna FLD NBR 15215 (Daylight Factor - Zero DLL). | test_frentes_106_a_115.py | 1 | - | - |
| `core/text_engine.py` | 95 | SketchBuild - Motor de Textos 2D na Tela e Rótulos Anotativos de Líder (Zero DLL / Pure Python) | test_frentes_71_a_75.py | 1 | - | - |
| `core/camera_path_interpolator.py` | 94 | Interpolador de Caminho de Câmera e Voo Panorâmico (Flythrough - Zero DLL). | test_frentes_41_a_45.py | 1 | - | - |
| `core/maintenance_planner.py` | 94 | Planejador de Manutenção Preventiva e Vida Útil de Playgrounds (NBR 16071-7 - Zero DLL). | test_frentes_41_a_45.py | 1 | - | - |
| `core/earthwork_bruckner_engine.py` | 93 | Motor de Movimentação de Terra e Diagrama de Massas de Brückner (Earthwork - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/fire_egress_route_engine.py` | 93 | Motor de Rotas de Fuga e Saídas de Emergência em Edifícios ABNT NBR 9077 (Fire Egress - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/permeable_pavement_engine.py` | 93 | Motor de Pavimentação Permeável e Drenagem Sustentável ABNT NBR 16416 (Permeable Pavement - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/dimension_tolerance_engine.py` | 90 | SketchBuild - Motor de Cotas com Tolerâncias e Desvios Dimensionais (Zero DLL / Pure Python) | test_frentes_81_a_85.py | 1 | - | - |
| `core/hidden_geometry_engine.py` | 89 | Motor de Geometria Oculta e Objetos Ocultos do SketchUp (Zero DLL). | test_opcao_a_parte_3_sketchup_native.py | 1 | - | - |
| `core/natural_ventilation_engine.py` | 88 | Motor de Ventilação Natural e Efeito Chaminé ABNT NBR 15220 / ASHRAE (Natural Ventilation - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/flip_edge_sandbox_engine.py` | 87 | Engine de Engenharia Reversa da Ferramenta Girar Aresta (Flip Edge Tool) da Caixa de Areia. | test_opcao_a_parte_6_sketchup_native.py | 1 | - | - |
| `core/shadow_casting_surface_engine.py` | 87 | SketchBuild - Sombras Projetadas em Superfícies e Lotes Vizinhos (Zero DLL / Pure Python) | test_frentes_96_a_100.py | 1 | - | - |
| `core/model_statistics_engine.py` | 86 | Motor de Estatísticas e Contagem de Entidades do SketchUp (Model Statistics - Zero DLL). | test_opcao_a_parte_3_sketchup_native.py | 1 | - | - |
| `core/terrain_generator.py` | 83 | Gerador de Terrenos Paramétricos e Malha Topográfica Sandbox (Zero DLL). | test_frentes_36_a_40.py | 1 | - | - |
| `core/atmosphere_scattering_engine.py` | 82 | SketchBuild - Céu Físico Rayleigh & Mie e Espalhamento Atmosférico (Zero DLL / Pure Python) | test_frentes_101_a_105.py | 1 | - | - |
| `core/graphic_export_2d_engine.py` | 82 | Engine de Engenharia Reversa da Caixa de Dialogo Exportar Grafico 2D (2D Graphic Export Options). | test_opcao_a_parte_6_sketchup_native.py | 1 | - | - |
| `core/mirror_tool.py` | 80 | Ferramenta de Espelhamento e Simetria 3D (Mirror / Flip Tool - Zero DLL). | test_frentes_41_a_45.py | 1 | - | - |
| `core/structural_analyzer.py` | 80 | Analisador Estrutural e de Tensões em Vigas e Pilares (FEA / NBR 7190 - Zero DLL). | test_frentes_36_a_40.py | 1 | - | - |
| `core/edge_divide_engine.py` | 79 | Engine de Engenharia Reversa da Ferramenta Dividir Aresta (Edge Divide Tool). | test_opcao_a_parte_5_sketchup_native.py | 1 | - | - |
| `core/water_caustics_shader_engine.py` | 79 | SketchBuild - Shader PBR de Água, Ondas Gerstner e Cáusticas (Zero DLL / Pure Python) | test_frentes_96_a_100.py | 1 | - | - |
| `core/cam_dxf_exporter.py` | 78 | Exportador de Arquivos DXF 2D para Fabricação Digital CNC e Corte a Laser (Zero DLL). | test_frentes_36_a_40.py | 1 | - | - |
| `core/position_camera_engine.py` | 76 | Engine de Engenharia Reversa da Ferramenta Posicionar Camera (Position Camera Tool). | test_opcao_a_parte_6_sketchup_native.py | 1 | - | - |
| `core/fog_depth_engine.py` | 75 | SketchBuild - Motor de Estilos de Névoa e Profundidade Atmosférica (Zero DLL / Pure Python) | test_frentes_76_a_80.py | 1 | - | - |
| `core/universal_accessibility_engine.py` | 75 | Motor de Acessibilidade Universal a Edificações ABNT NBR 9050 (Universal Accessibility - Zero DLL). | test_frentes_116_a_145.py | 1 | - | - |
| `core/color_by_tag_engine.py` | 73 | Motor do Modo 'Colorir por Etiqueta' do SketchUp (Color by Tag - Zero DLL). | test_opcao_a_parte_3_sketchup_native.py | 1 | - | - |
| `core/point_cloud_exporter.py` | 70 | Exportador de Nuvem de Pontos 3D (LiDAR / XYZ / PTS - Zero DLL). | test_frentes_41_a_45.py | 1 | - | - |
| `core/look_around_camera_engine.py` | 69 | Engine de Engenharia Reversa da Ferramenta Olhar ao Redor (Look Around Tool). | test_opcao_a_parte_6_sketchup_native.py | 1 | - | - |
| `core/background_sky_style_engine.py` | 67 | SketchBuild - Motor de Estilos de Céu, Solo e Horizonte Gradiente (Zero DLL / Pure Python) | test_frentes_81_a_85.py | 1 | - | - |
| `core/scale_tool.py` | 58 | Ferramenta de Escala e Redimensionamento Paramétrico (Scale Tool - Zero DLL). | test_frentes_36_a_40.py | 1 | - | - |
| `core/fog_settings_engine.py` | 56 | Engine de Engenharia Reversa da Caixa de Dialogo de Nevoa (Fog Settings Dialog). | test_opcao_a_parte_6_sketchup_native.py | 1 | - | - |

## VALIDADO (13)

| Módulo | Linhas | Descrição | Testes | App/rotas | DLL | Alertas |
|---|---|---|---|---|---|---|
| `core/su_api.py` | 2004 | Binding ctypes para a C API pública da Trimble (SketchUpAPI.dll). | test_add_geometry_native.py, test_attribute_injection.py, test_box_native.py... | 2 | sim | aproxima, stub |
| `core/skp_hidden_pruner.py` | 441 | Poda de ocultos direto no `model.dat` (sem abrir o SketchUp). | test_skp_topology_writer.py | 1 | - | exemplo |
| `core/skp_binary_reader.py` | 1587 | SketchBuild - Leitor Binário Nativo de Arquivos .SKP (Pure Python / Zero DLL) | test_add_geometry_native.py, test_attribute_injection.py, test_binary_mesh_extraction.py... | 3 | sim | - |
| `core/mesh_extractor.py` | 398 | Percorre a arvore Model -> Entities -> {Faces, ComponentInstances} de um | test_skp_topology_writer.py | 1 | sim | - |
| `core/topology/model.py` | 389 | Grafo de vértices, arestas e faces com as regras de modelagem do SketchUp. | test_add_geometry_native.py, test_attribute_injection.py, test_box_native.py... | 7 | - | - |
| `core/skp_topology_writer.py` | 232 | B2: grava uma `Topology` (vértices, arestas, faces com furos) na raiz de um `.skp` VFF 2021+. | test_skp_topology_writer.py | 1 | sim | - |
| `core/topology/pushpull.py` | 190 | F3: Empurrar/Puxar (Push/Pull) sobre o núcleo de topologia. | test_draw_api.py, test_skp_topology_writer.py, test_topology_cena.py... | 3 | - | - |
| `core/topology/edit.py` | 180 | F4: edição sobre o núcleo de topologia: Mover, Rotacionar, Escalar e Offset. | test_draw_api.py, test_topology_edit.py, test_topology_historico.py | 3 | - | - |
| `core/topology/cena.py` | 164 | F5: grupos e componentes sobre o núcleo de topologia. | test_multiformat_exporter.py, test_opcao_a_parte_2_sketchup_native.py, test_topology_cena.py... | 10 | - | - |
| `core/topology/sweep.py` | 135 | F5: Siga-me (Follow Me): varre uma face (perfil) ao longo de um caminho de arestas. | test_topology_sweep.py | 1 | - | - |
| `core/topology/draw.py` | 126 | F2: ferramentas de desenho (Linha, Retângulo, Círculo, Polígono, Arco, Mão livre) | test_draw_api.py, test_skp_topology_writer.py, test_topology_cena.py... | 3 | - | - |
| `core/topology/intersect.py` | 92 | F5: Intersect Faces. Cada par de faces em planos diferentes que se cruzam ganha a aresta da | test_draw_api.py, test_opcao_a_sketchup_native.py, test_topology_intersect.py | 4 | - | - |
| `core/topology/historico.py` | 79 | F6: histórico (desfazer e refazer) da Cena, com log de operações. | test_draw_api.py, test_topology_historico.py | 6 | - | - |
