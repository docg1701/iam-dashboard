"""Script to populate the database with test data for E2E testing.

This script creates:
- 20 mock clients with realistic Brazilian data
- Various document types and statuses
- Test users with different roles
- Sample questionnaire drafts
"""

import asyncio
import uuid
from datetime import datetime, date, timezone
from pathlib import Path
import sys

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_async_db
from app.models.client import Client
from app.models.user import User, UserRole
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.questionnaire_draft import QuestionnaireDraft
from app.repositories.client_repository import ClientRepository
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.services.client_service import ClientService
from app.services.user_service import UserService
from app.services.document_service import DocumentService


class TestDataPopulator:
    """Populates database with test data for E2E testing."""

    def __init__(self):
        self.clients_data = []
        self.users_data = []
        self.documents_data = []
        
    def generate_test_clients(self) -> list[dict]:
        """Generate 20 test clients with realistic Brazilian data."""
        clients = [
            {
                "name": "Dr. Ana Paula Silva",
                "cpf": "12345678901",
                "birth_date": date(1985, 3, 15),
                "email": "ana.silva@exemplo.com",
                "phone": "(11) 99999-1234",
                "profession": "Médica",
                "address": "Rua das Flores, 123 - São Paulo, SP"
            },
            {
                "name": "João Carlos Santos",
                "cpf": "23456789012", 
                "birth_date": date(1978, 7, 20),
                "email": "joao.santos@exemplo.com",
                "phone": "(21) 88888-5678",
                "profession": "Advogado",
                "address": "Av. Atlântica, 456 - Rio de Janeiro, RJ"
            },
            {
                "name": "Maria José Oliveira",
                "cpf": "34567890123",
                "birth_date": date(1990, 12, 5),
                "email": "maria.oliveira@exemplo.com", 
                "phone": "(31) 77777-9012",
                "profession": "Enfermeira",
                "address": "Rua Minas Gerais, 789 - Belo Horizonte, MG"
            },
            {
                "name": "Pedro Henrique Costa",
                "cpf": "45678901234",
                "birth_date": date(1982, 5, 10),
                "email": "pedro.costa@exemplo.com",
                "phone": "(41) 66666-3456", 
                "profession": "Engenheiro",
                "address": "Rua XV de Novembro, 321 - Curitiba, PR"
            },
            {
                "name": "Lucia Fernanda Lima",
                "cpf": "56789012345",
                "birth_date": date(1987, 9, 25),
                "email": "lucia.lima@exemplo.com",
                "phone": "(51) 55555-7890",
                "profession": "Professora", 
                "address": "Av. Borges de Medeiros, 654 - Porto Alegre, RS"
            },
            {
                "name": "Roberto Carlos Mendes",
                "cpf": "67890123456",
                "birth_date": date(1975, 1, 30),
                "email": "roberto.mendes@exemplo.com",
                "phone": "(61) 44444-2345",
                "profession": "Contador",
                "address": "SQN 123 Bloco A - Brasília, DF"
            },
            {
                "name": "Sandra Regina Souza",
                "cpf": "78901234567",
                "birth_date": date(1992, 4, 18),
                "email": "sandra.souza@exemplo.com",
                "phone": "(85) 33333-6789",
                "profession": "Fisioterapeuta",
                "address": "Rua do Sol, 987 - Fortaleza, CE"
            },
            {
                "name": "Carlos Eduardo Alves",
                "cpf": "89012345678",
                "birth_date": date(1980, 11, 8),
                "email": "carlos.alves@exemplo.com",
                "phone": "(71) 22222-0123",
                "profession": "Médico Ortopedista",
                "address": "Av. Sete de Setembro, 159 - Salvador, BA"
            },
            {
                "name": "Fernanda Cristina Rocha",
                "cpf": "90123456789",
                "birth_date": date(1989, 6, 12),
                "email": "fernanda.rocha@exemplo.com",
                "phone": "(48) 11111-4567",
                "profession": "Psicóloga",
                "address": "Rua Felipe Schmidt, 753 - Florianópolis, SC"
            },
            {
                "name": "Antonio José Barbosa",
                "cpf": "01234567890",
                "birth_date": date(1970, 8, 22),
                "email": "antonio.barbosa@exemplo.com",
                "phone": "(81) 99999-8901",
                "profession": "Empresário",
                "address": "Rua da Aurora, 357 - Recife, PE"
            },
            {
                "name": "Juliana Santos Pereira",
                "cpf": "12345098765",
                "birth_date": date(1986, 2, 14),
                "email": "juliana.pereira@exemplo.com",
                "phone": "(62) 88888-2345",
                "profession": "Dentista",
                "address": "Av. Goiás, 741 - Goiânia, GO"
            },
            {
                "name": "Marcos Paulo Silva",
                "cpf": "23456109876",
                "birth_date": date(1977, 10, 3),
                "email": "marcos.silva@exemplo.com",
                "phone": "(65) 77777-6789",
                "profession": "Veterinário",
                "address": "Rua das Palmeiras, 852 - Cuiabá, MT"
            },
            {
                "name": "Cristiane Almeida Santos",
                "cpf": "34567210987",
                "birth_date": date(1991, 12, 17),
                "email": "cristiane.santos@exemplo.com",
                "phone": "(27) 66666-0123",
                "profession": "Farmacêutica",
                "address": "Av. Vitória, 963 - Vitória, ES"
            },
            {
                "name": "Ricardo Ferreira Lima",
                "cpf": "45678321098",
                "birth_date": date(1983, 5, 28),
                "email": "ricardo.lima@exemplo.com",
                "phone": "(84) 55555-4567", 
                "profession": "Arquiteto",
                "address": "Rua Chile, 147 - Natal, RN"
            },
            {
                "name": "Beatriz Costa Oliveira",
                "cpf": "56789432109",
                "birth_date": date(1988, 7, 9),
                "email": "beatriz.oliveira@exemplo.com",
                "phone": "(98) 44444-8901",
                "profession": "Nutricionista",
                "address": "Av. dos Franceses, 258 - São Luís, MA"
            },
            {
                "name": "Alexandre Rodrigues Silva",
                "cpf": "67890543210",
                "birth_date": date(1974, 3, 6),
                "email": "alexandre.silva@exemplo.com",
                "phone": "(96) 33333-2345",
                "profession": "Piloto de Avião",
                "address": "Rua Amazonas, 369 - Macapá, AP"
            },
            {
                "name": "Camila Ribeiro Costa",
                "cpf": "78901654321",
                "birth_date": date(1993, 9, 21),
                "email": "camila.costa@exemplo.com",
                "phone": "(69) 22222-6789",
                "profession": "Jornalista",
                "address": "Av. Brasil, 470 - Porto Velho, RO"
            },
            {
                "name": "Daniel Souza Mendes",
                "cpf": "89012765432",
                "birth_date": date(1981, 1, 15),
                "email": "daniel.mendes@exemplo.com",
                "phone": "(68) 11111-0123",
                "profession": "Professor Universitário",
                "address": "Rua Rio Branco, 581 - Rio Branco, AC"
            },
            {
                "name": "Patrícia Lima Alves",
                "cpf": "90123876543",
                "birth_date": date(1985, 11, 27),
                "email": "patricia.alves@exemplo.com",
                "phone": "(95) 99999-4567",
                "profession": "Bióloga",
                "address": "Av. Boa Vista, 692 - Boa Vista, RR"
            },
            {
                "name": "Gustavo Martins Rocha",
                "cpf": "01234987654",
                "birth_date": date(1979, 4, 11),
                "email": "gustavo.rocha@exemplo.com",
                "phone": "(92) 88888-8901",
                "profession": "Engenheiro Florestal",
                "address": "Rua 7 de Setembro, 803 - Manaus, AM"
            }
        ]
        return clients

    def generate_test_users(self) -> list[dict]:
        """Generate test users including the three main personas with realistic data."""
        users = [
            # Dr. Ana - Medical Expert Persona
            {
                "username": "dr.ana.pereira",
                "email": "ana.pereira@medicoperito.com.br",
                "full_name": "Dra. Ana Beatriz Pereira Silva",
                "role": UserRole.COMMON_USER,
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
                "is_active": True,
                "totp_secret": None,
                "bio": "Médica do Trabalho especializada em perícias médicas trabalhistas. CRM-SP 123456. Processa 50-100 laudos médicos por semana.",
                "specialization": "Medicina do Trabalho e Perícias Médicas"
            },
            # João - Legal Professional Persona  
            {
                "username": "joao.santos.adv", 
                "email": "joao.santos@escritoriosantos.adv.br",
                "full_name": "João Carlos Santos Silva",
                "role": UserRole.ADMIN_USER,
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
                "is_active": True,
                "totp_secret": None,
                "bio": "Advogado trabalhista com 15 anos de experiência. OAB-SP 123456. Especialista em casos de acidente de trabalho e doenças ocupacionais.",
                "specialization": "Direito do Trabalho e Previdenciário"
            },
            # Carlos - IT Administrator Persona
            {
                "username": "carlos.ti.admin",
                "email": "carlos.oliveira@iam-dashboard.com.br", 
                "full_name": "Carlos Roberto Oliveira",
                "role": UserRole.SYSADMIN,
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
                "is_active": True,
                "totp_secret": None,
                "bio": "Administrador de TI com expertise em sistemas jurídicos. Responsável pela infraestrutura e segurança dos sistemas do escritório.",
                "specialization": "Administração de Sistemas e Segurança da Informação"
            },
            # Additional test users for variety
            {
                "username": "maria.coord",
                "email": "maria.coordenadora@iam-dashboard.com.br",
                "full_name": "Maria José Coordenadora",
                "role": UserRole.ADMIN_USER,
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
                "is_active": True,
                "totp_secret": None,
                "bio": "Coordenadora administrativa do escritório de advocacia.",
                "specialization": "Administração e Gestão"
            },
            {
                "username": "pedro.estagiario",
                "email": "pedro.estagiario@iam-dashboard.com.br",
                "full_name": "Pedro Henrique Estagiário",
                "role": UserRole.COMMON_USER,
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
                "is_active": True,
                "totp_secret": None,
                "bio": "Estagiário de direito, 8º semestre. Auxilia na organização de documentos e processos.",
                "specialization": "Estudante de Direito"
            }
        ]
        return users

    async def populate_clients(self, db_session):
        """Populate database with test clients."""
        client_repo = ClientRepository(db_session)
        client_service = ClientService(client_repo)
        
        created_clients = []
        
        for client_data in self.generate_test_clients():
            try:
                client = await client_service.create_client(
                    name=client_data["name"],
                    cpf=client_data["cpf"],
                    birth_date=client_data["birth_date"]
                )
                created_clients.append(client)
                print(f"✓ Created client: {client.name}")
            except Exception as e:
                print(f"✗ Failed to create client {client_data['name']}: {e}")
                
        return created_clients

    async def populate_users(self, db_session):
        """Populate database with test users."""
        user_repo = UserRepository(db_session)
        user_service = UserService(user_repo)
        
        created_users = []
        
        for user_data in self.generate_test_users():
            try:
                # Create user directly in repository to avoid password hashing
                user = User(
                    id=uuid.uuid4(),
                    username=user_data["username"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    hashed_password=user_data["hashed_password"],
                    is_active=user_data["is_active"],
                    totp_secret=user_data["totp_secret"],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                created_user = await user_repo.create(user)
                created_users.append(created_user)
                print(f"✓ Created user: {created_user.username} ({created_user.role.value})")
            except Exception as e:
                print(f"✗ Failed to create user {user_data['username']}: {e}")
                
        return created_users

    async def populate_documents(self, db_session, clients):
        """Populate database with test documents for clients."""
        doc_repo = DocumentRepository(db_session)
        doc_service = DocumentService(doc_repo)
        
        document_types = [
            (DocumentType.SIMPLE, "Exame de sangue", "Conteudo do exame de sangue simulado".encode('utf-8')),
            (DocumentType.COMPLEX, "Laudo medico completo", "Laudo medico detalhado simulado".encode('utf-8')),
            (DocumentType.SIMPLE, "Receita medica", "Receita medica simulada".encode('utf-8')),
            (DocumentType.COMPLEX, "Relatorio de pericia", "Relatorio de pericia medica simulado".encode('utf-8'))
        ]
        
        created_documents = []
        
        for i, client in enumerate(clients[:10]):  # Create documents for first 10 clients
            doc_type, filename, content = document_types[i % len(document_types)]
            
            try:
                result = await doc_service.create_document(
                    client_id=client.id,
                    filename=f"{filename}_{client.name.split()[0].lower()}.pdf",
                    content=content,
                    document_type=doc_type
                )
                
                # Update document status
                doc_id = uuid.UUID(result["document_id"])
                status = [DocumentStatus.PROCESSED, DocumentStatus.PROCESSING, DocumentStatus.FAILED][i % 3]
                await doc_service.update_document_status(doc_id, status)
                
                created_documents.append(result)
                print(f"✓ Created document: {filename} for {client.name}")
            except Exception as e:
                print(f"✗ Failed to create document for {client.name}: {e}")
                
        return created_documents

    async def populate_questionnaire_drafts(self, db_session, clients):
        """Populate database with test questionnaire drafts."""
        created_drafts = []
        
        questionnaire_samples = [
            {
                "content": """1. Qual a natureza da lesao apresentada pelo periciando?
2. A lesao e decorrente de acidente de trabalho?
3. Ha incapacidade laborativa temporaria ou permanente?
4. Qual o grau de incapacidade apresentado?
5. A lesao e compativel com as atividades exercidas?""",
                "profession": "Operario",
                "disease": "Lesao na coluna",
                "incident_date": "2024-01-15",
                "medical_date": "2024-01-20"
            },
            {
                "content": """1. Qual o diagnostico apresentado pelo periciando?
2. A doenca e de natureza ocupacional?
3. Existe nexo causal entre a atividade e a patologia?
4. Qual o prognostico da enfermidade?
5. Ha necessidade de afastamento das atividades?""",
                "profession": "Enfermeira",
                "disease": "Sindrome do tunel do carpo",
                "incident_date": "2024-02-10", 
                "medical_date": "2024-02-15"
            }
        ]
        
        for i, client in enumerate(clients[:5]):  # Create drafts for first 5 clients
            sample = questionnaire_samples[i % len(questionnaire_samples)]
            
            try:
                draft = QuestionnaireDraft(
                    id=uuid.uuid4(),
                    client_id=client.id,
                    user_id=None,  # Will be set when users are available
                    content=sample["content"],
                    profession=sample["profession"],
                    disease=sample["disease"],
                    incident_date=sample["incident_date"],
                    medical_date=sample["medical_date"],
                    template_type="medical_examination",
                    status="draft",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                db_session.add(draft)
                await db_session.commit()
                await db_session.refresh(draft)
                
                created_drafts.append(draft)
                print(f"✓ Created questionnaire draft for {client.name}")
            except Exception as e:
                print(f"✗ Failed to create questionnaire draft for {client.name}: {e}")
                
        return created_drafts

    async def run(self):
        """Run the complete data population process."""
        print("🚀 Starting test data population...")
        
        async for db_session in get_async_db():
            try:
                # Create clients
                print("\n📋 Creating test clients...")
                clients = await self.populate_clients(db_session)
                
                # Create users
                print("\n👥 Creating test users...")
                users = await self.populate_users(db_session)
                
                # Create documents
                print("\n📄 Creating test documents...")
                documents = await self.populate_documents(db_session, clients)
                
                # Create questionnaire drafts
                print("\n❓ Creating test questionnaire drafts...")
                drafts = await self.populate_questionnaire_drafts(db_session, clients)
                
                print(f"\n✅ Test data population completed!")
                print(f"   • Clients: {len(clients)}")
                print(f"   • Users: {len(users)}")
                print(f"   • Documents: {len(documents)}")
                print(f"   • Questionnaire drafts: {len(drafts)}")
                
                return {
                    "clients": clients,
                    "users": users, 
                    "documents": documents,
                    "questionnaire_drafts": drafts
                }
                
            except Exception as e:
                print(f"❌ Error during data population: {e}")
                await db_session.rollback()
                raise
            finally:
                break  # Exit the async generator


if __name__ == "__main__":
    populator = TestDataPopulator()
    asyncio.run(populator.run())