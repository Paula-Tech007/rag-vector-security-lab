<p align="center">
  <img src="assets/rag-vector-security-lab.png" alt="RAG Vector Security Lab" width="100%">
</p>

# RAG Vector Security Lab

Laboratório prático de **RAG e Agentic RAG aplicado à Segurança Cibernética**, utilizando PostgreSQL, pgvector, embeddings semânticos, Ollama e agentes de IA com Tool Calling, ReAct e Memory.

O projeto começou como um pipeline RAG seguro e está evoluindo progressivamente para uma arquitetura de **Agente SOC com IA**, mantendo controle de contexto, guardrails, rastreabilidade, memória de sessão e testes automatizados.

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
- manter contexto entre interações através de Memory;
- utilizar memória para orientar decisões e consultas posteriores;
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
Session Memory
 │
 ▼
Persistent Memory
 │
 ▼
SOC Agent
 │
 ▼
MCP / Multi-Agent
```

As etapas até **Session Memory** já foram implementadas e validadas.

A próxima evolução planejada é a implementação de **Persistent Memory**, permitindo que o agente recupere o contexto de uma investigação mesmo após o encerramento do processo Python.

As demais etapas continuam fazendo parte do roadmap do laboratório.

---

## 🏗️ Arquitetura atual

```text
                     ┌──────────────────────┐
                     │   Entrada do usuário │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │    Session Memory    │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │   Agente SOC / Qwen  │
                     └──────────┬───────────┘
                                │
                       decisão de ferramenta
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
                 ▼                             ▼
        responder diretamente           consultar_rag
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
                             contexto confiável    contexto insuficiente
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
                                    │
                                    ▼
                              Session Memory
```

A memória de sessão fornece ao agente o histórico necessário para interpretar referências contextuais entre diferentes interações.

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
Memory
   ↓
Agente
   ↓
Decisão
   ├── responder diretamente
   │
   └── utilizar ferramenta
              ↓
             RAG
              ↓
          observação
              ↓
            Agente
              ↓
        resposta final
              ↓
            Memory
```

O RAG não é substituído pelo agente.

Ele passa a funcionar como uma **ferramenta especializada de recuperação de conhecimento**.

A Memory também não substitui o RAG:

```text
RAG    → conhecimento externo recuperado
Memory → contexto e estado das interações
ReAct  → decisão, ação e observação
```

Esses componentes trabalham em conjunto dentro da arquitetura Agentic RAG.

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

## 🧠 Session Memory

O laboratório possui uma camada de **memória de sessão** integrada ao agente ReAct.

A implementação utiliza:

```text
SessionMemory
```

A memória mantém históricos independentes através de:

```text
session_id
```

Cada sessão pode armazenar mensagens com os papéis:

```text
user
assistant
tool
```

A implementação permite:

- adicionar mensagens;
- recuperar o histórico de uma sessão;
- manter sessões isoladas;
- limpar uma sessão;
- consultar o tamanho do histórico;
- validar `session_id`;
- validar papéis de mensagens;
- impedir conteúdo vazio;
- retornar cópias do histórico para evitar alteração externa acidental.

O agente utiliza:

```python
executar_react_com_memoria(...)
```

para combinar o histórico da sessão com o ciclo ReAct.

Fluxo:

```text
Interação 1
   ↓
Usuário informa contexto
   ↓
SessionMemory
   ↓
Agente responde
   ↓
SessionMemory
   ↓
Interação 2
   ↓
Histórico recuperado
   ↓
Agente interpreta o novo pedido
   ↓
Decide responder ou utilizar ferramenta
```

A memória atual é mantida durante a execução do processo Python.

Portanto:

```text
Processo Python ativo
        ↓
Memory disponível

Processo encerrado
        ↓
Memory em RAM é perdida
```

A persistência entre execuções será tratada na próxima etapa do projeto através de **Persistent Memory**.

---

## 🔗 Memory + ReAct + RAG

A integração completa entre Memory, ReAct e RAG foi validada em execução real.

O cenário utilizado foi uma investigação de phishing.

Primeira interação:

```text
Estamos investigando um incidente de phishing.
```

O contexto foi armazenado na sessão.

Na interação seguinte, o usuário solicitou:

```text
Consulte nossa base de conhecimento e verifique
se existe contexto relacionado a esse incidente.
```

A segunda mensagem não repetiu explicitamente o tipo do incidente.

O agente recuperou o contexto anterior da Memory e gerou uma chamada de ferramenta semelhante a:

```json
{
  "passo": 1,
  "ferramenta": "consultar_rag",
  "argumentos": {
    "pergunta": "O que é phishing e quais são os sinais de alerta comuns em um incidente de phishing?"
  },
  "status": "ok"
}
```

Isso validou o fluxo:

```text
Session Memory
      ↓
ReAct
      ↓
Native Tool Calling
      ↓
consultar_rag
      ↓
Embedding
      ↓
PostgreSQL + pgvector
      ↓
Threshold
      ↓
Observação
      ↓
Agente
      ↓
Resposta final
      ↓
Session Memory
```

O teste demonstrou que o agente consegue utilizar informações armazenadas anteriormente para contextualizar uma nova decisão e construir uma consulta ao RAG.

---

## 🛡️ Guardrails

A arquitetura possui controles para reduzir comportamentos inesperados:

- allowlist de ferramentas;
- validação dos argumentos;
- threshold mínimo para contexto;
- fallback quando não existe contexto confiável;
- limite de passos ReAct;
- proteção contra loops infinitos;
- isolamento de memória por `session_id`;
- validação das mensagens armazenadas em Memory;
- separação entre conhecimento recuperado e decisão do agente;
- credenciais fora do código-fonte.

Guardrails adicionais para grounding de respostas, falhas de ferramentas e persistência serão implementados nas próximas etapas.

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
| Python | RAG, agente, Memory e processamento |
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
│   ├── memory.py
│   ├── primeiro_embedding.py
│   └── rag.py
│
├── tests/
│   ├── test_agente_soc.py
│   ├── test_agent_loop.py
│   ├── test_agent_memory.py
│   ├── test_filtrar_contexto.py
│   ├── test_memory.py
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

A próxima evolução também utilizará persistência para permitir que a Memory sobreviva ao encerramento do processo do agente.

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
54 passed
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
- comportamento sem necessidade de ferramenta;
- Session Memory;
- armazenamento de mensagens;
- recuperação de histórico;
- isolamento entre sessões;
- limpeza de sessão;
- validação de `session_id`;
- validação de mensagens;
- proteção do histórico contra alteração externa;
- integração entre Memory e ReAct;
- utilização do histórico em interações posteriores;
- execução de ferramenta dentro do fluxo com Memory.

Além da suíte automatizada, foi validado um cenário real E2E utilizando:

```text
Memory
  ↓
ReAct
  ↓
Native Tool Calling
  ↓
RAG
  ↓
PostgreSQL + pgvector
  ↓
Ollama
  ↓
Resposta
```

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
- Session Memory;
- gerenciamento de estado por sessão;
- Guardrails;
- PostgreSQL;
- pgvector;
- Ollama;
- testes automatizados;
- segurança de credenciais;
- IA aplicada à Cibersegurança.

---

# 🗺️ Roadmap

O roadmap abaixo diferencia funcionalidades já implementadas das próximas evoluções do laboratório.

## 🧠 Memory e estado

- [x] Memory de sessão;
- [x] integração entre Memory e ReAct;
- [x] utilização de contexto anterior em novas decisões;
- [x] isolamento de memória por `session_id`;
- [x] validação automatizada da Session Memory;
- [x] validação E2E de Memory + ReAct + RAG;
- [ ] Memory persistente;
- [ ] histórico estruturado de investigação;
- [ ] estado compartilhado entre etapas do agente;
- [ ] recuperação seletiva de memória;
- [ ] políticas de retenção de memória.

---

## 🛡️ Robustez e segurança do agente

- [ ] Tool Error Handling;
- [ ] tratamento de indisponibilidade de banco e APIs;
- [ ] timeout controlado de ferramentas;
- [ ] retry controlado;
- [ ] validação avançada de argumentos;
- [ ] políticas de execução por ferramenta;
- [ ] grounding mais rígido das respostas;
- [ ] guardrails avançados.

---

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

---

## 🔧 Novas ferramentas do agente

- [ ] ferramenta de enriquecimento de IOC;
- [ ] ferramenta de consulta de vulnerabilidades;
- [ ] ferramenta de consulta de Threat Intelligence;
- [ ] ferramenta de correlação;
- [ ] ferramenta de consulta de eventos;
- [ ] ferramentas SOC especializadas.

---

## ⚙️ Automação

- [ ] integração com n8n;
- [ ] workflows de resposta a incidentes;
- [ ] entrada de alertas via webhook;
- [ ] integração com APIs de segurança;
- [ ] automação de triagem;
- [ ] automação de enriquecimento;
- [ ] escalonamento automatizado controlado.

---

## 🔌 MCP

- [ ] integração com Model Context Protocol;
- [ ] exposição controlada de ferramentas via MCP;
- [ ] servidores MCP especializados;
- [ ] integração entre agente e serviços externos.

---

## 🤖 Multi-Agent

- [ ] arquitetura Multi-Agent;
- [ ] agente de triagem;
- [ ] agente de Threat Intelligence;
- [ ] agente de enriquecimento;
- [ ] agente de correlação;
- [ ] agente de decisão;
- [ ] coordenação entre agentes.

---

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

---

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
        ┌──────────────┼────────────────┐
        │              │                │
        ▼              ▼                ▼
 Agente Triagem   Agente Threat    Agente Correlação
                       Intel
        │              │                │
        └──────────────┼────────────────┘
                       │
                       ▼
                   MCP / Tools
                       │
                       ▼
               Sistemas de Segurança
```

O objetivo de longo prazo é transformar o laboratório em uma arquitetura experimental de **Agentes de IA aplicados a operações SOC**, mantendo segurança, rastreabilidade, observabilidade, memória e controle das ações.

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
| Session Memory | ✅ Implementado |
| Memory + ReAct | ✅ Implementado |
| Memory + ReAct + RAG E2E | ✅ Validado |
| Testes automatizados | ✅ 54 testes |
| Persistent Memory | 📌 Próxima etapa |
| Tool Error Handling | 📌 Roadmap |
| n8n | 📌 Roadmap |
| MCP | 📌 Roadmap |
| Multi-Agent | 📌 Roadmap |
| Observabilidade | 📌 Roadmap |

**Projeto funcional, testado e em evolução contínua.**