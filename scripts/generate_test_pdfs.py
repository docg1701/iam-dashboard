"""Script to generate realistic test PDF documents for E2E testing.

This script creates various types of medical and legal documents that simulate
real-world scenarios for the IAM Dashboard system.
"""

import os
from pathlib import Path
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT


class TestPDFGenerator:
    """Generates realistic test PDF documents for various medical and legal scenarios."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=colors.black
        )

    def create_medical_exam_report(self, filename: str, patient_name: str, exam_type: str):
        """Create a medical examination report PDF."""
        doc = SimpleDocTemplate(
            str(self.output_dir / filename),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Header
        story.append(Paragraph("CLÍNICA MÉDICA TRABALHO & SAÚDE", self.title_style))
        story.append(Paragraph("CRM-SP: 123456 | CNPJ: 12.345.678/0001-90", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Title
        story.append(Paragraph(f"LAUDO DE {exam_type.upper()}", self.title_style))
        story.append(Spacer(1, 20))
        
        # Patient data
        story.append(Paragraph("DADOS DO PACIENTE", self.subtitle_style))
        patient_data = [
            ["Nome:", patient_name],
            ["Data do Exame:", datetime.now().strftime("%d/%m/%Y")],
            ["Médico Responsável:", "Dr. Roberto Silva - CRM-SP 98765"],
            ["Tipo de Exame:", exam_type]
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(patient_table)
        story.append(Spacer(1, 20))
        
        # Exam results
        story.append(Paragraph("RESULTADOS DO EXAME", self.subtitle_style))
        
        if "sangue" in exam_type.lower():
            results_text = """
            HEMOGRAMA COMPLETO:
            • Hemoglobina: 14,2 g/dL (Normal: 12,0-15,5)
            • Hematócrito: 42% (Normal: 36-45%)
            • Leucócitos: 7.200/mm³ (Normal: 4.000-11.000)
            • Plaquetas: 280.000/mm³ (Normal: 150.000-450.000)
            
            BIOQUÍMICA:
            • Glicemia de jejum: 92 mg/dL (Normal: 70-99)
            • Colesterol total: 185 mg/dL (Desejável: <200)
            • Triglicerídeos: 145 mg/dL (Normal: <150)
            • Creatinina: 0,9 mg/dL (Normal: 0,6-1,2)
            """
        elif "cardiológico" in exam_type.lower():
            results_text = """
            ELETROCARDIOGRAMA:
            • Ritmo sinusal regular
            • Frequência cardíaca: 72 bpm
            • Eixo elétrico normal
            • Sem alterações do segmento ST-T
            • Intervalo QT normal
            
            ECOCARDIOGRAMA:
            • Átrio esquerdo: 35mm (Normal: <40mm)
            • Ventrículo esquerdo: função sistólica preservada
            • Fração de ejeção: 65%
            • Válvulas cardíacas: sem alterações significativas
            """
        else:
            results_text = """
            EXAME FÍSICO GERAL:
            • Estado geral: Bom
            • Consciência: Lúcido e orientado
            • Marcha: Normal
            • Postura: Adequada
            
            SISTEMA MUSCULOESQUELÉTICO:
            • Amplitude de movimento: Preservada
            • Força muscular: Grau V/V nos quatro membros
            • Reflexos: Presentes e simétricos
            • Sem sinais de inflamação articular
            """
        
        story.append(Paragraph(results_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Conclusion
        story.append(Paragraph("CONCLUSÃO", self.subtitle_style))
        conclusion_text = """
        Com base nos exames realizados e na avaliação clínica, o paciente apresenta 
        condições de saúde compatíveis com suas atividades laborais. Não foram 
        identificadas alterações significativas que impeçam o exercício de suas 
        funções profissionais.
        
        Recomenda-se acompanhamento médico periódico conforme protocolo da medicina 
        do trabalho.
        """
        story.append(Paragraph(conclusion_text, self.styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Signature
        story.append(Paragraph("___________________________", self.styles['Normal']))
        story.append(Paragraph("Dr. Roberto Silva", self.styles['Normal']))
        story.append(Paragraph("CRM-SP 98765", self.styles['Normal']))
        story.append(Paragraph("Medicina do Trabalho", self.styles['Normal']))
        
        doc.build(story)

    def create_legal_expertise_report(self, filename: str, case_type: str):
        """Create a legal expertise report PDF."""
        doc = SimpleDocTemplate(
            str(self.output_dir / filename),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Header
        story.append(Paragraph("TRIBUNAL REGIONAL DO TRABALHO - 2ª REGIÃO", self.title_style))
        story.append(Paragraph("LAUDO PERICIAL MÉDICO", self.title_style))
        story.append(Spacer(1, 20))
        
        # Case data
        story.append(Paragraph("DADOS DO PROCESSO", self.subtitle_style))
        case_data = [
            ["Processo:", f"0001234-56.2024.5.02.0001"],
            ["Requerente:", "João Silva Santos"],
            ["Requerido:", "Empresa XYZ Ltda."],
            ["Perito:", "Dr. Carlos Medeiros - CRM-SP 54321"],
            ["Tipo:", case_type]
        ]
        
        case_table = Table(case_data, colWidths=[2*inch, 4*inch])
        case_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(case_table)
        story.append(Spacer(1, 20))
        
        # Questionnaire
        story.append(Paragraph("QUESITOS FORMULADOS", self.subtitle_style))
        
        questionnaire_text = """
        1. QUESITO: Qual a natureza da lesão apresentada pelo periciando?
        RESPOSTA: O periciando apresenta lesão degenerativa da coluna lombossacra, 
        caracterizada por discopatia nos níveis L4-L5 e L5-S1, com sinais de 
        comprometimento radicular.
        
        2. QUESITO: A lesão tem nexo causal com as atividades laborais?
        RESPOSTA: Sim. As atividades exercidas pelo periciando, que envolvem 
        levantamento repetitivo de peso e permanência prolongada em posição inadequada, 
        são fatores contributivos para o desenvolvimento da patologia apresentada.
        
        3. QUESITO: Há incapacidade laborativa?
        RESPOSTA: Sim. O periciando apresenta incapacidade parcial e permanente 
        para atividades que exijam esforço físico da coluna lombar, estimada em 
        25% de acordo com a tabela SUSEP.
        
        4. QUESITO: Há necessidade de tratamento?
        RESPOSTA: Sim. Recomenda-se tratamento fisioterápico, uso de medicação 
        anti-inflamatória e analgésica conforme necessário, além de adequação 
        ergonômica do posto de trabalho.
        """
        
        story.append(Paragraph(questionnaire_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Conclusion
        story.append(Paragraph("CONCLUSÃO", self.subtitle_style))
        conclusion_text = """
        Face ao exposto, conclui-se que o periciando apresenta lesão de natureza 
        ocupacional, com nexo causal estabelecido entre as atividades laborais 
        e a patologia diagnosticada. A incapacidade apresentada é parcial e 
        permanente, necessitando de acompanhamento médico especializado.
        """
        story.append(Paragraph(conclusion_text, self.styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Signature
        story.append(Paragraph("São Paulo, " + datetime.now().strftime("%d de %B de %Y"), self.styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph("___________________________", self.styles['Normal']))
        story.append(Paragraph("Dr. Carlos Medeiros", self.styles['Normal']))
        story.append(Paragraph("CRM-SP 54321", self.styles['Normal']))
        story.append(Paragraph("Perito Judicial", self.styles['Normal']))
        
        doc.build(story)

    def create_occupational_disease_report(self, filename: str, disease_type: str):
        """Create an occupational disease report PDF."""
        doc = SimpleDocTemplate(
            str(self.output_dir / filename),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Header
        story.append(Paragraph("CENTRO DE REFERÊNCIA EM SAÚDE DO TRABALHADOR", self.title_style))
        story.append(Paragraph("COMUNICAÇÃO DE ACIDENTE DE TRABALHO - CAT", self.title_style))
        story.append(Spacer(1, 20))
        
        # Worker data
        story.append(Paragraph("DADOS DO TRABALHADOR", self.subtitle_style))
        worker_data = [
            ["Nome:", "Maria Santos Silva"],
            ["CPF:", "123.456.789-01"],
            ["Data de Nascimento:", "15/03/1985"],
            ["Função:", "Operadora de Telemarketing"],
            ["Data de Admissão:", "10/01/2020"],
            ["Doença:", disease_type]
        ]
        
        worker_table = Table(worker_data, colWidths=[2*inch, 4*inch])
        worker_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(worker_table)
        story.append(Spacer(1, 20))
        
        # Disease description
        story.append(Paragraph("DESCRIÇÃO DA DOENÇA OCUPACIONAL", self.subtitle_style))
        
        if "túnel do carpo" in disease_type.lower():
            disease_text = """
            SÍNDROME DO TÚNEL DO CARPO - CID G56.0
            
            HISTÓRICO:
            A trabalhadora relata dor, formigamento e dormência nos dedos da mão 
            direita, principalmente no polegar, indicador e médio, com início há 
            aproximadamente 6 meses. Os sintomas se intensificam durante e após 
            a jornada de trabalho.
            
            EXAME FÍSICO:
            • Teste de Phalen: Positivo
            • Teste de Tinel: Positivo
            • Diminuição da sensibilidade nos dedos inervados pelo nervo mediano
            • Atrofia discreta da musculatura tenar
            
            ELETRONEUROMIOGRAFIA:
            • Velocidade de condução nervosa reduzida no nervo mediano
            • Latência distal aumentada
            • Compatível com síndrome do túnel do carpo moderada
            """
        else:
            disease_text = """
            LESÃO POR ESFORÇO REPETITIVO - CID M70.9
            
            HISTÓRICO:
            O trabalhador apresenta quadro de dor e limitação funcional nos membros 
            superiores, relacionado às atividades repetitivas executadas em sua 
            função. Início gradual dos sintomas há aproximadamente 8 meses.
            
            EXAME FÍSICO:
            • Dor à palpação em tendões flexores do punho
            • Limitação dolorosa da amplitude de movimento
            • Sinais de inflamação tendínea
            • Força muscular diminuída nos movimentos de preensão
            
            ULTRASSONOGRAFIA:
            • Espessamento e irregularidade dos tendões flexores
            • Presença de líquido intra-articular
            • Compatível com tenossinovite crônica
            """
        
        story.append(Paragraph(disease_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Occupational nexus
        story.append(Paragraph("NEXO OCUPACIONAL", self.subtitle_style))
        nexus_text = """
        A análise das atividades laborais demonstra exposição a fatores de risco 
        ergonômicos, incluindo:
        • Movimentos repetitivos dos membros superiores
        • Permanência prolongada na mesma posição
        • Pressão excessiva sobre estruturas anatômicas
        • Inadequação do mobiliário e equipamentos
        
        Há clara relação entre as atividades exercidas e o desenvolvimento da 
        patologia apresentada, caracterizando doença relacionada ao trabalho.
        """
        story.append(Paragraph(nexus_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Recommendations
        story.append(Paragraph("RECOMENDAÇÕES", self.subtitle_style))
        recommendations_text = """
        • Afastamento temporário das atividades laborais
        • Tratamento fisioterápico especializado
        • Adequação ergonômica do posto de trabalho
        • Implementação de pausas regulares durante a jornada
        • Acompanhamento médico periódico
        • Avaliação da necessidade de mudança de função
        """
        story.append(Paragraph(recommendations_text, self.styles['Normal']))
        
        doc.build(story)

    def generate_all_test_pdfs(self):
        """Generate all types of test PDF documents."""
        
        # Medical examination reports
        medical_exams = [
            ("exame_sangue_ana_silva.pdf", "Ana Beatriz Silva", "Exame de Sangue"),
            ("exame_cardiologico_joao_santos.pdf", "João Carlos Santos", "Exame Cardiológico"),
            ("exame_admissional_maria_oliveira.pdf", "Maria José Oliveira", "Exame Admissional"),
            ("exame_periodico_pedro_costa.pdf", "Pedro Henrique Costa", "Exame Periódico"),
            ("exame_demissional_lucia_lima.pdf", "Lúcia Fernanda Lima", "Exame Demissional"),
        ]
        
        for filename, patient, exam_type in medical_exams:
            self.create_medical_exam_report(filename, patient, exam_type)
            print(f"✅ Created: {filename}")
        
        # Legal expertise reports
        legal_reports = [
            ("pericia_coluna_lombar.pdf", "Lesão de Coluna Lombar"),
            ("pericia_acidente_trabalho.pdf", "Acidente de Trabalho"),
            ("pericia_doenca_ocupacional.pdf", "Doença Ocupacional"),
            ("pericia_incapacidade_laboral.pdf", "Incapacidade Laboral"),
        ]
        
        for filename, case_type in legal_reports:
            self.create_legal_expertise_report(filename, case_type)
            print(f"✅ Created: {filename}")
        
        # Occupational disease reports
        disease_reports = [
            ("cat_sindrome_tunel_carpo.pdf", "Síndrome do Túnel do Carpo"),
            ("cat_ler_dort.pdf", "LER/DORT"),
            ("cat_tendinite.pdf", "Tendinite Ocupacional"),
            ("cat_bursite.pdf", "Bursite Ocupacional"),
        ]
        
        for filename, disease_type in disease_reports:
            self.create_occupational_disease_report(filename, disease_type)
            print(f"✅ Created: {filename}")
        
        # Complex multi-page documents
        self.create_complex_medical_report()
        self.create_complex_legal_case()
        
        print(f"\n🎉 Successfully generated {len(medical_exams) + len(legal_reports) + len(disease_reports) + 2} test PDF documents!")

    def create_complex_medical_report(self):
        """Create a complex multi-page medical report."""
        filename = "laudo_completo_multipaginas.pdf"
        doc = SimpleDocTemplate(
            str(self.output_dir / filename),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title page
        story.append(Paragraph("LAUDO MÉDICO PERICIAL COMPLETO", self.title_style))
        story.append(Spacer(1, 50))
        
        # Add multiple sections to create a longer document
        sections = [
            ("ANAMNESE", """
            Paciente do sexo masculino, 45 anos, trabalhador da construção civil há 20 anos.
            Relata início de dor lombar há aproximadamente 2 anos, com piora progressiva.
            A dor é do tipo peso, com irradiação para membro inferior direito.
            Piora com esforços físicos e melhora com repouso.
            Nega traumas ou acidentes específicos.
            """),
            ("EXAME FÍSICO", """
            Paciente em bom estado geral, consciente e orientado.
            Marcha antálgica, com claudicação à esquerda.
            Inspeção: assimetria da cintura pélvica.
            Palpação: tensão da musculatura paravertebral lombar.
            Mobilidade: limitação dolorosa da flexão e rotação do tronco.
            Teste de Lasègue: positivo a 30° à direita.
            """),
            ("EXAMES COMPLEMENTARES", """
            RESSONÂNCIA MAGNÉTICA DA COLUNA LOMBAR:
            - Discopatia degenerativa L4-L5 e L5-S1
            - Protrusão discal posterior L5-S1
            - Estenose do canal vertebral discreta
            - Edema da medula óssea subcondral
            
            ELETRONEUROMIOGRAFIA:
            - Radiculopatia L5 à direita
            - Denervação aguda em músculos inervados por L5
            """),
            ("DISCUSSÃO", """
            O quadro clínico apresentado é compatível com discopatia degenerativa
            lombossacra associada a radiculopatia. A história ocupacional de 
            atividades com sobrecarga da coluna vertebral é fator contributivo
            para o desenvolvimento da patologia.
            
            A correlação entre os achados clínicos, radiológicos e 
            eletroneuromiográficos confirma o diagnóstico de lombalgia 
            ocupacional com comprometimento radicular.
            """)
        ]
        
        for title, content in sections:
            story.append(Paragraph(title, self.subtitle_style))
            story.append(Paragraph(content, self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        doc.build(story)
        print(f"✅ Created: {filename}")

    def create_complex_legal_case(self):
        """Create a complex legal case with multiple exhibits."""
        filename = "processo_trabalhista_complexo.pdf"
        doc = SimpleDocTemplate(
            str(self.output_dir / filename),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Cover
        story.append(Paragraph("PROCESSO TRABALHISTA", self.title_style))
        story.append(Paragraph("Reclamação Trabalhista c/c Indenização por Danos Morais", self.subtitle_style))
        story.append(Spacer(1, 30))
        
        # Case details
        details = [
            ("RECLAMANTE", "José Silva dos Santos"),
            ("RECLAMADA", "Indústria Metalúrgica ABC Ltda."),
            ("PROCESSO", "0001234-56.2024.5.02.0001"),
            ("VARA", "1ª Vara do Trabalho de São Paulo"),
            ("ADVOGADO", "João Carlos Santos Silva - OAB/SP 123456")
        ]
        
        for label, value in details:
            story.append(Paragraph(f"<b>{label}:</b> {value}", self.styles['Normal']))
            
        story.append(Spacer(1, 30))
        
        # Petition content
        petition_sections = [
            ("DOS FATOS", """
            O Reclamante foi admitido em 15/01/2020 para exercer a função de
            operador de máquinas, sendo submetido a condições inadequadas de
            trabalho que resultaram no desenvolvimento de doença ocupacional.
            
            Durante todo o período laboral, o Reclamante foi exposto a ruído
            excessivo, vibração e posturas inadequadas, sem o fornecimento
            adequado de equipamentos de proteção individual.
            """),
            ("DO DIREITO", """
            O artigo 157 da CLT estabelece que cabe às empresas cumprir e fazer
            cumprir as normas de segurança e medicina do trabalho. A NR-15
            regulamenta as atividades e operações insalubres.
            
            A Constituição Federal, em seu artigo 7º, inciso XXII, assegura
            aos trabalhadores urbanos e rurais a redução dos riscos inerentes
            ao trabalho, por meio de normas de saúde, higiene e segurança.
            """),
            ("DOS PEDIDOS", """
            Ante o exposto, requer-se:
            
            a) A condenação da Reclamada ao pagamento de indenização por
               danos morais no valor de R$ 50.000,00;
            
            b) O pagamento de adicional de insalubridade durante todo o
               período laboral;
            
            c) A condenação da Reclamada ao custeio do tratamento médico
               necessário à recuperação da saúde do Reclamante;
            
            d) A condenação da Reclamada aos ônus da sucumbência.
            """)
        ]
        
        for title, content in petition_sections:
            story.append(Paragraph(title, self.subtitle_style))
            story.append(Paragraph(content, self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        doc.build(story)
        print(f"✅ Created: {filename}")


if __name__ == "__main__":
    # Set output directory
    output_dir = Path(__file__).parent.parent / "test_pdfs"
    
    # Generate test PDFs
    generator = TestPDFGenerator(output_dir)
    generator.generate_all_test_pdfs()
    
    print(f"\n📁 All test PDFs saved to: {output_dir}")
    print(f"📊 Total files: {len(list(output_dir.glob('*.pdf')))}")