# IAM Dashboard - Especificações Técnicas NiceGUI

## 🏗️ Arquitetura de Componentes NiceGUI

### Estrutura de Diretórios
```
app/ui_components/
├── __init__.py
├── base/
│   ├── __init__.py
│   ├── theme.py              # Tema e estilos globais
│   ├── layout.py             # Layout base wrapper
│   └── components.py         # Componentes reutilizáveis
├── agents/
│   ├── __init__.py
│   ├── agent_card.py         # Card de agente
│   ├── pdf_processor.py      # UI do processador PDF
│   └── questionnaire_writer.py # UI do redator
├── shared/
│   ├── __init__.py
│   ├── file_upload.py        # Upload reutilizável
│   ├── progress_indicator.py # Loading states
│   ├── results_display.py    # Display de resultados
│   └── navigation.py         # Menu e navegação
└── pages/
    ├── __init__.py
    ├── dashboard.py          # Página principal
    ├── login.py              # Tela de login
    └── documents.py          # Gestão de documentos
```

## 🎨 Theme & Design System

### `app/ui_components/base/theme.py`
```python
from nicegui import ui
from dataclasses import dataclass
from typing import Dict

@dataclass
class IAMTheme:
    """Design tokens do sistema."""
    
    # Cores principais
    colors: Dict[str, str] = None
    
    # Tipografia
    fonts: Dict[str, str] = None
    
    # Espaçamentos
    spacing: Dict[str, str] = None
    
    # Breakpoints
    breakpoints: Dict[str, int] = None
    
    def __post_init__(self):
        self.colors = {
            'primary': '#2563EB',      # Blue 600
            'primary-dark': '#1E40AF', # Blue 700
            'secondary': '#64748B',    # Slate 500
            'success': '#10B981',      # Emerald 500
            'warning': '#F59E0B',      # Amber 500
            'error': '#EF4444',        # Red 500
            'surface': '#F8FAFC',      # Slate 50
            'text': '#1E293B',         # Slate 800
            'text-secondary': '#64748B', # Slate 500
            'border': '#E2E8F0',       # Slate 200
        }
        
        self.fonts = {
            'heading-1': 'text-2xl font-semibold text-slate-800',
            'heading-2': 'text-xl font-medium text-slate-700',
            'body': 'text-base text-slate-600',
            'caption': 'text-sm text-slate-500',
            'button': 'text-base font-medium',
        }
        
        self.spacing = {
            'xs': 'p-2',   # 8px
            'sm': 'p-3',   # 12px
            'md': 'p-4',   # 16px
            'lg': 'p-6',   # 24px
            'xl': 'p-8',   # 32px
        }
        
        self.breakpoints = {
            'mobile': 768,
            'tablet': 1024,
            'desktop': 1200,
        }

# Instância global do tema
theme = IAMTheme()

def apply_theme():
    """Aplica tema global na aplicação."""
    ui.colors(
        primary=theme.colors['primary'],
        secondary=theme.colors['secondary'],
        accent=theme.colors['success'],
        warning=theme.colors['warning'],
        negative=theme.colors['error'],
    )
    
    # CSS Global
    ui.add_head_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC;
        }
        
        /* Smooth transitions */
        * {
            transition: all 0.2s ease;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-thumb {
            background-color: #CBD5E1;
            border-radius: 4px;
        }
        
        /* Focus styles */
        *:focus {
            outline: 2px solid #2563EB;
            outline-offset: 2px;
        }
        
        /* Card hover effect */
        .hover-lift:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        
        /* Loading pulse */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .pulse-animation {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
    </style>
    ''')
```

## 🧱 Componentes Base Reutilizáveis

### `app/ui_components/base/components.py`
```python
from nicegui import ui
from typing import Optional, Callable, List
from .theme import theme

class IAMCard:
    """Card component reutilizável."""
    
    def __init__(
        self,
        title: str = "",
        icon: str = "",
        description: str = "",
        on_click: Optional[Callable] = None,
        disabled: bool = False,
        coming_soon: bool = False
    ):
        self.title = title
        self.icon = icon
        self.description = description
        self.on_click = on_click
        self.disabled = disabled or coming_soon
        self.coming_soon = coming_soon
        
    def render(self) -> ui.card:
        """Renderiza o card."""
        card_classes = (
            'w-64 h-56 p-6 cursor-pointer hover-lift '
            'flex flex-col items-center justify-between '
            'transition-all duration-200 '
        )
        
        if self.disabled:
            card_classes += 'opacity-50 cursor-not-allowed '
        
        with ui.card().classes(card_classes) as card:
            if self.on_click and not self.disabled:
                card.on('click', self.on_click)
            
            # Ícone
            ui.label(self.icon).classes('text-5xl mb-2')
            
            # Título
            ui.label(self.title).classes(
                'text-lg font-semibold text-center text-slate-800'
            )
            
            # Descrição
            if self.description:
                ui.label(self.description).classes(
                    'text-sm text-center text-slate-600 mt-2'
                )
            
            # Coming soon badge
            if self.coming_soon:
                ui.label('EM BREVE').classes(
                    'text-xs bg-amber-100 text-amber-800 '
                    'px-2 py-1 rounded-full mt-2'
                )
            
            # Botão (se não for coming soon)
            if not self.coming_soon:
                ui.button(
                    'USAR AGENTE',
                    on_click=self.on_click if not self.disabled else None
                ).props('flat').classes(
                    'w-full mt-4 bg-blue-600 text-white '
                    'hover:bg-blue-700' if not self.disabled else 'bg-gray-400'
                )
                
        return card

class IAMFileUpload:
    """Componente de upload de arquivos."""
    
    def __init__(
        self,
        on_upload: Callable,
        accept: str = '.pdf,.docx,.jpg,.jpeg,.png',
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        multiple: bool = False
    ):
        self.on_upload = on_upload
        self.accept = accept
        self.max_file_size = max_file_size
        self.multiple = multiple
        self.upload_ref = None
        
    def render(self) -> ui.column:
        """Renderiza área de upload."""
        with ui.column().classes('w-full') as container:
            # Área de drag & drop
            with ui.card().classes(
                'w-full h-48 border-2 border-dashed border-slate-300 '
                'hover:border-blue-500 hover:bg-blue-50 '
                'flex items-center justify-center cursor-pointer '
                'transition-all duration-200'
            ) as drop_zone:
                
                with ui.column().classes('items-center'):
                    ui.icon('cloud_upload', size='3em').classes('text-slate-400 mb-2')
                    ui.label('Arraste arquivos aqui').classes('text-lg text-slate-700')
                    ui.label('ou').classes('text-sm text-slate-500 my-1')
                    
                    # Upload invisível
                    self.upload_ref = ui.upload(
                        on_upload=self._handle_upload,
                        multiple=self.multiple,
                        max_file_size=self.max_file_size
                    ).props(f'accept="{self.accept}"').classes('hidden')
                    
                    ui.button(
                        'ESCOLHER ARQUIVO',
                        on_click=lambda: self.upload_ref.run_method('pickFiles')
                    ).props('flat').classes('bg-blue-600 text-white hover:bg-blue-700')
                    
                    ui.label('PDF, DOCX ou JPG • Máximo: 10MB').classes(
                        'text-xs text-slate-500 mt-2'
                    )
                
                # Drag & drop handlers
                drop_zone.on('dragover', lambda e: e.args['preventDefault']())
                drop_zone.on('drop', self._handle_drop)
                
        return container
    
    async def _handle_upload(self, e):
        """Processa upload de arquivo."""
        files = e.files if hasattr(e, 'files') else [e]
        
        for file in files:
            # Validação de tamanho
            if file.size > self.max_file_size:
                ui.notify(
                    f'Arquivo muito grande. Máximo: {self.max_file_size / 1024 / 1024:.0f}MB',
                    type='negative'
                )
                continue
            
            # Callback
            await self.on_upload(file)
    
    async def _handle_drop(self, e):
        """Processa drag & drop."""
        # Implementação do drag & drop
        e.args['preventDefault']()
        files = e.args.get('dataTransfer', {}).get('files', [])
        for file in files:
            await self._handle_upload(file)

class IAMProgressIndicator:
    """Indicador de progresso com estados."""
    
    def __init__(self, title: str = "Processando..."):
        self.title = title
        self.progress_value = 0
        self.status_text = ""
        self.container = None
        
    def render(self) -> ui.card:
        """Renderiza indicador de progresso."""
        with ui.card().classes('w-full p-8') as self.container:
            with ui.column().classes('items-center space-y-4'):
                # Ícone animado
                ui.icon('smart_toy', size='3em').classes(
                    'text-blue-600 pulse-animation'
                )
                
                # Título
                ui.label(self.title).classes('text-xl font-semibold text-slate-800')
                
                # Barra de progresso
                self.progress_bar = ui.linear_progress(
                    value=self.progress_value
                ).classes('w-full')
                
                # Porcentagem
                self.progress_label = ui.label('0%').classes(
                    'text-2xl font-bold text-blue-600'
                )
                
                # Status
                self.status_label = ui.label(self.status_text).classes(
                    'text-sm text-slate-600'
                )
                
                # Tempo estimado
                self.time_label = ui.label('').classes(
                    'text-sm text-slate-500'
                )
                
        return self.container
    
    def update(self, value: float, status: str = "", time_remaining: str = ""):
        """Atualiza progresso."""
        self.progress_value = value
        self.progress_bar.set_value(value)
        self.progress_label.set_text(f'{int(value * 100)}%')
        
        if status:
            self.status_label.set_text(status)
        
        if time_remaining:
            self.time_label.set_text(f'⏱️ Tempo estimado: {time_remaining}')

class IAMButton:
    """Botão customizado com estados."""
    
    def __init__(
        self,
        text: str,
        on_click: Optional[Callable] = None,
        variant: str = 'primary',  # primary, secondary, text
        icon: Optional[str] = None,
        loading: bool = False,
        disabled: bool = False,
        full_width: bool = False
    ):
        self.text = text
        self.on_click = on_click
        self.variant = variant
        self.icon = icon
        self.loading = loading
        self.disabled = disabled
        self.full_width = full_width
        
    def render(self) -> ui.button:
        """Renderiza botão."""
        # Classes baseadas na variante
        variant_classes = {
            'primary': 'bg-blue-600 text-white hover:bg-blue-700',
            'secondary': 'bg-white text-blue-600 border-2 border-blue-600 hover:bg-blue-50',
            'text': 'bg-transparent text-blue-600 hover:bg-blue-50',
        }
        
        classes = (
            f'{variant_classes.get(self.variant, variant_classes["primary"])} '
            f'font-medium px-4 py-2 rounded transition-all duration-200 '
            f'{"w-full" if self.full_width else ""} '
            f'{"opacity-50 cursor-not-allowed" if self.disabled or self.loading else ""}'
        )
        
        # Texto do botão
        button_text = self.text
        if self.loading:
            button_text = f'⏳ {self.text}...'
        
        button = ui.button(
            button_text,
            on_click=self.on_click if not (self.disabled or self.loading) else None
        ).props('flat' if self.variant != 'secondary' else '').classes(classes)
        
        # Adicionar ícone se especificado
        if self.icon and not self.loading:
            with button:
                ui.icon(self.icon).classes('mr-2')
        
        return button
```

## 📄 Implementação da Página Dashboard

### `app/ui_components/pages/dashboard.py`
```python
from nicegui import ui, app
from typing import Optional
from ..base.components import IAMCard
from ..base.theme import theme
from ..shared.navigation import SideMenu
from ...models.user import User

class DashboardPage:
    """Página principal do dashboard."""
    
    def __init__(self, user: User):
        self.user = user
        self.agents = self._get_available_agents()
        
    def _get_available_agents(self):
        """Retorna agentes disponíveis."""
        return [
            {
                'id': 'pdf_processor',
                'title': 'PROCESSADOR DE PDFs',
                'icon': '📄',
                'description': 'Analise documentos automaticamente',
                'available': True,
                'route': '/agent/pdf-processor'
            },
            {
                'id': 'questionnaire_writer',
                'title': 'REDATOR DE QUESITOS',
                'icon': '✍️',
                'description': 'Crie peças com inteligência',
                'available': True,
                'route': '/agent/questionnaire-writer'
            },
            {
                'id': 'doc_validator',
                'title': 'VALIDADOR DOCS',
                'icon': '✅',
                'description': 'Em desenvolvimento',
                'available': False,
                'coming_soon': 'Fevereiro'
            },
            {
                'id': 'deadline_manager',
                'title': 'GESTOR PRAZOS',
                'icon': '📅',
                'description': 'Em desenvolvimento',
                'available': False,
                'coming_soon': 'Março'
            }
        ]
    
    async def render(self):
        """Renderiza a página do dashboard."""
        # Container principal
        with ui.column().classes('w-full min-h-screen bg-slate-50'):
            # Header
            await self._render_header()
            
            # Conteúdo principal
            with ui.row().classes('flex-1 w-full max-w-7xl mx-auto p-6'):
                # Área de agentes
                with ui.column().classes('flex-1'):
                    await self._render_welcome_section()
                    await self._render_agents_grid()
                    await self._render_activity_feed()
                
                # Menu lateral
                SideMenu(self.user).render()
    
    async def _render_header(self):
        """Renderiza header."""
        with ui.header().classes(
            'bg-white shadow-sm border-b border-slate-200'
        ):
            with ui.row().classes(
                'w-full max-w-7xl mx-auto px-6 py-4 items-center justify-between'
            ):
                # Logo e título
                with ui.row().classes('items-center gap-3'):
                    ui.label('🏢').classes('text-2xl')
                    with ui.column().classes('gap-0'):
                        ui.label('IAM Dashboard').classes(
                            'text-xl font-semibold text-slate-800'
                        )
                        ui.label('Advocacia Digital').classes(
                            'text-sm text-slate-500'
                        )
                
                # Info do usuário
                with ui.row().classes('items-center gap-4'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('account_circle').classes('text-slate-600')
                        ui.label(self.user.name).classes('text-slate-700')
                    
                    ui.button(
                        '🚪 Sair',
                        on_click=lambda: ui.open('/logout')
                    ).props('flat').classes('text-slate-600 hover:text-slate-800')
    
    async def _render_welcome_section(self):
        """Renderiza seção de boas-vindas."""
        with ui.card().classes('w-full mb-6 bg-blue-50 border-blue-200'):
            with ui.column().classes('items-center py-4'):
                ui.label('🎯 SEUS ASSISTENTES INTELIGENTES').classes(
                    'text-2xl font-bold text-blue-900 mb-2'
                )
                ui.label('Clique em um agente para começar').classes(
                    'text-blue-700'
                )
    
    async def _render_agents_grid(self):
        """Renderiza grid de agentes."""
        with ui.row().classes(
            'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8'
        ):
            for agent in self.agents:
                card = IAMCard(
                    title=agent['title'],
                    icon=agent['icon'],
                    description=agent['description'],
                    on_click=lambda a=agent: self._handle_agent_click(a),
                    disabled=not agent['available'],
                    coming_soon=agent.get('coming_soon') is not None
                )
                card.render()
    
    async def _render_activity_feed(self):
        """Renderiza feed de atividades."""
        with ui.card().classes('w-full'):
            with ui.row().classes('justify-between items-center mb-4'):
                ui.label('📊 Atividade Recente').classes(
                    'text-lg font-semibold text-slate-800'
                )
                ui.button(
                    'Ver Tudo →',
                    on_click=lambda: ui.open('/activities')
                ).props('flat').classes('text-blue-600 hover:text-blue-700')
            
            # Lista de atividades
            activities = await self._get_recent_activities()
            
            with ui.column().classes('space-y-2'):
                for activity in activities[:5]:
                    with ui.row().classes(
                        'p-3 hover:bg-slate-50 rounded transition-colors'
                    ):
                        ui.label('•').classes('text-blue-600 mr-2')
                        ui.label(activity['description']).classes(
                            'flex-1 text-slate-700'
                        )
                        ui.label(activity['time']).classes(
                            'text-sm text-slate-500'
                        )
    
    async def _get_recent_activities(self):
        """Busca atividades recentes."""
        # Mock data - substituir por query real
        return [
            {
                'description': 'Laudo médico analisado - Cliente João Silva',
                'time': 'há 2 horas'
            },
            {
                'description': 'Quesitos trabalhistas gerados - Processo 123456',
                'time': 'há 3 horas'
            },
            {
                'description': '5 documentos processados - Cliente Maria Costa',
                'time': 'hoje, 09:30'
            }
        ]
    
    def _handle_agent_click(self, agent):
        """Handle click no agente."""
        if agent['available']:
            ui.open(agent['route'])
```

## 🔌 Integração com Rotas

### `app/main.py` (parcial)
```python
from nicegui import ui, app
from app.ui_components.base.theme import apply_theme
from app.ui_components.pages.dashboard import DashboardPage
from app.ui_components.agents.pdf_processor import PDFProcessorPage
from app.ui_components.agents.questionnaire_writer import QuestionnaireWriterPage

# Aplicar tema global
apply_theme()

# Middleware de autenticação
@app.middleware
async def auth_middleware(request, call_next):
    """Verifica autenticação em rotas protegidas."""
    protected_routes = ['/dashboard', '/agent/']
    
    if any(request.url.path.startswith(route) for route in protected_routes):
        if not app.storage.user.get('authenticated'):
            return ui.redirect('/login')
    
    return await call_next(request)

# Rotas
@ui.page('/')
async def index():
    """Redireciona para dashboard ou login."""
    if app.storage.user.get('authenticated'):
        ui.open('/dashboard')
    else:
        ui.open('/login')

@ui.page('/dashboard')
async def dashboard():
    """Página principal do dashboard."""
    user = app.storage.user.get('current_user')
    if user:
        page = DashboardPage(user)
        await page.render()

@ui.page('/agent/pdf-processor')
async def pdf_processor():
    """Página do processador de PDFs."""
    from app.ui_components.agents.pdf_processor import PDFProcessorPage
    page = PDFProcessorPage()
    await page.render()

@ui.page('/agent/questionnaire-writer')
async def questionnaire_writer():
    """Página do redator de quesitos."""
    from app.ui_components.agents.questionnaire_writer import QuestionnaireWriterPage
    page = QuestionnaireWriterPage()
    await page.render()

# Configurações responsivas
ui.run(
    title='IAM Dashboard',
    favicon='🏢',
    dark=False,
    tailwind=True,
    storage_secret='your-secret-key-here'
)
```

## 📱 Responsividade e Mobile

### Utility Classes para Responsividade
```python
class ResponsiveUtils:
    """Utilidades para design responsivo."""
    
    @staticmethod
    def is_mobile() -> bool:
        """Verifica se é dispositivo mobile."""
        # Implementar detecção via user agent ou viewport
        return False  # Placeholder
    
    @staticmethod
    def responsive_grid(mobile_cols: int = 1, tablet_cols: int = 2, desktop_cols: int = 3) -> str:
        """Retorna classes de grid responsivo."""
        return f'grid grid-cols-{mobile_cols} md:grid-cols-{tablet_cols} lg:grid-cols-{desktop_cols}'
    
    @staticmethod
    def responsive_text(mobile: str = 'base', desktop: str = 'lg') -> str:
        """Retorna classes de texto responsivo."""
        return f'text-{mobile} md:text-{desktop}'
    
    @staticmethod
    def hide_on_mobile() -> str:
        """Esconde elemento em mobile."""
        return 'hidden md:block'
    
    @staticmethod
    def show_on_mobile() -> str:
        """Mostra apenas em mobile."""
        return 'block md:hidden'
```

## 🎯 Padrões de Estado e Dados

### State Management
```python
from dataclasses import dataclass
from typing import Optional, List, Dict
from nicegui import app

@dataclass
class AppState:
    """Estado global da aplicação."""
    current_user: Optional[User] = None
    active_document: Optional[str] = None
    processing_queue: List[str] = None
    ui_preferences: Dict[str, any] = None
    
    def __post_init__(self):
        if self.processing_queue is None:
            self.processing_queue = []
        if self.ui_preferences is None:
            self.ui_preferences = {}

class StateManager:
    """Gerenciador de estado da aplicação."""
    
    @staticmethod
    def get_state() -> AppState:
        """Retorna estado atual."""
        if 'app_state' not in app.storage.user:
            app.storage.user['app_state'] = AppState()
        return app.storage.user['app_state']
    
    @staticmethod
    def update_state(updates: Dict[str, any]):
        """Atualiza estado."""
        state = StateManager.get_state()
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
        app.storage.user['app_state'] = state
    
    @staticmethod
    def clear_state():
        """Limpa estado."""
        app.storage.user['app_state'] = AppState()
```

## 🔧 Componentes Avançados

### Real-time Updates
```python
from nicegui import ui
import asyncio

class RealtimeComponent:
    """Componente com atualizações em tempo real."""
    
    def __init__(self, update_interval: int = 1):
        self.update_interval = update_interval
        self.is_running = False
        self.value_label = None
        
    async def render(self):
        """Renderiza componente."""
        with ui.card().classes('p-4'):
            ui.label('Atualizações em Tempo Real').classes('font-semibold mb-2')
            self.value_label = ui.label('Aguardando...').classes('text-2xl')
            
            with ui.row().classes('gap-2 mt-4'):
                ui.button('Iniciar', on_click=self.start)
                ui.button('Parar', on_click=self.stop)
        
        # Auto-start
        await self.start()
    
    async def start(self):
        """Inicia atualizações."""
        self.is_running = True
        asyncio.create_task(self._update_loop())
    
    def stop(self):
        """Para atualizações."""
        self.is_running = False
    
    async def _update_loop(self):
        """Loop de atualização."""
        while self.is_running:
            # Simular busca de dados
            value = await self._fetch_data()
            if self.value_label:
                self.value_label.set_text(str(value))
            await asyncio.sleep(self.update_interval)
    
    async def _fetch_data(self):
        """Busca dados do backend."""
        # Implementar chamada real à API
        import random
        return random.randint(1, 100)
```

## 🚀 Performance & Otimizações

### Lazy Loading de Componentes
```python
class LazyComponent:
    """Componente com carregamento lazy."""
    
    def __init__(self, loader_func):
        self.loader_func = loader_func
        self.container = None
        self.is_loaded = False
        
    async def render(self):
        """Renderiza placeholder e carrega conteúdo."""
        self.container = ui.column().classes('w-full')
        
        with self.container:
            # Skeleton loader
            with ui.card().classes('w-full h-32 animate-pulse bg-slate-200'):
                pass
        
        # Carregar conteúdo async
        asyncio.create_task(self._load_content())
        
        return self.container
    
    async def _load_content(self):
        """Carrega conteúdo real."""
        await asyncio.sleep(0.1)  # Yield para UI
        
        # Carregar conteúdo
        content = await self.loader_func()
        
        # Substituir skeleton
        self.container.clear()
        with self.container:
            content.render()
        
        self.is_loaded = True
```

## 📦 Componentes de Formulário

### Form Builder
```python
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class FormField:
    """Definição de campo de formulário."""
    name: str
    label: str
    type: str  # text, email, select, textarea, file
    required: bool = False
    placeholder: str = ""
    options: List[str] = None
    validation: Callable = None

class FormBuilder:
    """Construtor de formulários dinâmicos."""
    
    def __init__(self, fields: List[FormField], on_submit: Callable):
        self.fields = fields
        self.on_submit = on_submit
        self.form_data = {}
        
    def render(self):
        """Renderiza formulário."""
        with ui.card().classes('w-full p-6'):
            with ui.column().classes('space-y-4'):
                for field in self.fields:
                    self._render_field(field)
                
                # Botões
                with ui.row().classes('gap-2 mt-6'):
                    ui.button(
                        'Enviar',
                        on_click=self._handle_submit
                    ).props('type="submit"').classes(
                        'bg-blue-600 text-white hover:bg-blue-700'
                    )
                    
                    ui.button(
                        'Limpar',
                        on_click=self._handle_clear
                    ).props('flat').classes('text-slate-600')
    
    def _render_field(self, field: FormField):
        """Renderiza campo individual."""
        with ui.column().classes('w-full'):
            # Label
            label_text = field.label
            if field.required:
                label_text += ' *'
            ui.label(label_text).classes('text-sm font-medium text-slate-700 mb-1')
            
            # Input baseado no tipo
            if field.type == 'text' or field.type == 'email':
                input_field = ui.input(
                    placeholder=field.placeholder,
                    validation={'Type': field.type} if field.type == 'email' else None
                ).props(f'type="{field.type}"').classes('w-full')
                input_field.on('change', lambda e, f=field: self._update_data(f.name, e.value))
                
            elif field.type == 'select':
                select = ui.select(
                    options=field.options or [],
                    label=field.placeholder
                ).classes('w-full')
                select.on('change', lambda e, f=field: self._update_data(f.name, e.value))
                
            elif field.type == 'textarea':
                textarea = ui.textarea(
                    placeholder=field.placeholder
                ).classes('w-full')
                textarea.on('change', lambda e, f=field: self._update_data(f.name, e.value))
                
            elif field.type == 'file':
                IAMFileUpload(
                    on_upload=lambda file, f=field: self._update_data(f.name, file)
                ).render()
    
    def _update_data(self, field_name: str, value: Any):
        """Atualiza dados do formulário."""
        self.form_data[field_name] = value
    
    async def _handle_submit(self):
        """Processa envio do formulário."""
        # Validação
        for field in self.fields:
            if field.required and not self.form_data.get(field.name):
                ui.notify(f'{field.label} é obrigatório', type='negative')
                return
            
            if field.validation and field.name in self.form_data:
                if not field.validation(self.form_data[field.name]):
                    ui.notify(f'{field.label} inválido', type='negative')
                    return
        
        # Callback
        await self.on_submit(self.form_data)
    
    def _handle_clear(self):
        """Limpa formulário."""
        self.form_data = {}
        # Implementar limpeza visual dos campos
```

## 🎨 Animações e Transições

### Animation Utilities
```python
class AnimationUtils:
    """Utilidades para animações."""
    
    @staticmethod
    def fade_in(element, duration: float = 0.3):
        """Animação fade in."""
        element.classes('opacity-0')
        element.classes(f'transition-opacity duration-{int(duration * 1000)}')
        ui.timer(0.1, lambda: element.classes(remove='opacity-0'))
    
    @staticmethod
    def slide_in(element, direction: str = 'left', duration: float = 0.3):
        """Animação slide in."""
        translate_map = {
            'left': '-translate-x-full',
            'right': 'translate-x-full',
            'top': '-translate-y-full',
            'bottom': 'translate-y-full'
        }
        
        element.classes(f'{translate_map[direction]} opacity-0')
        element.classes(f'transition-all duration-{int(duration * 1000)}')
        ui.timer(0.1, lambda: element.classes(
            remove=f'{translate_map[direction]} opacity-0'
        ))
    
    @staticmethod
    def pulse(element, count: int = 3):
        """Animação pulse."""
        element.classes('animate-pulse')
        ui.timer(count * 0.5, lambda: element.classes(remove='animate-pulse'))
```