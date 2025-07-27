# Seção 12: Estrutura Unificada do Projeto (Monorepo)

A estrutura de diretórios reflete a separação de responsabilidades, com pastas claras para a aplicação (`app`), documentos (`docs`), testes (`tests`), etc., conforme detalhado no `docker.md`.

```plaintext
/sistema-advocacia-saas/
├── app/
│   ├── api/
│   ├── agents/
│   ├── core/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── ui_components/
│   ├── workers/
│   ├── containers.py
│   └── main.py
├── docs/
├── tests/
├── .env.example
├── Caddyfile
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```