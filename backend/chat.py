from connection import get_db_connection
from datetime import datetime, time
from bson import ObjectId # <-- Importe o ObjectId

# Conecta ao MongoDB
db = get_db_connection()
colecao = db["entregas"]  # coleção que você criou no NoSQLBooster


# 1. ATUALIZE A ASSINATURA DA FUNÇÃO para aceitar 'entregador_id'
def chat(op, numero_pedido=None, entregador_id=None):
    
    # Respostas estáticas (não precisam de ID)
    if op == 1:
        return "Claro! Eu sou seu assistente no sistema de entregas. 👋\n\nVocê pode me usar para tirar dúvidas rápidas sobre o sistema ou para consultar suas entregas do dia, pendentes e concluídas. Basta clicar nas opções!"
    elif op == 2:
        return "É bem simples!\n\n1. Clique em 'Cadastro' no menu ao lado.\n2. Preencha o formulário com os dados da entrega.\n3. Clique em 'Salvar Entrega'.\n\nProntinho! Se preferir, você também pode usar o atalho 'Adicionar Nova Entrega' no Dashboard."
    elif op == 3:
        return "O Dashboard é sua tela principal! 📊\n\nEle mostra um resumo rápido das suas atividades de hoje: quantas entregas você tem no total, quantas já concluiu e quantas ainda estão pendentes. É perfeito para organizar o seu dia!"

    # --- Respostas dinâmicas (AGORA PRECISAM DE ID) ---

    # 2. Validação de segurança: Verifique se o ID foi fornecido
    if not entregador_id:
        return "Ops! Não consegui identificar seu usuário. 😥 Por favor, saia e entre no sistema novamente."

    try:
        entregador_obj_id = ObjectId(entregador_id)
    except Exception:
        return "Ops! Seu ID de usuário parece inválido. 😥 Por favor, saia e entre no sistema novamente."

    # 3. Definição do período "Hoje"
    hoje = datetime.now().date()
    start_of_day = datetime.combine(hoje, time.min)
    end_of_day = datetime.combine(hoje, time.max)
    
    # 4. Criação da query BASE (que filtra por data E por entregador)
    base_query = {
        "entregador_id": entregador_obj_id,
        "data_criacao": {
            "$gte": start_of_day,
            "$lt": end_of_day
        }
    }

    if op == 4:
        # Busca de entregas criadas hoje (APENAS deste entregador)
        entregas = colecao.find(base_query).sort("data_criacao", -1)

        # Resposta
        resposta = "📦 Suas entregas para hoje:\n"
        encontrou = False
        for entrega in entregas:
            resposta += f"- Pedido: {entrega['numero_pedido']} ({entrega['status']})\n  Cliente: {entrega['nome_cliente']}\n  Endereço: {entrega['endereco_completo']}\n\n"
            encontrou = True

        if not encontrou:
            resposta = "Você ainda não tem entregas cadastradas para hoje. Que tal adicionar uma?"

        return resposta
    
    elif op == 5:
        # 5. Lógica de pendentes melhorada (tudo que NÃO é 'Concluída')
        query_pendentes = {
            **base_query, 
            "status": {"$ne": "Concluída"}
        }
        entregas = colecao.find(query_pendentes).sort("data_criacao", -1)

        # Resposta
        resposta = "📋 Suas entregas pendentes de hoje:\n"
        encontrou = False
        for entrega in entregas:
            resposta += f"- Pedido: {entrega['numero_pedido']} ({entrega['status']})\n  Cliente: {entrega['nome_cliente']}\n  Endereço: {entrega['endereco_completo']}\n\n"
            encontrou = True

        if not encontrou:
            resposta = "Boas notícias! Você não tem nenhuma entrega pendente para hoje. ✨"

        return resposta
    
    elif op == 6:
        # Busca de entregas com status "Concluída" (APENAS deste entregador)
        query_concluidas = {
            **base_query,
            "status": {"$regex": "^concluída$", "$options": "i"}
        }
        entregas = colecao.find(query_concluidas).sort("data_criacao", -1)

        # Resposta
        resposta = "✅ Suas entregas concluídas hoje:\n"
        encontrou = False
        for entrega in entregas:
            resposta += f"- Pedido: {entrega['numero_pedido']}\n  Cliente: {entrega['nome_cliente']}\n  Endereço: {entrega['endereco_completo']}\n\n"
            encontrou = True

        if not encontrou:
            resposta = "Você ainda não concluiu nenhuma entrega hoje. Continue assim!"

        return resposta
    
    elif op == 7:
        if not numero_pedido:
            return "Por favor, digite o número do pedido que você quer consultar."

        # Busca pelo identificador da entrega (E TAMBÉM pelo ID do entregador)
        entrega = colecao.find_one({
            "numero_pedido": {"$regex": f"^{numero_pedido}$", "$options": "i"},
            "entregador_id": entregador_obj_id
        })

        if not entrega:
            return f"Não encontrei nenhuma entrega sua com o número de pedido '{numero_pedido}'. 😕"

        # Resposta
        resposta = (
            f"🔍 Informações do Pedido: {entrega['numero_pedido']}\n"
            f"---------------------------------\n"
            f"- Cliente: {entrega['nome_cliente']}\n"
            f"- Endereço: {entrega['endereco_completo']}\n"
            f"- Status: {entrega['status']}\n"
            f"- Descrição: {entrega.get('descricao_entrega', 'N/A')}"
        )

        return resposta
    
    else:
        return "Desculpe, não entendi essa opção. Por favor, clique em um dos botões."