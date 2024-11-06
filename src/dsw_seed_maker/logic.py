from .comm import Database
from .models import ExampleRequestDTO, ExampleResponseDTO
from .comm.db import Database, DatabaseConnection
from psycopg import sql
from typing import List, Dict, Any

def example_logic(req_dto: ExampleRequestDTO) -> ExampleResponseDTO:
    return ExampleResponseDTO(
        message=req_dto.message.replace('server', 'client'),
    )

def connect_to_db_logic() -> Database:
    return Database(name='postgres', dsn='postgresql://postgres:postgres@localhost:15432/wizard')

def list_logic(resource_type: str) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
    db = connect_to_db_logic()
    if resource_type == 'all':
        return list_all_logic(db)
    elif resource_type == 'users':
        return {'users' : list_users_logic(db)}
    elif resource_type == 'projects_importers':
        return {'projects_importers' : list_projects_importers_logic(db)}
    elif resource_type == 'knowledge_models':
        return {'knowledge_models' : list_knowledge_models_logic(db)}
    elif resource_type == 'locale':
        return {'locale' : list_locales_logic(db)}

def list_all_logic(db) -> dict[str, list[dict[str, str | Any]] | list[dict[str, Any]]]:
    users= list_users_logic(db)
    projects_importers = list_projects_importers_logic(db)
    knowledge_models = list_knowledge_models_logic(db)
    locale = list_locales_logic(db)
    resources = {
        'users': users,
        'projects_importers': projects_importers,
        'knowledge_models': knowledge_models,
        'locale': locale
    }
    return resources

def list_users_logic(db) -> list[dict[str, str | Any]]:
    query = sql.SQL('SELECT * FROM user_entity')
    resources = db.execute_query(query)
    # Parse the dictionaries into instances
    parsed_resources = [
        {
            'uuid': str(row['uuid']),  # Convert UUID to string
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'role': row['role']
        }
        for row in resources
    ]
    return parsed_resources

def list_projects_importers_logic(db) -> list[dict[str, Any]]:
    query = sql.SQL('SELECT * FROM questionnaire_importer')
    resources = db.execute_query(query)
    # Parse the dictionaries into UserDTO instances
    parsed_resources: list[dict[str, Any]] = [
        {
            'id': row['id'],  # Convert UUID to string
            'name': row['name'],
            'description': row['description']
        }
        for row in resources
    ]
    return parsed_resources

def list_knowledge_models_logic(db) -> list[dict[str, Any]]:
    query = sql.SQL('SELECT * FROM package')
    resources = db.execute_query(query)
    # Parse the dictionaries into UserDTO instances
    parsed_resources = [
        {
            'id': row['id'],  # Convert UUID to string
            'name': row['name'],
            'km_id': row['km_id'],
            'description': row['description']
        }
        for row in resources
    ]
    return parsed_resources

def list_locales_logic(db) -> list[dict[str, Any]]:
    query = sql.SQL('SELECT * FROM locale')
    resources = db.execute_query(query)
    # Parse the dictionaries into UserDTO instances
    parsed_resources = [
        {
            'id': row['id'],  # Convert UUID to string
            'name': row['name'],
            'code': row['code'],
            'description': row['description']
        }
        for row in resources
    ]
    return parsed_resources