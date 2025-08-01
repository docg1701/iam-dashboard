"""Simple database setup and test data population for E2E testing."""

import asyncio
import uuid
from datetime import datetime, date, timezone
import psycopg2
from psycopg2.extras import RealDictCursor


def create_database_schema():
    """Create database schema directly with SQL."""
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        port="5432", 
        user="postgres",
        password="postgres",
        database="advocacia_db"
    )
    
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        print("🔧 Creating database schema...")
        
        # Create extensions
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        print("✅ Created pgcrypto extension")
        
        # Create enum types
        cursor.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('sysadmin', 'admin_user', 'common_user');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """)
        
        cursor.execute("""
        DO $$ BEGIN
            CREATE TYPE documenttype AS ENUM ('simple', 'complex');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """)
        
        cursor.execute("""
        DO $$ BEGIN
            CREATE TYPE documentstatus AS ENUM ('pending', 'processing', 'processed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """)
        print("✅ Created enum types")
        
        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role userrole NOT NULL,
            is_active BOOLEAN DEFAULT true NOT NULL,
            totp_secret VARCHAR(32),
            is_2fa_enabled BOOLEAN DEFAULT false NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        """)
        print("✅ Created users table")
        
        # Create clients table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            cpf VARCHAR(11) UNIQUE NOT NULL,
            birth_date DATE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        """)
        print("✅ Created clients table")
        
        # Create documents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            content_hash VARCHAR(64) NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            document_type documenttype NOT NULL,
            status documentstatus NOT NULL,
            client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            file_path VARCHAR(500) NOT NULL,
            processed_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        """)
        print("✅ Created documents table")
        
        # Create questionnaire drafts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questionnaire_drafts (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id),
            content TEXT NOT NULL,
            profession VARCHAR(100) NOT NULL,
            disease VARCHAR(200) NOT NULL,
            incident_date VARCHAR(10) NOT NULL,
            medical_date VARCHAR(10) NOT NULL,
            template_type VARCHAR(100) DEFAULT 'standard' NOT NULL,
            status VARCHAR(50) DEFAULT 'draft' NOT NULL,
            metadata_ JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        """)
        print("✅ Created questionnaire_drafts table")
        
        print("🎉 Database schema created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def populate_test_data():
    """Populate database with test data."""
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        port="5432", 
        user="postgres",
        password="postgres",
        database="advocacia_db"
    )
    
    conn.autocommit = True
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("📊 Populating test data...")
        
        # Create users (personas)
        users_data = [
            ("dr.ana.pereira", "Dra. Ana Beatriz Pereira Silva", "common_user"),
            ("joao.santos.adv", "João Carlos Santos Silva", "admin_user"),
            ("carlos.ti.admin", "Carlos Roberto Oliveira", "sysadmin"),
        ]
        
        created_users = []
        for username, full_name, role in users_data:
            user_id = str(uuid.uuid4())
            cursor.execute("""
            INSERT INTO users (id, username, hashed_password, role, is_active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """, (user_id, username, "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", role, True))
            
            created_users.append((user_id, username, full_name))
            print(f"✅ Created user: {username} ({role})")
        
        # Create clients
        clients_data = [
            ("Dr. Ana Paula Silva", "12345678901", date(1985, 3, 15)),
            ("João Carlos Santos", "23456789012", date(1978, 7, 20)),
            ("Maria José Oliveira", "34567890123", date(1990, 12, 5)),
            ("Pedro Henrique Costa", "45678901234", date(1982, 5, 10)),
            ("Lucia Fernanda Lima", "56789012345", date(1987, 9, 25)),
            ("Roberto Carlos Mendes", "67890123456", date(1975, 1, 30)),
            ("Sandra Regina Souza", "78901234567", date(1992, 4, 18)),
            ("Carlos Eduardo Alves", "89012345678", date(1980, 11, 8)),
            ("Fernanda Cristina Rocha", "90123456789", date(1989, 6, 12)),
            ("Antonio José Barbosa", "10123456789", date(1970, 8, 22)),
        ]
        
        created_clients = []
        for name, cpf, birth_date in clients_data:
            client_id = str(uuid.uuid4())
            cursor.execute("""
            INSERT INTO clients (id, name, cpf, birth_date)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """, (client_id, name, cpf, birth_date))
            
            created_clients.append((client_id, name))
            print(f"✅ Created client: {name}")
        
        # Create documents for first 5 clients
        document_types = [
            ("simple", "Exame de sangue"),
            ("complex", "Laudo medico completo"),
            ("simple", "Receita medica"),
            ("complex", "Relatorio de pericia"),
            ("simple", "Atestado medico"),
        ]
        
        for i, (client_id, client_name) in enumerate(created_clients[:5]):
            doc_type, doc_name = document_types[i]
            doc_id = str(uuid.uuid4())
            filename = f"{doc_name.lower().replace(' ', '_')}_{client_name.split()[0].lower()}.pdf"
            
            cursor.execute("""
            INSERT INTO documents (id, filename, content_hash, file_size, mime_type, document_type, status, client_id, file_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """, (
                doc_id, filename, f"hash_{i}", 1024, "application/pdf", 
                doc_type, "processed", client_id, f"/test_pdfs/{filename}"
            ))
            
            print(f"✅ Created document: {filename} for {client_name}")
        
        # Create questionnaire drafts for first 3 clients
        questionnaire_samples = [
            {
                "content": "1. Qual a natureza da lesao apresentada pelo periciando?\n2. A lesao e decorrente de acidente de trabalho?\n3. Ha incapacidade laborativa temporaria ou permanente?",
                "profession": "Operario",
                "disease": "Lesao na coluna",
                "incident_date": "2024-01-15",
                "medical_date": "2024-01-20"
            },
            {
                "content": "1. Qual o diagnostico apresentado pelo periciando?\n2. A doenca e de natureza ocupacional?\n3. Existe nexo causal entre a atividade e a patologia?",
                "profession": "Enfermeira",
                "disease": "Sindrome do tunel do carpo",
                "incident_date": "2024-02-10", 
                "medical_date": "2024-02-15"
            },
            {
                "content": "1. Ha limitacao funcional decorrente da patologia?\n2. Qual o grau de incapacidade apresentado?\n3. A patologia e compativel com as atividades exercidas?",
                "profession": "Secretaria",
                "disease": "LER/DORT",
                "incident_date": "2024-03-05",
                "medical_date": "2024-03-10"
            }
        ]
        
        for i, (client_id, client_name) in enumerate(created_clients[:3]):
            sample = questionnaire_samples[i]
            draft_id = str(uuid.uuid4())
            user_id = created_users[0][0]  # Dr. Ana's user ID
            
            cursor.execute("""
            INSERT INTO questionnaire_drafts (id, client_id, user_id, content, profession, disease, incident_date, medical_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """, (
                draft_id, client_id, user_id, sample["content"], 
                sample["profession"], sample["disease"], 
                sample["incident_date"], sample["medical_date"]
            ))
            
            print(f"✅ Created questionnaire draft for {client_name}")
        
        print("\n🎉 Test data population completed!")
        print(f"   • Users: {len(created_users)}")
        print(f"   • Clients: {len(created_clients)}")
        print(f"   • Documents: 5")
        print(f"   • Questionnaire drafts: 3")
        
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("🚀 Starting simple database setup...")
    
    # Create schema
    create_database_schema()
    
    # Populate test data
    populate_test_data()
    
    print("\n✅ Setup completed successfully!")
    print("\n📊 Test credentials:")
    print("   • Dr. Ana: username=dr.ana.pereira, password=secret")
    print("   • João: username=joao.santos.adv, password=secret")  
    print("   • Carlos: username=carlos.ti.admin, password=secret")
    print("\n📁 Test PDFs available in: test_pdfs/")
    print("   • 15 realistic medical and legal documents created")