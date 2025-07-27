# Guia de Referência **LangChain** (Python)

Manual avançado para desenvolvimento de agentes e aplicações LLM
*(Atualizado em 25 jul 2025)*

\#\#ão-geral rápida
LangChain é um *framework* modular que padroniza o uso de modelos de linguagem, embeddings, *vector stores*, ferramentas externas e fluxos de trabalho persistentes. Desde a v0.3 ele se divide em pacotes leves (`langchain-core`, `langchain`, `langchain-community` etc.) e integra-se nativamente ao **LangGraph** (orquestração) e **LangSmith** (observabilidade) [^1][^2].


| Camada | Pacote principal | Função |
| :-- | :-- | :-- |
| Abstrações básicas | `langchain-core` | Interfaces de modelo, mensagens, *Runnable*, callbacks |
| Componentes padrão | `langchain` | *Chains*, agentes, RAG, text-splitters |
| Integrações oficiais | `langchain-openai`, `langchain-anthropic`… | Conectores de provedores de modelo/BD |
| Integrações da comunidade | `langchain-community` | Ferramentas de terceiros mantidas pela comunidade [^3] |

## Instalação mínima

```bash
pip install -U "langchain[openai]" langgraph langsmith
```

Para evitar dependências pesadas, instale integrações específicas somente quando necessário (ex.: `pip install langchain-google-genai`) [^4][^5].

## 1. Núcleo de Execução – **Runnable**

Todos os objetos executáveis (modelos, *prompts*, *retrievers*, *parsers*, *chains*) herdam de `Runnable` e podem ser:

* **Invocados**  `.invoke(input)`
* **Transmissão síncrona** `.stream(input)`
* **Transmissão assíncrona** `.astream(input)`
* **Composição** por “|” (pipe) ou `RunnableSequence`.

```python
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

prompt = PromptTemplate.from_template("Traduza para francês:\n{text}")
llm    = ChatOpenAI(model="gpt-4o-mini", temperature=0)

chain = prompt | llm
for token in chain.stream({"text": "Bom dia"}):
    print(token, end="", flush=True)
```

O método `stream` envia tokens conforme são gerados, reduzindo a latência percebida [^6][^7].

## 2. Modelos e *Prompts*

### 2.1 Modelos de Chat

```python
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, streaming=True)
```

Parâmetros importantes:


| Parâmetro | Descrição |
| :-- | :-- |
| `model` | Nome do endpoint |
| `temperature` | Criatividade da saída |
| `streaming` | Permite fluxo token-a-token [^6] |

### 2.2 Prompt Templates

Use `ChatPromptTemplate` com **placeholders** de mensagem.

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [("system", "Você é um tradutor profissional."),
     ("human", "{texto_pt}"),
     MessagesPlaceholder("exemplos")]  # few-shot opcional
)
```


## 3. **Chains**

| Tipo | Para que serve | Classe |
| :-- | :-- | :-- |
| LLMChain | Chamada única ao modelo | `LLMChain` |
| Sequential | Pipeline linear | `SimpleSequentialChain` |
| RetrievalQA | RAG básico | `RetrievalQA` |
| Conversational | Chat com memória | `ConversationChain` |

Exemplo RAG rápido:

```python
from langchain.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA

docs = [Document(page_content="Python é uma linguagem...")]
store = FAISS.from_documents(docs, OpenAIEmbeddings())

qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-4o-mini"),
        chain_type="stuff",
        retriever=store.as_retriever(k=3)
)
qa.invoke({"query": "O que é Python?"})
```


## 4. **Memória**

### 4.1 Camada v0.3 – **LangGraph Persistence**

Recomendada para conversas longas, múltiplos usuários e retomada após falhas [^8][^9].

```python
from langgraph.prebuilt import register_llm_history
from langgraph.memory import GraphMemory

memory = GraphMemory.from_documents_backend("sqlite:///mem.db")
agent  = some_chain | register_llm_history(memory)
```


### 4.2 Memórias clássicas

| Classe | Uso | Observação |
| :-- | :-- | :-- |
| `ConversationBufferMemory` | Histórico completo | Volátil |
| `ConversationBufferWindowMemory` | Janela deslizante | Limite de *turns* |
| `ConversationSummaryMemory` | Resume longas conversas | Requer LLM |

[^10][^11][^12]

## 5. **Agentes**

### 5.1 ReAct pronto

```python
from langgraph.prebuilt import create_react_agent
from langchain.tools import Tool

def pesquisar_web(q): ...
tools = [Tool(name="Busca", func=pesquisar_web, description="...")]

agent = create_react_agent(
    model = "anthropic:claude-3-7-sonnet-latest",
    tools = tools,
    prompt = "Você é um assistente..."
)
print(agent.invoke({"messages":[{"role":"user","content":"Quem foi Ada Lovelace?"}]}))
```

`create_react_agent` já inclui streaming, *tool calling* e observabilidade via LangSmith [^13].

### 5.2 Toolkit GitHub

O `GithubToolkit` permite agentes que abrem PRs, comentam *issues* etc. [^14].

```python
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
toolkit = GitHubToolkit.from_github_api_wrapper(github_wrapper)
agent   = create_react_agent(model, toolkit.get_tools())
```


## 6. **Callbacks \& Observabilidade**

* **Handlers** derivados de `BaseCallbackHandler` capturam eventos (`on_llm_start`, `on_chain_end` …) [^15][^16].
* Anexe dinamicamente: `chain.invoke(inputs, config={"callbacks":[handler]})` [^17]
* Ou *bind* permanente: `chain.with_config(callbacks=[...])` [^18]

Exemplo de *logger*:

```python
class LogHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token, **kw): print(token, end="", flush=True)

chain.invoke({"text":"Olá"}, config={"callbacks":[LogHandler()]})
```

Para produção use **LangSmith**:

```python
import os, langsmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
# Ative em nível global – dashboards, métricas, replay
```


## 7. **Streaming avançado**

| API | O que transmite | Indicada para |
| :-- | :-- | :-- |
| `.stream / .astream` | Apenas saída final em chunks | Interfaces simples |
| `.astream_events` | Eventos intermediários + saída | UIs ricas, SSE, websockets |

[^6][^19][^20]

## 8. Integrações Principais

| Provedor | Pacote | Observação |
| :-- | :-- | :-- |
| OpenAI | `langchain-openai` | GPT-4o, embeddings, *moderation* |
| Anthropic | `langchain-anthropic` | Claude-3 |
| Google GenAI | `langchain-google-genai` | Gemini-2 [^5] |
| Local | `langchain-mistralai`, `langchain-huggingface` | Ollama/Mistral, Transformers |
| Vetores | `faiss`, `chromadb`, `pinecone` | RAG |

Instalação seletiva via `pip install langchain-openai` etc.

## 9. Testes, *Evals* e CI

1. **Unitários**: utilize `pytest` + *mocks* de modelo.
2. **LangChain Evals** (β): avalie resposta com outro LLM (`Comparison`, `Criteria`).
3. Integre com LangSmith para *regression tests* em CI.

## 10. Migração de código antigo

* Memórias `*Memory` 0.0.x continuam funcionando, mas considere LangGraph [^8].
* API legada (ReadTheDocs) está congelada; use `python.langchain.com/api_reference` [^21][^22].


## 11. Dicas de Performance

* Ative `streaming=True` para UX melhor.
* Use *embeddings* locais quando o custo de rede for alto.
* Cache com `@langchain_cache` ou *Redis*.
* Paralelize chamadas com `asyncio` ou `Runnable.map()`.


## 12. Recursos adicionais

* **Tutoriais oficiais** – `python.langchain.com/docs/tutorials/` [^23]
* **LangChain Academy** – cursos práticos no GitHub [^24]
* **Blog posts** sobre *memory* e callbacks [^10][^25][^26]
* **Exemplos Pinecone** de streaming avançado [^27]


## Conclusão

Este guia cobre desde a instalação mínima até recursos avançados como LangGraph, streaming e observabilidade. Com a arquitetura modular do LangChain, você monta pipelines robustos, mantém-nos auditáveis via LangSmith e evolui gradualmente substituindo peças conforme as necessidades do projeto. Explore os exemplos, adapte às suas cargas de trabalho e mantenha-se atento às notas de versão para aproveitar novos recursos sem esforço.

<div style="text-align: center">⁂</div>

[^1]: https://python.langchain.com/docs/introduction/

[^2]: https://docs.langchain.com

[^3]: https://github.com/langchain-ai/langchain-community

[^4]: https://pypi.org/project/langchain/

[^5]: https://github.com/langchain-ai/langchain-google

[^6]: https://python.langchain.com/docs/how_to/streaming/

[^7]: https://python.langchain.com/docs/concepts/streaming/

[^8]: https://python.langchain.com/docs/versions/migrating_memory/

[^9]: https://langchain-ai.github.io/langgraph/concepts/memory/

[^10]: https://dev.to/jamesbmour/langchain-part-4-leveraging-memory-and-storage-in-langchain-a-comprehensive-guide-h4m

[^11]: https://www.pinecone.io/learn/series/langchain/langchain-conversational-memory/

[^12]: https://python.langchain.com/api_reference/langchain/memory.html

[^13]: https://langchain-ai.github.io/langgraph/

[^14]: https://python.langchain.com/docs/integrations/tools/github/

[^15]: https://python.langchain.com/docs/concepts/callbacks/

[^16]: https://python.langchain.com/api_reference/core/callbacks.html

[^17]: https://python.langchain.com/docs/how_to/callbacks_runtime/

[^18]: https://python.langchain.com/docs/how_to/callbacks_attach/

[^19]: https://langchain-ai.github.io/langgraph/how-tos/streaming/

[^20]: https://www.youtube.com/watch?v=juzD9h9ewV8

[^21]: https://api.python.langchain.com/en/latest/reference.html

[^22]: https://python.langchain.com/api_reference/

[^23]: https://python.langchain.com/docs/tutorials/

[^24]: https://github.com/langchain-ai/langchain-academy

[^25]: https://futureagi.com/blogs/understanding-langchain-callback-how-to-use-it-effectively

[^26]: https://towardsdatascience.com/callbacks-and-pipeline-structures-in-langchain-925aa077227e/

[^27]: https://github.com/pinecone-io/examples/blob/master/learn/generation/langchain/handbook/09-langchain-streaming/09-langchain-streaming.ipynb

[^28]: https://python.langchain.com/docs/how_to/extraction_examples/

[^29]: https://github.com/langchain-ai/langchain

[^30]: https://python.langchain.com/docs/integrations/document_loaders/github/

[^31]: https://python.langchain.com/docs/contributing/reference/

[^32]: https://sj-langchain.readthedocs.io

[^33]: https://www.langchain.com

[^34]: https://api.python.langchain.com

[^35]: https://python.langchain.com/api_reference/core/documents.html

[^36]: https://js.langchain.com/docs/concepts/callbacks/

[^37]: https://hub.asimov.academy/tutorial/o-que-e-a-memory-do-langchain-e-como-utilizar/

[^38]: https://js.langchain.com/docs/how_to/streaming/

[^39]: https://python.langchain.com/docs/how_to/chatbots_memory/

