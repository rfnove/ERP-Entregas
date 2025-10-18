from flask import Flask, request, jsonify
from flask_cors import CORS
from chat import chat  # Importa a sua função original do arquivo chat.py
from connection import get_db_connection # chamar a conexão com o banco
from datetime import datetime #se precisar usar o registro de tempo igual no último pi

app = Flask(__name__)
CORS(app)  # Permite que o frontend se comunique com este servidor

@app.route('/chatbot', methods=['POST'])
def handle_chat_request():
    data = request.get_json()

    # Valida se a requisição tem o campo 'op'
    if not data or 'op' not in data:
        return jsonify({"error": "O parâmetro 'op' é obrigatório."}), 400

    try:
        # 1. Pega o número da opção e converte para inteiro
        option = int(data['op'])
        
        # 2. Pega o número do pedido, se estiver presente na requisição JSON
        # O valor será None se o campo não existir, o que é tratado pela função chat(op, numero_pedido=None)
        numero_pedido = data.get('numero_pedido') 
        
        # 3. Chama a função 'chat' com a opção e o número do pedido (pode ser None)
        response_message = chat(option, numero_pedido)
        
        # Retorna a resposta do seu script para o frontend
        return jsonify({"response": response_message})
        
    except (ValueError, TypeError):
        return jsonify({"error": "O parâmetro 'op' deve ser um número válido."}), 400

@app.route('/login', methods=['POST'])
def handle_login():
    data = request.get_json()

    # 1. Validação dos dados recebidos
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email e senha são obrigatórios."}), 400

    email = data.get('email')
    senha = data.get('password')

    # 2. Conexão com o banco de dados
    db = get_db_connection()
    if not db:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500
    
    colecao_entregador = db["entregador"]

    # 3. Busca pelo entregador no banco
    entregador = colecao_entregador.find_one({
        "email": email,
        "senha_hash": senha 
    })


    if entregador:

        return jsonify({"message": "Login bem-sucedido!"})
    else:

        return jsonify({"error": "Email ou senha inválidos."}), 401 # 401 = Não autorizado


@app.route('/entregas', methods=['POST'])
def handle_add_entrega():
    data = request.get_json()

    #campos obrigatórios
    required_fields = ['customerName', 'orderNumber', 'address', 'city', 'deliveryType', 'status', 'entregador_id']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Todos os campos obrigatórios devem ser preenchidos."}), 400
    
    db = get_db_connection()
    if not db:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500

    colecao_entregas = db["entregas"]

    # 3. Montagem do documento para salvar no Mongo
    nova_entrega = {
        "numero_pedido": data.get('orderNumber'),
        "nome_cliente": data.get('customerName'),
        "endereco_completo": data.get('address'),
        "cidade": data.get('city'),
        "tipo_entrega": data.get('deliveryType'),
        "status": data.get('status'),
        "descricao_entrega": data.get('notes', ''), 
        "data_criacao": datetime.now(), 
        "data_entrega_concluida": None, 
        "entregador_id": data.get('entregador_id')
    }
    
    try:
        ## Colocar os dados no banco
        result = colecao_entregas.insert_one(nova_entrega)
        
        ##
        return jsonify({
            "message": "Entrega cadastrada com sucesso!",
            "id": str(result.inserted_id) # Retorna o ID do novo documento criado
        }), 201 # 201 = Recurso Criado
        
    except Exception as e:
        return jsonify({"error": f"Ocorreu um erro ao salvar a entrega: {e}"}), 500

if __name__ == '__main__':
    # Roda o servidor na porta 5000
    app.run(port=5000, debug=True)
