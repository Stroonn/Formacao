import firebase_admin
from firebase_admin import auth, credentials, firestore
from flask import Flask, render_template, redirect, request, session, url_for
import json
import jsonify

# Inicializar o Firebase Admin SDK com o arquivo JSON
cred = credentials.Certificate('firebase-auth.json')  # Caminho para o arquivo json
firebase_admin.initialize_app(cred)

# Inicializar o Flask
app = Flask(__name__)


app.secret_key = 'slakdjfslkfjahglkcdlkcnanahaeoighjakdfjdslkfjasd'

db = firestore.client()

# Rota para a página inicial
@app.route('/')
def homepage():
  return render_template('homepage.html')
  
# Rota para a página de login
@app.route('/login')
def login():
  if 'user' in session:
    return redirect('/')
  return render_template('login.html')

# Rota para a página de registro
@app.route('/register')
def register():
  if 'user' in session:
    return redirect('/')
  return render_template('register.html')

# Rota para a página de logout
@app.route('/logout')
def logout():
    session.clear()  # Limpar a sessão
    return redirect(url_for('homepage'))
  
# Rota para a página de perfil
@app.route('/profile')
def profile():
    if 'user' in session:
        return render_template('profile.html', user=session['user'])
    else:
        return redirect('/login')
  
# Rota para a página de erro
@app.route('/error')
def error():
    return render_template('error.html')


# Rota para login com Google
@app.route('/login-google', methods=['POST'])
def login_google():
    token = request.json.get('token')
    try:
        # Verificar o token do Google
        decoded_token = auth.verify_id_token(token)
        user_email = decoded_token['email']

        # Definir a sessão do usuário
        session['user'] = user_email
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Erro ao autenticar com Google: {e}")
        return jsonify({'success': False}), 401



# Rota para o login
@app.route('/login', methods=['POST'])
def login_post():
  email = request.form['email']
  password = request.form['password']
  try:
    user = auth.get_user_by_email(email)
    doc_ref = db.collection('clientes').document(user.uid).get()
    if doc_ref.exists:
      stored_password = doc_ref.to_dict().get('senha')
      if stored_password == password:
        session['user'] = user.email
        return redirect('/')
    return redirect('/error')
  except Exception as e:
    print(f"Erro ao autenticar: {e}")
    return redirect('/error')

# Rota para o registro
@app.route('/register', methods=['POST'])
def register_post():
    # Dados do formulário
    nome = request.form['nome']
    email = request.form['email']
    password = request.form['password']
    telefone = request.form['telefone']
    cep = request.form['cep']
    nroCasa = request.form['nroCasa']
    complemento = request.form['complemento']
    cidade = request.form['cidade']
    uf = request.form['uf']
    bairro = request.form['bairro']
    logradouro = request.form['logradouro']
    siglaLogradouro = request.form['siglaLogradouro']

    try:
        # Criar usuário no Firebase Auth
        user = auth.create_user(email=email, password=password)
        
        bairro_ref = db.collection('bairro').document()
        bairro_ref.set({
            'nome_bairro': bairro
        })
        
        unidadesFederacao_ref = db.collection('unidadesFederacao').document()
        unidadesFederacao_ref.set({
            'nome_UF': uf
        })
        
        cidade_ref = db.collection('cidades').document()
        cidade_ref.set({
            'nome_cidade': cidade,
            'uf_id': unidadesFederacao_ref.id
        })
        
        logradouro_ref = db.collection('logradouros').document()
        logradouro_ref.set({
            'nome_logradouro': logradouro,
            'sigla_logradouro': siglaLogradouro
        })

        # Adicionar endereço ao Firestore
        endereco_ref = db.collection('enderecos').document()
        endereco_ref.set({
            'cep': cep,
            'nroCasa': nroCasa,
            'complemento': complemento,
            'cidade_id': cidade_ref.id,
            'logradouro_id': logradouro_ref.id,
            'bairro_id': bairro_ref.id
        })

        # Adicionar cliente ao Firestore
        cliente_ref = db.collection('clientes').document(user.uid)
        cliente_ref.set({
            'nome': nome,
            'telefone': telefone,
            'email': email,
            'senha': password,  # Lembre-se de usar hash na senha em produção
            'endereco_id': endereco_ref.id
        })

        # Definir a sessão do usuário
        session['user'] = user.email
        return redirect('/')
    except Exception as e:
        print(f"Erro: {e}")
        return redirect('/login')

# Rota para o logout
@app.route('/logout', methods=['POST'])
def logout_post():
    session.clear()
    return redirect('/')



if __name__ == "__main__":
    app.run(debug=True, port=3000)
