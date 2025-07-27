# Seção 11: Arquitetura de Backend (Single-Tenant)

Adotaremos o **Padrão de Repositório** para acesso a dados e **Serviços Modulares** para a lógica de negócio, com todas as dependências gerenciadas pelo `python-dependency-injector`. A autorização será baseada em papéis (RBAC).
