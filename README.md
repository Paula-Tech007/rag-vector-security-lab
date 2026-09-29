<p align="center">
  <img src="assets/rag-vector-security-lab.png" alt="RAG Vector Security Lab" width="100%">
</p>

# RAG Vector Security Lab

Laboratório prático de **RAG e Agentic RAG aplicado à Segurança Cibernética**, utilizando PostgreSQL, pgvector, embeddings semânticos, Ollama e agentes de IA com Tool Calling e ReAct.

O projeto começou como um pipeline RAG seguro e está evoluindo progressivamente para uma arquitetura de **Agente SOC com IA**, mantendo controle de contexto, guardrails, rastreabilidade e testes automatizados.

---

## 🎯 Objetivo

Construir e evoluir uma arquitetura de IA aplicada a cenários de Segurança Cibernética capaz de:

- armazenar conhecimento em banco vetorial;
- gerar embeddings semânticos;
- realizar busca por similaridade;
- aplicar threshold de confiança;
- recuperar somente contexto relevante;
- utilizar LLM local com Ollama;
- evitar respostas baseadas em contexto não confiável;
- permitir que um agente escolha quando utilizar ferramentas;
- executar ferramentas através de Native Tool Calling;
- trabalhar com ciclos controlados de Agent Loop e ReAct;
- registrar trace operacional das ações;
- limitar execuções autônomas por guardrails;
- proteger credenciais com variáveis de ambiente;
- validar comportamento através de testes automatizados.

---

## 🧠 Evolução da arquitetura

```text
RAG
 │
 ▼
Agent Routing
 │
 ▼
LLM-based Routing
 │
 ▼
Native Tool Calling
 │
 ▼
Agent Loop
 │
 ▼
ReAct
 │
 ▼
Memory
 │
 ▼
SOC Agent
 │
 ▼
MCP / Multi-Agent
```

As etapas até **ReAct** já foram implementadas.

As etapas seguintes fazem parte do roadmap do laboratório.

---

## 🏗️ Arquitetura atual

```text
                    ┌──────────────────────┐
                    │   Entrada do usuário │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Agente SOC / Qwen  │
                    └──────────┬───────────┘
                               │
                     decisão de ferramenta
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
        responder diretamente       consultar_rag
                                             │
                                             ▼
                                      gerar embedding
                                             │
                                             ▼
                                   PostgreSQL + pgvector
                                             │
                                             ▼
                                      busca semântica
                                             │
                                             ▼
                                   threshold de confiança
                                             │
                                  ┌──────────┴──────────┐
                                  │                     │
                                  ▼                     ▼
                           contexto confiável     contexto insuficiente
                                  │                     │
                                  ▼                     ▼
                             observação           fallback seguro
                                  │
                                  ▼
                           volta ao agente
                                  │
                                  ▼
                          próxima decisão
                                  │
                                  ▼
                           resposta final
```

---

## 🔎 Pipeline RAG

O RAG continua sendo uma ferramenta central da arquitetura.

```text
Pergunta
   ↓
Embedding
   ↓
PostgreSQL + pgvector
   ↓
Busca por similaridade
   ↓
Threshold
   ↓
Contexto confiável?
   ├── SIM → Ollama → Resposta baseada no contexto
   └── NÃO → Resposta segura
```

Quando nenhum documento atinge o threshold mínimo, o pipeline retorna:

```text
Nao ha informacao suficiente no contexto.
```

Nesse cenário, o RAG não envia contexto inadequado ao LLM.

---

## 🤖 Agentic RAG

Além do pipeline RAG tradicional, o laboratório possui uma camada de agente responsável por decidir quando utilizar ferramentas.

Isso muda o fluxo de:

```text
Pergunta → RAG → Resposta
```

para:

```text
Pergunta
   ↓
Agente
   ↓
Decisão
   ├── responder diretamente
   └── utilizar ferramenta
              ↓
             RAG
              ↓
          observação
              ↓
            Agente
              ↓
        resposta final
```

O RAG não é substituído pelo agente.

Ele passa a funcionar como uma **ferramenta especializada de recuperação de conhecimento**.

---

## 🧭 Agent Routing

A primeira evolução agentic implementada foi o roteamento de ferramentas.

O agente consegue distinguir situações em que deve:

```text
consultar_rag
```

ou:

```text
nenhuma ferramenta
```

O laboratório possui tanto roteamento determinístico quanto roteamento baseado em LLM para fins de aprendizado e comparação arquitetural.

---

## 🧠 LLM-based Tool Routing

O projeto evoluiu o roteamento para permitir que o modelo determine quando uma ferramenta é necessária.

Essa etapa introduziu a separação entre:

```text
entrada
   ↓
modelo
   ↓
decisão de ferramenta
   ↓
execução
```

Essa implementação foi mantida como parte da evolução didática do laboratório.

---

## 🛠️ Native Tool Calling

O agente utiliza o endpoint de chat do Ollama com definição estruturada de ferramentas.

Ferramenta atualmente disponível:

```text
consultar_rag
```

O modelo pode solicitar nativamente sua execução através de `tool_calls`.

Fluxo:

```text
Usuário
   ↓
Ollama / Qwen
   ↓
tool_call
   ↓
consultar_rag
   ↓
resultado
```

Somente ferramentas explicitamente permitidas podem ser executadas.

---

## 🔄 Agent Loop

O Agent Loop permite devolver o resultado da ferramenta ao modelo.

```text
Pergunta
   ↓
Agente
   ↓
Tool Call
   ↓
RAG
   ↓
Observação
   ↓
Agente
   ↓
Resposta final
```

Essa etapa permite que o modelo utilize o resultado real da ferramenta antes de produzir sua resposta.

---

## 🔁 ReAct

O laboratório implementa um ciclo ReAct controlado.

Conceitualmente:

```text
Reason
   ↓
Act
   ↓
Observe
   ↓
continuar ou finalizar
```

Na implementação, o raciocínio interno do modelo não é armazenado ou exposto.

O sistema registra apenas informações operacionais necessárias para auditoria:

```text
passo
ferramenta
argumentos
status
```

Exemplo de trace:

```json
{
  "passo": 1,
  "ferramenta": "consultar_rag",
  "argumentos": {
    "pergunta": "Como identificar e analisar um incidente de phishing?"
  },
  "status": "ok"
}
```

O número máximo atual de passos é:

```python
MAX_REACT_STEPS = 3
```

Isso funciona como um guardrail contra ciclos indefinidos.

---

## 🛡️ Guardrails

A arquitetura possui controles para reduzir comportamentos inesperados:

- allowlist de ferramentas;
- validação dos argumentos;
- threshold mínimo para contexto;
- fallback quando não existe contexto confiável;
- limite de passos ReAct;
- proteção contra loops infinitos;
- separação entre conhecimento recuperado e decisão do agente;
- credenciais fora do código-fonte.

---

## 🔐 Threshold de confiança

O projeto utiliza:

```python
SIMILARIDADE_MINIMA = 0.60
```

A decisão é centralizada em:

```python
contexto_confiavel(similaridade)
```

Somente documentos que atingem o limite configurado são considerados contexto confiável.

---

## 🔎 Exemplo de busca vetorial

Exemplo validado durante o desenvolvimento:

```text
Pergunta:
Houve alguma tentativa de phishing?

Resultado:

similaridade: 0.8217
status: ACEITO

Foi detectada uma tentativa de phishing contra funcionarios.
```

Outro resultado validado:

```text
Pergunta:
O firewall bloqueou alguma tentativa de acesso?

similaridade: 0.8897
status: ACEITO
```

Resultados abaixo do threshold são descartados.

---

## 🚫 Proteção contra contexto insuficiente

Exemplo validado:

```text
Pergunta:
Existe algum incidente envolvendo Kubernetes?

Melhor similaridade:
0.2987

Resultado:
Nao ha informacao suficiente no contexto.
```

O objetivo é impedir que documentos semanticamente distantes sejam utilizados como base para respostas.

---

## 🧰 Tecnologias

| Tecnologia | Utilização |
|---|---|
| Python | RAG, agente e processamento |
| PostgreSQL | Persistência de documentos |
| pgvector | Banco e busca vetorial |
| Sentence Transformers | Embeddings |
| Ollama | Execução local do LLM |
| Qwen | Modelo utilizado pelo agente |
| Docker | Infraestrutura PostgreSQL + pgvector |
| Pytest | Testes automatizados |
| Git | Versionamento |
| GitHub | Repositório e evolução do projeto |

---

## 📂 Estrutura do projeto

```text
rag-vector-security-lab/
│
├── assets/
│   └── rag-vector-security-lab.png
│
├── src/
│   ├── agente_soc.py
│   ├── busca_pgvector.py
│   ├── busca_semantica.py
│   ├── config.py
│   ├── ingestao_pgvector.py
│   ├── primeiro_embedding.py
│   └── rag.py
│
├── tests/
│   ├── test_agente_soc.py
│   ├── test_agent_loop.py
│   ├── test_filtrar_contexto.py
│   ├── test_native_tool_calling.py
│   ├── test_ollama_native_tools.py
│   ├── test_rag_refatoracao.py
│   ├── test_react.py
│   ├── test_threshold.py
│   ├── test_threshold_comportamento.py
│   └── test_tool_calling.py
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

O arquivo `.env` é local e não deve ser versionado.

---

## 🐘 PostgreSQL + pgvector

Subir a infraestrutura:

```powershell
docker compose up -d
```

Verificar:

```powershell
docker compose ps
```

O laboratório utiliza PostgreSQL com a extensão pgvector para persistência e recuperação vetorial.

---

## 🦙 Ollama

Modelos disponíveis no ambiente de desenvolvimento:

```text
qwen3:4b-instruct
embeddinggemma:latest
```

O agente utiliza Qwen para decisões e Native Tool Calling.

O pipeline de embeddings do RAG utiliza Sentence Transformers.

---

## 🧪 Testes automatizados

Execute:

```powershell
python -m pytest -q
```

Estado atual validado:

```text
40 passed
```

Os testes cobrem:

- threshold de confiança;
- filtragem de contexto;
- comportamento do RAG;
- roteamento do agente;
- LLM-based routing;
- Native Tool Calling;
- execução de ferramentas;
- Agent Loop;
- ReAct;
- limite de passos;
- comportamento sem necessidade de ferramenta.

---

## ▶️ Execução

### 1. Iniciar PostgreSQL

```powershell
docker compose up -d
```

### 2. Ativar ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Configurar variáveis de ambiente

Utilize o `.env.example` como referência.

Nunca versione credenciais reais ou o arquivo `.env`.

### 4. Executar testes

```powershell
python -m pytest -q
```

### 5. Executar RAG

```powershell
python src\rag.py "Houve alguma tentativa de phishing?"
```

---

## 📚 Conceitos explorados

O laboratório trabalha atualmente com:

- Retrieval-Augmented Generation (RAG);
- Agentic RAG;
- Vector Databases;
- Semantic Search;
- Embeddings;
- Context Retrieval;
- Threshold de confiança;
- LLM local;
- Tool Routing;
- Tool Calling;
- Native Tool Calling;
- Agent Loop;
- ReAct;
- Guardrails;
- PostgreSQL;
- pgvector;
- Ollama;
- testes automatizados;
- segurança de credenciais;
- IA aplicada à Cibersegurança.

---

# 🗺️ Roadmap

As funcionalidades abaixo são **evoluções planejadas** e ainda não devem ser interpretadas como funcionalidades implementadas.

## 🧠 Memory e estado

- [ ] Memory de sessão;
- [ ] Memory persistente;
- [ ] histórico estruturado de investigação;
- [ ] estado compartilhado entre etapas do agente;
- [ ] recuperação seletiva de memória.

## 🛡️ Robustez e segurança do agente

- [ ] Tool Error Handling;
- [ ] tratamento de indisponibilidade de banco e APIs;
- [ ] timeout controlado de ferramentas;
- [ ] retry controlado;
- [ ] validação avançada de argumentos;
- [ ] políticas de execução por ferramenta;
- [ ] guardrails avançados.

## 🔍 Capacidades SOC

- [ ] enriquecimento de IOCs;
- [ ] análise de IPs, domínios, URLs e hashes;
- [ ] Threat Intelligence;
- [ ] integração com MISP;
- [ ] consulta de CVEs e vulnerabilidades;
- [ ] correlação de eventos;
- [ ] classificação de incidentes;
- [ ] triagem SOC N1;
- [ ] decisão estruturada de incidentes;
- [ ] recomendação de escalonamento.

## 🔧 Novas ferramentas do agente

- [ ] ferramenta de enriquecimento de IOC;
- [ ] ferramenta de consulta de vulnerabilidades;
- [ ] ferramenta de consulta de Threat Intelligence;
- [ ] ferramenta de correlação;
- [ ] ferramenta de consulta de eventos;
- [ ] ferramentas SOC especializadas.

## ⚙️ Automação

- [ ] integração com n8n;
- [ ] workflows de resposta a incidentes;
- [ ] entrada de alertas via webhook;
- [ ] integração com APIs de segurança;
- [ ] automação de triagem;
- [ ] automação de enriquecimento;
- [ ] escalonamento automatizado controlado.

## 🔌 MCP

- [ ] integração com Model Context Protocol;
- [ ] exposição controlada de ferramentas via MCP;
- [ ] servidores MCP especializados;
- [ ] integração entre agente e serviços externos.

## 🤖 Multi-Agent

- [ ] arquitetura Multi-Agent;
- [ ] agente de triagem;
- [ ] agente de Threat Intelligence;
- [ ] agente de enriquecimento;
- [ ] agente de correlação;
- [ ] agente de decisão;
- [ ] coordenação entre agentes.

## 📊 Observabilidade e avaliação

- [ ] logging estruturado;
- [ ] tracing de execução;
- [ ] métricas de Tool Calling;
- [ ] métricas de latência;
- [ ] avaliação automática do RAG;
- [ ] avaliação das respostas do agente;
- [ ] avaliação de recuperação;
- [ ] acompanhamento de falhas de ferramentas;
- [ ] auditoria das ações do agente.

## 🌐 Serviços e interfaces

- [ ] API com FastAPI;
- [ ] endpoints para análise de incidentes;
- [ ] interface web;
- [ ] dashboard de investigações;
- [ ] visualização do trace operacional.

---

## 🚀 Visão futura

A evolução planejada do laboratório é:

```text
Evento / Alerta de Segurança
            ↓
        Agente SOC
            ↓
          Triagem
            ↓
           ReAct
            ↓
 ┌──────────┼───────────┐
 ↓          ↓           ↓
RAG    Threat Intel   Enriquecimento
 │          │           │
 └──────────┼───────────┘
            ↓
     Memory / Estado
            ↓
        Correlação
            ↓
   Decisão estruturada
            ↓
          n8n
            ↓
 Resposta / Escalonamento
```

Em uma evolução posterior:

```text
                  Orquestrador
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
Agente Triagem   Agente Threat    Agente Correlação
                     Intel
       │               │                │
       └───────────────┼────────────────┘
                       │
                       ▼
                  MCP / Tools
                       │
                       ▼
              Sistemas de Segurança
```

O objetivo de longo prazo é transformar o laboratório em uma arquitetura experimental de **Agentes de IA aplicados a operações SOC**, mantendo segurança, rastreabilidade, observabilidade e controle das ações.

---

## 👩‍💻 Autora

**Paula Sabino**

Cybersecurity • Inteligência Artificial • Automação • RAG • Agentic AI

GitHub: **Paula-Tech007**

---

## 📌 Status do laboratório

| Componente | Status |
|---|---|
| Pipeline RAG | ✅ Implementado |
| PostgreSQL + pgvector | ✅ Implementado |
| Embeddings | ✅ Implementado |
| Busca semântica | ✅ Implementado |
| Threshold | ✅ Implementado |
| Ollama | ✅ Implementado |
| Fallback seguro | ✅ Implementado |
| Agent Routing | ✅ Implementado |
| LLM-based Routing | ✅ Implementado |
| Native Tool Calling | ✅ Implementado |
| Agent Loop | ✅ Implementado |
| ReAct | ✅ Implementado |
| Trace operacional | ✅ Implementado |
| Limite de passos | ✅ Implementado |
| Testes automatizados | ✅ 40 testes |
| Memory | 📌 Roadmap |
| Tool Error Handling | 📌 Roadmap |
| n8n | 📌 Roadmap |
| MCP | 📌 Roadmap |
| Multi-Agent | 📌 Roadmap |
| Observabilidade | 📌 Roadmap |

**Projeto funcional, testado e em evolução contínua.**