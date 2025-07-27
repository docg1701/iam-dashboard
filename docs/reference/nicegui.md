# **NiceGUI: Referência para Sistema de Agentes Autônomos para Advocacia**

## **Framework Web Python para Interface de Usuário do Sistema SaaS de Advocacia**

---

### **Sobre Este Guia**

Este guia serve como referência específica do NiceGUI para o desenvolvimento do sistema SaaS de agentes autônomos para escritórios de advocacia. Foca nos padrões, componentes e implementações específicas necessárias para criar interfaces de usuário intuitivas para processamento de documentos legais, autenticação de usuários e gerenciamento de workflows de agentes IA.

### **Contexto do Projeto**

O NiceGUI é utilizado como framework principal para criar a interface web do nosso sistema de advocacia, integrando:
- Sistema de autenticação com 2FA
- Dashboard para gerenciamento de clientes e documentos  
- Interface para upload e processamento de PDFs
- Painéis de controle para agentes de IA
- Visualização de resultados de análise de documentos

---

## **Parte I: Fundamentos do NiceGUI**

Esta primeira parte estabelece a base conceitual necessária para entender não apenas *o que* o NiceGUI faz, mas *como* e *por que* ele o faz de uma maneira específica. Abordaremos a filosofia do projeto, sua arquitetura subjacente e os conceitos essenciais que governam todas as interações dentro do framework.

### **Capítulo 1: Introdução ao NiceGUI**

Este capítulo oferece uma visão geral do NiceGUI, seu lugar no ecossistema de frameworks de UI em Python e os princípios que guiam seu design.

#### **Visão Geral e Filosofia**

NiceGUI é uma biblioteca de código aberto em Python projetada para a criação de interfaces gráficas de usuário (GUIs) que são executadas em um navegador da web. Sua filosofia central é a de ser "backend-first" (priorizar o backend). Isso significa que a biblioteca abstrai e gerencia os detalhes complexos do desenvolvimento web — HTML, CSS e JavaScript — permitindo que o desenvolvedor se concentre exclusivamente em escrever código Python para definir tanto a lógica da aplicação quanto a sua interface de usuário.

Este enfoque oferece uma curva de aprendizado notavelmente suave para desenvolvedores Python, que podem criar aplicações web interativas sem a necessidade de conhecimento prévio em desenvolvimento front-end. Ao mesmo tempo, o NiceGUI não sacrifica a flexibilidade, oferecendo múltiplas vias para personalização avançada, que serão exploradas em capítulos posteriores.

A versatilidade do NiceGUI o torna ideal para uma ampla gama de projetos, incluindo, mas não se limitando a:

* **Micro-aplicações web e scripts:** Para tarefas rápidas que precisam de uma interface gráfica.  
* **Dashboards:** Para visualização de dados e monitoramento em tempo real.  
* **Projetos de robótica e IoT:** Como interface de controle e monitoramento para hardware. Exemplos práticos incluem a integração com ROS2 (Robot Operating System 2).  
* **Automação residencial inteligente:** Para criar painéis de controle personalizados.  
* **Interfaces para Machine Learning:** Para ajustar parâmetros, configurar algoritmos ou visualizar resultados de modelos. O exemplo de "AI Interface" demonstra essa capacidade.

#### **Arquitetura Subjacente**

Para entregar sua experiência de desenvolvimento simplificada, o NiceGUI se apoia em um conjunto de tecnologias robustas e de alto desempenho. Compreender essa pilha tecnológica é fundamental para desbloquear o potencial máximo da biblioteca, especialmente para customizações avançadas.

* **Servidor Web (Backend):** O núcleo do NiceGUI é construído sobre o **FastAPI**, um moderno e rápido framework web para Python. O FastAPI, por sua vez, utiliza o **Starlette** (um framework ASGI - Asynchronous Server Gateway Interface) e é servido pelo **Uvicorn** (um servidor web ASGI). Essa base garante excelente performance, suporte nativo para operações assíncronas (async/await) e uma base sólida e escalável para as aplicações.  
* **Interface do Usuário (Frontend):** A interface do usuário renderizada no navegador é construída com **Vue.js**, um framework JavaScript progressivo para a criação de interfaces. Mais especificamente, o NiceGUI utiliza o **Quasar Framework**, uma biblioteca de componentes Vue que oferece um conjunto extenso de elementos de UI de alta qualidade, prontos para uso e baseados nos princípios do Material Design.

Quando você usa ui.button(), por exemplo, o NiceGUI está, nos bastidores, instruindo o frontend Vue a renderizar um componente QBtn do Quasar. Essa arquitetura cria uma ponte transparente entre o código Python do backend e os componentes reativos do frontend.

#### **Autenticação e Gerenciamento de Sessão para Sistema de Advocacia**

No contexto do nosso sistema SaaS de advocacia, o NiceGUI oferece mecanismos robustos para autenticação e gerenciamento de sessão:

* **app.storage.user:** Armazenamento de dados específicos do usuário durante a sessão
* **Integração FastAPI:** Permite middleware de autenticação customizado para 2FA
* **Roteamento baseado em papéis:** Suporte nativo para RBAC (sysadmin, admin_user, common_user)
* **Persistência de sessão:** Mantém estado de autenticação entre requisições
* **Decoradores de página:** `@ui.page` com controle de acesso baseado em permissões

**Exemplo de implementação para nosso projeto:**
```python
# Gerenciamento de sessão para usuários do sistema de advocacia
@ui.page('/dashboard')
def dashboard():
    if not app.storage.user.get('authenticated'):
        ui.navigate.to('/login')
        return
    
    user_role = app.storage.user.get('role')
    if user_role in ['sysadmin', 'admin_user']:
        # Interface completa para administradores
        render_admin_dashboard()
    else:
        # Interface limitada para usuários comuns
        render_user_dashboard()
```

#### **Instalação e Primeira Aplicação**

Começar a usar o NiceGUI é um processo direto. A instalação é feita através do pip, o gerenciador de pacotes padrão do Python.

```bash
# Instalação via pip
pip install nicegui

# Instalação via conda-forge
conda install nicegui

# Instalação via Docker
docker pull zauberzeug/nicegui
```

Uma vez instalado, criar uma aplicação mínima requer apenas algumas linhas de código em um arquivo, por exemplo, main.py.

```python
from nicegui import ui

# Cria um elemento de texto (label) na página  
ui.label('Olá, NiceGUI!')

# Cria um botão que, ao ser clicado, exibe uma notificação  
ui.button('CLIQUE AQUI', on_click=lambda: ui.notify('O botão foi pressionado'))

# Inicia o servidor da aplicação  
ui.run()
```

#### **Exemplo 5: Menu e Abas Completo (Do Repositório GitHub)**

* **Objetivo:** Demonstrar um layout completo com header, footer, drawer lateral e sistema de abas.  
* **Funcionalidades Demonstradas:**  
  * Layout completo com header/footer  
  * Drawer lateral toggle  
  * Sistema de abas integrado  
  * Botão FAB (Floating Action Button)  
  * Integração de múltiplos elementos de layout  
* **Código-Fonte Completo (examples/menu_and_tabs/main.py):**

```python
#!/usr/bin/env python3
from nicegui import ui

with ui.header().classes(replace='row items-center') as header:
    ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
    with ui.tabs() as tabs:
        ui.tab('A')
        ui.tab('B')
        ui.tab('C')

with ui.footer(value=False) as footer:
    ui.label('Footer')

with ui.left_drawer().classes('bg-blue-100') as left_drawer:
    ui.label('Side menu')

with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
    ui.button(on_click=footer.toggle, icon='contact_support').props('fab')

with ui.tab_panels(tabs, value='A').classes('w-full'):
    with ui.tab_panel('A'):
        ui.label('Content of A')
    with ui.tab_panel('B'):
        ui.label('Content of B')
    with ui.tab_panel('C'):
        ui.label('Content of C')

ui.run()
```

#### **Exemplo 6: Tabela Avançada com Slots (Do Repositório GitHub)**

* **Objetivo:** Demonstrar uso avançado de tabelas com slots customizados para busca e adição de linhas.  
* **Funcionalidades Demonstradas:**  
  * Slots customizados em tabelas  
  * Busca integrada na tabela  
  * Adição dinâmica de linhas  
  * Seleção múltipla  
  * Paginação  
* **Código-Fonte Completo (examples/table_and_slots/main.py):**

```python
#!/usr/bin/env python3
import time
from nicegui import ui

columns = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True},
    {'name': 'age', 'label': 'Age', 'field': 'age', 'sortable': True},
]
rows = [
    {'id': 0, 'name': 'Alice', 'age': 18},
    {'id': 1, 'name': 'Bob', 'age': 21},
    {'id': 2, 'name': 'Lionel', 'age': 19},
    {'id': 3, 'name': 'Michael', 'age': 32},
    {'id': 4, 'name': 'Julie', 'age': 12},
    {'id': 5, 'name': 'Livia', 'age': 25},
    {'id': 6, 'name': 'Carol'},
]

with ui.table(title='My Team', columns=columns, rows=rows, selection='multiple', pagination=10).classes('w-96') as table:
    with table.add_slot('top-right'):
        with ui.input(placeholder='Search').props('type=search').bind_value(table, 'filter').add_slot('append'):
            ui.icon('search')
    with table.add_slot('bottom-row'):
        with table.row():
            with table.cell():
                ui.button(on_click=lambda: (
                    table.add_row({'id': time.time(), 'name': new_name.value, 'age': new_age.value}),
                    new_name.set_value(None),
                    new_age.set_value(None),
                ), icon='add').props('flat fab-mini')
            with table.cell():
                new_name = ui.input('Name')
            with table.cell():
                new_age = ui.number('Age')

ui.label().bind_text_from(table, 'selected', lambda val: f'Current selection: {val}')
ui.button('Remove', on_click=lambda: table.remove_rows(table.selected)) \
    .bind_visibility_from(table, 'selected', backward=lambda val: bool(val))

ui.run()
```

Para executar a aplicação, basta usar o interpretador Python:

```bash
python3 main.py
```

O NiceGUI iniciará o servidor Uvicorn e a interface estará disponível, por padrão, em http://localhost:8080/ no navegador. Uma das características mais convenientes para o desenvolvimento é o recarregamento automático: sempre que o arquivo main.py é salvo, o NiceGUI detecta a mudança e atualiza automaticamente a página no navegador, permitindo um ciclo de feedback instantâneo.

#### **Análise Comparativa (Posicionamento no Ecossistema)**

A motivação por trás da criação do NiceGUI ajuda a posicioná-lo em relação a outras bibliotecas populares no ecossistema Python.

* **Em relação ao Streamlit:** Os criadores do NiceGUI apreciam a simplicidade do Streamlit, mas consideraram que ele realiza "muita mágica no que diz respeito ao gerenciamento de estado". O Streamlit tende a reexecutar o script inteiro a cada interação do usuário, o que pode tornar o gerenciamento de estado em aplicações complexas um desafio. O NiceGUI adota um modelo de estado mais explícito, onde o estado da aplicação reside em variáveis e objetos Python padrão, oferecendo ao desenvolvedor maior controle e previsibilidade.  
* **Em relação ao JustPy:** O JustPy serviu de inspiração para o NiceGUI, mas foi considerado muito "HTML de baixo nível". O JustPy exige que o desenvolvedor pense mais em termos de tags HTML. O NiceGUI eleva o nível de abstração ao fornecer componentes de UI de alto nível baseados no Quasar, como ui.card, ui.dialog, e ui.table, o que acelera o desenvolvimento e garante uma aparência consistente e moderna.

Portanto, o NiceGUI ocupa um nicho específico: ele busca a simplicidade e a abordagem "Python-puro" do Streamlit, mas com um modelo de gerenciamento de estado mais tradicional e explícito, e oferece um conjunto de componentes de UI mais rico e de mais alto nível que o JustPy.

#### **A Dupla Natureza da Abstração**

A principal força do NiceGUI é sua capacidade de abstrair as complexidades do desenvolvimento web. Um iniciante pode ser produtivo sem escrever uma única linha de HTML, CSS ou JavaScript. No entanto, essa abstração é, por design, "permeável" (leaky). Para ir além do básico e customizar profundamente a aparência e o comportamento dos elementos, é necessário interagir com os sistemas subjacentes.

Discussões da comunidade de usuários revelam que a distinção entre os métodos de estilização .props(), .classes() e .style() pode ser um ponto de confusão inicial. Isso ocorre porque cada um desses métodos é uma porta de entrada para uma camada diferente da pilha de front-end:

* .props() interage com as **propriedades** dos componentes Quasar.  
* .classes() interage com as **classes** CSS, primariamente do framework Tailwind CSS.  
* .style() aplica **estilos CSS em linha** diretamente ao elemento HTML.

Da mesma forma, para usar um componente Quasar que não possui um wrapper ui. dedicado, o desenvolvedor pode usar ui.element('q-list'), referenciando diretamente o nome do componente Quasar.

Isso revela um caminho de aprendizado em dois estágios para a maestria do NiceGUI. O primeiro estágio envolve aprender a API Python e os componentes ui. padrão. O segundo estágio, necessário para personalização avançada, envolve aprender a alavancar seletivamente o poder dos frameworks Quasar e Tailwind CSS através dos métodos que o NiceGUI expõe. Este guia foi estruturado para facilitar ambos os estágios, tratando essa "permeabilidade" não como uma falha, mas como uma poderosa característica que garante a flexibilidade da biblioteca.

### **Capítulo 2: Conceitos Essenciais**

Este capítulo detalha os conceitos fundamentais que formam a base de qualquer aplicação NiceGUI. Dominar essas ideias é crucial para escrever código eficiente, reativo e de fácil manutenção.

#### **O Loop de Eventos Assíncrono**

O NiceGUI é construído sobre um loop de eventos async/await, uma abordagem moderna para concorrência em Python. Em vez de usar múltiplos threads, que podem introduzir complexidade e problemas de segurança de thread (thread safety), o NiceGUI executa todo o código em um único thread, usando a programação assíncrona para lidar com operações simultâneas.

Isso tem duas implicações práticas importantes:

1. **Eficiência de Recursos:** O modelo assíncrono é extremamente eficiente para lidar com operações de I/O (entrada/saída), como requisições de rede, acesso a bancos de dados ou espera por eventos do usuário. A aplicação não fica bloqueada enquanto espera por essas operações, permanecendo responsiva.  
2. **Handlers de Eventos Assíncronos:** Qualquer função de callback, como a passada para o parâmetro on_click de um botão, pode ser uma função síncrona (def) ou uma corrotina assíncrona (async def).

```python
from nicegui import ui  
import asyncio

# Handler síncrono  
def handle_sync_click():  
    ui.notify('Ação síncrona!')

# Handler assíncrono  
async def handle_async_click():  
    ui.notify('Iniciando ação assíncrona...')  
    await asyncio.sleep(2)  # Simula uma operação de I/O não bloqueante  
    ui.notify('Ação assíncrona concluída!')

ui.button('Clique Síncrono', on_click=handle_sync_click)  
ui.button('Clique Assíncrono', on_click=handle_async_click)

ui.run()
```

No exemplo acima, clicar no botão assíncrono não congela a interface do usuário; ela permanece totalmente interativa durante os 2 segundos de espera.

É fundamental entender que **todas as atualizações da UI devem ocorrer no thread principal** onde o loop de eventos está sendo executado. O NiceGUI gerencia isso automaticamente para handlers de eventos padrão. Para tarefas em segundo plano, mecanismos específicos devem ser usados, como será visto no Capítulo 12.

#### **Interface Declarativa e Contêineres de Contexto**

O NiceGUI adota um paradigma de UI declarativa, popularizado por frameworks como Flutter e SwiftUI. Em vez de criar objetos e adicioná-los imperativamente a um pai (ex: layout.add_child(button)), você declara a estrutura da sua UI usando a sintaxe do Python.

A principal ferramenta para isso é o gerenciador de contexto do Python, a instrução with. Elementos que podem conter outros elementos (contêineres) podem ser usados em uma instrução with. Qualquer elemento criado dentro do bloco with indentado é automaticamente adicionado como um filho do contêiner.

```python
from nicegui import ui

with ui.card().classes('w-64'):  
    ui.card_section()  
    ui.label('Um cartão com conteúdo')  
    with ui.row().classes('w-full justify-around'):  
        ui.button('OK')  
        ui.button('Cancelar')

ui.run()
```

Neste exemplo, a indentação do código espelha visualmente a hierarquia da UI: os botões estão dentro de uma ui.row, que por sua vez está dentro de uma ui.card. Essa abordagem torna o código de layout excepcionalmente legível e intuitivo.

#### **Vinculação de Dados (Data Binding)**

A vinculação de dados é um dos recursos mais poderosos do NiceGUI, permitindo uma conexão direta entre o estado da sua aplicação (os dados) e a interface do usuário (a visualização). Isso elimina a necessidade de escrever código manual para atualizar a UI sempre que um dado muda, e vice-versa.

O NiceGUI oferece um sistema de vinculação de dados direto e flexível através de uma família de métodos bind_.... Esses métodos podem criar vinculações unidirecionais ou bidirecionais.

* **Vinculação Bidirecional (bind_value):** O valor do elemento da UI e a propriedade do objeto de dados são mantidos em sincronia. Uma mudança em um reflete imediatamente no outro.

```python
from nicegui import ui

class AppData:  
    def __init__(self):  
        self.name = 'Mundo'

data = AppData()

# O valor do input está vinculado a data.name  
# Mudar o texto no input atualiza data.name  
# Mudar data.name programaticamente atualiza o texto no input  
ui.input('Nome').bind_value(data, 'name')  
ui.label().bind_text_from(data, 'name', backward=lambda name: f'Olá, {name}!')

ui.run()
```

* **Vinculação Unidirecional (bind_value_from, bind_value_to):** A atualização flui em apenas uma direção.  
  * bind_..._from(objeto_fonte, 'prop_fonte'): O elemento da UI é atualizado quando a propriedade no objeto_fonte muda.  
  * bind_..._to(objeto_alvo, 'prop_alvo'): A propriedade no objeto_alvo é atualizada quando o valor do elemento da UI muda.

O NiceGUI fornece métodos de vinculação para várias propriedades, não apenas para o valor. Alguns dos mais comuns são:

* bind_visibility: Torna um elemento visível ou invisível com base em um valor booleano.  
* bind_text / bind_content: Vincula o conteúdo textual de um elemento.  
* bind_source: Vincula a fonte de um elemento de mídia, como ui.image.

Funções de transformação (forward e backward) podem ser fornecidas para formatar ou converter valores durante o processo de vinculação.

#### **O Ciclo de Vida da Aplicação e da Página**

Entender o ciclo de vida de uma aplicação NiceGUI é crucial para executar código nos momentos certos, como inicializar recursos ou realizar limpezas.

O objeto app do NiceGUI fornece hooks para os principais eventos do ciclo de vida:

* app.on_startup: Registra uma função (síncrona ou assíncrona) a ser executada uma vez, quando o servidor é iniciado. Ideal para configurar conexões de banco de dados, inicializar modelos de ML, ou iniciar tarefas em segundo plano.  
* app.on_shutdown: Registra uma função a ser executada uma vez, quando o servidor está prestes a ser desligado. Ideal para fechar conexões e liberar recursos.  
* app.on_connect: Registra um handler para ser executado toda vez que um novo cliente se conecta.  
* app.on_disconnect: Registra um handler para ser executado quando um cliente se desconecta.

Um ponto importante é que certas informações, como as URLs em que a aplicação está sendo servida, não estão disponíveis durante o evento on_startup porque o servidor ainda não está totalmente em execução. Para acessar essas informações, pode-se fazê-lo dentro de uma função de página (@ui.page) ou registrar um callback com app.urls.on_change.

#### **O Estado é Explícito e Persistente**

Uma distinção fundamental do NiceGUI, derivada de sua filosofia, é o seu modelo de gerenciamento de estado explícito. Ao contrário de frameworks que podem reexecutar scripts e gerenciar o estado de forma "mágica", no NiceGUI, o estado da aplicação vive onde o desenvolvedor o coloca: em variáveis Python, instâncias de classes, ou no objeto de armazenamento persistente fornecido pelo framework.

Isso significa que o fluxo de uma aplicação NiceGUI é mais parecido com o de um servidor web tradicional. O estado não é efêmero por padrão; ele persiste enquanto o servidor estiver em execução (para estado global) ou durante a sessão de um usuário.

Para facilitar a persistência de dados entre interações e até mesmo recarregamentos de página, o NiceGUI fornece o objeto app.storage. Ele oferece diferentes escopos de armazenamento:

* app.storage.general: Um dicionário compartilhado por todos os usuários e sessões. Persiste enquanto o servidor estiver rodando.  
* app.storage.user: Um dicionário único para cada usuário (identificado por um ID de sessão armazenado em um cookie). Os dados aqui persistem entre recarregamentos de página para aquele usuário específico. É a base para funcionalidades como autenticação.  
* app.storage.browser: Um dicionário que armazena dados no localStorage do navegador do cliente. Os dados são específicos para aquele navegador e persistem mesmo que o navegador seja fechado e reaberto.

Esse controle explícito sobre o estado torna o NiceGUI extremamente adequado para aplicações complexas e com estado, como assistentes de múltiplos passos, carrinhos de compras ou painéis de controle interativos, onde um gerenciamento de estado implícito poderia se tornar confuso e propenso a erros. O padrão de design predominante no NiceGUI é: "Defina seu estado em objetos Python, e vincule sua UI a eles."

### **Capítulo 3: Layout e Estilização**

Este capítulo explora como organizar os elementos na página e customizar sua aparência. O NiceGUI oferece um sistema de layout flexível e múltiplas camadas de estilização, que, uma vez compreendidas, fornecem controle total sobre o design da interface.

#### **Construindo Layouts**

A organização espacial dos elementos é primariamente alcançada através de contêineres de layout. O NiceGUI usa um modelo baseado em flexbox por padrão, o que torna a criação de layouts fluidos e responsivos bastante natural. Os principais contêineres de layout são:

* **ui.row**: Organiza seus elementos filhos horizontalmente, um ao lado do outro.  
* **ui.column**: Organiza seus elementos filhos verticalmente, um abaixo do outro.  
* **ui.grid(columns=N)**: Organiza seus filhos em uma grade com um número fixo de colunas (N). Os elementos fluirão para preencher a grade da esquerda para a direita, de cima para baixo.  
* **ui.card**: Não é apenas um contêiner de conteúdo, mas também um elemento de layout fundamental para agrupar informações relacionadas visualmente.

```python
from nicegui import ui

ui.label('Layout com Linhas e Colunas').classes('text-h6')  
with ui.row().classes('w-full p-4 bg-gray-200'):  
    ui.label('Item 1 da Linha')  
    with ui.column().classes('p-2 bg-gray-300'):  
        ui.label('Item 1 da Coluna')  
        ui.label('Item 2 da Coluna')  
    ui.label('Item 2 da Linha')

ui.label('Layout com Grade').classes('text-h6 mt-4')  
with ui.grid(columns=3).classes('w-full p-4 bg-blue-200'):  
    for i in range(6):  
        with ui.card():  
            ui.label(f'Célula {i+1}')

ui.run()
```

#### **O Sistema de Estilização Tripartido**

Um dos aspectos mais importantes para dominar o NiceGUI é entender suas três principais formas de estilização. Cada uma corresponde a uma camada diferente da tecnologia web subjacente e tem um propósito específico. A confusão entre elas é um obstáculo comum para novos usuários, mas a distinção é clara:

1. .classes(...) - Para Layout e Estilo Utilitário (Tailwind CSS):  
   Este é o método preferido e mais idiomático para estilização no NiceGUI. Ele permite aplicar classes CSS a um elemento. O NiceGUI vem com o Tailwind CSS pré-configurado, um framework CSS "utility-first" que oferece um vasto conjunto de classes para controlar layout, cor, espaçamento, tipografia, etc. (ex: w-full, p-4, text-red-500, font-bold). A vantagem é a rapidez e a consistência. O editor de código VSCode, com a extensão oficial do Tailwind CSS, pode até fornecer autocompletar para essas classes dentro do seu código Python.  
2. .props(...) - Para Comportamento e Estilo Específico do Componente (Quasar):  
   Este método é usado para definir atributos no componente Quasar subjacente ou atributos HTML padrão. As propriedades do Quasar controlam aspectos específicos da aparência e do comportamento de um componente que não são facilmente alcançados com CSS genérico. Por exemplo, um ui.button pode receber as propriedades flat para remover a sombra, round para torná-lo circular, ou dense para torná-lo menor. Você também pode passar atributos HTML padrão como disabled ou tabindex.  
3. .style(...) - Para Estilos CSS Específicos e Únicos (CSS em Linha):  
   Este método aplica estilos CSS em linha (style="...") diretamente no elemento HTML. Ele deve ser usado como um último recurso, para propriedades CSS muito específicas que não são cobertas pelo Tailwind ou quando você precisa aplicar um valor de estilo dinâmico que seria complicado de gerenciar com classes.

A tabela a seguir serve como uma matriz de decisão para ajudar a escolher o método correto.

| Método | Tecnologia Subjacente | Propósito Principal | Exemplo | Quando Usar |
| :---- | :---- | :---- | :---- | :---- |
| .classes('...') | Tailwind CSS / CSS | Aplicar classes de utilidade para layout, espaçamento, cores, etc. | ui.label('...').classes('text-red-500 font-bold') | Para a maioria das necessidades de estilização e layout. O método preferido. |
| .style('...') | CSS em Linha | Aplicar estilos CSS específicos ou únicos que não são cobertos por Tailwind. | ui.label('...').style('text-shadow: 2px 2px #ff0000;') | Para propriedades CSS raras ou valores dinâmicos/calculados que não se encaixam bem em classes. |
| .props('...') | Atributos Quasar / HTML | Modificar o comportamento e a aparência específica do componente Quasar subjacente. | ui.button().props('flat round') | Para controlar propriedades específicas do Quasar (e.g., flat, round, dense) ou adicionar atributos HTML padrão (disabled, readonly). |

#### **Temas e Cores Globais**

Para uma identidade visual consistente em toda a aplicação, não é prático estilizar cada componente individualmente. O NiceGUI permite a definição de um esquema de cores global através da função ui.colors(). Você pode definir as cores primária (primary), secundária (secondary), de destaque (accent), e outras cores do tema Quasar.

```python
from nicegui import ui

# Define as cores globais antes de criar qualquer elemento  
ui.colors(primary='#5848a8', secondary='#e58429', accent='#29b5e5')

ui.label('Este texto usará as cores do tema.')  
ui.button('Botão Primário')  # Usará a cor primária  
ui.checkbox('Checkbox de Destaque').props('color=accent')  
ui.slider(min=0, max=100, value=50).props('color=secondary')

ui.run()
```

Além disso, elementos mais complexos como gráficos (ui.echart) também suportam a aplicação de temas para controlar sua paleta de cores e aparência.

#### **Design Responsivo**

Embora o NiceGUI não tenha um componente de alto nível chamado "responsivo", ele fornece todas as ferramentas necessárias para construir interfaces que se adaptam a diferentes tamanhos de tela, principalmente através do Tailwind CSS.

O Tailwind é um framework "mobile-first", o que significa que as classes de utilidade sem prefixo (ex: w-1/2) se aplicam a todos os tamanhos de tela, começando pelos menores. Para aplicar estilos diferentes em telas maiores, você usa prefixos de ponto de interrupção (breakpoints):

* sm:: Telas pequenas (small) e maiores.  
* md:: Telas médias (medium) e maiores.  
* lg:: Telas grandes (large) e maiores.  
* xl:: Telas extra grandes (extra large) e maiores.

```python
from nicegui import ui

with ui.row().classes('w-full gap-4'):  
    # Esta coluna ocupa a largura total em telas pequenas,  
    # metade da largura em telas médias, e um terço em telas grandes.  
    ui.card().classes('w-full md:w-1/2 lg:w-1/3 h-32')  
    ui.card().classes('w-full md:w-1/2 lg:w-1/3 h-32')  
    ui.card().classes('w-full md:w-1/2 lg:w-1/3 h-32')

ui.run()
```

Ao redimensionar a janela do navegador com este exemplo, as caixas se reorganizarão automaticamente. Existem também bibliotecas da comunidade, como a nicegui-tailwind-layout, que fornecem templates de layout responsivos pré-construídos para acelerar ainda mais o desenvolvimento.

---

## **Parte II: Referência Completa de Elementos da UI (ui.)**

Esta parte é o coração do guia de referência. Ela serve como uma enciclopédia detalhada para cada elemento de interface de usuário disponível no módulo ui. Cada componente é apresentado em um formato padronizado para facilitar a consulta e o aprendizado, incluindo sua descrição, parâmetros de inicialização, propriedades e métodos notáveis, acompanhados de exemplos de código práticos.

### **Capítulo 4: Controles Básicos e de Interação**

Este capítulo cobre os blocos de construção fundamentais de qualquer interface de usuário: elementos para exibir informações e para o usuário iniciar ações.

#### **ui.label**

* **Descrição:** O elemento mais fundamental para exibir texto na página. Ele renderiza o texto dentro de uma tag <div> HTML.  
* **Inicializador:** ui.label(text: str = '')  
  * text: O conteúdo textual a ser exibido.  
* **Propriedades Notáveis:**  
  * .text: Permite obter ou definir o conteúdo do label programaticamente.  
* **Métodos Notáveis:**  
  * .set_text(text: str): Atualiza o texto do label.  
  * bind_text_from(...): Vincula o texto do label a uma variável de dados.  
* **Exemplo:**

```python
from nicegui import ui  
import time

# Label estático  
ui.label('Este é um label estático.')

# Label com texto atualizado programaticamente  
my_label = ui.label('Aguarde...')  
ui.button('Definir Texto', on_click=lambda: my_label.set_text(f'Texto definido em {time.time()}'))

ui.run()
```

* **Uso Avançado:** É possível criar subclasses de ui.label para alterar a aparência com base no conteúdo, sobrescrevendo o método _handle_text_change.

#### **ui.link**

* **Descrição:** Cria um hyperlink (<a> tag) para navegar para outras páginas ou locais.  
* **Inicializador:** ui.link(text: str, target: Any, new_tab: bool = False)  
  * text: O texto visível do link.  
  * target: O destino do link. Pode ser uma string (URL absoluta ou caminho relativo), outra função de página do NiceGUI, ou outro elemento da UI na mesma página (usando seu ID com #).  
  * new_tab: Se True, abre o link em uma nova aba do navegador.  
* **Exemplo:**

```python
from nicegui import ui

@ui.page('/outra_pagina')  
def outra_pagina():  
    ui.label('Você está na outra página.')

# Link para uma URL externa em uma nova aba  
ui.link('NiceGUI no GitHub', 'https://github.com/zauberzeug/nicegui', new_tab=True)

# Link para outra página dentro da mesma aplicação  
ui.link('Ir para outra página', outra_pagina)

ui.run()
```

#### **ui.button**

* **Descrição:** Um botão padrão que o usuário pode clicar para acionar um evento. É baseado no componente QBtn do Quasar.  
* **Inicializador:** ui.button(text: str = '', on_click: Callable[..., Any] | None = None, color: str | None = 'primary', icon: str | None = None)  
  * text: O rótulo do botão.  
  * on_click: Uma função (síncrona ou assíncrona) a ser chamada quando o botão é clicado.  
  * color: A cor do botão. Pode ser uma cor do tema Quasar (primary, accent), uma cor do Tailwind (red-500) ou uma cor CSS padrão (#ff0000).  
  * icon: O nome de um ícone do conjunto Material Icons a ser exibido no botão.  
* **Propriedades Notáveis:**  
  * .enabled: Booleano para ativar/desativar o botão. Pode ser vinculado.  
* **Métodos Notáveis:**  
  * .disable(): Desativa o botão.  
  * .enable(): Ativa o botão.  
* **Exemplo:**

```python
from nicegui import ui

def lidar_com_clique():  
    ui.notify('Botão com ícone clicado!')

ui.button('Botão Simples', on_click=lambda: ui.notify('Clicado!'))  
ui.button('Botão com Ícone', icon='thumb_up', on_click=lidar_com_clique).props('color=positive')

# Botão de Ação Flutuante (FAB)  
with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):  
    ui.button(icon='add', on_click=lambda: ui.notify('FAB Clicado!')).props('fab color=accent')

ui.run()
```

O exemplo do FAB demonstra o uso de .props('fab') para estilizar o botão como um Floating Action Button, uma capacidade herdada diretamente do Quasar.

#### **ui.button_group**

* **Descrição:** Um contêiner para agrupar múltiplos ui.button, fazendo com que eles apareçam conectados visualmente. Baseado no QBtnGroup do Quasar.  
* **Inicializador:** ui.button_group()  
* **Uso:** Use como um gerenciador de contexto with.  
* **Exemplo:**

```python
from nicegui import ui

with ui.button_group().props('push'):  # A prop 'push' se aplica ao grupo  
    ui.button(icon='format_align_left', on_click=lambda: ui.notify('Alinhar à esquerda'))  
    ui.button(icon='format_align_center', on_click=lambda: ui.notify('Centralizar'))  
    ui.button(icon='format_align_right', on_click=lambda: ui.notify('Alinhar à direita'))

ui.run()
```

É importante notar que as propriedades de design (como push, flat, outline) devem ser aplicadas consistentemente tanto no ui.button_group quanto nos ui.button filhos para um visual coeso.

#### **ui.dropdown_button**

* **Descrição:** Um componente que combina um botão com um menu suspenso, revelando uma lista de ações ou opções quando clicado. Baseado no QBtnDropdown do Quasar.  
* **Inicializador:** ui.dropdown_button(text: str, auto_close: bool = False, color: str | None = 'primary', icon: str | None = None)  
  * text: O texto exibido no botão.  
  * auto_close: Se True, o menu se fecha automaticamente após um item ser clicado.  
* **Uso:** Use como um gerenciador de contexto with e aninhe elementos ui.item dentro dele.  
* **Exemplo:**

```python
from nicegui import ui

with ui.dropdown_button('Ferramentas', auto_close=True, icon='build'):  
    ui.item('Item 1', on_click=lambda: ui.notify('Clicou no Item 1'))  
    ui.item('Item 2', on_click=lambda: ui.notify('Clicou no Item 2'))  
    ui.separator()  
    ui.item('Item 3', on_click=lambda: ui.notify('Clicou no Item 3'))

ui.run()
```

#### **ui.icon**

* **Descrição:** Exibe um ícone do conjunto de ícones padrão (Material Icons) fornecido pelo Quasar.  
* **Inicializador:** ui.icon(name: str, color: str | None = None, size: str | None = None)  
  * name: O nome do ícone (ex: 'home', 'settings').  
  * color: A cor do ícone.  
  * size: O tamanho do ícone (ex: 'xs', '2rem', '50px').  
* **Exemplo:**

```python
from nicegui import ui

with ui.row().classes('items-center'):  
    ui.icon('thumb_up', color='positive', size='lg')  
    ui.icon('home', color='primary', size='3rem')  
    ui.icon('settings', color='gray-500')

ui.run()
```

#### **ui.badge**

* **Descrição:** Um pequeno elemento, geralmente numérico ou textual, usado para anexar informações a outro elemento, como um contador de notificações em um ícone ou botão. Baseado no QBadge do Quasar.  
* **Inicializador:** ui.badge(text: str = '', color: str | None = 'primary', text_color: str | None = None)  
  * text: O conteúdo do badge.  
* **Uso:** Geralmente aninhado dentro de outro elemento e posicionado com propriedades (.props('floating')).  
* **Exemplo:**

```python
from nicegui import ui

with ui.button(icon='mail', on_click=lambda: badge.set_text(int(badge.text) + 1)):  
    badge = ui.badge('0', color='red').props('floating')

ui.run()
```

#### **ui.chip**

* **Descrição:** Um elemento compacto que representa uma entidade, como uma tag, um contato ou uma escolha. Pode ser interativo (clicável, selecionável, removível). Baseado no QChip do Quasar.  
* **Inicializador:** ui.chip(text: str, icon: str | None = None, color: str | None = 'primary', selectable: bool = False, removable: bool = False, on_click: Callable | None = None)  
  * selectable: Se True, o chip pode ser alternado entre os estados selecionado e não selecionado.  
  * removable: Se True, exibe um ícone 'x' para remover o chip. Dispara um evento on_value_change.  
* **Exemplo:**

```python
from nicegui import ui

with ui.row().classes('gap-2'):  
    ui.chip('Padrão')  
    ui.chip('Clicável', icon='alarm', on_click=lambda: ui.notify('Chip clicado!')).props('color=secondary text-color=white')  
    ui.chip('Removível', removable=True, on_value_change=lambda e: ui.notify(f'Removido: {e.value}'))  
    ui.chip('Selecionável', selectable=True)

ui.run()
```

### **Capítulo 5: Entradas de Dados do Usuário**

Este capítulo detalha os elementos que permitem aos usuários inserir dados na aplicação, desde texto simples até seleções complexas.

#### **ui.input**

* **Descrição:** O elemento padrão para entrada de texto de linha única. É altamente configurável, com suporte para placeholders, validação, autocompletar e mais. Baseado no QInput do Quasar.  
* **Inicializador:** ui.input(label: str | None = None, placeholder: str | None = None, value: str = '', on_change: Callable | None = None, password: bool = False, password_toggle_button: bool = False, autocomplete: list[str] | None = None, validation: dict[str, Callable] | Callable | None = None)  
  * label: Um rótulo flutuante que descreve o campo.  
  * placeholder: Texto de ajuda exibido quando o campo está vazio.  
  * on_change: Callback acionado a cada pressionamento de tecla. O valor atualizado está em e.value.  
  * password: Se True, oculta os caracteres digitados.  
  * password_toggle_button: Se True, mostra um botão para alternar a visibilidade da senha.  
  * autocomplete: Uma lista de strings para sugestões de preenchimento automático.  
  * validation: Uma função que retorna uma mensagem de erro se a entrada for inválida (ou None se for válida), ou um dicionário de { 'mensagem': função_validadora }.  
* **Exemplo:**

```python
from nicegui import ui

ui.input(label='Seu Nome', placeholder='ex: João Silva',  
         on_change=lambda e: result.set_text(f'Você digitou: {e.value}'))  
result = ui.label()

ui.input('Senha', password=True, password_toggle_button=True)

ui.input('Email', validation={'Email inválido': lambda v: '@' in v and '.' in v.split('@')})

ui.run()
```

A validação pode ser uma corrotina async para verificações no lado do servidor. O QInput subjacente pode ser estilizado com as propriedades input-style e input-class via .props().

#### **ui.number**

* **Descrição:** Um campo de entrada especializado para valores numéricos, com botões opcionais para incrementar/decrementar.  
* **Inicializador:** ui.number(label: str | None = None, value: float | None = None, min: float | None = None, max: float | None = None, step: float = 1.0, precision: int | None = None, on_change: Callable | None = None)  
  * min, max: Limites mínimo e máximo para o valor.  
  * step: O incremento/decremento ao usar os botões.  
  * precision: O número de casas decimais permitidas.  
* **Exemplo:**

```python
from nicegui import ui

n = ui.number('Idade', value=18, min=0, max=120, step=1)  
ui.label().bind_text_from(n, 'value', lambda v: f'Idade selecionada: {v}')

ui.run()
```

#### **ui.textarea**

* **Descrição:** Semelhante ao ui.input, mas para entrada de texto de múltiplas linhas. Baseado no QInput com type="textarea".  
* **Inicializador:** ui.textarea(label: str | None = None, placeholder: str | None = None, value: str = '', on_change: Callable | None = None)  
* **Exemplo:**

```python
from nicegui import ui

ui.textarea(label='Comentários', placeholder='Deixe seu feedback aqui...') \
   .props('filled')

ui.run()
```

#### **ui.checkbox**

* **Descrição:** Uma caixa de seleção padrão (marcada/desmarcada). Baseado no QCheckbox do Quasar.  
* **Inicializador:** ui.checkbox(text: str, value: bool = False, on_change: Callable | None = None)  
  * text: O rótulo exibido ao lado da caixa de seleção.  
  * value: O estado inicial (marcado ou não).  
* **Exemplo:**

```python
from nicegui import ui

checkbox = ui.checkbox('Aceito os termos e condições.')  
ui.button('Enviar').bind_enabled_from(checkbox, 'value')

ui.run()
```

#### **ui.switch**

* **Descrição:** Um interruptor de alternância (on/off), visualmente diferente de um checkbox, mas funcionalmente similar.  
* **Inicializador:** ui.switch(text: str | None = None, value: bool = False, on_change: Callable | None = None)  
* **Exemplo:**

```python
from nicegui import ui

switch = ui.switch('Modo escuro')  
ui.label('Desligado').bind_text_from(switch, 'value', lambda v: 'Ligado' if v else 'Desligado')

ui.run()
```

#### **ui.radio**

* **Descrição:** Permite que o usuário selecione uma única opção de um conjunto. Baseado no QRadio do Quasar.  
* **Inicializador:** ui.radio(options: list | dict, value: Any | None = None, on_change: Callable | None = None)  
  * options: Pode ser uma lista de valores, ou um dicionário onde as chaves são os valores e os valores do dicionário são os rótulos exibidos.  
  * value: O valor da opção inicialmente selecionada.  
* **Exemplo:**

```python
from nicegui import ui

opcoes = {'SP': 'São Paulo', 'RJ': 'Rio de Janeiro', 'MG': 'Minas Gerais'}  
radio = ui.radio(opcoes, value='SP').props('inline')  
ui.label().bind_text_from(radio, 'value', lambda v: f'Estado selecionado: {opcoes[v]}')

ui.run()
```

#### **ui.toggle**

* **Descrição:** Um grupo de botões onde apenas um pode estar ativo por vez, semelhante a um ui.radio, mas com uma aparência de ui.button_group.  
* **Inicializador:** ui.toggle(options: list | dict, value: Any | None = None, on_change: Callable | None = None)  
* **Exemplo:**

```python
from nicegui import ui

toggle = ui.toggle({1: 'Um', 2: 'Dois', 3: 'Três'}, value=1)

ui.run()
```

#### **ui.select**

* **Descrição:** Um campo que, quando clicado, abre um menu suspenso de opções para seleção. Baseado no QSelect do Quasar.  
* **Inicializador:** ui.select(options: list | dict, value: Any | None = None, label: str | None = None, on_change: Callable | None = None, multiple: bool = False, clearable: bool = False)  
  * options: Lista ou dicionário de opções, como em ui.radio.  
  * multiple: Se True, permite a seleção de múltiplas opções. O valor será uma lista.  
  * clearable: Se True, exibe um ícone para limpar a seleção.  
* **Exemplo:**

```python
from nicegui import ui

opcoes_frutas = ['Maçã', 'Banana', 'Laranja', 'Manga']
ui.select(opcoes_frutas, label='Escolha uma fruta')  
ui.select(opcoes_frutas, label='Escolha várias frutas', multiple=True, clearable=True)

ui.run()
```

#### **ui.slider**

* **Descrição:** Um controle deslizante que permite ao usuário selecionar um valor numérico arrastando um marcador ao longo de uma trilha.  
* **Inicializador:** ui.slider(min: float, max: float, step: float = 1.0, value: float | None = None, on_change: Callable | None = None)  
* **Exemplo:**

```python
from nicegui import ui

slider = ui.slider(min=0, max=100, step=5, value=20).props('label-always')  
ui.label().bind_text_from(slider, 'value')

ui.run()
```

#### **ui.range**

* **Descrição:** Semelhante a um ui.slider, mas com dois marcadores para selecionar um intervalo (um valor mínimo e um máximo).  
* **Inicializador:** ui.range(min: float, max: float, value: dict | None = None, on_change: Callable | None = None)  
  * value: Um dicionário com chaves 'min' e 'max'.  
* **Exemplo:**

```python
from nicegui import ui

range_slider = ui.range(min=0, max=100, value={'min': 20, 'max': 80})  
ui.label().bind_text_from(range_slider, 'value', lambda v: f"Intervalo: {v['min']} - {v['max']}")

ui.run()
```

#### **ui.date / ui.time**

* **Descrição:** Componentes que abrem um seletor de data ou de hora, respectivamente. Baseados nos componentes QDate e QTime do Quasar.  
* **Inicializador:** ui.date(value: str | None = None, on_change: Callable | None = None) e ui.time(value: str | None = None, on_change: Callable | None = None)  
* **Uso:** Geralmente usados dentro de um ui.input com um ui.popup.  
* **Exemplo:**

```python
from nicegui import ui

with ui.input('Data') as date_input:  
    with date_input.add_slot('append'):  
        ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')  
    with ui.menu() as menu:  
        ui.date().bind_value(date_input)

with ui.input('Hora') as time_input:  
    with time_input.add_slot('append'):  
        ui.icon('access_time').on('click', lambda: menu_time.open()).classes('cursor-pointer')  
    with ui.menu() as menu_time:  
        ui.time().bind_value(time_input)

ui.run()
```

#### **ui.color_picker / ui.color_input**

* **Descrição:** ui.color_picker é um seletor de cores visual. ui.color_input é um campo de texto que abre um ui.color_picker em um popup.  
* **Exemplo:**

```python
from nicegui import ui

picker = ui.color_picker(on_pick=lambda e: button.style(f'background-color:{e.color}!important'))  
button = ui.button('Cor do botão muda')

color_input = ui.color_input(label='Cor de Fundo', value='#FFFFFF',  
                           on_change=lambda e: target.style(f'background-color:{e.value}'))  
target = ui.card().classes('w-32 h-32')

ui.run()
```

#### **ui.upload**

* **Descrição:** Um componente que permite aos usuários selecionar e enviar arquivos do seu dispositivo para o servidor.  
* **Inicializador:** ui.upload(on_upload: Callable, label: str = 'Upload', auto_upload: bool = False, multiple: bool = False)  
  * on_upload: Um callback que é acionado quando um arquivo é enviado. Ele recebe um argumento de evento e do tipo UploadEventArguments, onde e.content é um file-like object de bytes.  
  * auto_upload: Se True, o upload começa assim que o arquivo é selecionado.  
* **Exemplo:**

```python
from nicegui import ui  
from nicegui.events import UploadEventArguments

def handle_upload(e: UploadEventArguments):  
    text = e.content.read().decode('utf-8')  
    ui.notify(f'Arquivo "{e.name}" enviado com {len(text)} caracteres.')  
    content_label.set_text(text[:100] + '...')

ui.upload(on_upload=handle_upload, label='Envie um arquivo de texto').props('accept=.txt')  
content_label = ui.label('Conteúdo do arquivo aparecerá aqui.')

ui.run()
```

#### **ui.knob**

* **Descrição:** Um controle circular tipo dial para entrada de valores numéricos. Baseado no QKnob do Quasar.  
* **Inicializador:** ui.knob(value: float = 0.0, min: float = 0.0, max: float = 100.0, step: float = 1.0)  
* **Exemplo:**

```python
from nicegui import ui

knob = ui.knob(value=50, min=0, max=100, step=5).props('show-value size=100px color=primary')
ui.label().bind_text_from(knob, 'value', lambda v: f'Valor: {v}')

ui.run()
```

#### **ui.rating**

* **Descrição:** Controle de avaliação por estrelas. Baseado no QRating do Quasar.  
* **Inicializador:** ui.rating(max: int = 5, value: float = 0.0, size: str = '1em')  
* **Exemplo:**

```python
from nicegui import ui

rating = ui.rating(max=5, value=3.5, size='2em').props('color=yellow')
ui.label().bind_text_from(rating, 'value', lambda v: f'Avaliação: {v} estrelas')

ui.run()
```

### **Capítulo 6: Contêineres e Elementos de Agrupamento**

Estes elementos são usados para estruturar a página e agrupar outros componentes, criando layouts complexos e interfaces organizadas.

#### **ui.card (com ui.card_section, ui.card_actions)**

* **Descrição:** Um contêiner de conteúdo versátil que segue o padrão de "cartão" do Material Design. É um dos blocos de construção mais comuns para agrupar informações relacionadas.  
* **Uso:** ui.card é o contêiner principal. ui.card_section é usado para áreas de conteúdo principais, e ui.card_actions é tipicamente usado no final do cartão para conter botões de ação.  
* **Exemplo:**

```python
from nicegui import ui

with ui.card().classes('w-80'):  
    with ui.card_section():  
        ui.label('Título do Cartão').classes('text-h6')  
        ui.label('Subtítulo do Cartão').classes('text-subtitle2')  
    with ui.card_section():  
        ui.label('Este é o corpo do cartão, onde o conteúdo principal reside.')  
    with ui.card_actions().props('align=right'):  
        ui.button('Ação 1', on_click=lambda: ui.notify('Ação 1'))  
        ui.button('Ação 2', on_click=lambda: ui.notify('Ação 2'))

ui.run()
```

#### **ui.dialog**

* **Descrição:** Uma janela de diálogo modal que sobrepõe o conteúdo da página, exigindo a interação do usuário. Útil para confirmações, formulários ou para exibir informações importantes.  
* **Uso:** Um ui.dialog é criado, mas permanece oculto. Ele é aberto e fechado programaticamente através de seus métodos .open() e .close().  
* **Exemplo:**

```python
from nicegui import ui

with ui.dialog() as dialog, ui.card():  
    ui.label('Você tem certeza?')  
    with ui.row():  
        ui.button('Sim', on_click=lambda: (ui.notify('Confirmado!'), dialog.close()))  
        ui.button('Não', on_click=dialog.close)

ui.button('Abrir Diálogo', on_click=dialog.open)

ui.run()
```

#### **ui.expansion**

* **Descrição:** Um painel colapsável que consiste em um cabeçalho e uma área de conteúdo que pode ser expandida ou recolhida. Também conhecido como "accordion".  
* **Inicializador:** ui.expansion(text: str, caption: str | None = None, icon: str | None = None, group: str | None = None)  
  * text: O texto principal do cabeçalho.  
  * caption: Um texto secundário no cabeçalho.  
  * group: Se múltiplos ui.expansion compartilharem o mesmo nome de grupo, apenas um deles poderá estar aberto de cada vez.  
* **Exemplo:**

```python
from nicegui import ui

with ui.column():  
    with ui.expansion('Expandir para Detalhes', icon='info', group='my-group'):  
        ui.label('Aqui estão alguns detalhes importantes que estavam ocultos.')  
    with ui.expansion('Outra Expansão', icon='settings', group='my-group'):  
        ui.label('Mais conteúdo aqui.')

ui.run()
```

#### **ui.menu**

* **Descrição:** Um menu suspenso que aparece quando seu elemento âncora é ativado. Geralmente usado com botões ou ícones.  
* **Uso:** Um ui.menu é criado e, por padrão, ele se ancora ao seu elemento pai. Ele é aberto e fechado com .open() e .close().  
* **Exemplo:**

```python
from nicegui import ui

with ui.button(icon='menu'):  
    with ui.menu():  
        ui.menu_item('Item de Menu 1', on_click=lambda: ui.notify('Item 1'))  
        ui.menu_item('Item de Menu 2', on_click=lambda: ui.notify('Item 2'))  
        ui.separator()  
        ui.menu_item('Fechar', on_click=lambda: menu.close())  # 'menu' é o objeto retornado por ui.menu()

ui.run()
```

#### **ui.tabs (com ui.tab, ui.tab_panels, ui.tab_panel)**

* **Descrição:** Um conjunto completo de componentes para criar interfaces com abas. ui.tabs contém os cabeçalhos das abas (ui.tab), e ui.tab_panels contém o conteúdo correspondente (ui.tab_panel). A seleção é sincronizada entre eles.  
* **Exemplo:**

```python
from nicegui import ui

with ui.tabs().classes('w-full') as tabs:  
    one = ui.tab('Um')  
    two = ui.tab('Dois')

with ui.tab_panels(tabs, value=one).classes('w-full'):  
    with ui.tab_panel(one):  
        ui.label('Este é o conteúdo da primeira aba.')  
    with ui.tab_panel(two):  
        ui.label('Este é o conteúdo da segunda aba.')

ui.run()
```

#### **ui.stepper (com ui.step, ui.stepper_navigation)**

* **Descrição:** Um componente que guia o usuário através de um processo sequencial, passo a passo. ui.stepper é o contêiner, cada ui.step é uma etapa, e ui.stepper_navigation contém os botões para avançar/retroceder.  
* **Exemplo:**

```python
from nicegui import ui

with ui.stepper().props('vertical').classes('w-full') as stepper:  
    with ui.step('Passo 1'):  
        ui.label('Faça a primeira coisa.')  
        with ui.stepper_navigation():  
            ui.button('Próximo', on_click=stepper.next)  
    with ui.step('Passo 2'):  
        ui.label('Faça a segunda coisa.')  
        with ui.stepper_navigation():  
            ui.button('Voltar', on_click=stepper.previous).props('flat')  
            ui.button('Próximo', on_click=stepper.next)  
    with ui.step('Passo 3'):  
        ui.label('Você terminou!')  
        with ui.stepper_navigation():  
            ui.button('Concluir', on_click=lambda: ui.notify('Concluído!'))  
            ui.button('Voltar', on_click=stepper.previous).props('flat')

ui.run()
```

#### **ui.carousel (com ui.carousel_slide)**

* **Descrição:** Um componente para exibir uma série de "slides" de conteúdo em um carrossel que pode ser navegado. Baseado no QCarousel do Quasar.  
* **Inicializador:** ui.carousel(animated: bool = False, arrows: bool = False, navigation: bool = False)  
* **Exemplo:**

```python
from nicegui import ui

with ui.carousel(arrows=True, navigation=True).classes('w-64 h-32 bg-secondary rounded-box'):  
    with ui.carousel_slide():  
        ui.label('Primeiro Slide').classes('absolute-center text-white')  
    with ui.carousel_slide():  
        ui.label('Segundo Slide').classes('absolute-center text-white')  
    with ui.carousel_slide():  
        ui.label('Terceiro Slide').classes('absolute-center text-white')

ui.run()
```

#### **ui.splitter**

* **Descrição:** Divide o espaço em dois painéis redimensionáveis. Baseado no QSplitter do Quasar.  
* **Inicializador:** ui.splitter(value: float = 50, horizontal: bool = False)  
  * value: Posição inicial do divisor (0-100).  
  * horizontal: Se True, divide horizontalmente; se False, divide verticalmente.  
* **Exemplo:**

```python
from nicegui import ui

with ui.splitter(value=30).classes('h-96') as splitter:
    with splitter.before():
        ui.label('Painel Esquerdo')
        ui.button('Botão 1')
    with splitter.after():
        ui.label('Painel Direito')
        ui.button('Botão 2')

ui.run()
```

#### **ui.separator**

* **Descrição:** Uma linha divisória para separar visualmente seções de conteúdo. Baseado no QSeparator do Quasar.  
* **Inicializador:** ui.separator()  
* **Exemplo:**

```python
from nicegui import ui

ui.label('Seção 1')
ui.separator()
ui.label('Seção 2')
ui.separator().props('color=primary')
ui.label('Seção 3')

ui.run()
```

#### **ui.space**

* **Descrição:** Elemento de espaçamento flexível que empurra elementos adjacentes para as extremidades. Baseado no QSpace do Quasar.  
* **Exemplo:**

```python
from nicegui import ui

with ui.row().classes('w-full'):
    ui.button('Esquerda')
    ui.space()
    ui.button('Direita')

ui.run()
```

### **Capítulo 7: Elementos de Página e Navegação**

Este capítulo cobre elementos estruturais que definem o layout geral da página e facilitam a navegação.

#### **ui.header**

* **Descrição:** Cabeçalho fixo da página. Baseado no QHeader do Quasar.  
* **Exemplo:**

```python
from nicegui import ui

with ui.header().classes('bg-primary text-white'):
    with ui.row().classes('w-full items-center'):
        ui.button(icon='menu').props('flat')
        ui.label('Minha Aplicação').classes('text-h6')
        ui.space()
        ui.button(icon='account_circle').props('flat round')

ui.label('Conteúdo principal da página')

ui.run()
```

#### **ui.footer**

* **Descrição:** Rodapé da página. Baseado no QFooter do Quasar.  
* **Exemplo:**

```python
from nicegui import ui

ui.label('Conteúdo da página')

with ui.footer().classes('bg-grey-8 text-white'):
    ui.label('© 2024 Minha Empresa. Todos os direitos reservados.')

ui.run()
```

#### **ui.left_drawer / ui.right_drawer**

* **Descrição:** Gavetas laterais que podem ser abertas/fechadas. Baseadas no QDrawer do Quasar.  
* **Exemplo:**

```python
from nicegui import ui

with ui.left_drawer().classes('bg-blue-100') as left_drawer:
    ui.label('Menu Lateral')
    ui.separator()
    ui.button('Item 1', on_click=lambda: ui.notify('Item 1')).props('flat align=left').classes('w-full')
    ui.button('Item 2', on_click=lambda: ui.notify('Item 2')).props('flat align=left').classes('w-full')

with ui.header():
    ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
    ui.label('Aplicação com Drawer')

ui.label('Conteúdo principal')

ui.run()
```

#### **ui.page_sticky**

* **Descrição:** Elemento que permanece fixo em uma posição específica da tela. Baseado no QPageSticky do Quasar.  
* **Exemplo:**

```python
from nicegui import ui

ui.label('Conteúdo da página')

with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
    ui.button(icon='add', on_click=lambda: ui.notify('FAB clicado!')).props('fab color=accent')

ui.run()
```

#### **ui.toolbar**

* **Descrição:** Barra de ferramentas para agrupar ações relacionadas. Baseado no QToolbar do Quasar.  
* **Exemplo:**

```python
from nicegui import ui

with ui.toolbar().classes('bg-primary text-white'):
    ui.button(icon='menu').props('flat')
    ui.label('Toolbar Title').classes('text-h6')
    ui.space()
    ui.button(icon='search').props('flat')
    ui.button(icon='more_vert').props('flat')

ui.run()
```

#### **ui.breadcrumbs**

* **Descrição:** Navegação em migalhas para mostrar a hierarquia da página atual. Baseado no QBreadcrumbs do Quasar.  
* **Exemplo:**

```python
from nicegui import ui

with ui.breadcrumbs():
    ui.breadcrumb_item('Home', icon='home')
    ui.breadcrumb_item('Products', icon='inventory')
    ui.breadcrumb_item('Electronics', icon='devices')
    ui.breadcrumb_item('Smartphones')

ui.run()
```

#### **ui.pagination**

* **Descrição:** Controles de paginação para navegar entre páginas de dados. Baseado no QPagination do Quasar.  
* **Exemplo:**

```python
from nicegui import ui

pagination = ui.pagination(1, max=10, direction_links=True, boundary_links=True)
ui.label().bind_text_from(pagination, 'value', lambda v: f'Página atual: {v}')

ui.run()
```

### **Capítulo 8: Visualização de Dados e Mídia**

Este capítulo foca em elementos projetados para exibir dados estruturados, gráficos e conteúdo de mídia.

#### **Tabelas**

O NiceGUI oferece duas opções principais para exibir dados tabulares, cada uma com seus pontos fortes.

##### **ui.table**

* **Descrição:** Uma tabela rica em recursos, baseada no componente QTable do Quasar. É adequada para a maioria dos casos de uso de tabelas, oferecendo paginação, seleção, ordenação e filtragem do lado do cliente.  
* **Inicializador:** ui.table(columns: list[dict], rows: list[dict], row_key: str = 'id', selection: str | None = None, pagination: int | dict | None = None, on_select: Callable | None = None)  
  * columns: Uma lista de dicionários, onde cada dicionário define uma coluna (ex: {'name': 'nome', 'label': 'Nome', 'field': 'nome', 'sortable': True}).  
  * rows: Uma lista de dicionários, onde cada dicionário representa uma linha.  
  * selection: Pode ser 'single' ou 'multiple' para habilitar a seleção de linhas.  
  * pagination: Um inteiro para o número de linhas por página, ou um dicionário para configuração avançada.  
* **Exemplo:**

```python
from nicegui import ui

columns = [
    {'name': 'name', 'label': 'Nome', 'field': 'name', 'required': True, 'align': 'left'},
    {'name': 'age', 'label': 'Idade', 'field': 'age', 'sortable': True},
]
rows = [
    {'name': 'Alice', 'age': 18},
    {'name': 'Bob', 'age': 21},
    {'name': 'Carol'},
]

table = ui.table(columns=columns, rows=rows, row_key='name', selection='single',  
               on_select=lambda e: ui.notify(f"Selecionado: {e.selection}"))

ui.run()
```

##### **ui.aggrid**

* **Descrição:** Um wrapper para a poderosa biblioteca de data grid **AG Grid**. É a escolha ideal para cenários de dados complexos, grandes volumes de dados e funcionalidades avançadas como filtragem por coluna, edição in-loco, agrupamento e renderização customizada.  
* **Inicializador:** ui.aggrid(options: dict, html_columns: list[int] = [], theme: str = 'balham')  
  * options: Um dicionário que define a configuração completa do AG Grid, incluindo columnDefs (definições de coluna) e rowData (dados da linha).  
  * html_columns: Uma lista de índices de colunas que devem ser renderizadas como HTML bruto.  
* **Métodos Notáveis:**  
  * from_pandas(df): Método de classe para criar uma grade diretamente de um DataFrame Pandas.  
  * from_polars(df): Método de classe para criar uma grade a partir de um DataFrame Polars.  
  * get_selected_rows(): Retorna as linhas selecionadas.  
  * .on(event_type, handler): Ouve eventos específicos do AG Grid.  
* **Exemplo:**

```python
from nicegui import ui  
import pandas as pd

data = {'nome': ['Alice', 'Bob'], 'preco': [19.99, 29.99]}  
df = pd.DataFrame(data)

ui.aggrid.from_pandas(df).classes('max-h-40')

# Exemplo com opções customizadas  
grid_options = {  
    'columnDefs': [
        {'headerName': 'Nome', 'field': 'nome'},
        {'headerName': 'Preço', 'field': 'preco'},
    ],  
    'rowData': [
        {'nome': 'Produto A', 'preco': 19.99},
        {'nome': 'Produto B', 'preco': 29.99},
    ],  
    'rowSelection': 'multiple',  
}  
ui.aggrid(grid_options)

ui.run()
```

#### **Gráficos**

O NiceGUI se integra com várias bibliotecas de plotagem populares, oferecendo flexibilidade para diferentes necessidades de visualização.

##### **ui.echart**

* **Descrição:** Um wrapper para a biblioteca Apache ECharts, uma ferramenta de visualização de dados extremamente poderosa e flexível. É a solução de gráficos recomendada na maioria dos casos devido à sua riqueza de tipos de gráficos, interatividade e opções de personalização.  
* **Inicializador:** ui.echart(options: dict, on_point_click: Callable | None = None)  
  * options: Um dicionário Python que corresponde diretamente à estrutura de opções do ECharts.  
  * on_point_click: Um callback acionado quando um ponto de dados no gráfico é clicado.  
* **Exemplo:**

```python
from nicegui import ui

options = {  
    'xAxis': {'type': 'category', 'data': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']},  
    'yAxis': {'type': 'value'},  
    'series': [{'type': 'bar', 'data': [120, 200, 150, 80, 70]}]  
}

chart = ui.echart(options, on_point_click=ui.notify).classes('w-full h-64')

def update_chart():  
    chart.options['series'][0]['data'] = [x + 10 for x in chart.options['series'][0]['data']]
    chart.update()

ui.button('Atualizar', on_click=update_chart)

ui.run()
```

O ECharts no NiceGUI também suporta propriedades dinâmicas (prefixando a chave com :) para passar funções JavaScript como formatadores, e a aplicação de temas customizados.

##### **ui.highchart**

* **Descrição:** Um wrapper para a biblioteca Highcharts, outra opção popular para gráficos interativos.  
* **Inicializador:** ui.highchart(options: dict, type: str = 'chart', extras: list[str] = [])  
* **Exemplo:**

```python
from nicegui import ui

options = {  
    'title': {'text': 'Vendas Mensais'},  
    'xAxis': {'categories': ['Jan', 'Fev', 'Mar']},  
    'series': [{'name': 'Vendas', 'data': [1000, 1200, 900]}]  
}  
ui.highchart(options).classes('w-full h-64')

ui.run()
```

##### **ui.line_plot**

* **Descrição:** Um gráfico de linhas simples e leve, otimizado para atualizações de dados em alta frequência (streaming). É menos rico em recursos que o ECharts, mas muito mais performático para visualização em tempo real.  
* **Inicializador:** ui.line_plot(n: int = 1, limit: int = 100, update_every: int = 1)  
* **Métodos Notáveis:**  
  * .push(data): Adiciona novos pontos de dados ao gráfico.  
* **Exemplo:**

```python
from nicegui import ui  
import random

line_plot = ui.line_plot(n=2, limit=20, update_every=5).classes('w-full h-64')

def add_data():  
    line_plot.push([random.random(), random.random()])

ui.timer(0.1, add_data)

ui.run()
```

##### **ui.pyplot**

* **Descrição:** Um wrapper para a biblioteca Matplotlib, o padrão de fato para plotagem científica em Python. Permite que gráficos Matplotlib existentes sejam renderizados em uma aplicação NiceGUI.  
* **Uso:** Use como um gerenciador de contexto with. O código Matplotlib (usando pyplot) é executado dentro do bloco.  
* **Exemplo:**

```python
from nicegui import ui  
import numpy as np

with ui.pyplot(figsize=(3, 2)):  
    import matplotlib.pyplot as plt  
    x = np.linspace(0, 10, 100)  
    y = np.sin(x)  
    plt.plot(x, y)

ui.run()
```

A importação do Matplotlib pode ser desativada globalmente com a variável de ambiente MATPLOTLIB=false para economizar recursos se não for usada.

#### **Mídia**

##### **ui.image**

* **Descrição:** Exibe uma imagem. A fonte pode ser uma URL, um caminho para um arquivo local, uma string Base64 ou um objeto PIL.Image.  
* **Inicializador:** ui.image(source: str | Path | 'PIL.Image')  
* **Exemplo:**

```python
from nicegui import ui

# A partir de uma URL  
ui.image('https://picsum.photos/id/237/200/300')

# A partir de um arquivo local (requer que 'logo.png' exista)  
# ui.image('logo.png')

ui.run()
```

##### **ui.interactive_image**

* **Descrição:** Um elemento poderoso que exibe uma imagem e permite sobrepor conteúdo SVG, além de capturar eventos de mouse (cliques, movimentos) na imagem. Ideal para criar interfaces de anotação, mapas de calor ou qualquer interação baseada em coordenadas de imagem.  
* **Inicializador:** ui.interactive_image(source: str, on_mouse: Callable, events: list[str] = ['click'], cross: bool = False)  
  * on_mouse: Callback que recebe um MouseEventArguments com informações sobre o evento.  
  * content: Conteúdo SVG a ser sobreposto.  
* **Exemplo:**

```python
from nicegui import ui  
from nicegui.events import MouseEventArguments

def handle_mouse(e: MouseEventArguments):  
    if e.type == 'mousedown':  
        # Adiciona um círculo vermelho onde o usuário clicou  
        image.content += f'<circle cx="{e.image_x}" cy="{e.image_y}" r="5" fill="red" />'  
        image.update()

image = ui.interactive_image('https://picsum.photos/id/565/640/360',  
                           on_mouse=handle_mouse, events=['mousedown'])

ui.run()
```

##### **ui.audio / ui.video**

* **Descrição:** Incorpora um player de áudio ou vídeo HTML5 na página.  
* **Inicializador:** ui.audio(src: str, controls: bool = True, autoplay: bool = False, muted: bool = False) e ui.video(src: str,...)  
* **Exemplo:**

```python
from nicegui import ui

# URL de exemplo  
audio_url = 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'  
video_url = 'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4'

ui.audio(audio_url)  
ui.video(video_url).classes('w-64')

ui.run()
```

##### **ui.avatar**

* **Descrição:** Exibe um pequeno ícone, letra ou imagem, geralmente para representar um usuário. Baseado no QAvatar do Quasar.  
* **Inicializador:** ui.avatar(icon: str | None = None, color: str | None = 'primary', text_color: str | None = 'white', size: str | None = None)  
  * icon: Nome de um ícone do Material Icons ou um caminho de imagem prefixado com img:.  
* **Exemplo:**

```python
from nicegui import ui

with ui.row().classes('items-center gap-2'):  
    ui.avatar('person', text_color='white')  
    ui.avatar(icon='img:https://robohash.org/ui', size='lg')  
    ui.avatar(color='red', text_color='white', icon='A')

ui.run()
```

### **Capítulo 9: Texto, Marcação e Código**

Este capítulo cobre elementos especializados para exibir texto formatado, documentação e blocos de código.

#### **ui.markdown**

* **Descrição:** Renderiza texto formatado usando a sintaxe Markdown. É uma maneira poderosa de exibir conteúdo rico sem escrever HTML.  
* **Inicializador:** ui.markdown(content: str, extras: list[str] = ['fenced-code-blocks', 'tables'])  
  * content: A string contendo o código Markdown.  
  * extras: Uma lista de extensões da biblioteca markdown2 a serem ativadas. fenced-code-blocks (para blocos de código com ```) e tables são ativados por padrão.  
* **Exemplo:**

```python
from nicegui import ui

markdown_content = """  
# Título Principal  
Este é um parágrafo com texto em **negrito** e *itálico*.

- Item de lista 1  
- Item de lista 2

## Código
```python  
print("Olá, Markdown!")
```

| Coluna 1 | Coluna 2 |
|----------|----------|
| Dado 1   | Dado 2   |
"""  
ui.markdown(markdown_content).classes('p-4 bg-gray-100')

ui.run()
```

O ui.markdown pode ser estendido para renderizar destaque de sintaxe em blocos de código (com a extensão codehilite) e diagramas Mermaid (com a extensão mermaid).

#### **ui.html**

* **Descrição:** Renderiza uma string de HTML bruto diretamente na página. Útil como um "escape hatch" quando uma estrutura HTML específica é necessária e não há um elemento NiceGUI correspondente.  
* **Inicializador:** ui.html(content: str, tag: str = 'div')  
  * content: A string HTML a ser renderizada.  
  * tag: A tag HTML que envolverá o conteúdo.  
* **Exemplo:**

```python
from nicegui import ui

ui.html('<h1>Título em H1</h1><p>Um parágrafo com um <a href="#">link</a>.</p>')

ui.run()
```

#### **ui.mermaid**

* **Descrição:** Renderiza diagramas e fluxogramas a partir da sintaxe Mermaid, uma linguagem semelhante ao Markdown para criar visualizações.  
* **Inicializador:** ui.mermaid(content: str, config: dict | None = None)  
  * content: A string com a sintaxe do diagrama Mermaid.  
* **Exemplo:**

```python
from nicegui import ui

mermaid_syntax = """  
graph TD;  
    A[Início] --> B{Decisão};  
    B -->|Sim| C[Processo 1];  
    B -->|Não| D[Processo 2];  
    C --> E[Fim];  
    D --> E[Fim];  
"""  
ui.mermaid(mermaid_syntax)

ui.run()
```

#### **ui.restructured_text**

* **Descrição:** Renderiza texto formatado usando a sintaxe reStructuredText (RST), comumente usada na documentação Python (por exemplo, com Sphinx).  
* **Inicializador:** ui.restructured_text(content: str)  
* **Exemplo:**

```python
from nicegui import ui

rst_content = """  
================  
Título Principal  
================

Este é texto em **negrito** e *itálico*.

.. code-block:: python

   print("Olá, RST!")  
"""  
ui.restructured_text(rst_content)

ui.run()
```

#### **ui.code / ui.codemirror / ui.json_editor**

* **Descrição:** Um conjunto de elementos para exibir e editar código.  
  * ui.code: Exibe um bloco de código estático com destaque de sintaxe.  
  * ui.codemirror: Um editor de código completo no navegador, baseado no CodeMirror, com suporte a múltiplas linguagens e temas.  
  * ui.json_editor: Um editor especializado para visualizar e modificar estruturas JSON.  
* **Exemplo:**

```python
from nicegui import ui

ui.label('Código Estático (ui.code)').classes('text-h6')  
ui.code('''  
from nicegui import ui  
ui.label('Incepção de código!')  
ui.run()  
''').classes('w-full')

ui.label('Editor de Código (ui.codemirror)').classes('text-h6 mt-4')  
editor = ui.codemirror('print("Edite-me!")', language='Python').classes('h-32')

ui.label('Editor JSON (ui.json_editor)').classes('text-h6 mt-4')  
json_data = {'nome': 'Alice', 'idade': 30, 'ativa': True}  
ui.json_editor({'content': {'json': json_data}})

ui.run()
```

### **Capítulo 10: Feedback, Notificações e Progresso**

Estes elementos são essenciais para comunicar o estado da aplicação ao usuário, seja para confirmar uma ação, indicar atividade ou mostrar o progresso de uma tarefa.

#### **ui.notify**

* **Descrição:** Exibe uma mensagem de notificação transitória (também conhecida como "toast" ou "snackbar") na tela. É o método principal para fornecer feedback rápido ao usuário.  
* **Uso:** ui.notify(message: str, position: str = 'bottom', type: str | None = None,...)  
  * position: Onde na tela a notificação deve aparecer (ex: 'top', 'bottom-right').  
  * type: Tipo de notificação, que geralmente aplica uma cor e um ícone padrão (ex: 'positive', 'negative', 'warning').  
* **Exemplo:**

```python
from nicegui import ui

ui.button('Sucesso', on_click=lambda: ui.notify('Operação concluída com sucesso!', type='positive'))  
ui.button('Erro', on_click=lambda: ui.notify('Ocorreu um erro.', type='negative', position='top'))

ui.run()
```

#### **ui.tooltip**

* **Descrição:** Adiciona uma pequena dica de ferramenta que aparece quando o cursor do mouse passa sobre um elemento.  
* **Uso:** É um método chamado no elemento ao qual você deseja anexar a dica. elemento.tooltip(text: str)  
* **Exemplo:**

```python
from nicegui import ui

ui.button(icon='save').tooltip('Salvar alterações')  
ui.label('Passe o mouse aqui!').tooltip('Esta é uma dica de ferramenta informativa.')

ui.run()
```

#### **ui.spinner**

* **Descrição:** Exibe um indicador de carregamento animado para mostrar que uma operação está em andamento. Oferece vários estilos. Baseado no QSpinner do Quasar.  
* **Inicializador:** ui.spinner(type: str | None = 'default', size: str = '1em', color: str | None = 'primary')  
  * type: O estilo da animação (ex: 'dots', 'bars', 'audio').  
* **Exemplo:**

```python
from nicegui import ui

with ui.row().classes('gap-4'):  
    ui.spinner(size='lg')  
    ui.spinner('dots', size='lg', color='red')  
    ui.spinner('audio', size='lg', color='green')

ui.run()
```

#### **ui.linear_progress / ui.circular_progress**

* **Descrição:** Barras de progresso para visualizar a conclusão de uma tarefa. ui.linear_progress é uma barra horizontal, e ui.circular_progress é um anel.  
* **Inicializador:** ui.linear_progress(value: float = 0.0, show_value: bool = True) e ui.circular_progress(value: float = 0.0, show_value: bool = True)  
* **Exemplo:**

```python
from nicegui import ui

ui.label('Progresso Linear')  
slider1 = ui.slider(min=0, max=1, value=0.5)  
ui.linear_progress().bind_value_from(slider1, 'value')

ui.label('Progresso Circular')  
slider2 = ui.slider(min=0, max=1, value=0.7)  
ui.circular_progress(show_value=True).bind_value_from(slider2, 'value').classes('mx-auto')

ui.run()
```

O ui.circular_progress também pode atuar como um contêiner para aninhar outros elementos, como um botão.

#### **ui.log**

* **Descrição:** Uma área de texto otimizada para exibir logs ou mensagens de streaming. Novas mensagens são adicionadas ao final, e o log rola automaticamente, descartando as linhas mais antigas se um limite for atingido.  
* **Inicializador:** ui.log(max_lines: int | None = None)  
* **Métodos Notáveis:**  
  * .push(line: str): Adiciona uma nova linha ao log.  
  * .clear(): Limpa o log.  
* **Exemplo:**

```python
from nicegui import ui  
from datetime import datetime

log = ui.log(max_lines=10).classes('w-full h-40')  
ui.button('Adicionar ao Log', on_click=lambda: log.push(datetime.now().isoformat()))

ui.run()
```

#### **ui.skeleton**

* **Descrição:** Placeholder de carregamento que simula o layout do conteúdo enquanto está sendo carregado. Baseado no QSkeleton do Quasar.  
* **Inicializador:** ui.skeleton(type: str = 'rect', animation: str = 'pulse')  
* **Exemplo:**

```python
from nicegui import ui

with ui.row().classes('gap-4'):
    ui.skeleton(type='circle', size='50px')
    with ui.column():
        ui.skeleton(type='rect', width='200px', height='20px')
        ui.skeleton(type='rect', width='150px', height='20px')

ui.run()
```

#### **ui.timeline**

* **Descrição:** Exibe eventos em uma linha do tempo cronológica. Baseado no QTimeline do Quasar.  
* **Exemplo:**

```python
from nicegui import ui

with ui.timeline(color='primary', side='right'):
    with ui.timeline_entry(heading=True):
        ui.label('Timeline Header')
    
    with ui.timeline_entry(title='Event 1', subtitle='Feb 22', icon='event'):
        ui.label('First event description')
    
    with ui.timeline_entry(title='Event 2', subtitle='Feb 21', icon='done'):
        ui.label('Second event description')

ui.run()
```

### **Capítulo 11: Elementos Avançados e de Nicho**

Este capítulo explora componentes mais especializados que atendem a casos de uso específicos, como visualização 3D, mapas interativos e controle por joystick.

#### **ui.scene**

* **Descrição:** Um elemento poderoso que renderiza uma cena 3D interativa no navegador usando a biblioteca three.js (WebGL). Permite criar, manipular e interagir com objetos 3D diretamente do Python.  
* **Inicializador:** ui.scene(width: int, height: int, on_click: Callable | None = None)  
* **Uso:** Use como um gerenciador de contexto with. Dentro do bloco, você pode adicionar objetos à cena (ex: scene.box(), scene.sphere(), scene.stl()).  
* **Exemplo:**

```python
from nicegui import ui

with ui.scene(width=280, height=220) as scene:  
    scene.box().move(x=0, y=0, z=1)  
    scene.sphere().move(x=2, y=1, z=1).color('red')  
    # Carrega um arquivo STL local (requer que o arquivo exista)  
    # scene.stl('path/to/your/model.stl').scale(0.1)

ui.button('Adicionar Caixa', on_click=lambda: scene.box().move(z=3))

ui.run()
```

#### **ui.joystick**

* **Descrição:** Cria um joystick virtual na tela, útil para controlar robôs, personagens em jogos ou qualquer coisa que exija entrada de direção.  
* **Inicializador:** ui.joystick(on_move: Callable | None = None, on_end: Callable | None = None, color: str | None = 'blue')  
  * on_move: Callback acionado continuamente enquanto o joystick é movido. Recebe um evento com e.x e e.y.  
  * on_end: Callback acionado quando o joystick é solto.  
* **Exemplo:**

```python
from nicegui import ui

ui.joystick(on_move=lambda e: coordinates.set_text(f'x: {e.x:.2f}, y: {e.y:.2f}'),  
             on_end=lambda e: coordinates.set_text('Centro'))  
coordinates = ui.label('Centro')

ui.run()
```

#### **ui.leaflet**

* **Descrição:** Incorpora um mapa interativo usando a popular biblioteca Leaflet.js. Permite exibir marcadores, polígonos e capturar eventos de mapa.  
* **Inicializador:** ui.leaflet(center: tuple[float, float] = (0, 0), zoom: int = 13, draw_control: bool = False)  
* **Métodos Notáveis:**  
  * .marker(latlng): Adiciona um marcador no mapa.  
  * .tile_layer(url_template, options): Adiciona uma camada de mapa customizada.  
* **Exemplo:**

```python
from nicegui import ui

# Coordenadas do Cristo Redentor, Rio de Janeiro  
map_center = (-22.9519, -43.2105)  
map = ui.leaflet(center=map_center, zoom=15).classes('w-full h-96')  
map.marker(latlng=map_center)

ui.run()
```

#### **ui.tree**

* **Descrição:** Exibe dados hierárquicos em uma estrutura de árvore expansível e colapsável. Útil para navegadores de arquivos, organogramas, etc.  
* **Inicializador:** ui.tree(nodes: list[dict], node_key: str = 'id', label_key: str = 'label', children_key: str = 'children', on_select: Callable | None = None)  
* **Exemplo:**

```python
from nicegui import ui

nodes = [
    {
        'id': 'root',
        'label': 'Root',
        'icon': 'folder',
        'children': [
            {'id': 'docs', 'label': 'Documents', 'icon': 'folder', 'children': [
                {'id': 'readme.md', 'label': 'readme.md', 'icon': 'description'}
            ]},
            {'id': 'imgs', 'label': 'Images', 'icon': 'folder', 'children': [
                {'id': 'cat.jpg', 'label': 'cat.jpg', 'icon': 'image'}
            ]}
        ]
    }
]
ui.tree(nodes, label_key='label', on_select=lambda e: ui.notify(f"Selecionado: {e.value}"))

ui.run()
```

#### **ui.chat_message**

* **Descrição:** Um componente de UI pré-estilizado para exibir uma única mensagem em uma interface de chat. Baseado no QChatMessage do Quasar.  
* **Inicializador:** ui.chat_message(text: str | list[str], name: str | None = None, stamp: str | None = None, avatar: str | None = None, sent: bool = False)  
  * text: O corpo da mensagem. Pode ser uma lista de strings para mensagens com múltiplas partes.  
  * name: O nome do autor.  
  * stamp: Um carimbo de data/hora.  
  * avatar: URL para a imagem do avatar.  
  * sent: Se True, estiliza a mensagem como enviada pelo usuário atual (geralmente alinhada à direita).  
* **Exemplo:**

```python
from nicegui import ui

with ui.column().classes('w-full items-stretch'):  
    ui.chat_message('Olá! Como posso ajudar?',  
                    name='Assistente', avatar='https://robohash.org/assistente')  
    ui.chat_message('Eu gostaria de saber mais sobre o NiceGUI.',  
                    name='Usuário', sent=True, avatar='https://robohash.org/usuario')

ui.run()
```

---

## **Parte III: Tópicos Avançados e Padrões de Aplicação**

Esta parte transcende a referência de componentes individuais para focar em como combinar as funcionalidades do NiceGUI para construir aplicações robustas, escaláveis e complexas. Abordaremos a estruturação de projetos, interação com o backend, personalização profunda e as melhores práticas de implantação.

### **Capítulo 12: Estruturando Aplicações Complexas**

À medida que uma aplicação cresce, uma estrutura de código bem organizada torna-se essencial para a manutenibilidade. Este capítulo aborda os recursos do NiceGUI para gerenciar essa complexidade.

#### **Roteamento Multi-Página**

O NiceGUI possui um sistema de roteamento integrado que permite a criação tanto de Aplicações de Página Única (SPAs) quanto de aplicações web com múltiplas páginas tradicionais. O roteamento é definido usando o decorador @ui.page.

* **Definindo Páginas:** Cada função decorada com @ui.page('/caminho') define um novo endpoint e o conteúdo que será renderizado quando esse caminho for acessado.  
* **Passando Argumentos:** As rotas podem capturar parâmetros da URL, de forma semelhante ao FastAPI.

```python
from nicegui import ui

@ui.page('/')  
def pagina_inicial():  
    ui.label('Bem-vindo à Página Inicial!')  
    ui.link('Ver Perfil do Usuário 123', '/user/123')  
    ui.link('Ver Perfil do Usuário 456', '/user/456')

@ui.page('/user/{user_id}')  
def pagina_de_perfil(user_id: int):  
    ui.label(f'Exibindo perfil para o usuário com ID: {user_id}')  
    ui.link('Voltar para a página inicial', '/')

ui.run()
```

Neste exemplo, a rota /user/{user_id} captura o ID da URL e o passa como um argumento para a função pagina_de_perfil.

#### **Gerenciamento de Sessão e Autenticação**

O gerenciamento de estado por usuário é um recurso central, crucial para funcionalidades como login e personalização. O NiceGUI facilita isso através do objeto app.storage.user, que é um dicionário persistente atrelado à sessão do navegador do usuário.

O padrão de autenticação típico envolve:

1. Apresentar uma página de login (/login).  
2. Quando o usuário insere as credenciais corretas, definir um valor no armazenamento da sessão, como app.storage.user['authenticated'] = True.  
3. Em outras páginas, verificar a existência e o valor dessa chave. Se o usuário não estiver autenticado, redirecioná-lo para a página de login.

```python
from nicegui import app, ui  
from fastapi.responses import RedirectResponse

# O armazenamento é limpo a cada reinicialização do servidor para este exemplo.  
# Em uma aplicação real, você validaria contra um banco de dados.  
app.storage.user['authenticated'] = False

@ui.page('/')  
def pagina_principal():  
    if not app.storage.user.get('authenticated'):  
        return RedirectResponse('/login')  
    with ui.column().classes('absolute-center items-center'):  
        ui.label(f"Bem-vindo, usuário autenticado!").classes('text-2xl')  
        def logout():  
            app.storage.user['authenticated'] = False  
            ui.navigate.to('/login')  
        ui.button('Logout', on_click=logout)

@ui.page('/login')  
def pagina_login():  
    if app.storage.user.get('authenticated'):  
        return RedirectResponse('/')  
    def tentar_login():  
        if password.value == 'secreto':  
            app.storage.user['authenticated'] = True  
            ui.navigate.to('/')  
        else:  
            ui.notify('Senha incorreta', color='negative')  
    with ui.card().classes('absolute-center'):  
        ui.label('Login').classes('text-h6')  
        username = ui.input('Usuário').props('disabled')  # desabilitado para simplicidade  
        password = ui.input('Senha', password=True)  
        ui.button('Entrar', on_click=tentar_login)

ui.run(storage_secret='sua-chave-secreta-muito-longa')  # Necessário para app.storage.user
```

#### **Armazenamento Persistente**

Como visto, app.storage é a ferramenta para persistência. Por padrão, ele usa arquivos locais armazenados em um diretório .nicegui. Isso funciona bem para desenvolvimento e para aplicações de instância única.

No entanto, para implantações em produção que envolvem múltiplos processos de trabalho (workers) ou instâncias atrás de um balanceador de carga, um armazenamento local compartilhado não é viável. Para esses cenários, o NiceGUI pode ser configurado para usar um servidor **Redis** como backend de armazenamento. Isso permite que todas as instâncias da aplicação compartilhem o mesmo estado de sessão.

A configuração é feita através de variáveis de ambiente:

* NICEGUI_REDIS_URL: A URL de conexão do seu servidor Redis (ex: redis://localhost:6379).  
* NICEGUI_REDIS_KEY_PREFIX: Um prefixo opcional para as chaves armazenadas no Redis, para evitar colisões.

Quando a variável NICEGUI_REDIS_URL é definida, o app.storage passa a usar o Redis de forma transparente, sem necessidade de alterar o código da aplicação.

#### **Modularização de Código**

Para projetos grandes, colocar toda a UI em um único arquivo main.py rapidamente se torna insustentável. O NiceGUI encoraja a modularização, que é a prática de dividir a UI em componentes lógicos e reutilizáveis, cada um em seu próprio arquivo Python.

O padrão comum é criar funções que constroem uma parte da UI e, em seguida, importar e chamar essas funções na página principal.

**Exemplo (meu_modulo_ui.py):**

```python
# meu_modulo_ui.py  
from nicegui import ui

def criar_cartao_de_perfil(nome: str, cargo: str):  
    with ui.card():  
        ui.label(nome).classes('text-h6')  
        ui.label(cargo).classes('text-subtitle2')  
        ui.button('Contato')
```

**Exemplo (main.py):**

```python
# main.py  
from nicegui import ui  
from meu_modulo_ui import criar_cartao_de_perfil

@ui.page('/')  
def pagina_principal():  
    ui.label('Equipe').classes('text-h4')  
    with ui.row():  
        criar_cartao_de_perfil('Alice', 'Engenheira de Software')  
        criar_cartao_de_perfil('Bob', 'Designer de Produto')

ui.run()
```

Essa abordagem promove a reutilização de código, melhora a legibilidade e facilita o trabalho em equipe em projetos maiores.

### **Capítulo 13: Interação Profunda com o Backend**

Este capítulo explora como o NiceGUI lida com tarefas que vão além da resposta direta a eventos do usuário, como operações periódicas, cálculos demorados e integração com outras partes de um sistema backend.

#### **Timers e Tarefas Periódicas**

Para aplicações que precisam atualizar dados em tempo real, como dashboards de monitoramento ou relógios, o ui.timer é a ferramenta essencial. Ele permite agendar a execução de uma função em intervalos regulares.

* **Inicializador:** ui.timer(interval: float, callback: Callable, active: bool = True, once: bool = False)  
  * interval: O intervalo em segundos entre as chamadas do callback. Pode ser tão baixo quanto 0.01 (10ms).  
  * callback: A função (síncrona ou assíncrona) a ser executada.

```python
from nicegui import ui  
from datetime import datetime

clock_label = ui.label().classes('text-h4')

# Atualiza o label a cada segundo  
ui.timer(1.0, lambda: clock_label.set_text(datetime.now().strftime('%H:%M:%S')))

ui.run()
```

#### **Executando Tarefas Longas**

Uma regra de ouro em aplicações de UI é nunca bloquear o loop de eventos principal. Se um callback de botão executa uma tarefa que leva vários segundos (como uma consulta complexa a um banco de dados, uma chamada de API externa ou um cálculo pesado), a interface do usuário congelará e ficará sem resposta.

A solução do NiceGUI para isso é o módulo background_tasks. A função background_tasks.create() permite que você execute uma corrotina async em segundo plano, liberando imediatamente o loop de eventos para continuar processando interações da UI.

```python
from nicegui import ui, background_tasks  
import time

async def calculo_demorado():  
    ui.notify('Iniciando cálculo em segundo plano...')  
    # Simula um trabalho pesado  
    for i in range(5):  
        time.sleep(1)  
        print(f'Progresso do cálculo: {i+1}/5')  
    ui.notify('Cálculo concluído!', type='positive')

def iniciar_tarefa():  
    background_tasks.create(calculo_demorado())

ui.button('Iniciar Tarefa Demorada', on_click=iniciar_tarefa)  
ui.button('Botão Interativo', on_click=lambda: ui.notify('A UI está responsiva!'))

ui.run()
```

Enquanto o "cálculo demorado" está em execução, o "Botão Interativo" permanece totalmente funcional. Os exemplos "Progress" e "Global Worker" demonstram padrões para fornecer feedback de progresso de tarefas em segundo plano para o usuário.

#### **Integração com FastAPI**

Como o NiceGUI é construído sobre o FastAPI, ele expõe o objeto app do FastAPI subjacente para uso direto. Isso significa que você pode adicionar endpoints de API RESTful tradicionais à sua aplicação NiceGUI, criando um serviço híbrido que serve tanto uma UI interativa quanto uma API de dados.

Isso é feito usando os decoradores padrão do FastAPI, como @app.get() e @app.post(), no mesmo arquivo main.py.

```python
from nicegui import app, ui

# Dados de exemplo  
dados_db = {  
    'item1': {'nome': 'Produto A', 'preco': 19.99},  
    'item2': {'nome': 'Produto B', 'preco': 29.99},  
}

# Endpoint da API RESTful usando o app do FastAPI  
@app.get("/api/items/{item_id}")  
def ler_item(item_id: str):  
    if item_id in dados_db:  
        return dados_db[item_id]  
    return {'erro': 'Item não encontrado'}

# Interface do NiceGUI  
@ui.page('/')  
def pagina_principal():  
    ui.label('Aplicação Híbrida UI + API')  
    ui.label('Acesse /api/items/item1 para ver os dados da API.')

ui.run()
```

Esta integração perfeita é extremamente poderosa, permitindo que a mesma aplicação sirva dados para sua própria UI e para outros serviços ou clientes externos.

#### **Funções Refreshable**

O NiceGUI oferece um decorador especial @ui.refreshable que permite recriar seletivamente apenas uma parte da UI quando necessário, sem recarregar toda a página.

```python
import random
from nicegui import ui

numbers = []

@ui.refreshable
def number_ui():
    ui.label(', '.join(str(n) for n in sorted(numbers)))

def add_number():
    numbers.append(random.randint(0, 100))
    number_ui.refresh()

number_ui()
ui.button('Add random number', on_click=add_number)

ui.run()
```

#### **Tarefas CPU-bound**

Para operações que são computacionalmente intensivas, o NiceGUI oferece a função run.cpu_bound() que executa código em um processo separado, evitando bloquear o loop de eventos principal.

```python
import time
from nicegui import run, ui

def compute_sum(a: float, b: float) -> float:
    time.sleep(1)  # simulate a long-running computation
    return a + b

async def handle_click():
    result = await run.cpu_bound(compute_sum, 1, 2)
    ui.notify(f'Sum is {result}')

ui.button('Compute', on_click=handle_click)

ui.run()
```

#### **Captura de Eventos de Teclado**

O NiceGUI oferece suporte abrangente para capturar eventos de teclado globalmente na aplicação.

```python
from nicegui import ui
from nicegui.events import KeyEventArguments

def handle_key(e: KeyEventArguments):
    if e.key == 'f' and not e.action.repeat:
        if e.action.keyup:
            ui.notify('f was just released')
        elif e.action.keydown:
            ui.notify('f was just pressed')

keyboard = ui.keyboard(on_key=handle_key)
ui.checkbox('Track key events').bind_value_to(keyboard, 'active')

ui.run()
```

### **Capítulo 14: Personalização Extrema**

Embora o NiceGUI forneça um conjunto rico de componentes ui. prontos para uso, há momentos em que é necessária uma personalização mais profunda ou a integração de funcionalidades que não estão disponíveis nativamente. Este capítulo explora as "válvulas de escape" que dão ao desenvolvedor controle total sobre o frontend.

#### **Acessando Componentes Quasar com ui.element**

O Quasar Framework possui centenas de componentes, e nem todos têm um wrapper ui. dedicado no NiceGUI. A função ui.element é a ponte que permite instanciar qualquer componente Quasar (ou qualquer tag HTML) diretamente pelo seu nome.

* **Uso:** ui.element(tag_name: str)  
  * tag_name: O nome da tag do componente Quasar (ex: 'q-list', 'q-timeline') ou uma tag HTML padrão (ex: 'div', 'span').

Este método desbloqueia todo o poder do Quasar. Se você encontrar um componente na documentação do Quasar que precisa usar, ui.element é a maneira de fazê-lo.

```python
from nicegui import ui

ui.label('Exemplo de QTimeline do Quasar via ui.element').classes('text-h6')

# Usando ui.element para criar um componente QTimeline do Quasar  
with ui.element('q-timeline').props('color=secondary'):  
    with ui.element('q-timeline-entry').props('heading'):  
        ui.label('Cabeçalho da Timeline')

    with ui.element('q-timeline-entry').props('title="Evento 1" subtitle="Fevereiro 22" icon=event'):  
        ui.label('Lorem ipsum dolor sit amet...')

    with ui.element('q-timeline-entry').props('title="Evento 2" subtitle="Fevereiro 21" icon=delete'):  
        ui.label('Outro evento importante ocorreu aqui.')

ui.run()
```

Neste exemplo, estamos criando uma q-timeline e suas q-timeline-entry filhas, passando suas respectivas propriedades Quasar através do método .props().

#### **Trabalhando com Slots (.add_slot())**

O Vue.js (e, por extensão, o Quasar) usa um conceito chamado "slots" para injetar conteúdo em locais predefinidos dentro de um componente. Um componente complexo como uma tabela pode ter slots para o "cabeçalho", "corpo", "célula específica", etc. O NiceGUI expõe essa funcionalidade através do método .add_slot().

Usar with elemento: aninha conteúdo no slot padrão (default) do elemento. Para preencher um slot nomeado, usa-se with elemento.add_slot('nome_do_slot'):.

```python
from nicegui import ui

columns = [{'name': 'name', 'label': 'Nome', 'field': 'name'}]  
rows = [{'name': 'Alice'}, {'name': 'Bob'}]

table = ui.table(columns=columns, rows=rows, row_key='name')

# Preenchendo o slot 'top' da tabela para adicionar um título  
with table.add_slot('top'):  
    ui.label('Minha Tabela Customizada').classes('text-h5')

# Preenchendo o slot 'body-cell-name' para customizar como a célula do nome é renderizada  
# A sintaxe de template é Vue.js  
with table.add_slot('body-cell-name', template='<q-td :props="props"><q-badge color="blue">{{ props.value }}</q-badge></q-td>'):  
    pass  # O template Vue faz todo o trabalho aqui

ui.run()
```

O uso de slots é um conceito avançado que permite um nível de personalização de componentes quase ilimitado.

#### **Criando Componentes Vue Customizados**

Para o nível máximo de personalização, o NiceGUI permite que você crie seus próprios componentes de frontend usando Vue.js e os integre perfeitamente em sua aplicação Python. Isso é útil para encapsular lógica de UI complexa ou para integrar bibliotecas JavaScript de terceiros.

O processo envolve:

1. Criar um arquivo .js ou .vue que defina o componente Vue.  
2. Em seu código Python, criar uma classe que herda de ui.element e associá-la ao seu arquivo de componente.  
3. Usar sua nova classe como qualquer outro elemento ui..

Os exemplos "Custom Vue Component" e "Signature Pad" no repositório do NiceGUI são as referências definitivas para este processo. O exemplo "Signature Pad" demonstra inclusive como gerenciar dependências de pacotes NPM para o seu componente customizado usando um arquivo package.json. Esta é a "válvula de escape" final, garantindo que qualquer funcionalidade que possa ser implementada em um navegador moderno possa ser integrada a uma aplicação NiceGUI.

#### **Execução de JavaScript**

O NiceGUI permite executar código JavaScript arbitrário no navegador, oferecendo controle total sobre o frontend quando necessário.

```python
from nicegui import ui

def alert():
    ui.run_javascript('alert("Hello!")')

async def get_date():
    time = await ui.run_javascript('Date()')
    ui.notify(f'Browser time: {time}')

def access_elements():
    ui.run_javascript(f'getHtmlElement({label.id}).innerText += " Hello!"')

ui.button('fire and forget', on_click=alert)
ui.button('receive result', on_click=get_date)
ui.button('access elements', on_click=access_elements)
label = ui.label()

ui.run()
```

### **Capítulo 15: Configuração, Implantação e Testes**

Este capítulo final da Parte III aborda os aspectos práticos de finalizar, empacotar, implantar e testar uma aplicação NiceGUI.

#### **Parâmetros de ui.run()**

A função ui.run() que inicia a aplicação aceita vários parâmetros para configurar o comportamento do servidor e da janela (no modo nativo). Alguns dos mais importantes são:

* host: O endereço IP no qual o servidor deve escutar (padrão: '0.0.0.0' em produção, '127.0.0.1' com reload=True).  
* port: A porta do servidor (padrão: 8080).  
* title: O título da página exibido na aba do navegador (padrão: 'NiceGUI').  
* favicon: Caminho para um ícone de favoritos ou um emoji.  
* reload: Ativa ou desativa o recarregamento automático ao salvar o código (padrão: True). Essencial para desenvolvimento, deve ser False em produção.  
* native: Se True, executa a aplicação em uma janela de desktop nativa.  
* window_size: Tupla (largura, altura) para o tamanho da janela no modo nativo.  
* fullscreen: Se True, inicia a aplicação em tela cheia no modo nativo.  
* storage_secret: Uma chave secreta longa e aleatória necessária para criptografar os dados de app.storage.user.

```python
from nicegui import ui

# Configuração básica
ui.run()

# Configuração customizada
ui.run(
    host='0.0.0.0',
    port=8080,
    title='Minha Aplicação NiceGUI',
    dark=False,
    show=True,
    reload=True,  # Para desenvolvimento
    storage_secret='chave-secreta-longa'
)
```

#### **Modo Nativo e Empacotamento**

Ao executar com ui.run(native=True), o NiceGUI usa a biblioteca **PyWebView** para abrir a interface em uma janela de aplicativo de desktop, em vez de um navegador. Isso permite a criação de utilitários e pequenas aplicações de desktop multiplataforma.

```python
from nicegui import ui

# Janela nativa
ui.run(native=True)

# Janela com configurações
ui.run(
    native=True, 
    window_size=(1024, 768),
    fullscreen=False
)
```

Para distribuir essas aplicações nativas, o NiceGUI fornece um utilitário de linha de comando, nicegui-pack, que usa o **PyInstaller** para empacotar sua aplicação e suas dependências em um único arquivo executável.

```bash
# Empacota main.py em um executável chamado 'meuapp'  
nicegui-pack --onefile --name "meuapp" main.py
```

#### **Implantação com Docker e Proxy Reverso**

Para produção, a abordagem mais comum e robusta é a conteinerização com Docker. O NiceGUI é oficialmente distribuído como uma imagem Docker no Docker Hub, simplificando a implantação.

**Dockerfile:**

```dockerfile
FROM zauberzeug/nicegui:latest
COPY . /app/
EXPOSE 8080
CMD ["python", "main.py"]
```

**docker-compose.yml:**

```yaml
version: '3.8'
services:
  nicegui-app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - NICEGUI_STORAGE_PATH=/app/storage
      - NICEGUI_REDIS_URL=redis://redis:6379
    volumes:
      - ./storage:/app/storage
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

O repositório do NiceGUI contém exemplos de Dockerfile e docker-compose.yml que podem ser usados como ponto de partida. Em um cenário de produção típico, a aplicação NiceGUI é executada dentro de um contêiner e colocada atrás de um proxy reverso, como o **NGINX**. O proxy reverso é responsável por:

* **Terminação SSL/TLS:** Lidar com HTTPS, criptografando o tráfego entre o cliente e o servidor.  
* **Balanceamento de Carga:** Distribuir o tráfego entre múltiplas instâncias da aplicação NiceGUI para escalabilidade.  
* **Servir em um Sub-caminho:** Disponibilizar a aplicação em um caminho como https://meusite.com/meu-app/.

O repositório de exemplos do NiceGUI inclui configurações detalhadas para implantação com NGINX, cobrindo tanto o uso de sub-caminhos quanto a configuração de HTTPS.

#### **Framework de Testes**

Aplicações robustas exigem testes automatizados. O NiceGUI vem com um framework de testes integrado, construído sobre o popular **pytest**. Ele permite escrever testes que interagem com a UI de forma programática, verificam o estado dos elementos e garantem que a aplicação se comporte como esperado.

O exemplo "Pytests" no repositório oficial demonstra como configurar e escrever testes para uma aplicação NiceGUI, cobrindo interações como cliques de botão e verificação de texto em labels. A capacidade de testar a UI de forma confiável é um sinal da maturidade do framework e é crucial para o desenvolvimento de software de alta qualidade.

#### **Variáveis de Ambiente do NiceGUI**

A configuração do NiceGUI em diferentes ambientes (desenvolvimento, teste, produção) é frequentemente gerenciada por meio de variáveis de ambiente. A tabela a seguir consolida as principais variáveis de ambiente e suas funções, servindo como uma referência rápida para configuração e implantação.

| Variável | Padrão | Descrição |
| :---- | :---- | :---- |
| MATPLOTLIB | true | Defina como false para evitar a importação do Matplotlib e economizar recursos se a biblioteca não for usada. |
| NICEGUI_STORAGE_PATH | .nicegui | Altera o diretório para os arquivos de armazenamento locais quando o armazenamento baseado em arquivo está em uso. |
| MARKDOWN_CONTENT_CACHE_SIZE | 1000 | Define o tamanho máximo do cache na memória para snippets de conteúdo Markdown renderizados. |
| RST_CONTENT_CACHE_SIZE | 1000 | Define o tamanho máximo do cache na memória para snippets de conteúdo ReStructuredText renderizados. |
| NICEGUI_REDIS_URL | None | Fornece a URL de conexão para um servidor Redis. Se definida, o NiceGUI usará o Redis para o app.storage em vez de arquivos locais. |
| NICEGUI_REDIS_KEY_PREFIX | nicegui: | Define um prefixo para todas as chaves que o NiceGUI armazena no Redis, útil para evitar colisões em um banco de dados Redis compartilhado. |

---

## **Parte IV: Exemplos Práticos Completos**

Esta parte final do guia é dedicada a exemplos práticos e completos. A coleção de exemplos do NiceGUI não é apenas um material de aprendizado suplementar; ela é uma parte central e indispensável da documentação. Muitos padrões de design e integrações complexas são melhor compreendidos (e, em alguns casos, exclusivamente demonstrados) através desses exemplos de trabalho. Eles representam a "documentação viva" do framework, mostrando como combinar os blocos de construção dos capítulos anteriores para criar aplicações funcionais e sofisticadas.

### **Capítulo 16: Galeria de Exemplos Completos**

Cada exemplo nesta galeria será apresentado com um objetivo claro, uma lista das principais funcionalidades do NiceGUI que ele demonstra, o código-fonte completo e comentado, e uma breve análise de trechos de código importantes para destacar os padrões utilizados.

#### **Exemplo 1: Lista de Tarefas (Todo List)**

* **Objetivo:** Criar uma aplicação clássica de lista de tarefas onde os usuários podem adicionar, remover e marcar tarefas como concluídas.  
* **Funcionalidades Demonstradas:**  
  * Gerenciamento de estado explícito com uma classe de dados Python (dataclass).  
  * Uso de ui.refreshable para atualizar seletivamente uma parte da UI.  
  * Vinculação de dados bidirecional (bind_value) com ui.checkbox e ui.input.  
  * Layout com ui.card, ui.row e classes Tailwind CSS.  
  * Manipulação de eventos (on_click, on_change, keydown.enter).  
* **Código-Fonte Completo:**

```python
#!/usr/bin/env python3  
from dataclasses import dataclass, field  
from typing import Callable, List  
from nicegui import ui

@dataclass  
class TodoItem:  
    """Representa uma única tarefa na lista."""  
    name: str  
    done: bool = False

@dataclass  
class ToDoList:  
    """Gerencia a coleção de tarefas e notifica sobre mudanças."""  
    title: str  
    on_change: Callable

    items: List = field(default_factory=list)

    def add(self, name: str, done: bool = False) -> None:  
        self.items.append(TodoItem(name, done))  
        self.on_change()  # Dispara a atualização da UI

    def remove(self, item: TodoItem) -> None:  
        self.items.remove(item)  
        self.on_change()  # Dispara a atualização da UI

# A função decorada com @ui.refreshable pode ser chamada para reconstruir  
# apenas esta parte da UI, em vez de recarregar a página inteira.  
@ui.refreshable  
def todo_ui():  
    if not todos.items:  
        ui.label('A lista está vazia.').classes('mx-auto')  
        return

    # Barra de progresso mostrando a porcentagem de tarefas concluídas.  
    progress = sum(item.done for item in todos.items) / len(todos.items)  
    ui.linear_progress(progress, show_value=False)

    with ui.row().classes('justify-center w-full'):  
        ui.label(f'Concluídas: {sum(item.done for item in todos.items)}')  
        ui.label(f'Restantes: {sum(not item.done for item in todos.items)}')

    # Itera sobre os itens e cria os elementos da UI para cada um.  
    for item in todos.items:  
        with ui.row().classes('items-center w-full'):  
            # O checkbox atualiza a UI ao mudar e está vinculado ao atributo 'done' do item.  
            ui.checkbox(value=item.done, on_change=todo_ui.refresh).bind_value(item, 'done')  
            # O input permite editar o nome da tarefa e está vinculado ao atributo 'name'.  
            ui.input(value=item.name).classes('flex-grow').bind_value(item, 'name')  
            # Botão para remover o item. Usa uma lambda para capturar o item correto.  
            ui.button(on_click=lambda item=item: todos.remove(item), icon='delete').props('flat fab-mini color=grey')

# --- Lógica Principal da Aplicação ---

# Cria a instância da lista de tarefas. A função todo_ui.refresh é passada como o callback on_change.  
# Isso garante que sempre que a lista for modificada (add/remove), a UI será atualizada.  
todos = ToDoList('Minhas Tarefas do Fim de Semana', on_change=todo_ui.refresh)  
todos.add('Pedir pizza', done=True)  
todos.add('Lançar nova versão do NiceGUI')  
todos.add('Limpar a casa')  
todos.add('Ligar para a mãe')

with ui.card().classes('w-80 items-stretch mx-auto'):  
    # O título do cartão está vinculado ao título da lista de tarefas.  
    ui.label().bind_text_from(todos, 'title').classes('text-semibold text-2xl')  
    # A primeira chamada para todo_ui() para renderizar a lista inicial.  
    todo_ui()  
    # Campo de entrada para adicionar novos itens.  
    add_input = ui.input('Novo item').classes('mx-12')  
    # Adiciona um novo item ao pressionar Enter.  
    add_input.on('keydown.enter', lambda: todos.add(add_input.value))  
    # Limpa o campo de entrada após adicionar.  
    add_input.on('keydown.enter', lambda: add_input.set_value(''))

ui.run()
```

* **Análise:** Este exemplo é um paradigma para o gerenciamento de estado no NiceGUI. O estado da aplicação (todos) é um objeto Python puro (ToDoList). A UI (todo_ui) é uma representação visual desse estado. A reatividade é alcançada de duas formas: (1) bind_value para sincronização bidirecional instantânea (editar o texto no ui.input altera o .name do TodoItem) e (2) o padrão de callback on_change=todo_ui.refresh para reconstruir a lista quando itens são adicionados ou removidos, que é uma otimização de performance crucial.

#### **Exemplo 2: Dashboard Empresarial Completo**

* **Objetivo:** Criar um dashboard empresarial com métricas em tempo real, gráficos interativos e tabelas de dados.  
* **Funcionalidades Demonstradas:**  
  * Layout responsivo com header/footer  
  * Atualização automática de dados com ui.timer  
  * Múltiplos tipos de gráficos (ECharts)  
  * Integração de tabelas com dados dinâmicos  
  * Uso de cards para organização visual  
* **Código-Fonte Completo:**

```python
from nicegui import ui
import asyncio
from datetime import datetime
import random

# Dados simulados
data = {
    'sales': 12450,
    'users': 2847,
    'revenue': 45780,
    'growth': 23.5
}

@ui.refreshable
def metrics_cards():
    with ui.row().classes('w-full gap-4'):
        for metric, value in data.items():
            with ui.card().classes('flex-1'):
                with ui.card_section():
                    ui.label(metric.title()).classes('text-grey-7 text-sm')
                    ui.label(str(value)).classes('text-h4 text-weight-bold')

async def update_data():
    while True:
        await asyncio.sleep(5)
        # Simular atualização de dados
        data['sales'] += random.randint(-100, 200)
        data['users'] += random.randint(-10, 50)
        data['revenue'] += random.randint(-500, 1000)
        data['growth'] = round(random.uniform(-5, 30), 1)
        metrics_cards.refresh()

@ui.page('/')
def dashboard():
    with ui.header():
        ui.label('Dashboard Empresarial').classes('text-h5')

    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        metrics_cards()
        
        # Gráfico de vendas
        chart = ui.echart({
            'title': {'text': 'Vendas por Mês'},
            'xAxis': {'type': 'category', 'data': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai']},
            'yAxis': {'type': 'value'},
            'series': [{
                'name': 'Vendas',
                'type': 'line',
                'data': [2800, 3200, 2900, 3800, 4200],
                'smooth': True
            }]
        }).classes('w-full h-96')
        
        # Tabela de transações recentes
        transactions = [
            {'id': 1, 'client': 'Cliente A', 'value': 1250.00, 'status': 'Pago'},
            {'id': 2, 'client': 'Cliente B', 'value': 890.50, 'status': 'Pendente'},
            {'id': 3, 'client': 'Cliente C', 'value': 2100.00, 'status': 'Pago'},
        ]
        
        columns = [
            {'name': 'id', 'label': 'ID', 'field': 'id'},
            {'name': 'client', 'label': 'Cliente', 'field': 'client'},
            {'name': 'value', 'label': 'Valor', 'field': 'value'},
            {'name': 'status', 'label': 'Status', 'field': 'status'},
        ]
        
        ui.table(
            title='Transações Recentes',
            columns=columns,
            rows=transactions,
            row_key='id'
        ).classes('w-full')

# Inicia atualização automática
ui.run_with_asyncio(update_data())
ui.run()
```

#### **Exemplo 3: Sistema de Chat Interativo**

* **Objetivo:** Implementar uma interface de chat com múltiplas funcionalidades de mensageria.  
* **Funcionalidades Demonstradas:**  
  * ui.chat_message para interface de chat  
  * Scroll automático para novas mensagens  
  * Diferentes tipos de mensagem (enviada/recebida)  
  * Input com envio por Enter  
  * Avatars e timestamps  
* **Código-Fonte Completo:**

```python
from nicegui import ui
import asyncio
from datetime import datetime

messages = []

@ui.refreshable
def chat_messages():
    with ui.column().classes('w-full gap-2 max-h-96 overflow-y-auto'):
        for msg in messages:
            ui.chat_message(
                text=msg['text'],
                name=msg['user'],
                stamp=msg['time'],
                sent=msg['user'] == 'Você'
            )

async def send_message():
    if message_input.value.strip():
        # Adicionar mensagem do usuário
        messages.append({
            'text': message_input.value,
            'user': 'Você',
            'time': datetime.now().strftime('%H:%M')
        })

        user_msg = message_input.value
        message_input.value = ''
        chat_messages.refresh()
        
        # Simular resposta do bot após 1 segundo
        await asyncio.sleep(1)
        messages.append({
            'text': f'Você disse: "{user_msg}". Como posso ajudar?',
            'user': 'Bot',
            'time': datetime.now().strftime('%H:%M')
        })
        chat_messages.refresh()

@ui.page('/')
def chat_app():
    global message_input

    with ui.column().classes('w-full max-w-md mx-auto'):
        ui.label('Chat Bot').classes('text-h4 text-center mb-4')
        
        # Área de mensagens
        with ui.card().classes('w-full'):
            chat_messages()
        
        # Campo de entrada
        with ui.row().classes('w-full'):
            message_input = ui.input('Digite sua mensagem...').classes('flex-grow')
            message_input.on('keydown.enter', send_message)
            ui.button('Enviar', on_click=send_message).props('color=primary')

ui.run()
```

#### **Exemplo 4: Interface de IA para Transcrição de Áudio**

* **Objetivo:** Criar uma interface que permita upload de arquivo de áudio e transcrição usando IA.  
* **Funcionalidades Demonstradas:**  
  * ui.upload para envio de arquivos  
  * Processamento assíncrono de IA  
  * Feedback de progresso ao usuário  
  * Tratamento de erros  
* **Código-Fonte Completo:**

```python
#!/usr/bin/env python3
import io
import replicate  # Biblioteca para interagir com a API Replicate
from nicegui import ui
from nicegui.events import UploadEventArguments

# NOTA: Este exemplo requer uma chave de API da Replicate.
# Configure-a como uma variável de ambiente: export REPLICATE_API_TOKEN="..."

async def transcribe(e: UploadEventArguments):
    """
    Callback acionado pelo upload. Envia o áudio para a API e atualiza a UI.
    """
    transcription.text = 'Enviando e transcrevendo...'
    try:
        # Obtém o modelo 'whisper' da Replicate.
        model = replicate.models.get('openai/whisper')
        # Executa o modelo passando o conteúdo do arquivo de áudio.
        # A chamada.predict() é uma operação de rede demorada, por isso é 'await'.
        result = await model.predict(audio=io.BytesIO(e.content.read()))
        # Exibe a transcrição retornada pela API.
        transcription.text = result['transcription']
    except Exception as ex:
        transcription.text = f'Erro: {ex}'
        ui.notify(f'Ocorreu um erro: {ex}', color='negative')

# --- UI Principal ---
ui.label('Transcrição de Áudio com Whisper AI').classes('text-h4')
ui.label('Faça o upload de um arquivo de áudio (ex: MP3, WAV) para transcrevê-lo.')

# O componente de upload que dispara a função 'transcribe'.
ui.upload(on_upload=transcribe, auto_upload=True).props('accept=audio/*')

# Um cartão para exibir o resultado da transcrição.
with ui.card().classes('w-full mt-4'):
    ui.label('Transcrição:').classes('text-bold')
    transcription = ui.label('Aguardando upload...')

ui.run()
```

---

## **Conclusão**

NiceGUI se estabelece como uma biblioteca Python de UI notavelmente bem projetada, ocupando um nicho estratégico no ecossistema de desenvolvimento web. Sua filosofia "backend-first", construída sobre uma pilha de tecnologias modernas e robustas como FastAPI e Vue/Quasar, oferece uma proposta de valor única: a capacidade de construir aplicações web complexas e interativas com a simplicidade e a expressividade do Python.

A análise aprofundada revela que a força do NiceGUI reside em seu equilíbrio cuidadoso entre abstração e controle. Para iniciantes, ele oferece uma rampa de acesso suave, abstraindo as complexidades do desenvolvimento web. Para especialistas, ele fornece "válvulas de escape" bem definidas (.props, .classes, ui.element, componentes Vue customizados) que permitem um controle granular e a capacidade de alavancar todo o poder dos frameworks subjacentes.

O modelo de estado explícito, em contraste com a "mágica" de outras ferramentas, juntamente com seu suporte nativo a async/await, torna-o uma escolha sólida para aplicações com estado, em tempo real e orientadas a I/O. A combinação de um conjunto rico de componentes, um sistema de layout flexível, um framework de testes integrado e caminhos claros para implantação (Docker, NGINX, executáveis nativos) demonstra a maturidade e a prontidão do NiceGUI para projetos de produção.

Finalmente, a extensa galeria de exemplos não é apenas um recurso de aprendizado, mas uma parte integrante da própria documentação, estabelecendo padrões e demonstrando a vasta gama de domínios de aplicação, da robótica à inteligência artificial. Para qualquer desenvolvedor Python que deseje criar interfaces web sem se afastar do seu ecossistema de ferramentas preferido, o NiceGUI se apresenta como uma solução poderosa, elegante e excepcionalmente agradável de usar.

**Links importantes para referência:**
- **Documentação Oficial:** https://nicegui.io/documentation
- **Repositório GitHub:** https://github.com/zauberzeug/nicegui
- **Exemplos no GitHub:** https://github.com/zauberzeug/nicegui/tree/main/examples
- **Discussões da Comunidade:** https://github.com/zauberzeug/nicegui/discussions
