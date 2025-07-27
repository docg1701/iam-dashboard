# Caddy para Sistema de Advocacia SaaS

Este guia foca na implementação do Caddy como reverse proxy para o sistema de agentes autônomos de advocacia, cobrindo HTTPS automático e a integração com o ambiente Docker (NiceGUI/FastAPI, Celery).

## 1. Caddyfile para o Projeto

O `Caddyfile` abaixo é a configuração central para o Caddy, gerenciando todo o tráfego de entrada para a aplicação. Ele é projetado para ser simples, seguro e eficiente.

```caddyfile
# Bloco de configuração global
{
    # Habilita a API de administração do Caddy na porta 2019 (acessível apenas localmente)
    admin off

    # Configura o email para a emissão de certificados SSL/TLS via Let's Encrypt
    email seu-email@provedor.com.br
}

# Domínio principal da aplicação
# O Caddy irá obter e renovar automaticamente os certificados SSL/TLS para este domínio.
app.seuescritorio.com.br {
    # Redireciona todo o tráfego para o serviço da aplicação NiceGUI/FastAPI,
    # que está rodando no contêiner 'app' na porta 8000.
    reverse_proxy app:8000

    # Configura o log de acesso para este domínio.
    log {
        output file /var/log/caddy/app_access.log {
            # Rotaciona o arquivo de log quando ele atinge 10MB
            roll_size 10mb
            # Mantém até 5 arquivos de log antigos
            roll_keep 5
        }
        # Formata o log como JSON para fácil processamento por outras ferramentas.
        format json
    }

    # Adiciona headers de segurança para proteger a aplicação contra ataques comuns.
    header {
        # Força o uso de HTTPS por um longo período.
        Strict-Transport-Security "max-age=31536000;"
        # Previne que o navegador "adivinhe" o tipo de conteúdo.
        X-Content-Type-Options nosniff
        # Impede que a página seja carregada em um iframe.
        X-Frame-Options DENY
        # Ativa a proteção contra XSS do navegador.
        X-XSS-Protection "1; mode=block"
    }

    # Habilita a compressão (gzip e zstd) para acelerar o carregamento da página.
    encode gzip zstd
}

# Domínio para o Flower, a ferramenta de monitoramento do Celery
flower.seuescritorio.com.br {
    # Redireciona o tráfego para o serviço do Flower, que está no contêiner 'flower' na porta 5555.
    reverse_proxy flower:5555

    # Configura um log separado para o Flower.
    log {
        output file /var/log/caddy/flower_access.log
    }
}
```

## 2. Integração com Docker Compose

O Caddy é executado como um serviço dentro do `docker-compose.yml`, atuando como o ponto de entrada para todos os outros serviços da aplicação. A configuração abaixo está alinhada com o `docker-compose.yml` principal do projeto.

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Serviço do Caddy
  caddy:
    image: caddy:2.10-alpine
    container_name: advocacia_caddy
    restart: unless-stopped
    ports:
      - "80:80"      # Porta para tráfego HTTP e desafios ACME
      - "443:443"    # Porta para tráfego HTTPS
    volumes:
      # Monta o Caddyfile do host para dentro do contêiner
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      # Volume para armazenar dados do Caddy (certificados SSL)
      - caddy_data:/data
      # Volume para logs
      - ./logs/caddy:/var/log/caddy
    depends_on:
      - app
      - flower
    networks:
      - advocacia-network

  # Serviço da aplicação principal (NiceGUI/FastAPI)
  app:
    build: .
    container_name: advocacia_app
    # A porta 8000 do app não é exposta publicamente, apenas para a rede interna do Docker.
    # O Caddy é o único ponto de acesso externo.
    expose:
      - "8000"
    networks:
      - advocacia-network
    # ... resto da configuração do app

  # Serviço do Flower (monitoramento Celery)
  flower:
    build: .
    container_name: advocacia_flower
    command: celery -A app.workers.celery_app flower --port=5555
    expose:
      - "5555"
    networks:
      - advocacia-network
    # ... resto da configuração do flower

# ... outros serviços (worker, db, redis)

volumes:
  caddy_data:

networks:
  advocacia-network:
    driver: bridge
```

## 3. Comandos Essenciais

- **Validar a configuração do Caddyfile:**
  ```bash
  docker compose run --rm caddy caddy validate --config /etc/caddy/Caddyfile
  ```

- **Recarregar a configuração do Caddy sem downtime:**
  ```bash
  docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
  ```

- **Verificar os logs em tempo real:**
  ```bash
  docker compose logs -f caddy
  ```

Este guia simplificado e focado garante que o Caddy seja configurado de maneira otimizada e segura para o ambiente de produção do sistema de advocacia, seguindo as melhores práticas de proxy reverso e gerenciamento de SSL/TLS.