import pika
import json
import time
import random
from pymongo import MongoClient

# Configuracoes de Conexao
RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'scraping_queue'
MONGO_URI = 'mongodb://localhost:27017/'

def get_db_connection():
    """Conecta ao MongoDB"""
    client = MongoClient(MONGO_URI)
    return client['bf_stats_db']

def mock_battlefield_api(player_name, platform):
    """
    SIMULACAO: Finge que vai numa API externa buscar dados.
    Retorna dados aleatorios para podermos testar o sistema.
    """
    print(f"DEBUG: Consultando API externa para {player_name}...")
    time.sleep(2) # Simula o tempo de resposta da internet
    
    # Gera dados ficticios para teste
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
    """Funcao disparada quando chega uma mensagem na fila"""
    try:
        # 1. Ler a mensagem
        message = json.loads(body)
        player = message.get('player_name')
        platform = message.get('platform')
        
        print(f"Processando jogador: {player} na plataforma {platform}")

        # 2. Coletar dados (Scraping)
        data = mock_battlefield_api(player, platform)

        # 3. Salvar no MongoDB (Dados Brutos)
        db = get_db_connection()
        collection = db['raw_player_stats']
        
        # Inserimos os dados e adicionamos um timestamp
        data['created_at'] = time.time()
        collection.insert_one(data)
        
        print("Sucesso: Dados coletados e salvos no MongoDB.")

        # 4. Confirmar para o RabbitMQ que a tarefa foi feita
        # Isso remove a mensagem da fila
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        # Em caso de erro, nao enviamos o 'ack', entao a mensagem volta para a fila depois

def start_worker():
    """Inicia o loop do Worker"""
    print("Iniciando Worker Scraper...")
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    # Garante que a fila existe
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Define que so pega 1 tarefa por vez (para nao sobrecarregar)
    channel.basic_qos(prefetch_count=1)

    # Configura o consumo
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print("Aguardando mensagens na fila scraping_queue. Para sair pressione CTRL+C")
    channel.start_consuming()

if __name__ == '__main__':
    start_worker()