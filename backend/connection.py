# pip install pymongo - é necessário baixar essa biblioteca

from pymongo import MongoClient

def get_db_connection():

    try:
        # Conexão padrão (localhost, porta 27017)
        client = MongoClient("mongodb://localhost:27017/")

# mongodb://usuario:senha@localhost:27017/ - use isso se tiver criado um usuário e senha


        # Nome do banco que você já criou no NoSQLBooster
        db = client["ERP-ENTREGA"]

        print("Conexão estabelecida com sucesso.")
        return db

    except Exception as e:
        print("Erro ao conectar no MongoDB:", e)
        return None
