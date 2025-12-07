# Battlefield Stats Analyzer

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-API-green.svg)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-Messaging-orange.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Database-green.svg)
![Docker](https://img.shields.io/badge/Docker-Container-blue.svg)

---

## Visão Geral
**Battlefield Stats Analyzer** é um sistema desenvolvido para **praticar e aprimorar conhecimentos de programação full stack**, abrangendo **backend, frontend, integrações via API, containers Docker e banco de dados**.  
O objetivo é **coletar e analisar estatísticas de jogadores**, classificando automaticamente estilos de jogo e exibindo resultados em **dashboards e relatórios**.

---

## Arquitetura
O projeto segue uma **arquitetura modular baseada em microserviços**, com comunicação assíncrona via **RabbitMQ**:

**Fluxo de Dados:**
1.  **API (Flask):** Recebe o pedido de análise do usuário.
2.  **RabbitMQ (Scraping Queue):** Enfileira o pedido.
3.  **Worker Scraper:** Consome a fila, coleta dados (Mock/API Externa) e salva dados brutos no MongoDB.
4.  **RabbitMQ (Analysis Queue):** Notifica que há novos dados.
5.  **Worker Analyzer:** Processa os dados brutos, calcula KD Ratio, define a Patente (Novato/Veterano/Elite) e atualiza o banco.

---

## Fluxo de Funcionamento
1. Usuário envia uma requisição `POST /analyze-player` informando nome e plataforma.  
2. A API publica o pedido na fila `scraping`.  
3. O **Worker Scraper** consome a fila, coleta os dados e grava em `players_raw`.  
4. O **Worker Analyzer** lê esses dados, calcula estatísticas (ex: KD Ratio, acurácia, tempo de jogo) e salva o resultado em `players_analyzed`.  
5. O usuário pode consultar:
   - `GET /player/<player_name>`  
   - `GET /ranking?top=N`

---

## Regras de Classificação
| Métrica | Cálculo | Classificação |
|----------|----------|---------------|
| **KD Ratio** | `kills / deaths` | — |
| **Horas jogadas** | Extraídas de `time_played` | — |
| **Categoria do jogador** | • Novato ≤ 10h<br>• Veterano 10–50h<br>• Elite > 50h e KD ≥ 2.0 |
| **Nível de acurácia** | • low < 15%<br>• medium 15–25%<br>• high > 25% |

---

## Estrutura de Pastas
```
.
├── api/                  → API Flask (entrada de dados e consulta)
│    ├── app.py
│    ├── routes/
│    └── services/
│         ├── db.py
│         └── mq.py
│
├── worker_scraper/       → Worker de scraping (fila 'scraping')
│    ├── main.py
│    └── scrapers/
│         ├── tracker_scraper.py
│         └── mocks/
│              └── mock_response.json
│
├── worker_analyzer/      → Worker de análise (fila 'analysis')
│    ├── main.py
│    └── analyzer/
│         └── stats_processor.py
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Variáveis de Ambiente
Crie um `.env` na raiz baseada em `.env.example`:

```ini
MONGODB_URI=mongodb://<usuario>:<senha>@mongodb:27017/bf_stats
AMQP_URL=amqp://<usuario>:<senha>@rabbitmq:5672/
FLASK_ENV=development
```

---

## Como Rodar o Projeto

### Pré-requisitos
* Docker e Docker Compose
* Python 3.10+ (Opcional, se quiser rodar scripts locais fora do Docker)

### Passo a Passo

1.  **Clone o repositório**
    ```bash
    git clone [https://github.com/seu-usuario/battlefield-stats-analyzer.git](https://github.com/seu-usuario/battlefield-stats-analyzer.git)
    cd battlefield-stats-analyzer
    ```

2.  **Suba a Infraestrutura (RabbitMQ + MongoDB)**
    ```bash
    docker compose up -d
    ```

3.  **Configure o Ambiente Python (Local)**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    
    pip install flask pika pymongo requests
    ```

4.  **Inicie os Serviços (Em terminais separados)**
    * **Terminal 1 (API):** `python api/app.py`
    * **Terminal 2 (Scraper):** `python worker_scraper/main.py`
    * **Terminal 3 (Analyzer):** `python worker_analyzer/main.py`

## Endpoints da API

| Método | Rota | Descrição | Exemplo de Body |
| :--- | :--- | :--- | :--- |
| `POST` | `/analyze-player` | Envia jogador para análise | `{"player_name": "Nick", "platform": "pc"}` |
| `GET` | `/player/<nome>` | Retorna ficha do jogador | - |
| `GET` | `/ranking` | Retorna Top 10 (KD Ratio) | - |

## Exemplo de Uso

**1. Solicitar Análise:**
```bash
curl -X POST http://localhost:5000/analyze-player \
     -H "Content-Type: application/json" \
     -d '{"player_name":"Soldado01","platform":"pc"}'
```
## Licença

Projeto educacional e não comercial, uso *exclusivo* para estudo e experimentação.
