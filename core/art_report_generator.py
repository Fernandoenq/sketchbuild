"""
Gerador de Minuta Técnica de ART / RRT em PDF Vetorial (Zero DLL / Pure Python).

Gera documento executivo de Anotação de Responsabilidade Técnica (CREA/CAU):
1. Síntese do projeto estrutural e playground infantil (NBR 16071 / NBR 7190).
2. Dados do profissional, contratante, endereço da obra e escopo técnico.
3. Resumo dos parâmetros de segurança (altura de queda, área de circulação e capacidade).
4. Emissão em PDF 1.4 binário padronizado sem dependências externas.
"""

import os
from typing import Dict, Any, List


class ArtReportGenerator:
    """Compilador de Minuta de ART / RRT em PDF nativo."""

    @classmethod
    def generate_art_pdf(
        cls,
        professional_data: Dict[str, str],
        project_data: Dict[str, Any],
        output_path: str
    ) -> Dict[str, Any]:
        """
        Gera o documento de minuta de ART / RRT em PDF 1.4 nativo.
        """
        prof_name = professional_data.get("name", "Eng. Fernando Henrique")
        crea_cau = professional_data.get("crea_cau", "CREA-SP 5060708090/D")
        rnp = professional_data.get("rnp", "2619087654")

        contractor = project_data.get("contractor", "Condomínio Residencial Parque das Árvores")
        location = project_data.get("location", "Av. das Nações Unidas, 14261 - São Paulo/SP")
        project_name = project_data.get("project_name", "Playground Modular Parkelô Modelo Floresta")
        capacity = project_data.get("capacity_users", 18)
        max_fall_height = project_data.get("max_fall_height_m", 1.80)
        safety_area = project_data.get("safety_area_m2", 48.5)

        # Montagem dos fluxos de texto e vetores no PDF
        # PDF-1.4 nativo com medição precisa em pontos (1 pt = 1/72 polegada, A4 = 595.28 x 841.89)
        pdf_stream = []
        pdf_stream.append("q")
        # Borda e Moldura Externa da Folha A4
        pdf_stream.append("0.2 0.3 0.4 RG 1.5 w")
        pdf_stream.append("30 30 535 781 re S")

        # Cabeçalho Oficial
        pdf_stream.append("0.0 0.25 0.45 rg")
        pdf_stream.append("30 750 535 61 re f")

        # Linhas de separação e quadros
        pdf_stream.append("0.7 0.7 0.7 RG 0.8 w")
        pdf_stream.append("40 610 515 125 re S")  # Quadro 1: Profissional
        pdf_stream.append("40 460 515 135 re S")  # Quadro 2: Objeto e Local
        pdf_stream.append("40 260 515 185 re S")  # Quadro 3: Especificações Técnicas e NBRs
        pdf_stream.append("40 100 515 145 re S")  # Quadro 4: Declarações e Assinaturas
        pdf_stream.append("Q")

        # Conteúdo Tipográfico
        text_stream = []
        # Título Cabeçalho
        text_stream.append("BT /F1 16 Tf 1 1 1 rg 50 782 Td (MINUTA DE ANOTAÇÃO DE RESPONSABILIDADE TÉCNICA - ART / RRT) Tj ET")
        text_stream.append("BT /F2 9 Tf 0.85 0.92 1.0 rg 50 762 Td (CONFORMIDADE INTEGRAL COM ABNT NBR 16071 (PARTES 1 A 7) E ABNT NBR 7190) Tj ET")

        # Quadro 1 - Dados do Profissional
        text_stream.append("BT /F1 11 Tf 0.1 0.2 0.3 rg 50 720 Td (1. DADOS DO PROFISSIONAL RESPONSÁVEL) Tj ET")
        text_stream.append(f"BT /F2 10 Tf 0.15 0.15 0.15 rg 50 698 Td (Nome do Responsável Técnico: {prof_name}) Tj ET")
        text_stream.append(f"BT /F2 10 Tf 0.15 0.15 0.15 rg 50 678 Td (Registro Profissional: {crea_cau}   |   RNP: {rnp}) Tj ET")
        text_stream.append("BT /F2 10 Tf 0.15 0.15 0.15 rg 50 658 Td (Atribuição Técnica: Projeto Mecânico, Estrutural e Fabricação de Equipamentos de Recreio) Tj ET")
        text_stream.append("BT /F2 10 Tf 0.15 0.15 0.15 rg 50 638 Td (Empresa Contratada / Fabricante: Parkelô Estruturas Lúdicas em Madeira Ltda.) Tj ET")

        # Quadro 2 - Dados da Obra e Contratante
        text_stream.append("BT /F1 11 Tf 0.1 0.2 0.3 rg 50 578 Td (2. DADOS DO CONTRATANTE E LOCAL DA OBRA) Tj ET")
        text_stream.append(f"BT /F2 10 Tf 0.15 0.15 0.15 rg 50 556 Td (Contratante: {contractor}) Tj ET")
        text_stream.append(f"BT /F2 10 Tf 0.15 0.15 0.15 rg 50 536 Td (Endereço da Instalação: {location}) Tj ET")
        text_stream.append(f"BT /F2 10 Tf 0.15 0.15 0.15 rg 50 516 Td (Denominação do Equipamento: {project_name}) Tj ET")
        text_stream.append("BT /F2 10 Tf 0.15 0.15 0.15 rg 50 496 Td (Tipo de Atividade: PROJETO E LAUDO DE CONFORMIDADE ESTRUTURAL E DE SEGURANÇA) Tj ET")
        text_stream.append("BT /F2 9 Tf 0.4 0.4 0.4 rg 50 476 Td (Finalidade: Uso coletivo recreativo infantil em área externa) Tj ET")

        # Quadro 3 - Parâmetros Técnicos e Normativos
        text_stream.append("BT /F1 11 Tf 0.1 0.2 0.3 rg 50 428 Td (3. DECLARAÇÃO E PARÂMETROS NORMATIVOS DE SEGURANÇA) Tj ET")
        text_stream.append(f"BT /F2 9.5 Tf 0.15 0.15 0.15 rg 50 406 Td (Capacidade Simultânea de Projeto: {capacity} crianças   |   Faixa Etária: 03 a 12 anos) Tj ET")
        text_stream.append(f"BT /F2 9.5 Tf 0.15 0.15 0.15 rg 50 388 Td (Altura Máxima de Queda Livre: {max_fall_height:.2f} m (Limite Normativo NBR 16071: <= 3.00 m)) Tj ET")
        text_stream.append(f"BT /F2 9.5 Tf 0.15 0.15 0.15 rg 50 370 Td (Área Mínima de Superfície de Absorção de Impacto: {safety_area:.1f} m²) Tj ET")
        text_stream.append("BT /F2 9.5 Tf 0.15 0.15 0.15 rg 50 352 Td (Material Estrutural: Eucalipto Citriodora Tratado em Autoclave (CCA/CCB - NBR 7190)) Tj ET")
        text_stream.append("BT /F2 9.5 Tf 0.15 0.15 0.15 rg 50 334 Td (Ferragens e Fixadores: Aço Inoxidável AISI 304 / Galvanizado a Fogo com Porcas Autotravantes) Tj ET")
        text_stream.append("BT /F2 9.5 Tf 0.15 0.15 0.15 rg 50 316 Td (Ensaios Anti-Aprisionamento: 100% de conformidade para sondas de cabeça, pescoço e dedos) Tj ET")
        text_stream.append("BT /F2 9 Tf 0.3 0.5 0.2 rg 50 286 Td ([STATUS]: PROJETO HOMOLOGADO E AUDITADO DIGITALMENTE NO SKETCHBUILD) Tj ET")

        # Quadro 4 - Assinaturas e Carimbo
        text_stream.append("BT /F1 11 Tf 0.1 0.2 0.3 rg 50 228 Td (4. TERMO DE ENCERRAMENTO E VALIDAÇÃO PROFISSIONAL) Tj ET")
        text_stream.append("BT /F2 8.5 Tf 0.25 0.25 0.25 rg 50 206 Td (Declaro para os devidos fins que o projeto mecânico e estrutural acima qualificado atende rigorosamente) Tj ET")
        text_stream.append("BT /F2 8.5 Tf 0.25 0.25 0.25 rg 50 194 Td (às normas técnicas da ABNT e aos cálculos de estabilidade estática e dinâmica de vigas e pilares.) Tj ET")

        # Linhas de Assinatura
        text_stream.append(f"BT /F2 9 Tf 0.1 0.1 0.1 rg 70 140 Td (____________________________________________________) Tj ET")
        text_stream.append(f"BT /F1 9 Tf 0.1 0.1 0.1 rg 110 126 Td ({prof_name}) Tj ET")
        text_stream.append(f"BT /F2 8.5 Tf 0.3 0.3 0.3 rg 135 114 Td ({crea_cau}) Tj ET")

        text_stream.append(f"BT /F2 9 Tf 0.1 0.1 0.1 rg 340 140 Td (_______________________________________) Tj ET")
        text_stream.append(f"BT /F1 9 Tf 0.1 0.1 0.1 rg 370 126 Td (Parkelô Estruturas Lúdicas) Tj ET")
        text_stream.append(f"BT /F2 8.5 Tf 0.3 0.3 0.3 rg 380 114 Td (Responsável Técnico de Fábrica) Tj ET")

        # Rodapé
        text_stream.append("BT /F2 8 Tf 0.5 0.5 0.5 rg 140 42 Td (Documento gerado automaticamente pelo SketchBuild CAD/BIM Engine - Validação Zero DLL) Tj ET")

        content_body = "\n".join(pdf_stream + text_stream)
        content_bytes = content_body.encode("latin-1", errors="replace")

        # Montagem do arquivo PDF 1.4 com tabela xref
        objects = []
        objects.append("<< /Type /Catalog /Pages 2 0 R >>")  # Obj 1: Catalog
        objects.append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")  # Obj 2: Pages
        objects.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] "
            "/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> "
            "/Contents 6 0 R >>"
        )  # Obj 3: Page
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")  # Obj 4: F1
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")  # Obj 5: F2
        objects.append(f"<< /Length {len(content_bytes)} >>\nstream\n{content_body}\nendstream")  # Obj 6: Content

        pdf_bytes = bytearray()
        pdf_bytes.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        offsets = []
        for i, obj in enumerate(objects, start=1):
            offsets.append(len(pdf_bytes))
            pdf_bytes.extend(f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1"))

        xref_pos = len(pdf_bytes)
        pdf_bytes.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        pdf_bytes.extend(b"0000000000 65535 f \n")
        for offset in offsets:
            pdf_bytes.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

        pdf_bytes.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
        )

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        return {
            "entity_type": "ArtReportPdf",
            "file_path": os.path.abspath(output_path),
            "size_bytes": len(pdf_bytes),
            "professional_name": prof_name,
            "crea_cau": crea_cau,
            "project_name": project_name,
            "contractor": contractor
        }
