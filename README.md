# Battlefield Stats Analyzer

![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-API-lightgrey?logo=flask)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![MongoDB](https://img.shields.io/badge/MongoDB-Database-green?logo=mongodb)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-Queue-orange?logo=rabbitmq)

---

## Visão Geral
**Battlefield Stats Analyzer** é um sistema desenvolvido para **praticar e aprimorar conhecimentos de programação full stack**, abrangendo **backend, frontend, integrações via API, containers Docker e banco de dados**.  
O objetivo é **coletar e analisar estatísticas de jogadores**, classificando automaticamente estilos de jogo e exibindo resultados em **dashboards e relatórios**.

---

## Arquitetura
O projeto segue uma **arquitetura modular baseada em microserviços**, com comunicação assíncrona via **RabbitMQ**:

| Componente | Função |
|-------------|--------|
| **API** | Endpoint Flask responsável por receber requisições e publicar mensagens nas filas. |
| **Worker Scraper** | Obtém dados do jogador via API (ou mock) e armazena no banco. |
| **Worker Analyzer** | Processa e classifica os dados brutos em métricas consolidadas. |
| **RabbitMQ** | Fila de mensagens para desacoplamento dos serviços. |
| **MongoDB** | Banco NoSQL para armazenamento dos dados coletados e analisados. |

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
.
├── api/                  → API Flask (entrada de dados e consulta) |
│    ├── app.py  |                                                 
│    ├── routes/ |
│    └── services/ |
│    │       ├── db.py |
│    │       └── mq.py |
├── worker_scraper/       → Worker de scraping (fila 'scraping') |
│    ├── main.py |
│    └── scrapers/ |
│          ├── tracker_scraper.py |
│          └── mocks/ |
│                └── mock_response.json |
├── worker_analyzer/      → Worker de análise (fila 'analysis') |
│    ├── main.py |
│    └── analyzer/ |
│          └── stats_processor.py |
├── docker-compose.yml |
├── .env.example |
└── README.md |

---

Variáveis de Ambiente
Crie um `.env` na raiz baseada em `.env.example`:
```ini
MONGODB_URI=mongodb://mongodb:27017/bf_stats
AMQP_URL=amqp://guest:guest@rabbitmq:5672/
FLASK_ENV=development
```

---

## Execução com Docker
### 1. Build e subida:
  ```bash
  docker compose up -d --build
  ```
### 2. Logs:
```bash
  docker compose logs -f api worker_scraper worker_analyzer
```

### 3. Parada:
```bash
  docker compose down
```


--------------------------------------------------------------

🧭 Licença

Projeto educacional e não comercial, para estudo e experimentação.
