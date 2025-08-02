# Introduction

This document outlines the complete fullstack architecture for **Multi-Agent IAM Dashboard**, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

### Starter Template Analysis

**Status**: **N/A - Greenfield Project**

After reviewing the PRD and existing CLAUDE.md documentation, this is a greenfield implementation with a clear technology stack already specified. The project follows established patterns:
- **Backend**: FastAPI + SQLModel + PostgreSQL (chosen for ACID compliance and structured relationships)
- **Frontend**: Next.js 15 + React 19 + TypeScript + shadcn/ui (selected for modern responsive design)
- **Multi-Agent Framework**: Agno for efficient agent instantiation 
- **Deployment**: Custom VPS deployment model using Docker Compose + Terraform + Ansible

The architecture constraints are well-defined in the Project Brief, eliminating the need for starter template evaluation.

### Key Architectural Decisions Made

1. **Custom Implementation Service Model**: Each client gets dedicated VPS instances rather than multi-tenant SaaS, enabling complete brand customization and data isolation
2. **Monolith + Independent Agents Pattern**: Core platform (FastAPI + Next.js) with independent AI agents communicating through shared PostgreSQL database
3. **Full Customization Focus**: Complete branding system using CSS variables enabling visual identity transformation
4. **Deployment Automation**: Terraform + Ansible automation targeting 3-4 week implementation cycles

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-08-01 | 1.0 | Initial architecture document creation | Winston (Architect) |
