"""
Exportador de Ficha de Inspeção e Checklist de Campo Offline (NBR 16071-7 - Zero DLL).

Gera aplicação web e laudo técnico autocontido em HTML5 para auditoria em campo:
1. Checklist normativo oficial ABNT NBR 16071-7 (Rotina, Operacional e Anual).
2. Interface responsiva otimizada para tablets, smartphones e notebooks offline.
3. Campo de assinatura digital interativo na tela via HTML5 Canvas.
4. Exportação direta para impressão em prancha PDF via CSS @media print.
"""

import os
from typing import Dict, Any, List


class FieldInspectionExporter:
    """Gerador de Ficha Técnica de Inspeção de Campo da NBR 16071."""

    @classmethod
    def generate_inspection_html(
        cls,
        park_name: str,
        inspector_name: str,
        inspection_date: str,
        equipment_list: List[str] = None,
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Gera o documento HTML5 autocontido com o checklist de campo.
        """
        if not equipment_list:
            equipment_list = [
                "Playground Modular Eucalipto (Deck Duplo)",
                "Balanço Duplo com Cadeirinha e Pneu",
                "Escorregador Tubo Helicoidal PEAD",
                "Ponte Pênsil com Corrimão de Cordas",
                "Escalada de Troncos com Agarras"
            ]

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Checklist de Inspeção em Campo - ABNT NBR 16071-7</title>
  <style>
    :root {{
      --primary: #1A365D;
      --accent: #007791;
      --bg: #F7FAFC;
      --card: #FFFFFF;
      --text: #2D3748;
      --border: #E2E8F0;
      --success: #38A169;
      --danger: #E53E3E;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 20px;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
      background: var(--card);
      border-radius: 8px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
      padding: 30px;
    }}
    .header {{
      border-bottom: 2px solid var(--primary);
      padding-bottom: 15px;
      margin-bottom: 25px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    h1 {{
      font-size: 20px;
      color: var(--primary);
      margin: 0 0 5px 0;
    }}
    .subtitle {{
      font-size: 13px;
      color: #718096;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      background: #EDF2F7;
      padding: 15px;
      border-radius: 6px;
      margin-bottom: 25px;
      font-size: 13px;
    }}
    .section-title {{
      font-size: 16px;
      color: var(--accent);
      border-bottom: 1px solid var(--border);
      padding-bottom: 6px;
      margin-top: 25px;
      margin-bottom: 15px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
      font-size: 12.5px;
    }}
    th, td {{
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th {{
      background-color: #F8FAFC;
      color: var(--primary);
      font-weight: 600;
    }}
    .status-select {{
      padding: 4px 8px;
      border-radius: 4px;
      border: 1px solid #CBD5E0;
      font-size: 12px;
    }}
    .canvas-box {{
      border: 2px dashed #CBD5E0;
      border-radius: 6px;
      background: #FFFFFF;
      margin-top: 10px;
      touch-action: none;
    }}
    .btn {{
      background: var(--primary);
      color: white;
      border: none;
      padding: 10px 18px;
      font-size: 14px;
      border-radius: 5px;
      cursor: pointer;
      font-weight: 600;
    }}
    .btn:hover {{
      background: #2A4365;
    }}
    @media print {{
      body {{ background: white; padding: 0; }}
      .container {{ box-shadow: none; padding: 0; max-width: 100%; }}
      .no-print {{ display: none !important; }}
    }}
  </style>
</head>
<body>

<div class="container">
  <div class="header">
    <div>
      <h1>FICHA TÉCNICA DE INSPEÇÃO EM CAMPO</h1>
      <div class="subtitle">Auditoria Normativa de Segurança Infantil — ABNT NBR 16071 (Partes 1 a 7)</div>
    </div>
    <button class="btn no-print" onclick="window.print()">Imprimir / Salvar PDF</button>
  </div>

  <div class="meta-grid">
    <div><strong>Local / Parque:</strong> {park_name}</div>
    <div><strong>Inspetor Responsável:</strong> {inspector_name}</div>
    <div><strong>Data da Vistoria:</strong> {inspection_date}</div>
    <div><strong>Equipamentos Vistoriados:</strong> {len(equipment_list)} unidades</div>
  </div>

  <div class="section-title">1. Itens da Inspeção Visual de Rotina (Frequência Semanal/Diária)</div>
  <table>
    <thead>
      <tr>
        <th style="width: 50%;">Item Verificado</th>
        <th style="width: 25%;">Critério NBR 16071</th>
        <th style="width: 25%;">Avaliação</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Limpeza do piso de absorção e entorno</td>
        <td>Ausência de cacos de vidro, pregos e detritos</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>Estabilidade geral de pilares e postes</td>
        <td>Sem folgas anormais ou risco de tombamento</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>Peças faltantes ou vandalizadas</td>
        <td>Presença de todas as tampas e proteções</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
    </tbody>
  </table>

  <div class="section-title">2. Itens da Inspeção Operacional (Frequência Trimestral / Bimestral)</div>
  <table>
    <thead>
      <tr>
        <th style="width: 50%;">Item Verificado</th>
        <th style="width: 25%;">Critério NBR 16071</th>
        <th style="width: 25%;">Avaliação</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Folga de buchas, mananciais e rolamentos de balanço</td>
        <td>Movimento suave sem atrito excessivo</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>Aperto de parafusos e porcas autotravantes</td>
        <td>Torque adequado sem roscas expostas cortantes</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>Desgaste de correntes e elos de sustentação</td>
        <td>Redução máxima de 10% no diâmetro do elo</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>Guarda-corpos, balaústres e corrimãos</td>
        <td>Vãos livres entre 89mm e 230mm testados</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
    </tbody>
  </table>

  <div class="section-title">3. Itens da Inspeção Principal Anual</div>
  <table>
    <thead>
      <tr>
        <th style="width: 50%;">Item Verificado</th>
        <th style="width: 25%;">Critério NBR 16071</th>
        <th style="width: 25%;">Avaliação</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Integridade da madeira enterrada/sapata</td>
        <td>Sem sinais de podridão fúngica ou cupins</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>Corrosão galvânica e ferragens estruturais</td>
        <td>Sem perda de espessura nas cantoneiras de fixação</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>Camada de absorção de impacto do piso</td>
        <td>Espessura mínima de areia/borracha mantida</td>
        <td>
          <select class="status-select">
            <option value="C">Conforme</option>
            <option value="NC">Não Conforme</option>
            <option value="NA">N/A</option>
          </select>
        </td>
      </tr>
    </tbody>
  </table>

  <div class="section-title">4. Parecer e Assinatura Digital do Inspetor</div>
  <p style="font-size: 12px; color: #718096;">Assine no campo abaixo com o dedo ou caneta stylus para validação imediata:</p>
  <canvas id="signature-pad" class="canvas-box" width="600" height="150"></canvas>
  <div style="margin-top: 8px;" class="no-print">
    <button class="btn" style="padding: 5px 10px; font-size: 11px; background: #718096;" onclick="clearSignature()">Limpar Assinatura</button>
  </div>
</div>

<script>
  const canvas = document.getElementById('signature-pad');
  const ctx = canvas.getContext('2d');
  let painting = false;

  function startPos(e) {{
    painting = true;
    draw(e);
  }}
  function endPos() {{
    painting = false;
    ctx.beginPath();
  }}
  function draw(e) {{
    if (!painting) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || (e.touches && e.touches[0].clientX)) - rect.left;
    const y = (e.clientY || (e.touches && e.touches[0].clientY)) - rect.top;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#1A365D';
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
  }}
  function clearSignature() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }}

  canvas.addEventListener('mousedown', startPos);
  canvas.addEventListener('mouseup', endPos);
  canvas.addEventListener('mousemove', draw);
  canvas.addEventListener('touchstart', startPos);
  canvas.addEventListener('touchend', endPos);
  canvas.addEventListener('touchmove', draw);
</script>
</body>
</html>
"""
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

        return {
            "entity_type": "FieldInspectionHtml",
            "file_path": os.path.abspath(output_path) if output_path else "",
            "size_bytes": len(html.encode("utf-8")),
            "park_name": park_name,
            "inspector_name": inspector_name,
            "inspection_date": inspection_date,
            "items_count": 10
        }
