import firebase_admin
import pyrebase
from datetime import datetime, timezone
import re
import bcrypt
from firebase_admin import auth, credentials, firestore, storage
from flask import Flask, render_template, redirect, request, session, url_for, jsonify, flash, send_file
from functools import wraps
import uuid
from random import randint
import os
from dotenv import load_dotenv
from openai import OpenAI
import base64
from io import BytesIO
import json
from label import analyze_label
from image import process_image
from fpdf import FPDF
import io

load_dotenv()  # Carrega as variáveis do .env

config = {
    "apiKey": "AIzaSyD3SQxbl_WPLHQXKEYJdjaNY4YDsByEjI4",
  "authDomain": "rotulo-checker.firebaseapp.com",
  "projectId": "rotulo-checker",
  "storageBucket": "rotulo-checker.firebasestorage.app",
  "messagingSenderId": "405041107880",
  "appId": "1:405041107880:web:5d3827ff7ed8cd5608439d",
  "measurementId": "G-M2E0T677KY",
"databaseURL": "https://rotulo-checker-default-rtdb.firebaseio.com"
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
app.secret_key = os.getenv("SECRET_KEY")

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
                'data_inicio': datetime.now(timezone.utc),
                'plano_id': plano_ref.id,
                'qtde_processamento': 10,
                'ultimo_processamento': None,
                'ativa': True
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
    assinatura_docs = db.collection('Cliente').document(user_uid).collection('assinaturas').get()
    servicos = []

    for assinatura_doc in assinatura_docs:
        servico_docs = assinatura_doc.reference.collection('servico').get()
        for servico in servico_docs:
            servico_data = servico.to_dict()
            servico_data["id"] = str(servico.id)

            servico_data["tipo_servico"] = db.collection('tipo_servico').document(servico_data['tipo_servico_id']).get().to_dict()
            servico_data.pop('tipo_servico_id')
            servico_data["data_processamento"] = servico_data["data_processamento"].strftime("%d/%m/%Y")
            servicos.append(servico_data)

    return render_template("log.html", servicos=servicos)

@app.route('/planos', methods=['GET'])
@login_required
def planos():
    return render_template("plans.html")

@app.route('/processo', methods=['GET', 'POST'])
@login_required
def processo():
    produtos = db.collection('tipo_servico').get()
    produtos = [x.to_dict() | {"id": x.id} for x in produtos]

    imagem_url = None
    tipo_servico_id = None
    caminho_img_final = None

    if request.method == 'POST':
        user_uid = session.get("uid")
        tipo_servico_id = request.form.get("tipo_servico")
        imagem = request.files.get("image")

        if imagem:
            # Ler os bytes da imagem e codificar para Base64
            image_bytes = imagem.read()

            # Resetar o ponteiro do arquivo e fazer upload da imagem original
            imagem_stream = BytesIO(image_bytes)
            filename = f"{uuid.uuid4()}_{imagem.filename}"
            blob = bucket.blob(f"entrada/{filename}")
            blob.upload_from_file(imagem_stream, content_type=imagem.content_type)
            blob.make_public()
            imagem_url = blob.public_url  

            # 🏷️ Analisar a imagem com a função analyze_label
            
            legislacao_ref = db.collection('legislacao').document(
                db.collection('tipo_servico').document(tipo_servico_id).get().to_dict()["tipo"]
            )
            legislacao_doc = legislacao_ref.get()
            legislacao_dict = legislacao_doc.to_dict()
            
            result = analyze_label(BytesIO(image_bytes), legislacao_dict)
            
            path_processed_image = process_image(BytesIO(image_bytes))
            
            # Ler os bytes da imagem processada e codificar para Base64
            with open(path_processed_image, "rb") as processed_image_file:
                processed_image_bytes = processed_image_file.read()
            
            imagem_stream = BytesIO(processed_image_bytes)
            filename = f"{uuid.uuid4()}_{imagem.filename}"
            blob = bucket.blob(f"saida/{filename}")
            blob.upload_from_file(imagem_stream, content_type=imagem.content_type)
            blob.make_public()
            caminho_img_final = blob.public_url

            # Atualizando os dados do usuário no Firestore
            cliente_ref = db.collection('Cliente').document(user_uid)
            assinatura_ref = cliente_ref.collection('assinaturas').get()
            assinatura_ativa = None
            for assinatura in assinatura_ref:
                if assinatura.to_dict().get('ativa'):
                    assinatura_ativa = assinatura
                    break

            if assinatura_ativa:
                cliente_ref.collection('assinaturas').document(assinatura_ativa.id).update({
                    'qtde_processamento': firestore.Increment(-1),
                    'ultimo_processamento': datetime.now(timezone.utc)
                })
        
            # Salvando os resultados no Firestore
            servico_ref = cliente_ref.collection('assinaturas').document(assinatura_ativa.id).collection('servico').document()
            servico_ref.set({
                "data_processamento": datetime.now(timezone.utc),
                "erros": result["total_erros"],
                "img_entrada": imagem_url,
                "img_saida": caminho_img_final,
                "relatorio": result["detalhes_erros"],
                "tipo_servico_id": tipo_servico_id,
                "relatorio_completo": result["resultado_completo"]
            })

        return render_template("image_process.html", produtos=produtos, imagem_url=imagem_url, 
                               imagem_processed_url=caminho_img_final, tipo_servico_id=tipo_servico_id, 
                               errors=result["total_erros"], legislation_report=result)
    else:
        return render_template("image_process.html", produtos=produtos, imagem_url=caminho_img_final, 
                               imagem_processed_url='', tipo_servico_id=tipo_servico_id, 
                               errors=0, legislation_report={})
        



@app.route('/download-relatorio/<servico_id>')
def download_relatorio(servico_id):
    user_uid = session.get("uid")
    cliente_ref = db.collection('Cliente').document(user_uid)
    assinatura_ref = cliente_ref.collection('assinaturas').get()
    assinatura_ativa = None
    for assinatura in assinatura_ref:
        if assinatura.to_dict().get('ativa'):
            assinatura_ativa = assinatura
            break

    if assinatura_ativa:
        cliente_ref.collection('assinaturas').document(assinatura_ativa.id).update({
            'qtde_processamento': firestore.Increment(-1),
            'ultimo_processamento': datetime.now(timezone.utc)
        })
    
    
    # Obtenha o serviço correspondente (simulação, ajuste conforme necessário)
    servico = cliente_ref.collection('assinaturas').document(assinatura_ativa.id).collection('servico').document(servico_id).get().to_dict()
    
    if not servico or "relatorio_completo" not in servico:
        return "Relatório não encontrado", 404
    
    relatorio = servico["relatorio_completo"]
    
    # Criar o PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=8)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, "Relatório Completo", ln=True, align="C")
    pdf.ln(10)

    def add_dict_to_pdf(pdf, data, indent1=0, indent2=0):
        for key, value in data.items():
            if isinstance(value, dict):
                pdf.set_font("Arial", style='B', size=10)
                pdf.cell(0, 8, f"{' ' * indent1}{key}:", ln=True)
                pdf.ln(1)
                add_dict_to_pdf(pdf, value, indent1 + 10)
            else:
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 8, f"{' ' * (indent1 + 1)}{key}: {value}")
                pdf.ln(1)

    add_dict_to_pdf(pdf, relatorio)

    # Criar buffer de memória
    pdf_output = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')  # Gerar conteúdo do PDF como bytes
    pdf_output.write(pdf_bytes)  # Escrever no buffer
    pdf_output.seek(0)  # Voltar ao início para leitura

    return send_file(
        pdf_output,
        download_name="relatorio_completo.pdf",
        as_attachment=True,
        mimetype="application/pdf"
)
    

if __name__ == "__main__":
    app.run(debug=True, port=3000)
