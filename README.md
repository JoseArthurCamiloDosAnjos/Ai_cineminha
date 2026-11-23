# AI_Cineminha

Assistente virtual inteligente para descoberta de filmes, trailers e informações sobre cinema. Um chatbot que entende linguagem natural e recomenda filmes baseados em gênero, ator, diretor, plataforma de streaming, ano, humor e muito mais.

---

## Objetivo

O **AI_Cineminha** é um assistente conversacional especializado em cinema que ajuda usuários a:

- Descobrir filmes por gênero (comédia, ação, terror, romance, ficção científica, drama, animação, etc.)
- Encontrar filmes por ator, diretor ou ano de lançamento
- Buscar trailers e teasers no YouTube
- Consultar disponibilidade em plataformas de streaming (Netflix, Prime Video, Disney+, Max)
- Obter sinopses, elenco, classificação indicativa e duração
- Comparar filmes e receber listas personalizadas
- Explorar filmes nacionais, clássicos, lançamentos, premiados e pouco conhecidos

---

## Tecnologias

### Backend (Python)
| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **FastAPI** | Latest | API REST assíncrona para comunicação com frontend |
| **ChatterBot** | Latest | Engine de NLP para classificação de intenções em português |
| **SQLite** | Built-in | Armazenamento do modelo treinado (banco `assistente.sqlite3`) |
| **Uvicorn** | Latest | Servidor ASGI para rodar a aplicação FastAPI |
| **Requests** | Latest | Requisições HTTP para DuckDuckGo API (fallback de busca) |
| **Threading** | Built-in | Lock para thread-safety no acesso ao ChatterBot |

### Frontend (React)
| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **React** | 19.3.1 | Interface de usuário reativa |
| **Vite** | 8.3.6 | Build tool e dev server ultrarrápido |
| **React Markdown** | 10.1.0 | Renderização de markdown nas respostas do bot |
| **Oxlint** | 1.90.0 | Linter rápido para TypeScript/JavaScript |

### Dados de Treinamento
- **intencoes.csv** — 300+ exemplos de perguntas mapeadas para 70+ intenções
- **respostas.csv** — Respostas template para cada intenção (com placeholders como `{ator}`, `{titulo}`, `{ano}`)
- **treinar.py** — Script que carrega CSVs e treina o ChatterBot via `ListTrainer`

---

## Arquitetura

```
┌─────────────────┐     HTTP/JSON      ┌─────────────────┐
│   Frontend      │ ◄─────────────────► │    Backend      │
│   (React/Vite)  │   POST /chat       │   (FastAPI)     │
└─────────────────┘                    └────────┬────────┘
                                                │
                                                ▼
                                         ┌─────────────────┐
                                         │  ChatterBot     │
                                         │  (SQLite + NLP) │
                                         └────────┬────────┘
                                                  │
                                    ┌─────────────┴─────────────┐
                                    ▼                           ▼
                            ┌───────────────┐           ┌───────────────┐
                            │ Ações Locais  │           │ DuckDuckGo    │
                            │ (abrir_video) │           │ API (fallback)│
                            └───────────────┘           └───────────────┘
```

**Fluxo da conversa:**
1. Usuário envia mensagem no frontend
2. Frontend faz `POST /chat` com histórico de mensagens
3. Backend extrai última mensagem → normaliza texto (lowercase, remove acentos, pontuação)
4. ChatterBot classifica intenção e retorna confiança
5. Se confiança ≥ 0.40: retorna resposta template (ou executa ação `abrir_video`)
6. Se confiança < 0.40: faz fallback na DuckDuckGo API + registra no `historico.csv`

---

## Passo a Passo para Rodar

### Pré-requisitos
- **Python 3.10+** (testado no 3.11)
- **Node.js 18+** e **npm**
- **Git** (opcional, para clonar)

---

### 1. Clonar / Baixar o Projeto
```bash
git clone <url-do-repositorio>
cd Ai_cineminha
```

---

### 2. Configurar o Backend

```bash
# Entrar na pasta do backend
cd Back

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows)
.\venv\Scripts\activate

# Linux/macOS: source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
# Ou manualmente:
pip install fastapi uvicorn chatterbot requests
```

> **Nota:** Se não existir `requirements.txt`, instale manualmente:
> ```bash
> pip install fastapi uvicorn chatterbot requests
> ```

---

### 3. Treinar o Modelo (Primeira vez / Atualizar dados)

```bash
# Ainda na pasta Back, com venv ativo
python treinar.py
```
Saída esperada: `Treinamento concluído.`

Isso cria/atualiza `assistente.sqlite3` com o conhecimento das intenções e respostas.

---

### 4. Rodar o Backend

```bash
# Na pasta Back, com venv ativo
python -m uvicorn main:app --reload
```
- Servidor sobe em: **http://localhost:8000**
- Docs automáticas (Swagger): **http://localhost:8000/docs**

---

### 5. Configurar e Rodar o Frontend

```bash
# Em novo terminal, na raiz do projeto
cd Front

# Instalar dependências
npm install

# Rodar em modo desenvolvimento
npm run dev
```
- Frontend abre em: **http://localhost:5173** (porta padrão do Vite)

---

### 6. Rodar Tudo Junto (Opcional)

Na raiz do projeto (`Ai_cineminha`):
```bash
npm run dev
```
Isso usa `concurrently` para subir backend (porta 8000) e frontend (porta 5173) simultaneamente.

---

## Exemplos de Uso

| Categoria | Exemplos de Perguntas |
|-----------|----------------------|
| **Gêneros** | "Me indique um filme de terror", "Quero uma comédia para rir" |
| **Ator/Diretor** | "Filmes com Leonardo DiCaprio", "O que o Nolan dirigiu?" |
| **Ano/Época** | "Filmes de 2023", "Clássicos dos anos 90" |
| **Streaming** | "O que tem na Netflix?", "Filmes no Prime Video" |
| **Trailers** | "Quero ver o trailer de Duna", "Me mostre trailers de ação" |
| **Específicos** | "Filmes brasileiros", "Documentários sobre natureza", "Trilogias recomendadas" |
| **Detalhes** | "Sinopse de Interestelar", "Elenco de The Office", "Classificação indicativa de Coringa" |
| **Comparação** | "Qual é melhor: Matrix ou Inception?" |
| **Vídeo** | "Abrir vídeo de trailer de Avatar" → abre YouTube |

---

## Estrutura de Pastas

```
Ai_cineminha/
├── Back/                    # Backend Python/FastAPI
│   ├── main.py             # API FastAPI (endpoint /chat)
│   ├── assistente.py       # Pipeline NLP + ChatterBot + DuckDuckGo
│   ├── acoes.py            # Ações especiais (abrir_video no YouTube)
│   ├── treinar.py          # Script de treinamento do modelo
│   ├── intencoes.csv       # Perguntas de treino (300+ linhas)
│   ├── respostas.csv       # Respostas template (68 intenções)
│   ├── assistente.sqlite3  # Banco do ChatterBot (gerado ao treinar)
│   ├── historico.csv       # Log de fallbacks (baixa confiança)
│   ├── respostas.csv       # Respostas para treinamento
│   └── venv/               # Ambiente virtual (ignorado no git)
│
├── Front/                   # Frontend React/Vite
│   ├── src/
│   │   ├── App.jsx         # Componente principal do chat
│   │   ├── main.jsx        # Entry point React
│   │   ├── App.css         # Estilos do chat
│   │   └── index.css       # Estilos globais
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── node_modules/       # (ignorado no git)
│
├── package.json            # Scripts raiz (concurrently)
└── README.md               # Esta documentação
```

---

## Personalização

### Adicionar Novas Intenções
1. Edite `Back/intencoes.csv` — adicione linhas: `nova_intencao,pergunta exemplo`
2. Edite `Back/respostas.csv` — adicione: `nova_intencao,resposta template`
3. Rode `python treinar.py` novamente
4. Reinicie o backend

### Placeholders nas Respostas
Use `{ator}`, `{diretor}`, `{titulo}`, `{ano}`, `{filme1}`, `{filme2}`, `{genero}` nas respostas — o frontend/backend pode substituir dinamicamente (atualmente não implementado no pipeline, mas preparado).

### Ajustar Limiar de Confiança
Em `Back/assistente.py`:
```python
LIMITE = 0.40  # Aumente para ser mais seletivo, diminua para aceitar mais
```

---

## Solução de Problemas

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: chatterbot` | `pip install chatterbot` no venv ativo |
| `sqlite3.OperationalError: database is locked` | Pare outras instâncias do backend; delete `assistente.sqlite3` e re-treine |
| Frontend não conecta no backend | Verifique se backend roda na porta 8000 e CORS permite `localhost:5173` |
| "Não encontrei uma resposta" frequente | Diminua `LIMITE` ou adicione mais exemplos em `intencoes.csv` |
| Erro ao abrir vídeo | Verifique se `webbrowser` funciona no seu SO; teste `python -m webbrowser -t "https://youtube.com"` |

---

## Licença

Projeto educacional / uso livre. Sem licença formal definida.

---

## Contribuição

1. Faça fork
2. Crie branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Adiciona X'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra Pull Request

---

**Desenvolvido com ❤️ para amantes de cinema**