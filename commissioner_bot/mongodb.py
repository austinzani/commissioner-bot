import pymongo


class MongoDatabase:
    def __init__(self, connection_url, database_name, collection_name):
        self.client = pymongo.MongoClient(connection_url)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

    def insert_transaction(self, transaction):
        self.collection.insert_one(transaction)

    def get_transaction(self, transaction_id):
        return self.collection.find_one({"transaction_id": transaction_id})

    def get_all_tasks(self):
        return list(self.collection.find())

    def close_connection(self):
        self.client.close()
