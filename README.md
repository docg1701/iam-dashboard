# IAM Dashboard

Sistema de gerenciamento de identidade e controle de acesso com arquitetura multi-agente, oferecendo infraestrutura de automação IA personalizada em instâncias VPS dedicadas.

## Sobre o Projeto

O IAM Dashboard é um serviço de implementação customizada que transforma o modelo rígido de controle de acesso em um sistema flexível baseado em agentes, permitindo que 90% dos funcionários acessem as funcionalidades necessárias (vs. <10% com sistemas tradicionais).

## Características Principais

- **Sistema de Permissões Revolucionário:** Controle granular por agente em vez de papéis rígidos
- **Arquitetura Multi-Agente:** 4 agentes independentes para diferentes funcionalidades
- **Customização Completa:** Identidade visual personalizada por cliente
- **Infraestrutura Dedicada:** VPS brasileiro com isolamento total de dados
- **Deploy Automatizado:** Scripts SSH para implementação em 30 dias

## Tech Stack

- **Frontend:** Next.js 15 + React 19 + TypeScript + shadcn/ui
- **Backend:** FastAPI + SQLModel + PostgreSQL
- **Agentes:** Arquitetura independente com comunicação via banco compartilhado
- **Deploy:** Docker + SSH + systemd em VPS brasileiros

## Agentes do Sistema

1. **Client Management:** CRUD completo de clientes com validação CPF
2. **PDF Processing:** Processamento de documentos
3. **Reports Analysis:** Relatórios e analytics
4. **Audio Recording:** Gravação e transcrição de áudio

## Status do Projeto

✅ Arquitetura completa definida  
✅ Documentação técnica abrangente  
✅ Sistema de permissões inovador  
🚧 Implementação em desenvolvimento