import pika
import json
import time
import requests
from pymongo import MongoClient

# Configuracoes
RABBITMQ_HOST = 'localhost'
SCRAPING_QUEUE = 'scraping_queue'
ANALYSIS_QUEUE = 'analysis_queue'
MONGO_URI = 'mongodb://localhost:27017/'

def get_db_connection():
    client = MongoClient(MONGO_URI)
    return client['bf_stats_db']

def fetch_battlefield_stats(player_name, platform):
    """
    CONEXAO REAL: Busca dados na GameTools API para BATTLEFIELD 6.
    Docs: https://api.gametools.network/docs#/Battlefield%206/bf6player_bf6_player__get
    """
    print(f"DEBUG: Buscando dados BF6 para {player_name} ({platform})...")
    
    # IMPORTANTE: 
    # O BF6 é focado na nova geração. As plataformas geralmente são:
    # 'pc', 'ps5', 'xboxseries' (verifique se 'xbox' funciona para Series S/X)
    
    # Tentativa padrão na rota de estatísticas
    url = f"https://api.gametools.network/bf6/stats/?name={player_name}&platform={platform}"
    
    # DICA: Se der erro 404, tente mudar '/stats/' para '/player/' na URL acima,
    # pois o nome do endpoint na documentação que você mandou é "bf6_player".

    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 404:
            print(f"Erro: Jogador {player_name} não encontrado no BF6.")
            return None
            
        if response.status_code != 200:
            print(f"Erro API BF6: {response.status_code}")
            return None

        api_data = response.json()
        
        # O BF6 pode retornar o tempo em milissegundos ou segundos. 
        # Ajuste a divisão se o número de horas ficar estranho.
        seconds_played = api_data.get('secondsPlayed', 0)
        hours_played = round(seconds_played / 3600, 2)

        return {
            "player_name": player_name,
            "platform": platform,
            "api_source": "GameTools_BF6_Real",
            "stats": {
                # Campos comuns do BF (confirme se os nomes das chaves são iguais no JSON do BF6)
                "kills": api_data.get('kills', 0),
                "deaths": api_data.get('deaths', 0),
                "wins": api_data.get('wins', 0),
                "losses": api_data.get('loses', 0),
                
                # Tratamento de erro caso o campo venha vazio ou diferente
                "accuracy_percent": float(str(api_data.get('accuracy', '0')).replace('%','')),
                
                "time_played_hours": hours_played,
                "headshots": api_data.get('headshots', 0),
                
                # BF6 tem classes novas, podemos tentar pegar a classe favorita se a API mandar
                "favorite_class": api_data.get('classes', [{}])[0].get('class_name', 'Unknown') if api_data.get('classes') else "N/A"
            }
        }

    except Exception as e:
        print(f"Exceção ao conectar na API BF6: {e}")
        return None

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        player = message.get('player_name')
        platform = message.get('platform') # pc, ps5, xbox
        
        print(f"Scraper: Iniciando busca para {player}...")

        # CHAMADA REAL AQUI
        data = fetch_battlefield_stats(player, platform)

        if data:
            # Salvar no MongoDB
            db = get_db_connection()
            collection = db['raw_player_stats']
            data['created_at'] = time.time()
            
            result = collection.insert_one(data)
            document_id = str(result.inserted_id)
            print("Sucesso: Dados REAIS salvos no MongoDB.")

            # Avisar o Analyzer
            analysis_payload = {
                "player_name": player,
                "document_id": document_id
            }

            ch.queue_declare(queue=ANALYSIS_QUEUE, durable=True)
            ch.basic_publish(
                exchange='',
                routing_key=ANALYSIS_QUEUE,
                body=json.dumps(analysis_payload),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            print("Sucesso: Enviado para fila de analise.")
        
        else:
            print("Aviso: Nao foi possivel coletar dados (Jogador nao existe ou API offline).")

        # Sempre damos o ACK, mesmo se falhar a busca, para tirar a mensagem da fila
        # Num sistema real, poderiamos mandar para uma fila de "retry" (tentar de novo)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Erro critico no Scraper: {e}")
        # Se der erro de codigo, nao damos ACK para tentar de novo ou logar
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_worker():
    print("Iniciando Worker Scraper (MODO REAL - BF2042)...")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=SCRAPING_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=SCRAPING_QUEUE, on_message_callback=callback)
    print("Aguardando mensagens na fila scraping_queue...")
    channel.start_consuming()

if __name__ == '__main__':
    start_worker()