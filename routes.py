import firebase_admin
import pyrebase
from datetime import datetime
import re
import bcrypt
from firebase_admin import auth, credentials, firestore, storage
from flask import Flask, render_template, redirect, request, session, url_for, jsonify, flash, g
from functools import wraps
import uuid

config = {

}

firebase = pyrebase.initialize_app(config)
pyauth = firebase.auth()

cred = credentials.Certificate('firebase-auth.json')
firebase_admin.initialize_app(cred, {
    "storageBucket": "rotulo-checker.firebasestorage.app"
})
db = firestore.client()
bucket = storage.bucket()

# Inicializar o Flask
app = Flask(__name__)
app.secret_key = 'slakdjfslkfjahglkcdlkcnanahaeoighjakdfjdslkfjasd'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_logged_in"):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rota para a página inicial
@app.route('/')
def homepage():
    return render_template('homepage.html')

# Rota para a página de logout
@app.route('/logout')
def logout():
    session.clear()  # Limpar a sessão
    return redirect(url_for('homepage'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        result = request.form
        email = result["email"]
        password = result["password"]
        
        try:
            user = pyauth.sign_in_with_email_and_password(email, password)
            session["is_logged_in"] = True
            session["email"] = user["email"]
            session["uid"] = user["localId"]

            return redirect(url_for("homepage"))
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 401
    else:
        if session.get("is_logged_in"):
            return redirect(url_for("homepage"))
        return render_template("login.html")

# Rota para o registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Dados do formulário
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        cpf_cnpj = request.form['cpf_cnpj']
        phone = request.form['phone']
        cep = request.form['cep']
        street = request.form['street']
        number = request.form['number']
        city = request.form['city']
        state = request.form['state']
        bairro = request.form['bairro']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Verificar se as senhas coincidem
        if password != confirm_password:
            return "As senhas não coincidem", 400

        try:
            # Criar hash da senha
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Criar usuário no Firebase Authentication
            user = auth.create_user(email=email, password=password)
            
            # Fazer login com o usuário criado
            user_data = pyauth.sign_in_with_email_and_password(email, password)
            session["is_logged_in"] = True
            session["email"] = user_data["email"]
            session["uid"] = user_data["localId"]  # Acessar o UID corretamente

            # Adicionar unidade federativa ao Firestore
            uf_ref = db.collection('unidades_federacao').document()
            uf_ref.set({
                'nomeUF': state
            })

            # Adicionar cidade ao Firestore
            cidade_ref = db.collection('cidades').document()
            cidade_ref.set({
                'nomeCidade': city,
                'unidadeFederacao_id': uf_ref.id  # Referência à unidade federativa
            })

            # Adicionar bairro ao Firestore
            bairro_ref = db.collection('bairros').document()
            bairro_ref.set({
                'nomeBairro': bairro
            })

            # Adicionar logradouro ao Firestore
            logradouro_ref = db.collection('logradouros').document()
            logradouro_ref.set({
                'nomeLogradouro': street,
                'siglaLogradouro': 'Av.'  # Ajuste conforme necessário
            })

            # Adicionar endereço ao Firestore
            endereco_ref = db.collection('enderecos').document()
            endereco_ref.set({
                'cep': cep,
                'nroCasa': number,
                'cidade_id': cidade_ref.id,  # Referência à cidade
                'logradouro_id': logradouro_ref.id,  # Referência ao logradouro
                'bairro_id': bairro_ref.id  # Referência ao bairro
            })
            
            plano_ref = db.collection('planos').document('plano_bronze')

            # Adicionar cliente ao Firestore
            cliente_ref = db.collection('Cliente').document(user_data["localId"])  # Usar o UID correto
            cliente_ref.set({
                'nome': f"{first_name} {last_name}",
                'telefone': phone,
                'email': email,
                'senha': hashed_password.decode('utf-8'),
                'cpf_cnpj': cpf_cnpj,
                'endereco_id': endereco_ref.id
            })

            assinatura_ref = cliente_ref.collection('assinaturas').document()
            assinatura_ref.set({
                'data_fim': None,
                'data_inicio': None,
                'plano_id': plano_ref.id,
                'qtde_processamento': 10,
                'ultimo_processamento': None
            })

            return redirect(url_for("homepage"))
        except auth.EmailAlreadyExistsError:
            return "E-mail já cadastrado. Use outro e-mail ou faça login.", 400
        except Exception as e:
            print(f"Erro: {e}")
            return f"Erro ao registrar usuário: {str(e)}", 500
    else:
        return render_template('register.html')

@app.route('/log', methods=['GET'])
@login_required
def log():
    user_uid = session.get("uid")
    
    # Pegando todos os documentos da coleção "assinatura" do cliente
    assinatura_docs = db.collection('Cliente').document("Cliente_1").collection('assinaturas').get()
    servicos = []

    for assinatura_doc in assinatura_docs:
        servico_docs = assinatura_doc.reference.collection('servico').get()
        for servico in servico_docs:
            servico = servico.to_dict()
            servico["tipo_servico"] = db.collection('tipo_servico').document(servico['tipo_servico_id']).get().to_dict()
            servico.pop('tipo_servico_id')
            servico["data_processamento"] = servico["data_processamento"].strftime("%d/%m/%Y")
            servicos.append(servico)

    return render_template("log.html", servicos=servicos)

@app.route('/planos', methods=['GET'])
@login_required
def planos():
    return render_template("plans.html")

@app.route('/processo', methods=['GET', 'POST'])
@login_required
def processo():
    if request.method == 'GET':
        tipos = db.collection('tipo_servico').get()
        produtos = [x.to_dict() | {"id": x.id} for x in tipos]  # Garantindo que 'id' esteja acessível no HTML
        return render_template("image_process.html", produtos=produtos)

    elif request.method == 'POST':
        
        user_uid = session.get("uid")
        # Pegando os dados do formulário
        tipo_servico_id = request.form.get("tipo_servico")
        imagem = request.files.get("image")

        if imagem:
            # Gerando um nome único para a imagem
            filename = f"{uuid.uuid4()}_{imagem.filename}"
            blob = bucket.blob(f"entrada/{filename}")

            # Enviando a imagem para o Firebase Storage
            blob.upload_from_file(imagem, content_type=imagem.content_type)
            blob.make_public()
            img_url = blob.public_url  # URL pública da imagem

            # Atualizando os dados do usuário
            cliente_ref = db.collection('Cliente').document("Cliente_1")  # Usar o UID correto
            assinatura_ref = cliente_ref.collection('assinaturas').document()

            servico_ref = assinatura_ref.collection('servico').document()
            servico_ref.set({
                "data_processamento": datetime.utcnow().isoformat(),
                "erros": 3,
                "img_entrada": img_url,
                "img_saida": "",
                "relatorio": "",
                "tipo_servico_id": tipo_servico_id
            })

            return redirect(url_for('processo'))  # Recarrega a página

    return redirect(url_for('processo'))
    

if __name__ == "__main__":
    app.run(debug=True, port=3000)
