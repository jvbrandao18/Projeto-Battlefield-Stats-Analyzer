from flask import Flask, jsonify
import pika
from pymongo import MongoClient

app = Flask(__name__)

# Configurações de conexão (apontando para o seu Docker local)
RABBITMQ_HOST = 'localhost'
MONGO_URI = 'mongodb://localhost:27017/'

@app.route('/')
def home():
    """Rota simples para ver se a API está de pé"""
    return jsonify({
        "projeto": "Battlefield Stats Analyzer",
        "status": "Online 🚀",
        "instrucao": "Acesse /test-connection para verificar o banco e a fila."
    })

@app.route('/test-connection')
def test_connection():
    """Testa se conseguimos falar com o Docker"""
    status = {"rabbitmq": "pendente", "mongodb": "pendente"}
    
    # 1. Testar RabbitMQ
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        if connection.is_open:
            status["rabbitmq"] = "Conectado com Sucesso! ✅"
            connection.close()
    except Exception as e:
        status["rabbitmq"] = f"Erro: {str(e)} ❌"

    # 2. Testar MongoDB
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        # O comando 'ping' força uma verificação real de conexão
        client.admin.command('ping')
        status["mongodb"] = "Conectado com Sucesso! ✅"
    except Exception as e:
        status["mongodb"] = f"Erro: {str(e)} ❌"

    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True, port=5000)