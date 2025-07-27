# Seção 18: Tratamento de Erros

A aplicação terá uma estratégia de tratamento de erros em camadas, com *exception handlers* no FastAPI, exceções customizadas nos serviços e políticas de retentativa (`retry`) nos workers Celery.
