from flask import Flask, jsonify, request
import pika
import json
from pymongo import MongoClient

app = Flask(__name__)

# Configurações
RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'scraping_queue'
MONGO_URI = 'mongodb://localhost:27017/'

@app.route('/')
def home():
    return jsonify({
        "status": "Online",
        "mensagem": "API Battlefield Stats Analyzer pronta."
    })

@app.route('/analyze-player', methods=['POST'])
def analyze_player():
    """
    Recebe o pedido de analise e envia para a fila do RabbitMQ
    """
    data = request.get_json()
    
    # Validacao simples
    if not data or 'player_name' not in data or 'platform' not in data:
        return jsonify({"status": "Erro", "mensagem": "Campos 'player_name' e 'platform' sao obrigatorios."}), 400

    player_name = data['player_name']
    platform = data['platform']

    try:
        # Conectar ao RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # Preparar a mensagem
        task_payload = {
            "player_name": player_name,
            "platform": platform,
            "status": "pendente"
        }
        
        # Publicar na fila
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(task_payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        connection.close()
        return jsonify({"status": "Sucesso", "mensagem": f"Jogador {player_name} enviado para analise."}), 202

    except Exception as e:
        return jsonify({"status": "Erro", "detalhe": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)