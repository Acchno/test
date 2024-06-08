from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estoque.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(80), nullable=False)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_item = db.Column(db.String(80), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    acao = db.Column(db.String(10), nullable=False)  # 'add' ou 'remove'
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(80), nullable=False)

@app.route('/add', methods=['POST'])
def add_item():
    with app.app_context():
        data = request.json
        nome = data.get('nome').lower()
        quantidade = data.get('quantidade', 1)
        usuario = data.get('usuario')
        
        item = Item.query.filter_by(nome=nome).first()
        if item:
            item.quantidade += quantidade
            item.ultima_atualizacao = datetime.utcnow()
            item.usuario = usuario
        else:
            item = Item(nome=nome, quantidade=quantidade, usuario=usuario)
            db.session.add(item)
        
        log = Log(nome_item=nome, quantidade=quantidade, acao='add', usuario=usuario)
        db.session.add(log)
        
        db.session.commit()
        return jsonify({"message": "Item adicionado com sucesso!"})

@app.route('/remove', methods=['POST'])
def remove_item():
    with app.app_context():
        data = request.json
        nome = data.get('nome').lower()
        quantidade = data.get('quantidade', 1)
        usuario = data.get('usuario')

        item = Item.query.filter_by(nome=nome).first()
        if item and item.quantidade >= quantidade:
            item.quantidade -= quantidade
            item.ultima_atualizacao = datetime.utcnow()
            item.usuario = usuario
            if item.quantidade == 0:
                db.session.delete(item)
            
            log = Log(nome_item=nome, quantidade=quantidade, acao='remove', usuario=usuario)
            db.session.add(log)
            
            db.session.commit()
            return jsonify({"message": "Item removido com sucesso!"})
        else:
            return jsonify({"message": "Quantidade insuficiente ou item não encontrado!"}), 400

@app.route('/estoque', methods=['GET'])
def get_estoque():
    with app.app_context():
        itens = Item.query.all()
        result = []
        for item in itens:
            result.append({
                "nome": item.nome,
                "quantidade": item.quantidade,
                "ultima_atualizacao": item.ultima_atualizacao,
                "usuario": item.usuario
            })
        return jsonify(result)

@app.route('/log', methods=['GET'])
def get_log():
    with app.app_context():
        logs = Log.query.all()
        result = []
        for log in logs:
            result.append({
                "nome_item": log.nome_item,
                "quantidade": log.quantidade,
                "acao": log.acao,
                "data_hora": log.data_hora,
                "usuario": log.usuario
            })
        return jsonify(result)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
