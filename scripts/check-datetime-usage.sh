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

# Descoberta automática de diretórios com código Python
echo "🔍 Descobrindo automaticamente diretórios Python..."
SEARCH_DIRS=$(find . -type f -name "*.py" \
    -not -path "./.venv/*" \
    -not -path "*/.venv/*" \
    -not -path "./.git/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/node_modules/*" \
    -not -path "*/.pytest_cache/*" \
    -not -path "*/.mypy_cache/*" \
    -not -path "*/.ruff_cache/*" \
    -not -path "*/htmlcov/*" \
    -not -path "*/.tox/*" \
    -not -path "*/build/*" \
    -not -path "*/dist/*" \
    -not -path "*/.cache/*" \
    -not -path "*/.turbo/*" \
    -not -path "*/site-packages/*" \
    | xargs -n1 dirname | sort -u | tr '\n' ' ')

# Buscar por datetime.utcnow()
echo "📁 Diretórios descobertos para verificação:"
echo "$SEARCH_DIRS" | tr ' ' '\n' | sed 's/^/   - /' | grep -v '^   - $'
echo ""

# Contador de violações
violations=0

for dir in $SEARCH_DIRS; do
    if [ -d "$dir" ]; then
        echo "🔍 Verificando $dir..."
        
        # Usar análise AST Python para detectar uso real de datetime.utcnow()
        found_files=$(find "$dir" -name "*.py" -type f 2>/dev/null || true)
        
        if [ -n "$found_files" ]; then
            current_violations=0
            
            while read -r file; do
                if [ -f "$file" ]; then
                    # Exclui arquivos de teste específicos sobre datetime (falsos positivos)
                    if [[ "$file" != *"test_no_deprecated_datetime.py" ]]; then
                        # Usar Python para análise AST precisa
                        violations_output=$(python3 -c "
import ast
import sys

class DatetimeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []
    
    def visit_Attribute(self, node):
        # Detectar datetime.utcnow()
        if (isinstance(node.value, ast.Name) and 
            node.value.id == 'datetime' and 
            node.attr == 'utcnow'):
            self.violations.append(node.lineno)
        # Detectar module.datetime.utcnow()
        elif (isinstance(node.value, ast.Attribute) and 
              isinstance(node.value.value, ast.Name) and
              node.value.attr == 'datetime' and 
              node.attr == 'utcnow'):
            self.violations.append(node.lineno)
        self.generic_visit(node)

try:
    with open('$file', 'r', encoding='utf-8') as f:
        content = f.read()
    tree = ast.parse(content)
    visitor = DatetimeVisitor()
    visitor.visit(tree)
    
    if visitor.violations:
        lines = content.split('\n')
        for line_num in visitor.violations:
            if line_num <= len(lines):
                print(f'{line_num}:{lines[line_num-1].strip()}')
except:
    pass
" 2>/dev/null)
                        
                        if [ -n "$violations_output" ]; then
                            echo -e "${RED}❌ ERRO: Encontrado uso de datetime.utcnow() deprecated!${NC}"
                            echo -e "${YELLOW}📄 Arquivo: $file${NC}"
                            echo "$violations_output" | while IFS=':' read -r line_num code_line; do
                                echo -e "   ${RED}→ Linha $line_num: $code_line${NC}"
                            done
                            echo ""
                            current_violations=$((current_violations + 1))
                        fi
                    fi
                fi
            done <<< "$found_files"
            
            violations=$((violations + current_violations))
            
            if [ $current_violations -gt 0 ]; then
                echo -e "${RED}⚠️  SOLUÇÃO NECESSÁRIA:${NC}"
                echo "   Substitua: datetime.utcnow()"
                echo "   Por: datetime.now(timezone.utc)"
                echo ""
                echo -e "${YELLOW}📖 Consulte CLAUDE.md seção 'CRITICAL DATETIME RULE' para mais detalhes${NC}"
                echo ""
            fi
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