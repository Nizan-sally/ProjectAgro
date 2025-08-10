from flask import Flask, request, jsonify, g
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from datetime import timedelta
import os
from config.settings import get_secret_key

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = get_secret_key()
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)

# Conexão com banco de dados
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('agroinsight.db')
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Autenticação
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    
    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)
    
    return jsonify({"msg": "Credenciais inválidas"}), 401

# Rotas protegidas
@app.route('/api/commodities', methods=['GET'])
@jwt_required()
def get_commodities():
    """Retorna dados de commodities agrícolas brasileiras."""
    db = get_db()
    commodities = db.execute(
        'SELECT * FROM commodities ORDER BY timestamp DESC LIMIT 100'
    ).fetchall()
    
    return jsonify([dict(row) for row in commodities])

@app.route('/api/commodities/<commodity>', methods=['GET'])
@jwt_required()
def get_commodity_history(commodity):
    """Retorna histórico de preços para uma commodity específica."""
    days = request.args.get('days', 30, type=int)
    db = get_db()
    data = db.execute(
        'SELECT * FROM commodities WHERE commodity = ? AND timestamp > datetime("now", ?) '
        'ORDER BY timestamp',
        (commodity, f'-{days} days')
    ).fetchall()
    
    return jsonify([dict(row) for row in data])

@app.route('/api/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    """Retorna alertas contextuais para o agronegócio brasileiro."""
    db = get_db()
    alerts = db.execute(
        'SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 50'
    ).fetchall()
    
    return jsonify([dict(row) for row in alerts])

@app.route('/api/reports/daily', methods=['GET'])
@jwt_required()
def get_daily_report():
    """Gera relatório diário de commodities agrícolas."""
    from core.report_generator import ReportGenerator
    report = ReportGenerator(get_db()).generate_daily_report()
    return jsonify(report)

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(status="ok", service="agroinsight-api")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)