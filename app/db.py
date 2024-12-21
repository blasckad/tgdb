import os
from arango import ArangoClient

class ArangoDB:
    def __init__(self, db_name, username, password):
        self.client = ArangoClient()
        self.db = self.client.db(
            name=db_name,
            username=username,
            password=password
        )

    def _connect(self):
        system_db = self.client.db('_system', username=self.username, password=self.password, host=self.host)
        if not system_db.has_database(self.db_name):
            system_db.create_database(self.db_name)
        return self.client.db(self.db_name, username=self.username, password=self.password, host=self.host)

    def get_collection(self, name, edge=False):
        if not self.db.has_collection(name):
            return self.db.create_collection(name, edge=edge)
        return self.db.collection(name)
