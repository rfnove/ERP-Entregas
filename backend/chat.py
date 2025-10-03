from connection import get_db_connection
from datetime import datetime

# Conecta ao MongoDB
db = get_db_connection()
colecao = db["entregas"]  # coleção que você criou no NoSQLBooster


def chat(op):
    if op == 1:
        return "O sistema consiste em 3 partes principais e a forma de ter acesso a elas é clicando nas opções no menu à esquerda da tela. A primeira é o Dashboard que traz análises rápidas e relevantes para as atividades do dia a dia. A segunda é o cadastro de entregas, onde você clica para criar uma nova entrega e só necessita preencher as informações que são requisitadas. Por fim, o chatbot é um meio de obter respostas rápidas e relevantes do sistema, por exemplo sobre como utilizar o sistema, entregas do dia, entregas pendentes, dentre outras."
    elif op == 2:
        return "Para cadastrar uma nova entrega é necessário clicar no botão de 'Cadastro' no menu ou'Adicionar Nova Entrega' através da aba do Dashboard. Feito isso, basta preencher o formulário com todas as informações referentes a entrega e clicar no botão 'Salvar Entrega'.\n Caso seja necessário existe um botão de limpar formulário."
    elif op == 3:
        return "O Dashboard serve como uma análise a respeito das suas atividades recentes, como a quantidade de entregas cadastradas, entregas feitas, entregas pendentes, dentre outras. Para acessá-lo basta clicar no botão 'Dashboard' no menu."
    elif op == 4:
        # Data de hoje (ignora hora/minuto/segundo)
        hoje = datetime.now().date()

        # Busca entregas criadas hoje
        entregas = colecao.find({
            "data_criacao": {
                "$gte": datetime.combine(hoje, datetime.min.time()),
                "$lt": datetime.combine(hoje, datetime.max.time())
            }
        })

        # Monta a resposta
        resposta = "Entregas do dia:\n"
        encontrou = False
        for entrega in entregas:
            resposta += f"- Pedido: {entrega['numero_pedido']}, Cliente: {entrega['nome_cliente']}, Endereço: {entrega['endereco_completo']}\n"
            encontrou = True

        if not encontrou:
            resposta = "Nenhuma entrega cadastrada para hoje."

        return resposta
    elif op == 5:
        # Busca entregas pendentes (status diferente de concluído)
        entregas = colecao.find({"status": "Em andamento"})

        resposta = "📋 Entregas pendentes:\n"
        encontrou = False
        for entrega in entregas:
            resposta += f"- Pedido: {entrega['numero_pedido']}, Cliente: {entrega['nome_cliente']}, Endereço: {entrega['endereco_completo']}\n"
            encontrou = True

        if not encontrou:
            resposta = "Não há entregas pendentes no momento."

        return resposta