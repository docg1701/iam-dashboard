# Agno para Sistema de Agentes Autônomos de Advocacia

---
**📅 Documentação Atualizada**: 25/01/2025  
**🔗 Biblioteca**: agno 1.7.x  
**📌 Contexto**: Sistema SaaS de advocacia com agentes especializados  
**⚠️ Foco**: Agentes PDF Processor e Legal Document Drafting
---

## Agentes para Sistema de Advocacia

### 1. Agente Processador de PDFs

**Responsabilidade**: Ingestão e processamento de documentos legais para busca RAG

```python
from agno import Agent
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.google import GoogleGenerativeAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from app.services.document_service import DocumentService
from app.repositories.document_repository import DocumentRepository
import os

class PDFProcessorAgent(Agent):
    """
    Agente especializado em processar documentos PDF para o sistema de advocacia.
    Utiliza Llama-Index para orquestração de embeddings e armazenamento.
    """
    def __init__(self, gemini_api_key: str, db_connection_string: str):
        os.environ["GOOGLE_API_KEY"] = gemini_api_key
        
        # Configurar LLM e Embedding Model via Llama-Index
        llm = Gemini(model="models/gemini-1.5-pro")
        embed_model = GoogleGenerativeAIEmbedding(model_name="models/text-embedding-004")

        # Configurar Vector Store (pgvector)
        vector_store = PGVectorStore.from_params(
            dsn=db_connection_string,
            table_name="document_chunks",
            embed_dim=768,
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        super().__init__(
            name="PDFProcessor",
            instructions="""
            Você é um agente de IA focado no processamento de documentos legais. Sua função é orquestrar a extração de texto, geração de embeddings e armazenamento no banco de dados vetorial.
            """,
            llm=llm,
            show_tool_calls=True,
            tools=[
                self.ingest_document
            ]
        )
        
        self.index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
        self.document_service = DocumentService(db_connection_string)

    def ingest_document(self, pdf_path: str, document_id: str, client_id: str) -> dict:
        """
        Ferramenta completa para ingerir um documento PDF, processá-lo e armazená-lo.
        """
        try:
            # Llama-Index lida com a leitura e chunking do PDF
            from llama_index.core import SimpleDirectoryReader
            
            # Carrega o documento
            documents = SimpleDirectoryReader(input_files=[pdf_path]).load_data()
            
            # Adiciona metadados essenciais para filtragem
            for doc in documents:
                doc.metadata["document_id"] = document_id
                doc.metadata["client_id"] = client_id

            # O Llama-Index gerencia a criação de nós, embeddings e armazenamento
            self.index.insert_documents(documents)
            
            self.document_service.update_document_status(document_id, "completed")
            
            return {"status": "success", "document_id": document_id, "nodes_created": len(documents)}
        except Exception as e:
            self.document_service.update_document_status(document_id, "failed", str(e))
            return {"status": "error", "message": str(e)}

class LegalDocumentDraftingAgent(Agent):
    """
    Agente especializado em redigir documentos legais usando um pipeline RAG com Llama-Index.
    """
    def __init__(self, gemini_api_key: str, db_connection_string: str):
        os.environ["GOOGLE_API_KEY"] = gemini_api_key
        
        llm = Gemini(model="models/gemini-1.5-pro")
        embed_model = GoogleGenerativeAIEmbedding(model_name="models/text-embedding-004")
        vector_store = PGVectorStore.from_params(dsn=db_connection_string, table_name="document_chunks", embed_dim=768)
        index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

        super().__init__(
            name="LegalDrafter",
            instructions="""
            Você é um advogado especialista em redação de documentos legais. Sua principal ferramenta é um sistema RAG para buscar informações em uma base de conhecimento e gerar documentos.
            """,
            llm=llm,
            tools=[self.draft_document]
        )
        
        self.index = index

    def draft_document(self, query: str, client_id: str) -> str:
        """
        Busca informações relevantes para a query de um cliente específico e gera uma resposta.
        """
        try:
            # Cria um retriever com filtro para o cliente específico
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=5,
                filters={"client_id": client_id}
            )
            
            # Cria um query engine com o retriever filtrado
            query_engine = RetrieverQueryEngine.from_args(
                retriever=retriever,
                llm=self.llm
            )
            
            # Executa a consulta
            response = query_engine.query(query)
            
            return str(response)
        except Exception as e:
            return f"Erro ao gerar o documento: {str(e)}"


---



## 2. Getting Started

To begin using Agno, follow the installation steps and try out the basic examples.

### Installation

To install Agno, you can use `pip`:

```shell
pip install -U agno
```

### Example - Reasoning Agent

This example demonstrates how to build a Reasoning Agent that uses `ReasoningTools` and `YFinanceTools` to obtain financial information.

Save the following code to a file, for example, `reasoning_agent.py`:

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-20250514"),
    tools=[
        ReasoningTools(add_instructions=True),
        YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
    ],
    instructions=[
        "Use tables to display data",
        "Only output the report, no other text",
    ],
    markdown=True,
)
agent.print_response(
    "Write a report on NVDA",
    stream=True,
    show_full_reasoning=True,
    stream_intermediate_steps=True,
)
```

To run the agent, create a virtual environment, install dependencies, and export your `ANTHROPIC_API_KEY`:

```shell
uv venv --python 3.12
source .venv/bin/activate

uv pip install agno anthropic yfinance

export ANTHROPIC_API_KEY=sk-ant-api03-xxxx

python reasoning_agent.py
```

### Example - Multi-Agent Teams

When the number of tools grows or you need to handle multiple concepts, use a team of agents to distribute the workload.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.team import Team

web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    instructions="Always include sources",
    show_tool_calls=True,
    markdown=True,
)

finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=OpenAIChat(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
    instructions="Use tables to display data",
    show_tool_calls=True,
    markdown=True,
)

agent_team = Team(
    mode="coordinate",
    members=[web_agent, finance_agent],
    model=OpenAIChat(id="gpt-4o"),
    success_criteria="A comprehensive financial news report with clear sections and data-driven insights.",
    instructions=["Always include sources", "Use tables to display data"],
    show_tool_calls=True,
    markdown=True,
)

agent_team.print_response("What's the market outlook and financial performance of AI semiconductor companies?", stream=True)
```

Install dependencies and run the Agent team:

```shell
pip install duckduckgo-search yfinance

python agent_team.py
```

---



## 3. Architecture and Design

Agno is built with a modular architecture, focused on performance and extensibility. The framework is designed to facilitate the creation of complex multi-agent systems, with well-defined components for managing models, tools, memory, and agent collaboration.

### Project Structure

The Agno repository is organized as follows:

- `libs/agno/agno/`: Contains the core source code of the Agno framework, including implementations of agents, models, tools, storage, and teams.
- `cookbook/`: Practical examples and recipes for using Agno in different scenarios, ranging from basic concepts to advanced applications.
- `scripts/`: Utility scripts for development, formatting, validation, and testing.
- `docs/`: Detailed project documentation (although README.md points to `docs.agno.com`).
- `tests/`: Unit and integration tests to ensure code quality.

### Core Components

Agno is composed of several key components that work together to form an agentic system:

- **Agents (`Agent`)**: The atomic unit of work. An agent can be configured with a language model, a set of tools, and specific instructions to perform tasks.
- **Models (`Models`)**: Abstractions for different language model providers (LLMs), such as Anthropic, OpenAI, etc. Agno offers a unified interface for interacting with these models.
- **Tools (`Tools`)**: Functionalities that agents can use to interact with the outside world, such as searching the web for information, accessing financial APIs, etc. Tools are modular and can be easily extended.
- **Teams (`Team`)**: Enable collaboration between multiple agents to solve more complex problems. Teams can operate in different coordination modes.
- **Storage and Memory (`Storage` & `Memory`)**: Components for managing agents' short-term and long-term memory, allowing them to retain information and learn over time.
- **Vector Databases (`VectorDB`)**: Integration with various vector databases for agentic search and information retrieval (RAG).

### Typical Execution Flow

A typical execution flow in Agno involves:

1.  **Agent Initialization**: An `Agent` is instantiated with a `Model` and a list of `Tools`.
2.  **Instruction Definition**: Instructions are provided to the agent to guide its behavior and how it should use tools.
3.  **Task Execution**: The agent receives a task (prompt) and, based on its instructions and available tools, decides what actions to take.
4.  **Reasoning and Tool Usage**: The agent can use its `ReasoningTools` to plan and execute the task, invoking other tools as needed to gather information or perform actions.
5.  **Response Generation**: After processing the task and using the tools, the agent generates a formatted response according to the instructions.

---



## 4. Core Concepts

To effectively understand and utilize Agno, it is crucial to grasp its core concepts.

### Agents

In Agno, an `Agent` is the fundamental unit of work. Each agent is an autonomous entity capable of reasoning, interacting with tools, and processing information. They are configured with:

-   **Model (`model`)**: The language model (LLM) that the agent will use for its reasoning and text generation.
-   **Tools (`tools`)**: A set of functionalities that the agent can invoke to perform specific actions, such as fetching financial data, searching the web, etc.
-   **Instructions (`instructions`)**: Guidelines that direct the agent's behavior and how it should interact with tools and format its outputs.

### Models

Agno provides an abstraction for interacting with various LLM providers. This ensures that your code is model-agnostic, allowing for easy switching between different models and providers (e.g., Anthropic, OpenAI). The unified interface simplifies the integration and use of LLMs in your agents.

### Tools

`Tools` are the bridge between agents and the external world. They encapsulate specific functionalities that agents can use to perform tasks. Examples of tools include:

-   `ReasoningTools`: Tools to assist in the agent's reasoning process.
-   `YFinanceTools`: Tools to interact with the Yahoo Finance API to get stock data, analyst recommendations, etc.
-   `DuckDuckGoTools`: Tools for performing web searches.

Tools are designed to be modular and extensible, allowing developers to create their own custom tools to meet specific needs.

### Teams

To handle more complex tasks that require collaboration or exceed the capacity of a single agent, Agno introduces the concept of a `Team`. A team consists of multiple agents working together to achieve a common goal. Teams can be configured with:

-   **Members (`members`)**: The list of agents that make up the team.
-   **Mode (`mode`)**: Defines how agents in the team coordinate their actions (e.g., `coordinate`).
-   **Success Criteria (`success_criteria`)**: Defines what constitutes a successful completion of the task for the team.

### Memory and Storage

Agno provides mechanisms for agents to have both short-term and long-term memory. This is crucial for agents that need to retain information across multiple interactions or sessions. The `Storage` and `Memory` drivers allow agents to learn and adapt based on past experiences.

### Vector Databases

For agentic search and Retrieval Augmented Generation (RAG), Agno integrates with over 20 vector databases. This allows agents to efficiently search and retrieve relevant information from large volumes of data, improving the quality and relevance of their responses.

---



## 5. API Reference

Agno is a Python framework that exposes its functionalities through classes and methods. While detailed API documentation for each class and method is available in the official documentation (docs.agno.com), this section will provide an overview of how the APIs are structured and used.

### Main Classes

-   **`Agent`**: The central class for creating and managing agents. Its methods include `print_response` for interacting with the agent and getting responses.
-   **`Team`**: The class for orchestrating multiple agents in a team. Methods like `print_response` allow interaction with the team as a whole.
-   **`Models`**: Modules and classes within `agno.models` provide interfaces for different LLM providers (e.g., `agno.models.anthropic.Claude`, `agno.models.openai.OpenAIChat`).
-   **`Tools`**: Modules and classes within `agno.tools` contain the implementations of tools that agents can use (e.g., `agno.tools.reasoning.ReasoningTools`, `agno.tools.yfinance.YFinanceTools`).

### Method and Parameter Structure

Agno classes and methods are designed to be intuitive and flexible. For example, the `Agent` class accepts parameters such as `model`, `tools`, `instructions`, and `markdown` to configure the agent's behavior. Tools, in turn, expose specific methods for their functionalities (e.g., `YFinanceTools` might have methods for `stock_price`, `analyst_recommendations`, etc.).

### Structured Outputs

Agno supports structured outputs, allowing agents to return responses in well-defined formats, such as JSON, using `json_mode` or structured output features provided by language models.

### FastAPI Routes

Agno offers pre-built FastAPI routes to serve your agents in production, facilitating the deployment of APIs for your agentic systems.

For complete details on each method, its parameters, and return values, please refer to the official Agno documentation.

---



## 6. Configuration Guide

Configuring Agno involves installing dependencies, setting environment variables, and, in some cases, configuring specific tools and models.

### Dependency Installation

Agno can be installed via `pip`:

```shell
pip install -U agno
```

For examples that use specific tools, such as `anthropic`, `yfinance`, or `duckduckgo-search`, you will need to install the corresponding libraries:

```shell
uv pip install agno anthropic yfinance
```

or

```shell
pip install duckduckgo-search yfinance
```

### Environment Variables

Some models and tools require API keys that must be configured as environment variables. For example, to use Anthropic models:

```shell
export ANTHROPIC_API_KEY=sk-ant-api03-xxxx
```

Other important environment variables include:

-   `AGNO_TELEMETRY`: Determines whether Agno should send telemetry data about model usage. It can be disabled by setting it to `false`:

```shell
export AGNO_TELEMETRY=false
```

### Model Configuration

When instantiating an agent, you configure the model to be used. For example, to use Anthropic's Claude:

```python
from agno.models.anthropic import Claude

agent = Agent(
    model=Claude(id="claude-sonnet-4-20250514"),
    # ...
)
```

Or to use OpenAI Chat:

```python
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    # ...
)
```

### Tool Configuration

Tools are configured by being passed to the agent. Some tools may have specific parameters for their initialization. For example, `YFinanceTools` can be configured to include different types of financial data:

```python
from agno.tools.yfinance import YFinanceTools

tools=[
    YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
]
```

### Team Configuration

Agent teams are configured with their members and a coordination mode:

```python
from agno.team import Team

agent_team = Team(
    mode="coordinate",
    members=[web_agent, finance_agent],
    model=OpenAIChat(id="gpt-4o"),
    success_criteria="A comprehensive financial news report with clear sections and data-driven insights.",
    instructions=["Always include sources", "Use tables to display data"],
    show_tool_calls=True,
    markdown=True,
)
```

---



## 7. Advanced Usage

This section covers more advanced topics to maximize Agno's potential, including customization, extensibility, and integration with other systems.

### Customization and Extensibility

Agno is designed to be highly extensible, allowing you to add your own custom components:

-   **Adding New Vector Databases**: You can integrate new vector databases by implementing the `VectorDb` interface and adding your class to `libs/agno/agno/vectordb`.
-   **Adding New Model Providers**: To integrate new LLMs, you can create a new model class that inherits from `OpenAILike` (if compatible with the OpenAI API) or implement a custom interface for other providers.
-   **Creating New Tools**: Develop custom tools by implementing the `Toolkit` class and registering your functions. This allows your agents to interact with specific APIs and services in your domain.

### Integration with Other Tools/Frameworks

Agno can be integrated with other frameworks and tools in your development ecosystem. For example, the ability to serve agents via pre-built FastAPI routes facilitates integration with existing web applications or microservices.

### Advanced Configuration Options

Beyond basic configurations, Agno offers advanced options for optimization and control:

-   **Team Modes**: Explore different coordination modes for agent teams to optimize collaboration and performance for specific tasks.
-   **Telemetry Configuration**: Control the sending of telemetry data to ensure privacy and compliance with your organization's policies.

### Plugin Development (if applicable)

While Agno does not explicitly mention a formal plugin system, the modular architecture for models, tools, and vector databases functions as a plugin mechanism, allowing developers to significantly extend the framework's functionalities.

---



## 8. Troubleshooting

This section addresses common issues you might encounter when using Agno and provides solutions to help you debug and resolve these problems.

### Installation Errors

-   **Problem**: `pip install agno` fails or results in dependency errors.
    -   **Solution**: Ensure you are using a compatible Python version (generally Python 3.8+). Consider using a virtual environment (`venv` or `uv venv`) to isolate dependencies and avoid conflicts. Check if `uv` is installed (`pip install uv`).

### API Key Issues

-   **Problem**: Authentication errors when using language models or tools that require API keys.
    -   **Solution**: Verify that the correct environment variable (e.g., `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) is set and that the key is valid. Ensure there are no typos in the key or the environment variable name.

### Unexpected Agent Behavior

-   **Problem**: The agent does not behave as expected, does not use tools correctly, or generates irrelevant responses.
    -   **Solution**:
        -   **Instructions**: Review the `instructions` provided to the agent. They should be clear, concise, and specific. Ambiguous instructions can lead to unpredictable behavior.
        -   **Tools**: Check if the correct tools have been passed to the agent and if they are configured properly. Ensure that the tools have the necessary permissions to operate.
        -   **Model**: Experiment with different language models. Some models may be better suited for certain tasks or may interpret instructions differently.
        -   **Debugging**: Use `show_full_reasoning=True` and `stream_intermediate_steps=True` when calling `print_response` to see the agent's reasoning process and tool calls, which can help identify where the problem occurs.

### Performance Issues

-   **Problem**: Agents or teams are slow or consuming too many resources.
    -   **Solution**:
        -   **Prompt Optimization**: Optimize your prompts and instructions to be more efficient and direct, reducing the number of tokens processed.
        -   **Model Selection**: Smaller or more efficient models can be faster and consume fewer resources. Consider using lighter models for tasks that do not require the full capability of larger models.
        -   **Parallelization**: Agno is designed for high performance. Ensure your tool calls and logic leverage asynchronous execution when possible.
        -   **Monitoring**: Use Agno's monitoring tools (agno.com) to identify performance bottlenecks and areas that need optimization.

### Output Formatting Errors

-   **Problem**: The agent's output is not formatted correctly (e.g., not using tables, not Markdown).
    -   **Solution**: Verify that the `markdown=True` parameter is set in the agent and that the instructions include clear guidelines on the desired output format (e.g., `"Use tables to display data"`).

---



## 9. Best Practices

Following best practices when developing with Agno can significantly improve the quality, performance, and maintainability of your agentic systems.

### Security Recommendations

-   **API Key Management**: Never embed API keys directly in your source code. Use environment variables or a secure secret management system to store and access your keys.
-   **Input Validation**: Always validate inputs provided to your agents and tools to prevent code injection or malicious data.
-   **Access Control**: If your agents interact with external systems, implement the principle of least privilege, granting only the necessary permissions.
-   **Activity Monitoring**: Monitor your agents' activity to detect anomalous behavior or misuse attempts.

### Performance Optimization Tips

-   **Prompt Optimization**: Craft concise and effective prompts to reduce the number of tokens processed by LLMs, which can lower costs and latency.
-   **Appropriate Model Selection**: Choose the most suitable language model for the task. Smaller, faster models may suffice for simple tasks, while larger models are needed for complex reasoning.
-   **Tool Parallelization**: Leverage Agno's ability to execute tool calls asynchronously to improve performance, especially in scenarios with multiple API calls.
-   **Response Caching**: For tool or model calls that return static or infrequently changing results, consider implementing a caching mechanism to avoid redundant calls.

### Code Organization Guidelines

-   **Modularization**: Organize your code into logical modules for agents, tools, models, and teams. This improves readability and maintainability.
-   **Component Reusability**: Create generic tools and agents that can be reused across different parts of your application or in other projects.
-   **Versioning**: Use version control systems (like Git) and follow semantic versioning practices to manage changes in your code.

### Testing Strategies

-   **Unit Tests**: Write unit tests for your individual tools and components to ensure they function as expected.
-   **Integration Tests**: Test the interaction between agents and tools, and between agents in teams, to ensure the complete workflow functions correctly.
-   **End-to-End Tests**: Create tests that simulate real-world usage scenarios to verify the overall behavior of the agentic system.
-   **Performance Tests**: Monitor the performance of your agents and teams under load to identify bottlenecks and optimize efficiency.

### Deployment Considerations

-   **Virtual Environments**: Always use virtual environments to manage your project's dependencies, ensuring that the correct library versions are used.
-   **Containers**: Consider using containers (e.g., Docker) to package your Agno applications, ensuring consistent execution environments in development and production.
-   **Production Monitoring**: Implement robust monitoring for your agents in production, using Agno's monitoring tools or other observability solutions.

---



## 10. Common Pitfalls

When developing with Agno, it's important to be aware of some common pitfalls that can lead to issues or unexpected behavior.

### Typical Developer Mistakes

-   **Ambiguous Instructions**: Providing vague or contradictory instructions to agents can result in inaccurate responses or incorrect tool usage. Always be as clear and specific as possible.
-   **Tool Overload**: Assigning too many tools to a single agent can overwhelm it, making reasoning less efficient and increasing the likelihood of errors. Consider splitting responsibilities among multiple agents in a team.
-   **Ignoring Context**: Failing to provide sufficient context to the agent or not managing memory properly can cause the agent to "forget" important information from previous interactions.

### "Gotchas" and Unexpected Behaviors

-   **API Latency**: Calls to language models and external APIs can introduce latency. Do not assume responses will be instantaneous and design your systems to handle delays.
-   **Model Hallucinations**: Language models can occasionally generate incorrect information or "hallucinate." Always validate critical information generated by agents, especially in sensitive applications.
-   **Token Cost**: Using language models incurs a cost associated with the number of tokens processed. Long prompts, verbose responses, or infinite loops can quickly increase costs. Monitor usage and optimize prompts.

### Version Compatibility Issues

-   **Outdated Dependencies**: Ensure that all your dependencies, including Agno itself and tool libraries, are up-to-date to avoid compatibility problems.
-   **Model API Changes**: Language model providers may update their APIs, which might require adjustments to your Agno code. Stay informed about changes in the APIs of the models you use.

### Resource Management Problems

-   **Excessive Memory Usage**: Agents and teams can consume memory, especially with large data volumes or complex interactions. Monitor memory usage and optimize data storage.
-   **Rate Limits**: Language model APIs and external tools often have rate limits. Implement retry logic with exponential backoff to handle these limits and prevent failures.

### Configuration Errors

-   **Missing Environment Variables**: The absence of necessary environment variables for API keys or other configurations can cause failures. Always check that all required variables are defined.
-   **Incorrect Tool Configuration**: Incorrect parameters when initializing tools can lead to errors or unexpected tool behavior.

---



## 11. Performance Optimization

Agno is built with a focus on performance, but continuous optimization is crucial for scalable agentic systems. This section details strategies to ensure your agents and teams operate with maximum efficiency.

### Agno Performance Metrics

Agno excels in key performance metrics:

-   **Agent Instantiation**: Approximately ~3μs on average.
-   **Memory Footprint**: Approximately ~6.5Kib on average per agent.

These numbers, while individually small, are critical when scaling to thousands of agents, where small inefficiencies can become significant bottlenecks.

### Optimization Strategies

1.  **Prompt and Instruction Optimization**:
    -   **Conciseness**: Shorter, more direct prompts reduce the number of tokens processed by the LLM, decreasing latency and costs.
    -   **Clarity**: Clear and specific instructions prevent the agent from needing multiple iterations or complex reasoning to understand the task.

2.  **Intelligent Model Selection**:
    -   **Smaller Models for Simple Tasks**: For tasks that do not require complex reasoning or large context capacity, use smaller, faster language models. This saves resources and time.
    -   **Larger Models for Complexity**: Reserve more powerful models for tasks that truly demand in-depth reasoning, nuanced understanding, or large volumes of information.

3.  **Tool Call Parallelization**:
    -   Agno is designed to be highly asynchronous. Whenever possible, structure your tool calls to execute in parallel, especially when there are no dependencies between them. This minimizes waiting time for external API responses.

4.  **Efficient Memory and Storage Management**:
    -   **Short-Term Memory**: Efficiently use Agno's session memory, storing only the context relevant to the current interaction.
    -   **Long-Term Memory (VectorDB)**: When using vector databases, optimize indexing and retrieval to ensure that only the most relevant information is fetched, reducing processing load.

5.  **Response Caching**:
    -   For tool or model calls that produce results that do not change frequently, implement a caching mechanism. This avoids redundant calls and speeds up responses.

6.  **Performance Monitoring and Analysis**:
    -   Use Agno's monitoring tools (available at agno.com) to track the performance of your agents in real-time. Identify bottlenecks, latencies, and resource usage for targeted optimizations.
    -   Conduct load and stress tests to understand how your agentic systems behave under different demand levels.

### Performance Comparison (Agno vs. Other Frameworks)

Agno demonstrates superior performance compared to other frameworks, such as LangGraph, in instantiation and memory usage tests. While Agno provides benchmarks, it is always recommended that you run your own evaluations in your environment to obtain accurate results.

---



## 12. Security Considerations

Security is a critical aspect in the development of any system, and agentic systems are no exception. This section highlights key security considerations when working with Agno.

### Secure Credential Management

-   **Environment Variables**: Always use environment variables to store API keys, access tokens, and other sensitive credentials. Never hardcode them directly into your source code or include them in version control repositories.
-   **Secret Management Systems**: For production environments, consider using dedicated secret management systems (e.g., HashiCorp Vault, AWS Secrets Manager, Azure Key Vault) to securely manage and inject credentials.

### Input and Output Validation

-   **Input Validation**: Any input provided to your agents, whether from users, external APIs, or other sources, must be rigorously validated. This helps prevent attacks such as prompt injection, code injection, or data manipulation.
-   **Output Sanitization**: Outputs generated by agents should be sanitized before being displayed to users or used in other systems. This is crucial to prevent Cross-Site Scripting (XSS) attacks or other types of injection vulnerabilities.

### Access Control and Permissions

-   **Principle of Least Privilege**: Grant your agents and the tools they use only the minimum necessary permissions to perform their functions. Avoid granting unrestricted access to sensitive systems or data.
-   **Authentication and Authorization**: If your agents interact with protected APIs or services, ensure that authentication and authorization are correctly implemented. Use short-lived access tokens and credential rotation mechanisms.

### Monitoring and Auditing

-   **Activity Logging**: Implement comprehensive logging of agent activities, including tool calls, model interactions, and any relevant security events. This is essential for auditing, anomaly detection, and incident response.
-   **Behavior Monitoring**: Monitor your agents' behavior in real-time to identify unusual patterns or suspicious activities that might indicate a compromise or misuse.

### Data Security

-   **Encryption**: Encrypt sensitive data in transit and at rest. Use secure communication protocols (HTTPS/TLS) for all network interactions.
-   **Data Retention**: Define clear data retention policies for information processed or stored by your agents, ensuring compliance with privacy regulations.

### LLM-Specific Attacks

-   **Prompt Injection**: Be aware that malicious users may attempt to manipulate agent behavior through carefully crafted prompts. Implement filters and validations to mitigate these attacks.
-   **Data Leakage**: Language models can inadvertently leak sensitive information present in their training data or previous interactions. Exercise caution when handling confidential data and consider anonymization techniques.

---



## 13. Contributing Guidelines

Agno is an open-source project and welcomes contributions from the community. Following these guidelines ensures a smooth contribution process and maintains project quality.

### How to Contribute

The contribution workflow follows the *fork and pull request* model:

1.  **Fork the Repository**: Create a fork of the official Agno repository on GitHub.
2.  **Create a Branch**: Create a new branch for your feature or fix (`git checkout -b my-new-feature`).
3.  **Development**: Implement your feature or improvement.
4.  **Tests**: Ensure your code passes all existing tests and add new tests for your functionality, if applicable.
5.  **Formatting and Validation**: Run the code formatting and validation scripts (`./scripts/format.sh` and `./scripts/validate.sh` for Unix, or `.\scripts\format.bat` and `.\scripts\validate.bat` for Windows) to ensure compliance with project code standards.
6.  **Commit**: Make commits with clear and descriptive messages.
7.  **Pull Request (PR)**: Submit a Pull Request to the main Agno repository.

### Pull Request Guidelines

To maintain a clear and organized project history, follow these guidelines when submitting Pull Requests:

-   **Title Format**: Your PR title must start with a type tag enclosed in square brackets, followed by a space and a concise subject.
    -   Example: `[feat] Add user authentication`
    -   Valid types: `[feat]` (new feature), `[fix]` (bug fix), `[docs]` (documentation changes), `[test]` (test addition/modification), `[refactor]` (code refactoring), `[build]` (build system changes), `[ci]` (CI changes), `[chore]` (maintenance tasks), `[perf]` (performance improvement), `[style]` (code formatting), `[revert]` (commit reversion).
-   **Link to Issue**: The PR description should ideally reference the issue it addresses using keywords like `fixes #<issue_number>`, `closes #<issue_number>`, or `resolves #<issue_number>`.

### Development Environment Setup

1.  **Clone the Repository**: `git clone https://github.com/agno-agi/agno`
2.  **Install `uv`**: Check if `uv` is installed (`uv --version`). If not, install with `pip install uv`.
3.  **Create Virtual Environment**: Run `./scripts/dev_setup.sh` (Unix) or `.\scripts\dev_setup.bat` (Windows).
4.  **Activate Virtual Environment**: `source .venv/bin/activate` (Unix) or `.\venv\Scripts\activate` (Windows).

### Adding New Components

-   **New Vector Database**: Create a directory in `libs/agno/agno/vectordb` and implement a class that follows the `VectorDb` interface.
-   **New Model Provider**: Create a directory in `libs/agno/agno/models` and implement a class that inherits from `OpenAILike` or a custom interface.
-   **New Tool**: Create a directory in `libs/agno/agno/tools` and implement a class that inherits from `Toolkit`.

Always add usage examples for new components in the `cookbook/` directory.

---



## 14. Appendices

This section provides additional information and useful resources for developers working with Agno.

### License

The Agno project is licensed under the terms of the [Mozilla Public License Version 2.0 (MPL-2.0)](/home/ubuntu/agno/LICENSE). This license permits the use, modification, and distribution of the software, with certain conditions related to the availability of modified source code.

### Additional Resources

-   **Official Documentation**: For the most complete and up-to-date documentation, visit [docs.agno.com](https://docs.agno.com).
-   **Cookbook**: Practical examples and usage recipes for Agno can be found in the `cookbook` directory of the GitHub repository or directly at [github.com/agno-agi/agno/tree/main/cookbook](https://github.com/agno-agi/agno/tree/main/cookbook).
-   **Community Forum**: Participate in discussions and get support in the Agno community forum at [community.agno.com](https://community.agno.com/).
-   **Discord**: Join the community on Discord for real-time discussions and support at [discord.gg/4MtYHHrgA8](https://discord.gg/4MtYHHrgA8).
-   **Monitoring**: Monitor your agents in real-time at [agno.com](https://app.agno.com).

### Cursor Setup for Agno Documentation

For developers using Cursor, it is possible to integrate Agno's complete documentation to facilitate development:

1.  In Cursor, go to the "Cursor Settings" menu.
2.  Find the "Indexing & Docs" section.
3.  Add `https://docs.agno.com/llms-full.txt` to the list of documentation URLs.
4.  Save the changes.

This will allow Cursor to access Agno documentation to assist in development.

---

