import pymongo
import os


class MongoDatabase:
    def __init__(self, connection_url, database_name):
        self.client = pymongo.MongoClient(connection_url)
        self.db = self.client[database_name]

    def close_connection(self):
        self.client.close()


class MongoCollection:
    def __init__(self, db: MongoDatabase, collection_name: str):
        self.collection = db.db[collection_name]

    def insert(self, data):
        self.collection.insert_one(data)

    def update(self, search, data):
        self.collection.update_one(search, data)

    def get(self, search):
        return self.collection.find_one(search)

    def get_all(self, search = None):
        return list(self.collection.find(search))

    def delete(self, search):
        return self.collection.delete_many(search)

    def delete_all(self, search):
        return self.collection.delete_many(search)


db = MongoDatabase(os.environ['MONGODB_CONNECTION_URL'], 'commissioner_bot')
player_collection = MongoCollection(db, 'players')
manager_collection = MongoCollection(db, 'managers')
reaction_collection = MongoCollection(db, 'reactions')
guild_preferences_collection = MongoCollection(db, 'guild_preferences')
dm_collection = MongoCollection(db, 'direct_messages')
