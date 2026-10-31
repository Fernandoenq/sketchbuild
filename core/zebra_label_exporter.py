"""
Exportador de Etiquetas Térmicas Zebra ZPL II para Fábrica (Zero DLL).

Gera comandos industriais de etiquetagem para rastreabilidade de peças:
1. Sintaxe nativa Zebra Programming Language (ZPL II - ^XA ... ^XZ).
2. Código de barras Code 128 (^BC) e QR Code 2D (^BQ) de rastreamento de lote.
3. Informações completas de usinagem, tratamento autoclave e dimensões em milímetros.
4. Geração paralela de visualização gráfica SVG da etiqueta (100 x 50 mm / 4 x 2 pol).
"""

import os
from typing import Dict, Any, List


class ZebraLabelExporter:
    """Compilador de etiquetas industriais em ZPL II e SVG."""

    @classmethod
    def generate_zpl(
        cls,
        part_name: str = "Pilar Eucalipto Citriodora",
        part_sku: str = "PKL-EUC-16-220",
        dimensions_mm: str = "D160 x L2200 mm",
        lot_batch: str = "LOTE-2026-X84",
        treatment: str = "Autoclave CCA NBR 7190",
        serial_number: str = "SN-98421",
        qr_url: str = "https://parkelo.com.br/trace/PKL-EUC-16-220"
    ) -> str:
        """
        Gera o código ZPL II puro compatível com impressoras Zebra 203 DPI (8 dots/mm).
        Tamanho da etiqueta padrão: 100mm x 50mm (800 x 400 dots).
        """
        zpl = [
            "^XA",  # Início de formato
            "^PW800",  # Largura da etiqueta: 800 dots (100mm)
            "^LL400",  # Comprimento: 400 dots (50mm)
            "^LH0,0",  # Origem
            # Borda externa
            "^FO20,20^GB760,360,3^FS",
            # Linha horizontal de separação do cabeçalho
            "^FO20,85^GB760,2^FS",
            # Cabeçalho da Empresa
            "^FO40,35^A0N,32,32^FDPARKELO LUDICA - NBR 16071^FS",
            "^FO540,40^A0N,22,22^FDFABRICA BR^FS",
            # Nome da Peça
            "^FO40,105^A0N,26,26^FDPECA: " + part_name.upper() + "^FS",
            "^FO40,140^A0N,22,22^FDDIMENSOES: " + dimensions_mm + "^FS",
            "^FO40,170^A0N,20,20^FDMULTI-LOTE: " + lot_batch + " | " + treatment + "^FS",
            # Código de Barras Code 128
            "^FO40,210^BCN,70,Y,N,N",
            "^FD" + part_sku + "^FS",
            # QR Code no canto direito
            "^FO610,130^BQN,2,5",
            "^FDQA," + qr_url + "^FS",
            "^FO610,310^A0N,18,18^FDRASTREABILIDADE^FS",
            # Rodapé com serial
            "^FO40,340^A0N,18,18^FDSERIAL: " + serial_number + "  |  CONTROLE DE QUALIDADE APROVADO^FS",
            "^XZ"  # Fim de formato
        ]
        return "\n".join(zpl)

    @classmethod
    def generate_preview_svg(
        cls,
        part_name: str,
        part_sku: str,
        dimensions_mm: str,
        lot_batch: str,
        serial_number: str
    ) -> str:
        """
        Gera pré-visualização vetorial SVG da etiqueta térmica.
        """
        svg = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="300" viewBox="0 0 600 300">',
            '  <rect width="600" height="300" rx="10" fill="#FFFFFF" stroke="#2D3748" stroke-width="3" />',
            '  <line x1="20" y1="65" x2="580" y2="65" stroke="#718096" stroke-width="1.5" />',
            f'  <text x="30" y="45" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#1A365D">PARKELÔ LÚDICA — NBR 16071</text>',
            f'  <text x="460" y="45" font-family="Arial, sans-serif" font-size="14" fill="#718096">FÁBRICA IND</text>',
            f'  <text x="30" y="100" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#2D3748">{part_name}</text>',
            f'  <text x="30" y="130" font-family="Arial, sans-serif" font-size="15" fill="#4A5568">Dimensões: {dimensions_mm}</text>',
            f'  <text x="30" y="155" font-family="Arial, sans-serif" font-size="13" fill="#718096">Lote: {lot_batch} | Tratamento Autoclave CCA</text>',
            # Simulação visual de barras Code 128
            '  <g id="barcode" fill="#1A202C">',
        ]

        # Gera padrão decorativo de barras
        x_bar = 30
        for i in range(35):
            width = 3 if i % 3 == 0 else 6 if i % 5 == 0 else 2
            svg.append(f'    <rect x="{x_bar}" y="175" width="{width}" height="65" />')
            x_bar += width + 3

        svg.append(f'    <text x="30" y="260" font-family="monospace" font-size="14" fill="#1A202C">{part_sku}</text>')
        svg.append('  </g>')

        # QR Code simulado no canto direito
        svg.append('  <rect x="470" y="100" width="100" height="100" fill="#F7FAFC" stroke="#CBD5E0" stroke-width="2" />')
        svg.append('  <rect x="485" y="115" width="25" height="25" fill="#1A365D" />')
        svg.append('  <rect x="530" y="115" width="25" height="25" fill="#1A365D" />')
        svg.append('  <rect x="485" y="160" width="25" height="25" fill="#1A365D" />')
        svg.append('  <rect x="525" y="155" width="15" height="15" fill="#1A365D" />')
        svg.append('  <text x="472" y="220" font-family="Arial, sans-serif" font-size="11" fill="#718096">RASTREABILIDADE</text>')

        # Rodapé
        svg.append(f'  <text x="30" y="285" font-family="Arial, sans-serif" font-size="12" fill="#718096">SERIAL: {serial_number}  |  CONTROLE DE QUALIDADE APROVADO</text>')
        svg.append('</svg>')

        return "\n".join(svg)

    @classmethod
    def export_label(
        cls,
        part_name: str,
        part_sku: str,
        dimensions_mm: str,
        lot_batch: str,
        output_zpl_path: str,
        output_svg_path: str = None
    ) -> Dict[str, Any]:
        """
        Exporta o arquivo de impressão ZPL e o arquivo visual SVG.
        """
        zpl_content = cls.generate_zpl(part_name, part_sku, dimensions_mm, lot_batch)
        with open(output_zpl_path, "w", encoding="utf-8") as f:
            f.write(zpl_content)

        svg_content = cls.generate_preview_svg(part_name, part_sku, dimensions_mm, lot_batch, "SN-98421")
        if output_svg_path:
            with open(output_svg_path, "w", encoding="utf-8") as f:
                f.write(svg_content)

        return {
            "entity_type": "ZebraThermalLabel",
            "zpl_file_path": os.path.abspath(output_zpl_path),
            "svg_file_path": os.path.abspath(output_svg_path) if output_svg_path else "",
            "zpl_size_bytes": len(zpl_content.encode("utf-8")),
            "part_sku": part_sku,
            "part_name": part_name,
            "label_dimensions": "100x50mm (ZPL II 203 DPI)"
        }
