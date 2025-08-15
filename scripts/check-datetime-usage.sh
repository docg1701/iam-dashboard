#!/bin/bash

# Script de validação para uso de datetime.utcnow() deprecated
# Criado para prevenir regressão do problema identificado por Quinn QA
# Parte das correções arquiteturais - Story 1.3

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🕐 Verificando uso de datetime.utcnow() deprecated..."

# Diretórios para verificar
SEARCH_DIRS="apps/api/src apps/api/tests"

# Buscar por datetime.utcnow()
echo "📁 Procurando em: $SEARCH_DIRS"

# Contador de violações
violations=0

for dir in $SEARCH_DIRS; do
    if [ -d "$dir" ]; then
        echo "🔍 Verificando $dir..."
        
        # Buscar por datetime.utcnow em arquivos Python
        found_files=$(find "$dir" -name "*.py" -type f -exec grep -l "datetime\.utcnow" {} \; 2>/dev/null || true)
        
        if [ -n "$found_files" ]; then
            echo -e "${RED}❌ ERRO: Encontrado uso de datetime.utcnow() deprecated!${NC}"
            echo ""
            
            # Mostrar detalhes das violações
            for file in $found_files; do
                echo -e "${YELLOW}📄 Arquivo: $file${NC}"
                grep -n "datetime\.utcnow" "$file" | while read -r line; do
                    echo -e "   ${RED}→ $line${NC}"
                done
                echo ""
                violations=$((violations + 1))
            done
            
            echo -e "${RED}⚠️  SOLUÇÃO NECESSÁRIA:${NC}"
            echo "   Substitua: datetime.utcnow()"
            echo "   Por: datetime.now(timezone.utc)"
            echo ""
            echo -e "${YELLOW}📖 Consulte CLAUDE.md seção 'CRITICAL DATETIME RULE' para mais detalhes${NC}"
            echo ""
        fi
    fi
done

if [ $violations -eq 0 ]; then
    echo -e "${GREEN}✅ Sucesso! Nenhum uso de datetime.utcnow() encontrado.${NC}"
    echo "🎯 Todos os timestamps estão usando datetime.now(timezone.utc)"
    exit 0
else
    echo -e "${RED}💥 FALHA: $violations arquivo(s) com datetime.utcnow() deprecated${NC}"
    echo ""
    echo "🔧 Para corrigir automaticamente, execute:"
    echo "   find apps/api -name '*.py' -exec sed -i 's/datetime\.utcnow()/datetime.now(timezone.utc)/g' {} +"
    echo "   # ATENÇÃO: Verifique os imports após a correção automática!"
    echo ""
    exit 1
fi