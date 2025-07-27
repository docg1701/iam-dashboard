# Gemini API para Sistema de Advocacia

**Processamento de Documentos Legais com IA**
Este guia foca no uso da Google Gemini API v1 para processamento de documentos legais no sistema de agentes autônomos para advocacia. Cobre extração de texto, análise semântica, geração de embeddings para RAG e criação de documentos legais automatizados.

## 1. Setup Inicial para Sistema de Advocacia

```bash
# Instalação do SDK Python oficial
pip install -U google-generativeai
```

```python
import google.generativeai as genai
import os
from typing import List, Dict

# Configuração com API key do ambiente
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Modelo otimizado para documentos legais
model = genai.GenerativeModel('gemini-1.5-pro')
```

## 2. Processamento de Documentos Legais

### Extração de Texto de PDFs Simples

```python
async def extract_text_from_simple_pdf(pdf_content: bytes, client_context: str) -> Dict:
    """
    Extrai texto de PDFs digitais usando Gemini API
    Args:
        pdf_content: Conteúdo binário do PDF
        client_context: Contexto do cliente para personalização
    """
    
    prompt = f"""
    Analise este documento legal e extraia as seguintes informações:
    1. Tipo de documento (contrato, petição, parecer, etc.)
    2. Partes envolvidas
    3. Resumo executivo (máx. 200 palavras)
    4. Cláusulas principais ou pontos importantes
    5. Datas relevantes
    
    Contexto do cliente: {client_context}
    
    Formate a resposta como JSON estruturado.
    """
    
    # Upload do documento
    file = genai.upload_file(pdf_content, mime_type="application/pdf")
    
    # Análise com contexto legal
    response = model.generate_content([prompt, file])
    
    return {
        "extracted_text": response.text,
        "document_analysis": parse_legal_analysis(response.text),
        "file_reference": file.name
    }

def parse_legal_analysis(response_text: str) -> Dict:
    """Parse da análise legal estruturada"""
    try:
        import json
        return json.loads(response_text)
    except:
        return {"raw_analysis": response_text}
```

### Geração de Embeddings para RAG

```python
def generate_document_embeddings(text_chunks: List[str]) -> List[List[float]]:
    """
    Gera embeddings para chunks de documentos legais
    Args:
        text_chunks: Lista de chunks de texto do documento
    Returns:
        Lista de embeddings (vetores de 768 dimensões)
    """
    embeddings = []
    
    for chunk in text_chunks:
        # Usar modelo de embedding específico
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=chunk,
            task_type="retrieval_document",  # Otimizado para busca
            title="Documento Legal"  # Contexto para melhor embedding
        )
        embeddings.append(result['embedding'])
    
    return embeddings

# Exemplo de uso com chunks de documentos
async def process_document_for_rag(document_text: str, document_id: str) -> List[Dict]:
    """Processa documento completo para armazenamento RAG"""
    
    # Dividir documento em chunks
    chunks = chunk_legal_document(document_text)
    
    # Gerar embeddings
    embeddings = generate_document_embeddings([chunk['text'] for chunk in chunks])
    
    # Preparar dados para armazenamento no pgvector
    processed_chunks = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        processed_chunks.append({
            'id': f"{document_id}_{i}",
            'document_id': document_id,
            'page_number': chunk['page'],
            'text_content_preview': chunk['text'][:500],
            'vector': embedding,
            'legal_context': chunk.get('context', 'general')
        })
    
    return processed_chunks

def chunk_legal_document(text: str, chunk_size: int = 1000) -> List[Dict]:
    """
    Divide documento legal em chunks semânticos
    Considera parágrafos, seções e contexto legal
    """
    chunks = []
    paragraphs = text.split('\n\n')
    
    current_chunk = ""
    current_page = 1
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'page': current_page,
                    'context': identify_legal_context(current_chunk)
                })
                current_page += 1
            current_chunk = paragraph + "\n\n"
    
    # Adicionar último chunk
    if current_chunk:
        chunks.append({
            'text': current_chunk.strip(),
            'page': current_page,
            'context': identify_legal_context(current_chunk)
        })
    
    return chunks

def identify_legal_context(text: str) -> str:
    """Identifica o contexto legal do chunk"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['contrato', 'acordo', 'cláusula']):
        return 'contract'
    elif any(word in text_lower for word in ['petição', 'requerimento', 'solicitação']):
        return 'petition'
    elif any(word in text_lower for word in ['sentença', 'decisão', 'julgamento']):
        return 'judgment'
    elif any(word in text_lower for word in ['parecer', 'opinião', 'análise']):
        return 'opinion'
    else:
        return 'general'
```

### Geração de Documentos Legais

```python
async def generate_legal_document(template_type: str, context_data: Dict, similar_docs: List[str]) -> str:
    """
    Gera documento legal usando RAG e templates
    Args:
        template_type: Tipo do documento (petição, contrato, etc.)
        context_data: Dados do caso/cliente
        similar_docs: Documentos similares para referência (RAG)
    """
    
    prompt = f"""
    Como especialista em direito brasileiro, crie um(a) {template_type} baseado nos seguintes dados:
    
    DADOS DO CASO:
    {format_case_data(context_data)}
    
    DOCUMENTOS DE REFERÊNCIA:
    {format_reference_docs(similar_docs)}
    
    INSTRUÇÕES:
    1. Use linguagem jurídica apropriada
    2. Inclua todas as fundamentações legais necessárias
    3. Siga a estrutura padrão para este tipo de documento
    4. Cite artigos de lei quando relevante
    5. Mantenha tom formal e técnico
    
    Gere o documento completo, pronto para uso.
    """
    
    response = model.generate_content(prompt)
    
    return response.text

def format_case_data(data: Dict) -> str:
    """Formata dados do caso para o prompt"""
    formatted = []
    for key, value in data.items():
        formatted.append(f"- {key.title()}: {value}")
    return "\n".join(formatted)

def format_reference_docs(docs: List[str]) -> str:
    """Formata documentos de referência para o prompt"""
    if not docs:
        return "Nenhum documento de referência fornecido."
    
    formatted = []
    for i, doc in enumerate(docs, 1):
        # Limitar tamanho para não exceder limite do prompt
        preview = doc[:1000] + "..." if len(doc) > 1000 else doc
        formatted.append(f"DOCUMENTO {i}:\n{preview}\n")
    
    return "\n".join(formatted)
```


## 2. Listagem e Metadados de Modelos

```python
# Lista todos os modelos disponíveis
models = client.models.list()
for m in models:
    print(m.name, m.supported_actions)
```

_Exemplo de saída_:


| Modelo | Actions |
| :-- | :-- |
| gemini-2.5-pro | generateContent, embedContent, ... |
| gemini-2.5-flash | generateContent, embedContent, ... |
| gemini-embedding-001 | embedContent |
| gemini-2.5-flash-preview-tts | generateSpeech |
| gemini-2.5-pro-preview-tts | generateSpeech |
| gemini-2.5-flash-preview-native-audio-dialog | chat, generateSpeech |

## 3. Geração de Texto e Chat (2.5 Pro \& 2.5 Flash)

### 3.1. `generateContent`

```python
response = client.generate_content(
    model="gemini-2.5-pro",
    prompt=genai.Prompt.from_text("Explique o teorema de Bayes."),
    temperature=0.2,
    max_output_tokens=512
)
print(response.text)
```

*Gemini 2.5 Pro*: raciocínio complexo, long context (até 1 Mi token)[^1].

### 3.2. Conversação (Chat)

```python
chat = client.chat(
    model="gemini-2.5-flash",
    messages=[
        genai.ChatMessage(system="Você é assistente SaaS."),
        genai.ChatMessage(user="Como configuro RAG com PostgreSQL?")
    ]
)
print(chat.last.text)
```

*Gemini 2.5 Flash*: custo-eficiente, low-latency para agentes[^1].

## 4. Embeddings (RAG)

```python
# Gera embeddings do texto
embed = client.embed_content(
    model="gemini-embedding-001",
    content=["Texto de documento A", "Texto de documento B"]
)
vectors = embed.embeddings  # lista de vetores (listas de floats)
```

Use p. ex. FAISS ou pgvector para indexação, similar ao PostgreSQL[^2].

## 5. OCR de PDF (via Gemini + PyMuPDF)

### 5.1. Extração de texto com “layers” embutido

```python
chat = client.chat(
    model="gemini-2.5-pro",
    messages=[genai.ChatMessage(user="Extraia o texto deste PDF: [base64_do_pdf]")]
)
print(chat.last.text)
```

Ou use PyMuPDF + Tesseract (veja guia anterior) e depois envie texto a Gemini para sumarização.

## 6. Pipeline RAG Completo

1. **Extração**: OCR via PyMuPDF+pytesseract → texto bruto.
2. **Chunking**: seções de ~1 000 tokens.
3. **Embeddings**: `gemini-embedding-001` → vetores.
4. **Indexação**: FAISS/pgvector.
5. **Retrieval**: busca top-k.
6. **Prompting**:
```python
docs = [doc.text for doc in retrieved]
prompt = genai.Prompt.from_messages([
    genai.ChatMessage(system="Você é um agente RAG."),
    genai.ChatMessage(user=f"Contexto:\n{docs}\nPergunta: {user_query}")
])
ans = client.generate_content(model="gemini-2.5-pro", prompt=prompt)
print(ans.text)
```


## 7. Text-to-Speech (TTS)

### 7.1. Gemini 2.5 Flash Preview TTS

```python
audio = client.generate_speech(
    model="gemini-2.5-flash-preview-tts",
    input=genai.TTSInput(text="Olá, este é um exemplo de TTS."),
    voice="male-1",
    language_code="pt-BR"
)
with open("output.wav", "wb") as f:
    f.write(audio.audio)
```

_Suporta multi-speaker e controle de estilo_[^3].

## 8. Speech-to-Text (STT)

```python
# Reconhecimento de fala (Live API)
stt = client.recognize_speech(
    model="gemini-2.5-flash",
    audio=genai.SpeechInput.from_file("input.wav"),
    config=genai.SpeechConfig(
        language_code="pt-BR",
        enable_automatic_punctuation=True
    )
)
print(stt.transcript)
```


## 9. Visão Computacional (Multimodal)

### 9.1. Análise de Imagem

```python
response = client.generate_content(
    model="gemini-2.5-pro",
    prompt=genai.Prompt.from_multimodal(
        text="Descreva a cena nesta foto.",
        image=open("foto.jpg", "rb")
    )
)
print(response.text)
```


### 9.2. Conversão de Imagem → Texto (OCR via flash-imagem)

```python
res = client.chat(
    model="gemini-2.0-flash-preview-image-generation",
    messages=[genai.ChatMessage(user="Extraia o texto desta imagem.")],
    image=open("scan.jpg", "rb")
)
print(res.last.text)
```


## 10. Agentes Autônomos

```python
from google.genai.agent import Agent, Tool

# Defina ferramentas (ex.: RAG, TTS, STT)
tools = [
    Tool(name="rag_query", func=lambda q: rag_chain.run(q)),
    Tool(name="tts", func=lambda t: client.generate_speech(...)),
    # ...
]
agent = Agent(model="gemini-2.5-flash", tools=tools)

# Execução autônoma
result = agent.run("Agende reunião: extraia dados do PDF e envie e-mail.")
print(result)
```


### **Checklist de Produção**

- [ ] Cliente `genai.Client()` configurado com variáveis de ambiente.
- [ ] Scripts de retry/backoff para chamadas API.
- [ ] Indexação de embeddings em armazenamento dedicado.
- [ ] Monitoramento de latência e erros (Prometheus + Grafana).
- [ ] Políticas de rate limit conforme quotas Gemini.
- [ ] CI/CD: testes end-to-end dos fluxos (RAG, TTS, STT, visão).
- [ ] Logging estruturado (request_id, model, duration).

Com este guia, sua aplicação SaaS em Python terá acesso a todo o ecossistema Gemini: modelos de **texto** (2.5 Pro/Flash), **embeddings**, **TTS/STT** e **visão multimodal**, permitindo agentes autônomos, OCR de PDF, pipeline RAG, e experiências conversacionais ricos em multimídia.

<div style="text-align: center">⁂</div>

[^1]: https://ai.google.dev/gemini-api/docs/models

[^2]: https://ieeexplore.ieee.org/document/10984793/

[^3]: https://developers.googleblog.com/en/gemini-api-io-updates/

[^4]: https://www.ijraset.com/best-journal/Video-Summarizer

[^5]: https://irjaeh.com/index.php/journal/article/view/821

[^6]: https://ijrpr.com/uploads/V6ISSUE4/IJRPR44056.pdf

[^7]: https://dl.acm.org/doi/10.1145/3696673.3723069

[^8]: https://www.mdpi.com/2079-9292/14/5/1020

[^9]: https://ijsrem.com/download/conversational-image-recognition-chatbot/

[^10]: https://ijarsct.co.in/Paper25204.pdf

[^11]: https://ijarsct.co.in/Paper23380.pdf

[^12]: https://www.scirp.org/journal/doi.aspx?doi=10.4236/ajor.2024.146009

[^13]: https://www.youtube.com/watch?v=bCIQ4tWJsTs

[^14]: https://ai.google.dev/api/models

[^15]: https://googleapis.github.io/python-genai/

[^16]: https://developers.google.com/learn/pathways/solution-ai-gemini-getting-started-web

[^17]: https://ai.google.dev/gemini-api/docs/quickstart

[^18]: https://firebase.google.com/docs/ai-logic/models

[^19]: https://ai.google.dev

[^20]: https://www.youtube.com/watch?v=CaxPa1FuHx4

[^21]: http://arxiv.org/pdf/2501.09798.pdf

[^22]: http://arxiv.org/pdf/2406.03839.pdf

[^23]: http://arxiv.org/pdf/2412.16594.pdf

[^24]: http://conference.scipy.org/proceedings/scipy2011/pdfs/starnes.pdf

[^25]: http://arxiv.org/pdf/2402.09615.pdf

[^26]: https://arxiv.org/pdf/2312.11444.pdf

[^27]: https://joss.theoj.org/papers/10.21105/joss.05205.pdf

[^28]: https://joss.theoj.org/papers/10.21105/joss.03168.pdf

[^29]: https://arxiv.org/pdf/2305.04032.pdf

[^30]: https://arxiv.org/abs/2402.07023

[^31]: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference

[^32]: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com

[^33]: https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart

[^34]: https://cloud.google.com/vertex-ai/generative-ai/docs/models

[^35]: https://aistudio.google.com

[^36]: https://www.youtube.com/watch?v=qfWpPEgea2A

[^37]: https://gist.github.com/DF-wu/72ec3a7c2ff3247fc33b3eda07e048d0

[^38]: https://ai.google.dev/api

[^39]: https://en.wikipedia.org/wiki/Gemini_(language_model)

[^40]: https://hub.asimov.academy/tutorial/como-utilizar-a-api-do-gemini-com-python/

