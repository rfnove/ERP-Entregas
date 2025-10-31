import json
import random
import pymongo # Importante: para ler os IDs
from datetime import datetime, timedelta
from faker import Faker
from bson import ObjectId

# --- 1. CONFIGURAÇÃO OBRIGATÓRIA ---

# Cole aqui sua string de conexão completa (a mesma do seu 'connection.py')
MONGO_URI = "mongodb://localhost:27017" # <-- MUDE AQUI

# O nome exato do seu banco de dados
DATABASE_NAME = "ERP-ENTREGA" # <-- MUDE AQUI

# Quantas entregas fictícias você quer criar?
NUM_ENTREGAS = 300 

# -------------------------------------

fake = Faker('pt_BR')

# Classe especial para converter ObjectId e Datetime para o formato JSON do Mongo
class MongoJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            # Formato Extended JSON v2 para datas
            return {"$date": o.isoformat()}
        if isinstance(o, ObjectId):
            # Formato Extended JSON v2 para ObjectIds
            return {"$oid": str(o)}
        return super().default(o)

# --- 2. Buscar IDs de Entregadores Reais ---

lista_entregador_ids = []
try:
    print(f"Conectando ao MongoDB em '{MONGO_URI}'...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    # Busca apenas o campo _id da coleção de entregadores
    entregadores_cursor = db.entregador.find({}, {"_id": 1})
    
    lista_entregador_ids = [doc["_id"] for doc in entregadores_cursor]
    
    client.close()
    
    if not lista_entregador_ids:
        print("\n!!! ERRO !!!")
        print(f"Nenhum entregador encontrado na coleção 'entregador' do banco '{DATABASE_NAME}'.")
        print("Você precisa cadastrar entregadores antes de rodar este script.")
        exit() # Para o script
        
    print(f"Sucesso! {len(lista_entregador_ids)} IDs de entregadores foram carregados.")

except Exception as e:
    print(f"\n!!! ERRO AO CONECTAR NO MONGODB !!!")
    print(f"Verifique sua MONGO_URI e DATABASE_NAME. Erro: {e}")
    exit() # Para o script

# --- 3. Gerar Entregas Fictícias ---

print(f"Gerando {NUM_ENTREGAS} entregas fictícias...")
entregas = []
lista_status = ["Pendente", "Em andamento", "Concluída"]

for i in range(NUM_ENTREGAS):
    
    # Pondera a escolha para ter mais "Concluída" (bom para os gráficos)
    status_escolhido = random.choices(lista_status, weights=[0.1, 0.1, 0.8], k=1)[0]
    
    # Gera datas nos últimos 90 dias (bom para os gráficos)
    data_criacao = fake.date_time_between(start_date="-90d", end_date="now")
    data_conclusao = None
    
    if status_escolhido == "Concluída":
        # Define uma data de conclusão algumas horas/dias após a criação
        data_conclusao = data_criacao + timedelta(hours=random.randint(1, 48))
        # Garante que a data de conclusão não seja no futuro
        if data_conclusao > datetime.now():
            data_conclusao = datetime.now()
            
    nova_entrega = {
        "_id": ObjectId(), # Cria um novo ID único para a *entrega*
        "numero_pedido": fake.unique.ean(length=13),
        "nome_cliente": fake.name(),
        "endereco_completo": fake.street_address(),
        "cidade": "São Paulo",
        "tipo_entrega": random.choice(["Padrão", "Expressa", "Shoppe"]),
        "status": status_escolhido,
        "descricao_entrega": fake.sentence(nb_words=6),
        "data_criacao": data_criacao,
        "data_entrega_concluida": data_conclusao,
        
        # --- A MÁGICA ACONTECE AQUI ---
        # Associa a entrega a um ID de entregador REAL e ALEATÓRIO
        "entregador_id": random.choice(lista_entregador_ids) 
    }
    entregas.append(nova_entrega)

print("Geração concluída.")

# --- 4. Salvar Arquivo JSON ---

output_filename = 'entregas_para_importar2.json'
try:
    with open(output_filename, 'w', encoding='utf-8') as f:
        # Usa o Encoder especial para salvar datas e IDs corretamente
        json.dump(entregas, f, cls=MongoJsonEncoder, indent=2, ensure_ascii=False)
        
    print(f"\nSucesso! Arquivo salvo como: '{output_filename}'")
    print(f"Este arquivo contém {len(entregas)} entregas prontas para importação.")

except Exception as e:
    print(f"\nOcorreu um erro ao salvar o arquivo JSON: {e}")