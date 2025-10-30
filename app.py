# api/app.py
from flask import Flask, request, jsonify
from services.mq import publish
from services.db import get_db
import time

app = Flask(__name__)

@app.post("/analyze-player")
def analyze_player():
    data = request.get_json(force=True)
    player = data.get("player_name")
    platform = data.get("platform","pc")
    if not player:
        return jsonify({"error":"player_name é obrigatório"}), 400

    # throttle 5min
    db = get_db()
    last = db.players_raw.find_one(
        {"player_name": player, "platform": platform},
        sort=[("fetched_at",-1)]
    )
    if last and (time.time() - last["fetched_at"].timestamp()) < 300:
        return jsonify({"status":"recent","detail":"aguarde 5 min"}), 429

    publish("scraping", {"player_name": player, "platform": platform})
    return jsonify({"status":"accepted"}), 202

@app.get("/player/<player_name>")
def get_player(player_name):
    platform = request.args.get("platform","pc")
    db = get_db()
    doc = db.players_analyzed.find_one(
        {"player_name": player_name, "platform": platform},
        {"_id":0}
    )
    return (jsonify(doc), 200) if doc else (jsonify({"error":"not found"}), 404)

@app.get("/ranking")
def ranking():
    top = int(request.args.get("top",10))
    db = get_db()
    cur = db.players_analyzed.aggregate([
        {"$sort": {"kd_ratio": -1}},
        {"$limit": top},
        {"$project": {"_id":0,"player_name":1,"platform":1,"kd_ratio":1,"classification":1}}
    ])
    return jsonify(list(cur)), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
