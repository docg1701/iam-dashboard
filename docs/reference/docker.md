# Docker & Docker Compose para Sistema de Advocacia

Este guia foca na containerização do sistema SaaS de agentes autônomos para advocacia, cobrindo desenvolvimento local, orquestração de serviços (PostgreSQL + pgvector + Redis + Caddy) e deploy single-tenant por escritório de advocacia.

## Configuração Docker Compose para Sistema de Advocacia

### docker-compose.yml Principal

```yaml
version: '3.8'

services:
  # Aplicação principal NiceGUI
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+psycopg://postgres:advocacia123@db:5432/advocacia_db
      - REDIS_URL=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./app:/app/app
      - ./docs:/app/docs
      - uploads:/app/uploads
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - advocacia-network

  # PostgreSQL com pgvector
  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=advocacia_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=advocacia123
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-extensions.sql:/docker-entrypoint-initdb.d/init-extensions.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d advocacia_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - advocacia-network

  # Redis para Celery
  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - advocacia-network

  # Worker Celery para processamento de PDFs
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.workers.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+psycopg://postgres:advocacia123@db:5432/advocacia_db
      - REDIS_URL=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./app:/app/app
      - uploads:/app/uploads
    depends_on:
      - db
      - redis
    networks:
      - advocacia-network

  # Caddy para reverse proxy e HTTPS
  caddy:
    image: caddy:2.10-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - app
    networks:
      - advocacia-network

volumes:
  postgres_data:
  redis_data:
  uploads:
  caddy_data:
  caddy_config:

networks:
  advocacia-network:
    driver: bridge
```

### Dockerfile Otimizado

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema para OCR e PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copiar código da aplicação
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exposir porta da aplicação
EXPOSE 8000

# Comando padrão
CMD ["python", "-m", "app.main"]
```

### Script de Inicialização PostgreSQL

```sql
-- scripts/init-extensions.sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Criar usuário específico da aplicação (opcional)
-- CREATE USER advocacia_app WITH PASSWORD 'app_password';
-- GRANT ALL PRIVILEGES ON DATABASE advocacia_db TO advocacia_app;
```

### Arquivo .env.example

```env
# Configurações da aplicação
SECRET_KEY=your-secret-key-here
DEBUG=false

# Banco de dados
DATABASE_URL=postgresql+psycopg://postgres:advocacia123@localhost:5432/advocacia_db

# Redis
REDIS_URL=redis://localhost:6379/0

# APIs externas
GEMINI_API_KEY=your-gemini-api-key

# Configurações de upload
MAX_UPLOAD_SIZE_MB=50
UPLOAD_FOLDER=uploads
```

## Índice

- Introdução
- Arquitetura de referência SaaS com Docker
- Fundamentos do Engine, imagens e camadas
- Dockerfile avançado: multi-stage, caches e buildx
- Docker Compose v2 detalhado: sintaxe, perfis, segredos e overrides
- Redes, volumes e políticas de recurso
- Rootless Docker \& user namespaces
- Saúde, dependências e initial ordering
- Segurança e supply-chain (scans, SBOM e políticas)
- Deployment: Swarm stacks, CI/CD e zero-downtime
- Observabilidade: logs, métricas e tracing
- Cookbook de cenários prontos
- Checklist final de produção


## Introdução

Docker encapsula uma aplicação e suas dependências em **imagens imutáveis**, garantindo portabilidade e previsibilidade desde o laptop até a nuvem. Compose complementa esse fluxo descrevendo serviços, redes e volumes em YAML — e, na versão 2, migrou para um **plugin Go integrado ao CLI** (_docker compose_) que traz start/stop mais rápidos, novos comandos e suporte a **perfis**[^1][^2].

Para workloads LLM, há requisitos específicos — GPU pass-through, tráfego de streaming, escalonamento horizontal rápido e politicas de memória agressivas. Este material alinha boas práticas Docker a esses desafios, mantendo o foco em operação **multi-tenant** e **developer-friendly**.

## Arquitetura de Referência para SaaS Python + LLMs

| Camada | Responsabilidade | Serviço | Porta | Escala | Observações |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Edge | TLS/offload, roteamento, WAF | Caddy/Nginx | 80/443 | 𝑁× | Contêiner exposto via Compose |
| API | Auth, CRUD REST, Admin | FastAPI | 8000 | auto | Live-reload em volume bind |
| Worker | Inferência LLM | Python gRPC + GPU | 9000 | auto | Healthcheck gRPC |
| Cache | Sessões, embeddings | Redis/Valkey | 6379 | cluster | Volume dedicado |
| Pipeline | Build/CI | buildx + registry | 5000 | 1 | Cache remoto S3 |

> Estratégia baseia-se em **imagens multi-stage mínimas**, Compose com **perfis** para ligar apenas o que cada ambiente necessita e **segredos montados em `/run/secrets`** para dados sensíveis[^3].

## Fundamentos do Docker Engine

### Imagens, layers e copy-on-write

- Cada `RUN`/`COPY` cria uma **camada legível**; no buildx, camadas podem ser exportadas para back-ends (S3, GHA, registry) via `--cache-to`/`--cache-from`[^4].
- **UnionFS** garante _copy-on-write_, permitindo dezenas de instâncias sem duplicar bytes.


### Ciclo de vida

1. **Pull**/build de imagem.
2. **Create** (define cgroup, namespace).
3. **Start** (PID 1).
4. **Healthcheck** (opcional) altera status no metadata[^5].
5. **Stop** ou reinício automático via políticas Compose.

## Dockerfile Profundo: Multi-Stage Builds, Caches e buildx

### Multi-Stage

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12 AS build
WORKDIR /src
COPY pyproject.toml poetry.lock .
RUN pip install poetry && poetry export -f requirements.txt --output /deps.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=build /deps.txt .
RUN pip install -r /deps.txt --no-cache-dir
COPY . .
CMD ["uvicorn","api:app","--host","0.0.0.0","--port","8000"]
```

- Imagem final contém **apenas runtime**; toolchain fica descartada[^6][^7].
- `buildx build --push --platform linux/amd64,linux/arm64` gera multi-arch e compartilha cache com `--cache-to=type=registry,ref=myrepo/cache`[^8][^4].


### Cache mounts

```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip pip install -r /deps.txt[^74]
```

Reaproveita downloads entre builds locais ou CI.

## Docker Compose v2 em Detalhes

### Estrutura global

```yaml
version: "3.8"

services:
  api:
    build: .
    profiles: ["web"]
    env_file: prod.env
    ports: ["8000:8000"]
    secrets: [db_password]
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL","curl -f http://localhost:8000/docs || exit 1"]
      interval: 10s
      retries: 3

  db:
    image: postgres:16
    profiles: ["db","tests"]
    volumes:
      - pgdata:/var/lib/postgresql/data
    secrets: [db_password]
    healthcheck:
      test: ["CMD","pg_isready","-U","postgres"]
      interval: 10s
      retries: 5

secrets:
  db_password:
    file: ./secrets/db_password.txt[^22][^56]

volumes:
  pgdata:
```


#### Novidades v2

- Comando único `docker compose` integrado, sem Python[^9].
- `--profile` ou variável `COMPOSE_PROFILES` ativa subconjuntos (ex.: somente banco para CI)[^10][^11].
- `depends_on` possui condições avançadas `service_started`, `service_healthy`, `service_completed_successfully`[^12][^13].


#### Overrides e extensões

- Arquivo `docker-compose.override.yml` injeta ajustes locais[^14].
- Blocos `x-` permitem **snippets reutilizáveis**[^15].


## Redes, Volumes e Políticas de Recurso

### Redes

| Tipo | Driver | Uso | Observação |
| :-- | :-- | :-- | :-- |
| default | bridge | comunicação interna | DNS `service` resolve contêiner[^16] |
| host | host | baixa latência | sem isolamento |
| macvlan | macvlan | IP exposto na LAN | cuidado com switches |

### Volumes

- **Named** (`pgdata`) persistem dados fora do lifecycle.
- **Bind** para código hot-reload, atentos a performance no Mac/WSL2.


### Memory \& CPU Limits

Compose v3+ (`deploy.resources`) ou v2 (`mem_limit`, `cpus`) definem contornos de uso[^17][^18][^19].

```yaml
deploy:
  resources:
    limits:
      cpus: "0.5"
      memory: 1G
    reservations:
      memory: 256M
```


## Rootless Docker e Namespaces

Executar Docker sem root mitiga vulnerabilidades do daemon[^20].

```bash
# Instalando modo rootless
dockerd-rootless-setuptool.sh install
export PATH=/usr/bin:$PATH
systemctl --user start docker
```

- Requer `newuidmap/newgidmap` e 65,536 sub-uids[^20].
- Para iniciar serviços no boot sem login, habilite `loginctl enable-linger`[^21].
- Discussões de trade-offs na comunidade indicam que só contêiner precisa rodar como user 1,000:1,000 e evitar `privileged`[^22].


## Healthchecks, Ordering e Startup

Healthchecks no Compose mantêm serviço marcado `healthy` e permitem gating de dependentes[^23][^5].

```yaml
depends_on:
  db:
    condition: service_healthy
```

Tabela de opções:


| Campo | Padrão | Significado |
| :-- | :-- | :-- |
| test | none | comando 0-exit = healthy[^5] |
| interval | 30s | frequência[^23] |
| retries | 3 | tentativas |
| start_period | 0s | grace period start |
| timeout | 30s | falha se exceder[^24] |

Casos prontos no GitHub[^25].

## Segredos \& Configs

Compose oferece `secrets` fora de variáveis de ambiente[^26][^27].

- Arquivos montados em `/run/secrets/<name>` com permissão `0400`.
- _Pattern_ `_FILE` oficial (ex.: `MYSQL_ROOT_PASSWORD_FILE`)[^28].
- Não exige Swarm para modo “compose-only”.


## Segurança de Supply-Chain

| Ferramenta | Tipo | Destaque |
| :-- | :-- | :-- |
| Trivy | OSS | SBOM + vulnerabilities[^29] |
| Docker Scout | SaaS | análise contínua no Hub[^30] |
| Inline cache | supply-chain | garante reprodutibilidade[^4] |

Integre ao CI:

```yaml
- name: Scan
  run: trivy image --exit-code 1 myapp:sha-$GITHUB_SHA
```


## Deployment com Swarm Stacks

Embora K8s seja comum, **Swarm** ainda é nativo ao Engine e basta `docker stack deploy`[^31][^32].

```bash
docker swarm init
docker stack deploy -c compose.yml prod
```

- `replicas`, `update_config` e `rollback_config` garantem zero-downtime.
- Stack usa Compose v3 (legacy spec) — converta se necessário.


## Observabilidade

### Logs

- `docker logs -f api` para STDOUT; preferir output JSON estruturado.
- Integre Fluent Bit ou Loki como sidecar.


### Métricas

- `docker system df`, `docker stats` para uso de recursos.
- Cadvisor+Prometheus expõem container-level metrics.


### Tracing

- Monte `/var/run/docker.sock` em agentes e cole labels de imagem via OpenTelemetry.


## Cookbook de Cenários

| Nome | Compose snippet | Notas |
| :-- | :-- | :-- |
| **Blue/Green** | `version: "3"; deploy.update_config.order: start-first` | Minimiza downtime Swarm |
| **Rootless CI** | `docker buildx build --build-context default --builder rootless` | Cache seguro |
| **GPU LLM** | `runtime: nvidia; deploy.resources: reservations.devices` | GPU pass-through |
| **Perfis E2E** | declarados `profiles: ["e2e"]` | CI executa só serviços mock[^11] |
| **Secrets rotation** | `secrets: external: true` + Vault injector | Zero-restart update |

## Checklist Final de Produção

- [ ] Imagem multi-stage <200 MB e sem tools de build[^6].
- [ ] `USER 1000:1000` em Dockerfile; rootless opcional[^20].
- [ ] Healthchecks configurados e `depends_on: service_healthy`[^12].
- [ ] Recursos limitados (`memory`, `cpus`) e swap desativado[^17].
- [ ] Segredos fora de env vars, montados em `/run/secrets`[^3].
- [ ] buildx cache push/pull remoto para CI frio[^4].
- [ ] Vulnerability scan gate no pipeline (Trivy/Scout)[^30][^29].
- [ ] Observabilidade (Prometheus \& structured logs) implantada.
- [ ] Atualizações atômicas via `docker compose up --detach --pull always`.

Com a adoção das práticas apresentadas — de **multi-stage builds enxutos** a **segredos dedicados**, passando por **profiles em Compose v2** e **rootless Engine** — sua plataforma SaaS em Python e LLMs ganhará **builds mais rápidos, imagens menores, segurança reforçada e operações previsíveis**. Docker permanece o pano de fundo ideal para orquestrar serviços poliglotas e orientados a IA, mantendo a complexidade baixa e a portabilidade máxima.

<div style="text-align: center">⁂</div>

[^1]: https://www.howtogeek.com/devops/whats-new-in-docker-compose-v2/

[^2]: https://nickjanetakis.com/blog/docker-tip-94-docker-compose-v2-and-profiles-are-the-best-thing-ever

[^3]: https://docs.docker.com/compose/how-tos/use-secrets/

[^4]: https://docs.docker.com/build/cache/backends/

[^5]: https://github.com/peter-evans/docker-compose-healthcheck

[^6]: https://docs.docker.com/build/building/multi-stage/

[^7]: https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/

[^8]: https://stackoverflow.com/questions/76351391/difference-between-cache-to-from-and-mount-type-cache-in-docker-buildx-build

[^9]: https://www.linode.com/docs/guides/how-to-use-docker-compose-v2/

[^10]: https://docs.docker.com/compose/how-tos/profiles/

[^11]: https://tourmalinecore.com/articles/docker-compose-profiles-templates

[^12]: https://www.warp.dev/terminus/docker-compose-depends-on

[^13]: https://github.com/docker/compose/issues/8154

[^14]: https://docs.nautobot.com/projects/core/en/v1.4.8/development/docker-compose-advanced-use-cases/

[^15]: https://stackoverflow.com/questions/65018992/docker-compose-not-accepting-extensions-starting-with-x-invalid-top-level-p

[^16]: https://tech-couch.com/post/advanced-docker-compose-features

[^17]: https://www.baeldung.com/ops/docker-memory-limit

[^18]: https://stackoverflow.com/questions/42345235/how-to-specify-memory-cpu-limit-in-docker-compose-version-3

[^19]: https://www.geeksforgeeks.org/devops/configure-docker-compose-memory-limits/

[^20]: https://docs.docker.com/engine/security/rootless/

[^21]: https://github.com/docker/compose/issues/7244

[^22]: https://www.reddit.com/r/docker/comments/1cntywv/root_or_rootless/

[^23]: https://www.warp.dev/terminus/docker-compose-health-check

[^24]: https://docs.rapidminer.com/10.3/hub/install/docker-compose/healthchecks.html

[^25]: https://github.com/rodrigobdz/docker-compose-healthchecks

[^26]: https://dev.to/spacelift/how-to-keep-docker-secrets-secure-gmh

[^27]: https://stackoverflow.com/questions/42139605/how-do-you-manage-secret-values-with-docker-compose-v3-1

[^28]: https://phase.dev/blog/docker-compose-secrets

[^29]: https://www.pomerium.com/blog/docker-image-scanning-tools

[^30]: https://docs.docker.com/docker-hub/repos/manage/vulnerability-scanning/

[^31]: https://docs.docker.com/engine/swarm/

[^32]: https://docs.docker.com/engine/swarm/stack-deploy/

[^33]: https://www.onlinescientificresearch.com/articles/integration-of-sonarqube-the-quality-inspector-for-go--docker-compose.pdf

[^34]: http://link.springer.com/10.1007/978-1-4842-3784-7_7

[^35]: https://ieeexplore.ieee.org/document/10207272/

[^36]: https://jurnal.polgan.ac.id/index.php/sinkron/article/view/14091

[^37]: http://biorxiv.org/lookup/doi/10.1101/2024.03.04.583307

[^38]: http://link.springer.com/10.1007/s11760-019-01490-9

[^39]: https://dl.acm.org/doi/10.1145/3696378

[^40]: https://link.springer.com/10.1007/s13755-024-00327-1

[^41]: https://www.semanticscholar.org/paper/7855d030945cd78b417e77cfcaa86c68f85761c8

[^42]: https://arxiv.org/abs/2205.08138

[^43]: https://linkinghub.elsevier.com/retrieve/pii/S0010465518302042

[^44]: https://joss.theoj.org/papers/10.21105/joss.01578.pdf

[^45]: https://arxiv.org/pdf/2207.09167.pdf

[^46]: https://arxiv.org/pdf/1711.01758.pdf

[^47]: https://www.linkedin.com/pulse/simplify-your-docker-setup-extensions-composeyml-hamza-waheed-tma2f

[^48]: https://docs.nautobot.com/projects/core/en/stable/development/core/docker-compose-advanced-use-cases/

[^49]: https://www.reddit.com/r/selfhosted/comments/173v4kj/how_to_secure_secrets_in_dockercompose_setup/

[^50]: https://link.springer.com/10.1007/s10270-022-01027-8

[^51]: https://ieeexplore.ieee.org/document/8814532/

[^52]: http://ieeexplore.ieee.org/document/7217926/

[^53]: https://academic.oup.com/bioinformatics/article/doi/10.1093/bioinformatics/btaf144/8101491

[^54]: https://ieeexplore.ieee.org/document/9155639/

[^55]: https://ieeexplore.ieee.org/document/9557386/

[^56]: https://www.semanticscholar.org/paper/c47c143956799248f313359218325af35b92e61f

[^57]: https://dl.acm.org/doi/10.1145/2594368.2601470

[^58]: https://dl.acm.org/doi/10.1145/3357223.3365759

[^59]: https://www.semanticscholar.org/paper/c93af1ce7b7898bb7728a3e9f0b51b2085d7fc58

[^60]: https://arxiv.org/pdf/2303.06729.pdf

[^61]: http://arxiv.org/pdf/2405.09398.pdf

[^62]: http://arxiv.org/pdf/2411.16639.pdf

[^63]: https://arxiv.org/pdf/2301.12377.pdf

[^64]: https://www.bitdoze.com/docker-compose-secrets/

[^65]: https://stackoverflow.com/questions/65115627/safe-ways-to-specify-postgres-parameters-for-healthchecks-in-docker-compose

[^66]: https://github.com/docker/compose/issues/11582

[^67]: https://www.youtube.com/watch?v=pgf0Tc1ugEY

[^68]: https://journals.pan.pl/dlibra/publication/137168/edition/119984/content

[^69]: https://ieeexplore.ieee.org/document/10077796/

[^70]: https://ieeexplore.ieee.org/document/10655149/

[^71]: https://ieeexplore.ieee.org/document/10517410/

[^72]: https://ieeexplore.ieee.org/document/8939461/

[^73]: https://www.mdpi.com/2079-8954/12/10/414

[^74]: https://link.springer.com/10.1007/s11694-022-01719-1

[^75]: https://linkinghub.elsevier.com/retrieve/pii/S1226798824040170

[^76]: https://ieeexplore.ieee.org/document/10099458/

[^77]: https://ieeexplore.ieee.org/document/10075516/

[^78]: https://arxiv.org/pdf/2210.01073.pdf

[^79]: https://joss.theoj.org/papers/10.21105/joss.01603.pdf

[^80]: https://arxiv.org/pdf/2309.00166.pdf

[^81]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11866752/

[^82]: https://sysdig.com/learn-cloud-native/how-to-implement-docker-image-scanning-with-open-source-tools/

[^83]: https://mvysny.github.io/docker-build-cache/

[^84]: https://collabnix.com/getting-started-with-docker-multi-stage-builds/

[^85]: https://arxiv.org/html/2412.06089v2

[^86]: https://www.qeios.com/read/00QWFP/pdf

[^87]: http://arxiv.org/pdf/2502.11708.pdf

[^88]: https://zenodo.org/record/3267028/files/docker_integrity.pdf

[^89]: https://arxiv.org/pdf/1707.03341.pdf

[^90]: https://pmc.ncbi.nlm.nih.gov/articles/PMC6042832/

[^91]: https://docs.docker.com/reference/compose-file/extension/

[^92]: https://www.docker.com/blog/announcing-compose-v2-general-availability/

[^93]: https://dev.to/rajeshgheware/docker-compose-advanced-techniques-a-comprehensive-guide-to-production-deployments-1goi

[^94]: https://reintech.io/blog/customize-docker-compose-extension-fields-overrides

[^95]: http://arxiv.org/pdf/2212.07376.pdf

[^96]: https://arxiv.org/pdf/2208.12106.pdf

[^97]: https://arxiv.org/pdf/2307.03958.pdf

[^98]: https://arxiv.org/pdf/2208.11280.pdf

[^99]: https://docs.docker.com/reference/cli/docker/compose/

[^100]: https://docs.rapidminer.com/2024.1/hub/install/docker-compose/healthchecks.html

[^101]: https://docs.docker.com/compose/how-tos/startup-order/

[^102]: https://docs.docker.com/engine/containers/resource_constraints/

[^103]: https://zenodo.org/record/3387092/files/main.pdf

[^104]: https://arxiv.org/pdf/1509.08231.pdf

[^105]: https://arxiv.org/pdf/2311.06823.pdf

[^106]: https://f1000research.com/articles/6-52/v1/pdf

[^107]: https://docs.docker.com/guides/swarm-deploy/

[^108]: https://www.youtube.com/watch?v=vIfS9bZVBaw

[^109]: https://forums.docker.com/t/ubuntu-20-04-installation-of-docker-compose-w-docker-rootless/122043

[^110]: https://docs.gitlab.com/tutorials/container_scanning/

[^111]: https://dev.to/depot/how-to-use-cache-mounts-to-speed-up-docker-builds-59e5

[^112]: https://stackoverflow.com/questions/39875575/use-docker-compose-with-docker-swarm

