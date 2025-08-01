#!/usr/bin/env python3
"""Script to populate additional test data: 20 clients and 10 PDFs."""

import asyncio
import os
import random
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_async_db
from app.models.client import Client
from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.client_repository import ClientRepository
from app.repositories.document_repository import DocumentRepository
from app.services.client_service import ClientService
from app.services.document_service import DocumentService


class AdditionalTestDataPopulator:
    """Populator for additional test data."""

    def __init__(self):
        self._generate_client_data()
        
        self.pdf_samples = [
            {
                "filename": "exame_medico_ocupacional.pdf",
                "content": self._generate_medical_pdf_content("Exame Médico Ocupacional"),
                "doc_type": DocumentType.COMPLEX
            },
            {
                "filename": "laudo_pericial_trabalho.pdf", 
                "content": self._generate_medical_pdf_content("Laudo Pericial Trabalhista"),
                "doc_type": DocumentType.COMPLEX
            },
            {
                "filename": "relatorio_acidente_trabalho.pdf",
                "content": self._generate_legal_pdf_content("Relatório de Acidente de Trabalho"),
                "doc_type": DocumentType.SIMPLE
            },
            {
                "filename": "atestado_medico_perito.pdf",
                "content": self._generate_medical_pdf_content("Atestado Médico Pericial"),
                "doc_type": DocumentType.SIMPLE
            },
            {
                "filename": "parecer_tecnico_seguranca.pdf",
                "content": self._generate_technical_pdf_content("Parecer Técnico de Segurança"),
                "doc_type": DocumentType.COMPLEX
            },
            {
                "filename": "documentos_previdenciarios.pdf",
                "content": self._generate_legal_pdf_content("Documentos Previdenciários"),
                "doc_type": DocumentType.SIMPLE
            },
            {
                "filename": "historico_medico_completo.pdf",
                "content": self._generate_medical_pdf_content("Histórico Médico Completo"),
                "doc_type": DocumentType.COMPLEX
            },
            {
                "filename": "contrato_trabalho_clt.pdf",
                "content": self._generate_legal_pdf_content("Contrato de Trabalho CLT"),
                "doc_type": DocumentType.SIMPLE
            },
            {
                "filename": "avaliacao_incapacidade.pdf",
                "content": self._generate_medical_pdf_content("Avaliação de Incapacidade"),
                "doc_type": DocumentType.COMPLEX
            },
            {
                "filename": "documentacao_trabalhista.pdf",
                "content": self._generate_legal_pdf_content("Documentação Trabalhista Completa"),
                "doc_type": DocumentType.SIMPLE
            }
        ]

    def _generate_medical_pdf_content(self, title: str) -> bytes:
        """Generate realistic medical PDF content."""
        content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 500>>stream
BT
/F1 12 Tf
50 700 Td
({title}) Tj
0 -20 Td
(Paciente: João Silva Santos) Tj
0 -20 Td
(Data do Exame: {datetime.now().strftime('%d/%m/%Y')}) Tj
0 -20 Td
(CID: M25.3 - Lesão por Esforço Repetitivo) Tj
0 -20 Td
(Diagnóstico: Tendinite no ombro direito) Tj
0 -20 Td
(Recomendações: Afastamento por 30 dias) Tj
0 -20 Td
(Fisioterapia recomendada) Tj
0 -20 Td
(Uso de anti-inflamatórios conforme prescrição) Tj
0 -20 Td
(Retorno em 15 dias para reavaliação) Tj
0 -20 Td
(Dr. Ana Beatriz Pereira Silva) Tj
0 -20 Td
(CRM/SP 123456) Tj
ET
endstream endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
0000000178 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
730
%%EOF"""
        return content.encode('utf-8')

    def _generate_legal_pdf_content(self, title: str) -> bytes:
        """Generate realistic legal PDF content."""
        content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 600>>stream
BT
/F1 12 Tf
50 700 Td
({title}) Tj
0 -20 Td
(Processo: 1234567-89.2024.5.02.0001) Tj
0 -20 Td
(Requerente: João Silva Santos) Tj
0 -20 Td
(Requerido: Empresa ABC Ltda) Tj
0 -20 Td
(Data do Acidente: 15/03/2024) Tj
0 -20 Td
(Local: Setor de Produção - Linha 3) Tj
0 -20 Td
(Natureza: Acidente com máquina industrial) Tj
0 -20 Td
(Lesões: Fratura no punho direito) Tj
0 -20 Td
(Afastamento: 45 dias) Tj
0 -20 Td
(Benefício: Auxílio-doença acidentário) Tj
0 -20 Td
(Advogado: Dr. João Legal Santos) Tj
0 -20 Td
(OAB/SP 654321) Tj
0 -20 Td
(São Paulo, {datetime.now().strftime('%d/%m/%Y')}) Tj
ET
endstream endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
0000000178 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
830
%%EOF"""
        return content.encode('utf-8')

    def _generate_technical_pdf_content(self, title: str) -> bytes:
        """Generate realistic technical PDF content."""
        content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 550>>stream
BT
/F1 12 Tf
50 700 Td
({title}) Tj
0 -20 Td
(Empresa: Indústria XYZ Ltda) Tj
0 -20 Td
(CNPJ: 12.345.678/0001-90) Tj
0 -20 Td
(Setor Analisado: Produção Industrial) Tj
0 -20 Td
(Responsável Técnico: Eng. Carlos Silva) Tj
0 -20 Td
(CREA: 1234567-D/SP) Tj
0 -20 Td
(Riscos Identificados:) Tj
0 -20 Td
(- Ruído excessivo acima de 85dB) Tj
0 -20 Td
(- Movimentação repetitiva) Tj
0 -20 Td
(- Exposição a produtos químicos) Tj
0 -20 Td
(Recomendações:) Tj
0 -20 Td
(- Uso obrigatório de EPIs) Tj
0 -20 Td
(- Rodízio de funcionários) Tj
0 -20 Td
(- Treinamento em segurança) Tj
ET
endstream endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
0000000178 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
780
%%EOF"""
        return content.encode('utf-8')

    def _generate_valid_cpf(self) -> str:
        """Generate a valid CPF number with check digits."""
        # Generate first 9 digits
        cpf = [random.randint(0, 9) for _ in range(9)]
        
        # Calculate first check digit
        sum1 = sum(cpf[i] * (10 - i) for i in range(9))
        digit1 = (sum1 * 10) % 11
        if digit1 == 10:
            digit1 = 0
        cpf.append(digit1)
        
        # Calculate second check digit
        sum2 = sum(cpf[i] * (11 - i) for i in range(10))
        digit2 = (sum2 * 10) % 11
        if digit2 == 10:
            digit2 = 0
        cpf.append(digit2)
        
        # Convert to string
        return ''.join(map(str, cpf))

    def _generate_client_data(self):
        """Generate client data with valid CPFs."""
        names = [
            # Medical professionals and patients
            "Maria Silva Santos",
            "João Carlos Oliveira", 
            "Ana Paula Rodrigues",
            "Carlos Eduardo Ferreira",
            "Luciana Mendes Costa",
            "Roberto Alves Lima",
            "Fernanda Souza Martins",
            "Paulo Ricardo Nunes",
            "Juliana Santos Barbosa",
            "Marcos Vinícius Silva",
            
            # Legal professionals and clients
            "Dra. Patrícia Legal Pereira",
            "Advogado José da Silva",
            "Cliente Industrial Ltda",
            "Trabalhador Manuel Santos",
            "Empresa ABC Construções",
            "Funcionário Pedro Costa",
            "Companhia XYZ Logística",
            "Operário Lucas Martins",
            "Indústria DEF Metalúrgica",
            "Técnico Rafael Oliveira"
        ]
        
        birth_dates = [
            date(1985, 3, 15), date(1978, 7, 22), date(1992, 11, 8),
            date(1980, 5, 30), date(1987, 9, 12), date(1975, 2, 18),
            date(1990, 12, 3), date(1983, 6, 25), date(1988, 4, 14),
            date(1979, 10, 7), date(1982, 1, 20), date(1976, 8, 15),
            date(1985, 3, 10), date(1990, 11, 25), date(1988, 7, 5),
            date(1981, 12, 18), date(1987, 4, 22), date(1984, 9, 8),
            date(1979, 6, 12), date(1986, 2, 28)
        ]
        
        self.clients_data = []
        for i, name in enumerate(names):
            cpf = self._generate_valid_cpf()
            birth_date = birth_dates[i]
            self.clients_data.append((name, cpf, birth_date))

    async def create_clients(self, db_session) -> List[Client]:
        """Create 20 additional test clients."""
        client_repo = ClientRepository(db_session)
        client_service = ClientService(client_repo)
        
        created_clients = []
        
        print("Creating 20 additional test clients...")
        
        for i, (name, cpf, birth_date) in enumerate(self.clients_data, 1):
            try:
                client = await client_service.create_client(
                    name=name,
                    cpf=cpf,
                    birth_date=birth_date
                )
                created_clients.append(client)
                print(f"  {i:2d}. Created client: {name} (CPF: {cpf})")
                
            except Exception as e:
                print(f"  {i:2d}. Failed to create client {name}: {e}")
                continue
        
        print(f"\nSuccessfully created {len(created_clients)} clients")
        return created_clients

    async def create_documents(self, db_session, clients: List[Client]):
        """Create 10 test PDF documents distributed among clients."""
        doc_repo = DocumentRepository(db_session)
        doc_service = DocumentService(doc_repo)
        
        created_documents = []
        
        print("\nCreating 10 test PDF documents...")
        
        # Distribute documents among first 10 clients
        for i, pdf_data in enumerate(self.pdf_samples, 1):
            try:
                # Use modulo to cycle through available clients
                client = clients[(i - 1) % len(clients)]
                
                doc = await doc_service.create_document(
                    client_id=client.id,
                    filename=pdf_data["filename"],
                    content=pdf_data["content"],
                    document_type=pdf_data["doc_type"]
                )
                
                created_documents.append(doc)
                print(f"  {i:2d}. Created document: {pdf_data['filename']} for {client.name}")
                
                # Set some documents as processed for testing
                if i % 3 == 0:  # Every 3rd document
                    doc_obj = await doc_service.get_document_by_id(doc["document_id"])
                    await doc_service.update_document_status(
                        doc_obj.id, 
                        DocumentStatus.PROCESSED,
                        "Processed by test script"
                    )
                    print(f"      → Set as PROCESSED")
                elif i % 4 == 0:  # Every 4th document
                    doc_obj = await doc_service.get_document_by_id(doc["document_id"])
                    await doc_service.update_document_status(
                        doc_obj.id, 
                        DocumentStatus.PROCESSING,
                        "Currently processing"
                    )
                    print(f"      → Set as PROCESSING")
                
            except Exception as e:
                print(f"  {i:2d}. Failed to create document {pdf_data['filename']}: {e}")
                continue
        
        print(f"\nSuccessfully created {len(created_documents)} documents")
        return created_documents

    async def populate_all_data(self):
        """Populate all additional test data."""
        print("=== Additional Test Data Population ===")
        print("Creating 20 clients and 10 PDF documents...\n")
        
        try:
            # Get database session
            async for db_session in get_async_db():
                # Create clients first
                clients = await self.create_clients(db_session)
                
                if not clients:
                    print("No clients created, skipping document creation")
                    return
                
                # Create documents
                documents = await self.create_documents(db_session, clients)
                
                print(f"\n=== Population Complete ===")
                print(f"Total clients created: {len(clients)}")
                print(f"Total documents created: {len(documents)}")
                print("\nData Summary:")
                print(f"  Medical professionals: {len([c for c in clients[:10]])}")
                print(f"  Legal professionals/clients: {len([c for c in clients[10:]])}")
                
                # Count document types based on PDF samples
                medical_docs = len([pdf for pdf in self.pdf_samples if 'medico' in pdf['filename'] or 'exame' in pdf['filename'] or 'laudo' in pdf['filename']])
                legal_docs = len([pdf for pdf in self.pdf_samples if 'legal' in pdf['filename'] or 'contrato' in pdf['filename'] or 'trabalhista' in pdf['filename']])
                technical_docs = len([pdf for pdf in self.pdf_samples if 'tecnico' in pdf['filename'] or 'seguranca' in pdf['filename']])
                
                print(f"  Medical documents: {medical_docs}")
                print(f"  Legal documents: {legal_docs}")
                print(f"  Technical documents: {technical_docs}")
                
                break  # Exit after first successful session
                
        except Exception as e:
            print(f"Error during population: {e}")
            raise


async def main():
    """Main function to run the population script."""
    populator = AdditionalTestDataPopulator()
    await populator.populate_all_data()


if __name__ == "__main__":
    asyncio.run(main())