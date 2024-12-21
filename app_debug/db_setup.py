from config import get_database

def setup_collections():
    db = get_database()

    # Создание коллекций, если они не существуют
    if not db.has_collection('Nodes'):
        db.create_collection('Nodes')

    if not db.has_collection('Edges'):
        db.create_collection('Edges', edge=True)

    return db
