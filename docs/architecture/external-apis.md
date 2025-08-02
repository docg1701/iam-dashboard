# External APIs

The Multi-Agent IAM Dashboard has minimal external API dependencies due to its custom implementation service model focusing on data isolation and self-contained functionality.

### OpenAI Embeddings API (Agent 2 - PDF Processing)

- **Purpose:** Generate vector embeddings for PDF document chunks to enable semantic search and RAG capabilities
- **Documentation:** https://platform.openai.com/docs/api-reference/embeddings
- **Base URL:** https://api.openai.com/v1
- **Authentication:** Bearer token (API key)
- **Rate Limits:** 3,000 requests per minute, 1,000,000 tokens per minute

**Key Endpoints Used:**
- `POST /embeddings` - Generate embeddings for text chunks from PDF documents

### Let's Encrypt ACME API (Infrastructure)

- **Purpose:** Automatic SSL certificate provisioning and renewal for client domain configurations
- **Documentation:** https://letsencrypt.org/docs/acme-protocol-updates/
- **Base URL:** https://acme-v02.api.letsencrypt.org
- **Authentication:** ACME protocol with domain validation
- **Rate Limits:** 50 certificates per registered domain per week

**Integration Notes:** Handled automatically by Caddy reverse proxy during VPS deployment. No direct API integration required in application code.
