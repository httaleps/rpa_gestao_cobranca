from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///techsolutions.db'
db = SQLAlchemy(app)

# ── MODELOS (tabelas do banco) ──────────────────────────────────────────────
class Cliente(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(100))
    telefone      = db.Column(db.String(20))
    endereco      = db.Column(db.String(200))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    faturas       = db.relationship('Fatura', backref='cliente', lazy=True)

class Fatura(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    cliente_id     = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    valor          = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.String(20))
    status         = db.Column(db.String(20), default='pendente')
    data_emissao   = db.Column(db.DateTime, default=datetime.utcnow)

# ── ROTAS ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clientes', methods=['POST'])
def cadastrar_cliente():
    dados = request.form
    cliente = Cliente(
        nome=dados['nome'],
        email=dados['email'],
        telefone=dados['telefone'],
        endereco=dados['endereco']
    )
    db.session.add(cliente)
    db.session.commit()
    return jsonify({'mensagem': 'Cliente cadastrado!', 'id': cliente.id})

@app.route('/faturas', methods=['POST'])
def emitir_fatura():
    dados = request.form
    fatura = Fatura(
        cliente_id=dados['cliente_id'],
        valor=float(dados['valor']),
        data_vencimento=dados['data_vencimento']
    )
    db.session.add(fatura)
    db.session.commit()
    return jsonify({'mensagem': 'Fatura emitida!', 'id': fatura.id})

@app.route('/faturas', methods=['GET'])
def listar_faturas():
    faturas = Fatura.query.all()
    resultado = []
    for f in faturas:
        resultado.append({
            'id': f.id,
            'cliente': f.cliente.nome,
            'valor': f.valor,
            'vencimento': f.data_vencimento,
            'status': f.status
        })
    return jsonify(resultado)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas automaticamente
    app.run(debug=True)