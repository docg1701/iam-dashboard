# External APIs

Based on the PRD requirements and component design, the system requires several external API integrations to support the custom implementation service model:

## Brazilian VPS Provider APIs (Optional)

- **Purpose:** Optional automation for VPS management and domain configuration
- **Providers:** Contabo, Hostinger, Locaweb APIs (when available)
- **Integration:** SSH-based deployment preferred over API automation
- **Cost Optimization:** Manual setup preferred to avoid API complexity

## Domain and SSL Management

- **Purpose:** Domain registration and SSL certificate management for Brazilian domains (.com.br)
- **Providers:** Registro.br (official Brazilian domain registry), Let's Encrypt (SSL)
- **Integration:** Manual domain setup with automated SSL via Caddy and Let's Encrypt
- **Cost Advantage:** Free SSL certificates vs. paid managed services

---
