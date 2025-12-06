import pika
import json
import time
import random
from pymongo import MongoClient

# Configuracoes
RABBITMQ_HOST = 'localhost'
SCRAPING_QUEUE = 'scraping_queue'
ANALYSIS_QUEUE = 'analysis_queue' # Nova fila
MONGO_URI = 'mongodb://localhost:27017/'

def get_db_connection():
    client = MongoClient(MONGO_URI)
    return client['bf_stats_db']

def mock_battlefield_api(player_name, platform):
    print(f"DEBUG: Consultando API externa para {player_name}...")
    time.sleep(1) # Simula tempo de rede
    return {
        "player_name": player_name,
        "platform": platform,
        "api_source": "Battlefieldtracker_Mock",
        "stats": {
            "kills": random.randint(100, 5000),
            "deaths": random.randint(50, 4000),
            "wins": random.randint(10, 200),
            "losses": random.randint(10, 200),
            "accuracy_percent": round(random.uniform(10.0, 30.0), 2),
            "time_played_hours": random.randint(5, 300),
            "headshots": random.randint(20, 1000)
        }
    }

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        player = message.get('player_name')
        platform = message.get('platform')
        
        print(f"Scraper: Processando {player}...")
        data = mock_battlefield_api(player, platform)

        # Salvar no MongoDB
        db = get_db_connection()
        collection = db['raw_player_stats']
        data['created_at'] = time.time()
        
        # Insert_one retorna o ID do documento criado
        result = collection.insert_one(data)
        document_id = str(result.inserted_id)
        
        print("Sucesso: Dados salvos no MongoDB.")

        # --- NOVIDADE: Avisar o Analyzer ---
        # Preparamos a mensagem para a proxima etapa
        analysis_payload = {
            "player_name": player,
            "document_id": document_id
        }

        # Publicamos na fila de analise
        ch.queue_declare(queue=ANALYSIS_QUEUE, durable=True)
        ch.basic_publish(
            exchange='',
            routing_key=ANALYSIS_QUEUE,
            body=json.dumps(analysis_payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print("Sucesso: Enviado para fila de analise.")
        # -----------------------------------

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Erro no Scraper: {e}")

def start_worker():
    print("Iniciando Worker Scraper...")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=SCRAPING_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=SCRAPING_QUEUE, on_message_callback=callback)
    print("Aguardando mensagens na fila scraping_queue...")
    channel.start_consuming()

if __name__ == '__main__':
    start_worker()