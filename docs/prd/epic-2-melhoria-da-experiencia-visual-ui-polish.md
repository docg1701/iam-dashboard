# Epic 2: Melhoria da Experiência Visual (UI Polish)

**Prioridade**: 🟡 IMPORTANTE (Após Epic 1)  
**Duração**: 2 sprints (4 semanas)  
**Problema Base**: Interface "feia e quadrada" com qualidade visual 2/10

**Contexto**: Análise UX revelou interface funcional mas visualmente inadequada para uso profissional. Sistema parece "ferramenta gratuita dos anos 2000" prejudicando confiança e adoção.

## Story 2.1: Implementação do Design System Nativo
**Objetivo**: Elevar qualidade visual de 2/10 para 7-8/10 usando apenas recursos nativos

**Implementação**:
- Design tokens via CSS variables Quasar nativos
- Paleta de cores profissional Material Design
- Tipografia hierarchical usando classes nativas
- Spacing system baseado no grid 8px

**Constraints Técnicos**:
- Apenas CSS variables nativas Quasar
- Material Design color palette oficial
- Typography scale padrão do framework
- Spacing classes q-pa-*, q-ma-* nativas

**Design System Spec**:
```css
:root {
  /* Primary Palette */
  --q-primary: #2563EB;
  --q-secondary: #10B981; 
  --q-accent: #F59E0B;
  
  /* Semantic Colors */
  --q-positive: #059669;
  --q-negative: #DC2626;
  --q-info: #0EA5E9;
  --q-warning: #D97706;
  
  /* Surface Colors */
  --q-surface: #FFFFFF;
  --q-background: #F8FAFC;
  --q-card: #FFFFFF;
}
```

**DoD**: Design system profissional implementado usando 100% recursos nativos

## Story 2.2: Micro-interações e Animações Nativas
**Objetivo**: Adicionar polish visual através de transições e feedback nativo

**Implementação**:
- Hover effects usando pseudo-selectors CSS nativos
- Loading states com q-spinner e skeleton components
- Feedback visual via q-notify system nativo
- Transições CSS para mudanças de estado

**Constraints Técnicos**:
- Apenas CSS transitions e transforms nativos
- Q-spinner e q-skeleton components oficiais
- Q-notify system para feedback
- Pseudo-selectors (:hover, :active, :focus) nativos

**Micro-interactions Spec**:
```css
/* Hover Effects */
.q-btn:hover {
  transform: translateY(-2px);
  transition: transform 0.3s ease;
}

/* Loading States */
.q-card--loading {
  opacity: 0.7;
  transition: opacity 0.3s ease;
}
```

**DoD**: Interface polished com feedback visual moderno usando apenas recursos nativos