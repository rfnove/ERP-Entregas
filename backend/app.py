from flask import Flask, request, jsonify
from flask_cors import CORS
from chat import chat  # Importa a sua função original do arquivo chat.py
from connection import get_db_connection # chamar a conexão com o banco
from datetime import datetime, time, timedelta #se precisar usar o registro de tempo igual no último pi
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
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
        
        # 2. Pega os outros dados (podem ser None)
        numero_pedido = data.get('numero_pedido') 
        entregador_id = data.get('entregador_id') # <<< ADICIONA ESTA LINHA
        
        # 3. Chama a função 'chat' com TODOS os parâmetros
        response_message = chat(option, numero_pedido, entregador_id) # <<< ATUALIZA ESTA LINHA
        
        # Retorna a resposta do seu script para o frontend
        return jsonify({"response": response_message})
        
    except (ValueError, TypeError):
        return jsonify({"error": "O parâmetro 'op' deve ser um número válido."}), 400
    
@app.route('/login', methods=['POST'])
def handle_login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email e senha são obrigatórios."}), 400

    email = data.get('email')
    senha_digitada = data.get('password') # Senha em texto puro

    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500
    
    colecao_entregador = db["entregador"]

    # 3. Busca pelo entregador SOMENTE PELO EMAIL
    entregador = colecao_entregador.find_one({"email": email})

    # 4. Verifica se o entregador existe E se a senha bate com o hash
    #    (O campo no Mongo DEVE se chamar 'senha_hash')
    if entregador and check_password_hash(entregador.get('senha_hash'), senha_digitada):
        
        # Opcional: Retornar o ID do entregador para usar nas outras telas
        return jsonify({
            "message": "Login bem-sucedido!",
            "entregador_id": str(entregador.get('_id')),
            "nome": entregador.get('nome')
        })
    else:
        return jsonify({"error": "Email ou senha inválidos."}), 401


#
# 3. ADICIONE ESTA NOVA ROTA /register
#
@app.route('/register', methods=['POST'])
def handle_register():
    data = request.get_json()

    # 1. Validação dos dados (ATUALIZADO)
    if not data or not data.get('email') or not data.get('password') or not data.get('name') or not data.get('cpf'):
        return jsonify({"error": "Nome, email, CPF e senha são obrigatórios."}), 400

    nome = data.get('name')
    email = data.get('email')
    cpf = data.get('cpf') # <-- ADICIONADO
    senha_texto_puro = data.get('password')

    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500
    
    colecao_entregador = db["entregador"]

    # 2. Verifica se o email já existe
    if colecao_entregador.find_one({"email": email}):
        return jsonify({"error": "Este email já está cadastrado."}), 409 # 409 = Conflito
    
    # 2b. Verifica se o CPF já existe (ADICIONADO)
    if colecao_entregador.find_one({"cpf": cpf}):
        return jsonify({"error": "Este CPF já está cadastrado."}), 409 # 409 = Conflito

    # 3. CRIA O HASH DA SENHA
    senha_hash = generate_password_hash(senha_texto_puro)

    # 4. Cria o novo documento de entregador (ATUALIZADO)
    novo_entregador = {
        "nome": nome,
        "email": email,
        "cpf": cpf, # <-- ADICIONADO
        "senha_hash": senha_hash, # Salva o HASH, não a senha pura
        "data_cadastro": datetime.now()
    }

    # 5. Salva no banco
    try:
        result = colecao_entregador.insert_one(novo_entregador)
        return jsonify({
            "message": "Entregador cadastrado com sucesso!",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"error": f"Ocorreu um erro ao cadastrar: {e}"}), 500

@app.route('/entregas', methods=['POST'])
def handle_add_entrega():
    data = request.get_json()

    #campos obrigatórios
    required_fields = ['customerName', 'orderNumber', 'address', 'city', 'deliveryType', 'status', 'entregador_id']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Todos os campos obrigatórios devem ser preenchidos."}), 400
    
    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500

    colecao_entregas = db["entregas"]
    try:
        entregador_obj_id = ObjectId(data.get('entregador_id'))
    except Exception:
        return jsonify({"error": "ID do entregador inválido."}), 400
    
    status_inicial = data.get('status')
    data_conclusao = None
    if status_inicial == 'Concluída':
        data_conclusao = datetime.now()
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
        "entregador_id": entregador_obj_id
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


# Em app.py
# Lembre-se de ter as importações no topo do arquivo:
# from bson import ObjectId
# from datetime import datetime, time

# Em app.py
# (Lembre-se de ter 'ObjectId' importado de 'bson')

@app.route('/entregas', methods=['GET'])
def handle_get_entregas():
    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500

    colecao_entregas = db["entregas"]
    
    # --- ESTA É A MUDANÇA PRINCIPAL ---
    
    # 1. Pega os filtros da URL
    query_filter = {}
    status_filter = request.args.get('status')
    data_filter_str = request.args.get('data')
    entregador_id_filter = request.args.get('entregador_id') # <<< Pega o novo ID

    # 2. VALIDAÇÃO OBRIGATÓRIA
    if not entregador_id_filter:
        return jsonify({"error": "O 'entregador_id' é obrigatório para esta consulta."}), 400

    # 3. Adiciona o ID do entregador ao filtro de busca
    # Tenta converter para ObjectId, se falhar, usa a string (para IDs antigos)
    try:
        query_filter['entregador_id'] = ObjectId(entregador_id_filter)
    except Exception:
        query_filter['entregador_id'] = entregador_id_filter

    # Adiciona os outros filtros (data, status)
    if status_filter:
        query_filter['status'] = status_filter
        
    if data_filter_str:
        try:
            filter_date = datetime.strptime(data_filter_str, '%Y-%m-%d')
            start_of_day = datetime.combine(filter_date, time.min)
            end_of_day = datetime.combine(filter_date, time.max)
            query_filter['data_criacao'] = {'$gte': start_of_day, '$lt': end_of_day}
        except ValueError:
            return jsonify({"error": "Formato de data inválido. Use AAAA-MM-DD."}), 400

    try:
        # A busca agora SEMPRE filtrará pelo entregador_id
        entregas_cursor = colecao_entregas.find(query_filter).sort("data_criacao", -1)
            
        lista_entregas = []
        for entrega in entregas_cursor:
            # (Loop de conversão de dados, como já tínhamos)
            if '_id' in entrega:
                entrega['_id'] = str(entrega['_id'])
            if 'data_criacao' in entrega and isinstance(entrega['data_criacao'], datetime):
                entrega['data_criacao'] = entrega['data_criacao'].isoformat()
            if 'data_entrega_concluida' in entrega and isinstance(entrega['data_entrega_concluida'], datetime):
                entrega['data_entrega_concluida'] = entrega['data_entrega_concluida'].isoformat()
            if 'entregador_id' in entrega and isinstance(entrega['entregador_id'], ObjectId):
                entrega['entregador_id'] = str(entrega['entregador_id'])

            lista_entregas.append(entrega)
            
        return jsonify(lista_entregas), 200
        
    except Exception as e:
        print(f"Erro na rota /entregas: {e}") 
        return jsonify({"error": f"Ocorreu um erro ao buscar as entregas: {e}"}), 500
#
# NOVO ENDPOINT (PATCH) - Para atualizar o status de UMA entrega
#
@app.route('/entregas/<string:entrega_id>', methods=['PATCH'])
def handle_update_status(entrega_id):
    data = request.get_json()
    
    # 1. Validação simples
    if not data or 'status' not in data:
        return jsonify({"error": "O novo 'status' é obrigatório."}), 400
        
    new_status = data.get('status')
    
    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500
        
    colecao_entregas = db["entregas"]
    
    try:
        # Converte o ID de string (que veio da URL) de volta para ObjectId
        object_id_to_find = ObjectId(entrega_id)
    except Exception:
        return jsonify({"error": "ID de entrega inválido."}), 400

    # 3. Prepara a atualização
    update_data = {
        '$set': {
            'status': new_status
        }
    }
    
    # Se o status for 'Concluída', atualiza a data de conclusão
    if new_status == 'Concluída':
        update_data['$set']['data_entrega_concluida'] = datetime.now()
    else:
        # Garante que a data de conclusão fique nula se voltar para outro status
        update_data['$set']['data_entrega_concluida'] = None

    # 4. Executa a atualização no banco
    result = colecao_entregas.update_one(
        {'_id': object_id_to_find},
        update_data
    )
    
    if result.matched_count > 0:
        return jsonify({"message": "Status atualizado com sucesso!"}), 200
    else:
        return jsonify({"error": "Entrega não encontrada."}), 404
    
@app.route('/dashboard-stats', methods=['GET'])
def handle_dashboard_stats():
    # 1. Validação do ID do Entregador
    entregador_id_filter = request.args.get('entregador_id')
    if not entregador_id_filter:
        return jsonify({"error": "O 'entregador_id' é obrigatório."}), 400

    try:
        entregador_obj_id = ObjectId(entregador_id_filter)
    except Exception:
        return jsonify({"error": "ID do entregador inválido."}), 400

    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500
        
    colecao_entregas = db["entregas"]

    # 2. Definir o intervalo de "Hoje"
    # Usamos data_criacao, pois é o campo que temos. Idealmente, seria "data_agendada".
    today = datetime.now().date()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    # 3. Montar a query base
    base_query = {
        "entregador_id": entregador_obj_id,
        "data_criacao": {
            "$gte": start_of_day,
            "$lt": end_of_day
        }
    }

    try:
        # 4. Calcular estatísticas
        total_hoje = colecao_entregas.count_documents(base_query)
        
        concluidas_hoje = colecao_entregas.count_documents({
            **base_query,
            "status": "Concluída"
        })
        
        # Pendentes são todas que NÃO estão "Concluídas"
        pendentes_hoje = colecao_entregas.count_documents({
            **base_query,
            "status": {"$ne": "Concluída"}
        })

        total_geral = colecao_entregas.count_documents({
            "entregador_id": entregador_obj_id})
        # 5. Buscar últimas 3 atividades recentes (de hoje)
        recentes_cursor = colecao_entregas.find(base_query).sort("data_criacao", -1).limit(3)
        
        lista_recentes = []
        for entrega in recentes_cursor:
            # Converte para formatos amigáveis para JSON
            entrega['_id'] = str(entrega['_id'])
            entrega['entregador_id'] = str(entrega['entregador_id'])
            entrega['data_criacao'] = entrega['data_criacao'].isoformat()
            if entrega['data_entrega_concluida'] and isinstance(entrega['data_entrega_concluida'], datetime):
                entrega['data_entrega_concluida'] = entrega['data_entrega_concluida'].isoformat()
            lista_recentes.append(entrega)
            
        # 6. Retornar os dados
        return jsonify({
            "total_hoje": total_hoje,
            "concluidas_hoje": concluidas_hoje,
            "pendentes_hoje": pendentes_hoje,
            "atividades_recentes": lista_recentes,
            "total_geral": total_geral
        }), 200

    except Exception as e:
        print(f"Erro na rota /dashboard-stats: {e}")
        return jsonify({"error": f"Ocorreu um erro ao calcular estatísticas: {e}"}), 500

@app.route('/analytics/deliveries-over-time', methods=['GET'])
def handle_deliveries_over_time():
    # 1. Validação do ID do Entregador (igual a antes)
    entregador_id_filter = request.args.get('entregador_id')
    if not entregador_id_filter:
        return jsonify({"error": "O 'entregador_id' é obrigatório."}), 400

    try:
        entregador_obj_id = ObjectId(entregador_id_filter)
    except Exception:
        return jsonify({"error": "ID do entregador inválido."}), 400

    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500
        
    colecao_entregas = db["entregas"]

    # 2. DEFINIR O INTERVALO DE DATAS (Lógica igual a antes)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        if start_date_str and end_date_str:
            start_date_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date_dt = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date_dt = datetime.now().date()
            start_date_dt = end_date_dt - timedelta(days=6)
            
        if (end_date_dt - start_date_dt).days > 90:
            return jsonify({"error": "O intervalo de datas não pode ser maior que 90 dias."}), 400
        if start_date_dt > end_date_dt:
            return jsonify({"error": "A data inicial não pode ser maior que a data final."}), 400

        start_datetime = datetime.combine(start_date_dt, time.min)
        end_datetime = datetime.combine(end_date_dt, time.max)
        
    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use AAAA-MM-DD."}), 400

    try:
        # 3. Pipeline de Agregação 1: ENTREGAS CRIADAS
        pipeline_criadas = [
            {
                "$match": {
                    "entregador_id": entregador_obj_id,
                    "data_criacao": {"$gte": start_datetime, "$lte": end_datetime}
                }
            },
            {
                "$project": {
                    "data_dia": {"$dateToString": {"format": "%Y-%m-%d", "date": "$data_criacao", "timezone": "America/Sao_Paulo"}}
                }
            },
            {
                "$group": {"_id": "$data_dia", "total": {"$sum": 1}}
            }
        ]
        
        # 4. Pipeline de Agregação 2: ENTREGAS CONCLUÍDAS
        pipeline_concluidas = [
            {
                "$match": {
                    "entregador_id": entregador_obj_id,
                    "status": "Concluída", # Apenas as concluídas
                    "data_entrega_concluida": {"$gte": start_datetime, "$lte": end_datetime} # Filtra pela data de CONCLUSÃO
                }
            },
            {
                "$project": {
                    # Agrupa pela data de CONCLUSÃO
                    "data_dia": {"$dateToString": {"format": "%Y-%m-%d", "date": "$data_entrega_concluida", "timezone": "America/Sao_Paulo"}}
                }
            },
            {
                "$group": {"_id": "$data_dia", "total": {"$sum": 1}}
            }
        ]

        # Executa as duas agregações
        result_criadas = list(colecao_entregas.aggregate(pipeline_criadas))
        result_concluidas = list(colecao_entregas.aggregate(pipeline_concluidas))
        
        # 5. Processar dados para preencher dias vazios (LÓGICA ATUALIZADA)
        
        # Converte resultados em dicionários para busca rápida
        criadas_data = {item['_id']: item['total'] for item in result_criadas}
        concluidas_data = {item['_id']: item['total'] for item in result_concluidas}

        labels = []
        data_criadas = []     # Nova lista para a linha 1
        data_concluidas = []  # Nova lista para a linha 2

        # Loop pelo intervalo de datas
        current_date = start_date_dt
        while current_date <= end_date_dt:
            current_date_str = current_date.strftime("%Y-%m-%d")
            label_str = current_date.strftime("%d/%m")
            
            # Pega o total de cada dicionário (ou 0 se não existir)
            total_criadas = criadas_data.get(current_date_str, 0)
            total_concluidas = concluidas_data.get(current_date_str, 0)
            
            labels.append(label_str)
            data_criadas.append(total_criadas)
            data_concluidas.append(total_concluidas)
            
            current_date += timedelta(days=1)

        # 6. Retornar os dados formatados (NOVO FORMATO)
        return jsonify({
            "labels": labels,
            "data_criadas": data_criadas,
            "data_concluidas": data_concluidas
        }), 200

    except Exception as e:
        print(f"Erro na rota /analytics/deliveries-over-time: {e}")
        return jsonify({"error": f"Ocorreu um erro ao calcular estatísticas: {e}"}), 500
#
@app.route('/analytics/status-distribution', methods=['GET'])
def handle_status_distribution():
    # 1. Validação do ID do Entregador
    entregador_id_filter = request.args.get('entregador_id')
    if not entregador_id_filter:
        return jsonify({"error": "O 'entregador_id' é obrigatório."}), 400

    try:
        entregador_obj_id = ObjectId(entregador_id_filter)
    except Exception:
        return jsonify({"error": "ID do entregador inválido."}), 400

    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Não foi possível conectar ao banco de dados."}), 500
        
    colecao_entregas = db["entregas"]

    # 2. Pipeline de Agregação
    # Queremos TODAS as entregas, sem filtro de data
    pipeline = [
        {
            "$match": { # Filtra apenas pelo entregador
                "entregador_id": entregador_obj_id
            }
        },
        {
            "$group": { # Agrupa pelo campo 'status'
                "_id": "$status",
                "total": { "$sum": 1 } # Conta quantos documentos em cada grupo
            }
        },
        {
            "$sort": { "total": -1 } # Opcional: ordena do status mais comum para o menos
        }
    ]

    try:
        aggregation_result = list(colecao_entregas.aggregate(pipeline))
        
        # 3. Formatar dados para o Chart.js
        # O resultado é [ {"_id": "Concluída", "total": 50}, {"_id": "Pendente", "total": 15} ]
        
        labels = [] # Ex: ["Concluída", "Pendente"]
        data = []   # Ex: [50, 15]

        for item in aggregation_result:
            labels.append(item['_id'])
            data.append(item['total'])
            
        # 4. Retornar os dados
        return jsonify({
            "labels": labels,
            "data": data
        }), 200

    except Exception as e:
        print(f"Erro na rota /analytics/status-distribution: {e}")
        return jsonify({"error": f"Ocorreu um erro ao calcular estatísticas: {e}"}), 500
#
if __name__ == '__main__':
    # Roda o servidor na porta 5000
    app.run(port=5000, debug=True)
