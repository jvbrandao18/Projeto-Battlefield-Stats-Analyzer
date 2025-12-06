import pika
import json
import time
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configuracoes
RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'analysis_queue' # O Analyzer escuta esta fila
MONGO_URI = 'mongodb://localhost:27017/'

def get_db_connection():
    client = MongoClient(MONGO_URI)
    return client['bf_stats_db']

def calculate_classification(kd_ratio, hours_played):
    """
    Regras de Negocio:
    - Novato: <= 10 horas
    - Veterano: 10 a 50 horas
    - Elite: > 50 horas E KD >= 2.0
    """
    if hours_played <= 10:
        return "Novato"
    elif hours_played > 50 and kd_ratio >= 2.0:
        return "Elite"
    else:
        return "Veterano"

def callback(ch, method, properties, body):
    print("Analyzer: Recebi uma tarefa!")
    try:
        message = json.loads(body)
        document_id = message.get('document_id')
        player_name = message.get('player_name')

        # 1. Buscar os dados brutos no Banco
        db = get_db_connection()
        collection = db['raw_player_stats']
        
        # Buscamos pelo ID que o Scraper nos mandou
        player_data = collection.find_one({"_id": ObjectId(document_id)})

        if not player_data:
            print("Erro: Jogador nao encontrado no banco.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # 2. Extrair metricas
        stats = player_data.get('stats', {})
        kills = stats.get('kills', 0)
        deaths = stats.get('deaths', 1) # Evitar divisao por zero
        if deaths == 0: deaths = 1
        
        hours = stats.get('time_played_hours', 0)

        # 3. Calcular KD Ratio (Kills dividido por Deaths)
        kd_ratio = round(kills / deaths, 2)

        # 4. Definir Classificacao
        rank_class = calculate_classification(kd_ratio, hours)

        print(f"Processando {player_name}: KD={kd_ratio}, Horas={hours} -> Rank: {rank_class}")

        # 5. Atualizar o documento no MongoDB com a analise
        update_data = {
            "analysis": {
                "kd_ratio": kd_ratio,
                "classification": rank_class,
                "processed_at": time.time()
            }
        }

        collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_data}
        )
        
        print("Sucesso: Analise salva no banco.")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Erro no Analyzer: {e}")

def start_analyzer():
    print("Iniciando Worker Analyzer...")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print(f"Aguardando mensagens na fila {QUEUE_NAME}...")
    channel.start_consuming()

if __name__ == '__main__':
    start_analyzer()