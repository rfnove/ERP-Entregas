from flask import Flask, request, jsonify
from flask_cors import CORS
from chat import chat  # Importa a sua função original do arquivo chat.py

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

if __name__ == '__main__':
    # Roda o servidor na porta 5000
    app.run(port=5000, debug=True)