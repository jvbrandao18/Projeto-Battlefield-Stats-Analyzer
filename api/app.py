from flask import Flask, jsonify, request
import pika
import json
from pymongo import MongoClient, DESCENDING

app = Flask(__name__)

# Configurações
RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'scraping_queue'
MONGO_URI = 'mongodb://localhost:27017/'

def get_db_collection():
    """Conecta ao banco e retorna a colecao de estatisticas"""
    client = MongoClient(MONGO_URI)
    db = client['bf_stats_db']
    return db['raw_player_stats']

@app.route('/')
def home():
    return jsonify({
        "status": "Online",
        "rotas": [
            "POST /analyze-player",
            "GET /player/<nome>",
            "GET /ranking"
        ]
    })

# --- ROTA DE ENVIO (POST) ---
@app.route('/analyze-player', methods=['POST'])
def analyze_player():
    data = request.get_json()
    
    if not data or 'player_name' not in data or 'platform' not in data:
        return jsonify({"status": "Erro", "mensagem": "Campos obrigatorios faltando."}), 400

    player_name = data['player_name']
    platform = data['platform']

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        task_payload = {
            "player_name": player_name,
            "platform": platform,
            "status": "pendente"
        }
        
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(task_payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        return jsonify({"status": "Sucesso", "mensagem": f"Jogador {player_name} enviado para fila."}), 202

    except Exception as e:
        return jsonify({"status": "Erro", "detalhe": str(e)}), 500

# --- NOVAS ROTAS DE LEITURA (GET) ---

@app.route('/player/<string:player_name>', methods=['GET'])
def get_player(player_name):
    """Busca os dados de um jogador especifico"""
    collection = get_db_collection()
    
    # Busca o documento mais recente desse jogador
    # sort descendo pelo _id garante que pegamos o ultimo inserido
    player_data = collection.find_one(
        {"player_name": player_name},
        sort=[('_id', DESCENDING)]
    )

    if player_data:
        # Convertendo o ObjectId para string para nao dar erro no JSON
        player_data['_id'] = str(player_data['_id'])
        return jsonify(player_data), 200
    else:
        return jsonify({"status": "Erro", "mensagem": "Jogador nao encontrado ou ainda nao processado."}), 404

@app.route('/ranking', methods=['GET'])
def get_ranking():
    """Retorna o TOP 10 jogadores baseado no KD Ratio"""
    collection = get_db_collection()
    
    # Busca usuarios que ja tem analise feita (campo 'analysis' existe)
    # Ordena por KD Ratio (decrescente: -1 ou DESCENDING)
    # Limita a 10 resultados
    top_players = collection.find(
        {"analysis": {"$exists": True}}
    ).sort("analysis.kd_ratio", DESCENDING).limit(10)

    lista_ranking = []
    for doc in top_players:
        doc['_id'] = str(doc['_id'])
        lista_ranking.append(doc)

    return jsonify(lista_ranking), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)