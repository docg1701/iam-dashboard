# Seção 4: Modelos de Dados

Os modelos de dados, definidos com SQLAlchemy, refletem a estrutura necessária para a aplicação e para a integração com o Llama-Index.

* **User:** Gerencia usuários e seus papéis (`sysadmin`, `admin_user`, `common_user`).
* **Client:** Armazena informações dos clientes do escritório.
* **Document:** Rastreia metadados e status dos arquivos PDF enviados.
* **DocumentChunk:** Armazena os nós (chunks) de texto vetorizados, compatível com o `PGVectorStore` do Llama-Index.
