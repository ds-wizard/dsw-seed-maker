import os
from dotenv import load_dotenv
import pathlib
from typing import Any
from psycopg import sql

from .comm import S3Storage
from .models import ExampleRequestDTO, ExampleResponseDTO
from .comm.db import Database

load_dotenv()


def example_logic(req_dto: ExampleRequestDTO) -> ExampleResponseDTO:
    return ExampleResponseDTO(
        message=req_dto.message.replace('server', 'client'),
    )


def connect_to_db_logic() -> Database:
    return Database(name=os.getenv("DSW_DB_CONN_NAME"), dsn=os.getenv("DSW_DB_CONN_STR"))


def connect_to_s3_logic() -> S3Storage:
    return S3Storage(
        url=os.getenv("DSW_S3_URL"),
        username=os.getenv("DSW_S3_USERNAME"),
        password=os.getenv("DSW_S3_PASSWORD"),
        bucket=os.getenv("DSW_S3_BUCKET"),
        region=os.getenv("DSW_S3_REGION"),
        multi_tenant=True
    )


def list_logic(resource_type: str) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
    db = connect_to_db_logic()
    if resource_type == 'all':
        return list_all_logic(db)
    if resource_type == 'users':
        return {'users': list_users_logic(db)}
    if resource_type == 'project_importers':
        return {'project_importers': list_project_importers_logic(db)}
    if resource_type == 'knowledge_models':
        return {'knowledge_models': list_knowledge_models_logic(db)}
    if resource_type == 'locales':
        return {'locales': list_locales_logic(db)}
    if resource_type == 'document_templates':
        return {'document_templates': list_document_templates_logic(db)}
    if resource_type == 'projects':
        return {'projects': list_projects_logic(db)}
    if resource_type == 'documents':
        return {'documents': list_documents_logic(db)}

    raise ValueError(f'Invalid resource type: {resource_type}')


def list_all_logic(db) -> dict[str, list[dict[str, str | Any]] | list[dict[str, Any]]]:
    users = list_users_logic(db)
    project_importers = list_project_importers_logic(db)
    knowledge_models = list_knowledge_models_logic(db)
    locales = list_locales_logic(db)
    document_templates = list_document_templates_logic(db)
    projects = list_projects_logic(db)
    documents = list_documents_logic(db)
    resources = {
        'users': users,
        'project_importers': project_importers,
        'knowledge_models': knowledge_models,
        'locales': locales,
        'document_templates': document_templates,
        'projects': projects,
        'documents': documents
    }
    return resources


def list_users_logic(db) -> list[dict[str, str | Any]]:
    query = sql.SQL('SELECT * FROM user_entity')
    resources = db.execute_query(query)
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


def list_project_importers_logic(db) -> list[dict[str, Any]]:
    query = sql.SQL('SELECT * FROM questionnaire_importer')
    resources = db.execute_query(query)
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
    parsed_resources = [
        {
            'id': row['id'],
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
    parsed_resources = [
        {
            'id': row['id'],
            'name': row['name'],
            'code': row['code'],
            'description': row['description']
        }
        for row in resources
    ]
    return parsed_resources


def list_document_templates_logic(db) -> list[dict[str, Any]]:
    query = sql.SQL('SELECT * FROM document_template')
    resources = db.execute_query(query)
    parsed_resources = [
        {
            'id': row['id'],
            'name': row['name'],
            'template_id': row['template_id']
        }
        for row in resources
    ]
    return parsed_resources


def list_projects_logic(db) -> list[dict[str, Any]]:
    query = sql.SQL('SELECT * FROM questionnaire')
    resources = db.execute_query(query)
    parsed_resources = [
        {
            'uuid': str(row['uuid']),  # Convert UUID to string
            'name': row['name']
        }
        for row in resources
    ]
    return parsed_resources


def list_documents_logic(db) -> list[dict[str, Any]]:
    query = sql.SQL('SELECT * FROM document')
    resources = db.execute_query(query)
    parsed_resources = [
        {
            'uuid': str(row['uuid']),  # Convert UUID to string
            'name': row['name']
        }
        for row in resources
    ]
    return parsed_resources


def download_file_logic(file_name: str, target_path: str) -> bool:
    s3 = connect_to_s3_logic()
    s3.ensure_bucket()
    target_path = pathlib.Path(target_path)
    downloaded_file = s3.download_file(file_name, target_path)

    if downloaded_file:
        print(f"File '{file_name}' downloaded to '{target_path}'.")
    else:
        print(f"File '{file_name}' not found in bucket '{s3.bucket}'.")

    return downloaded_file

def process_input(data, output_dir):
    db = connect_to_db_logic()
    for resource_type, items in data.items():
        handler = resource_handlers.get(resource_type)
        file = create_seed_files_db(resource_type, output_dir)
        if handler:
            # Call the handler for each item in the list associated with this resource type
            for item in items:
                handler(item, db, file)
        else:
            print(f"Unrecognized resource type: {resource_type}")

def create_seed_files_db(resource_type, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"add_{resource_type}.sql")
    file = open(file_path, 'w')
    return file

def write_seed_files_db(file, resource_type, resource):
    data = "INSERT INTO {table} VALUES {values};".format(table=resource_tables[resource_type], values=resource)
    file.write(data + "\n")

# Define generic handler functions for each resource type
def handle_user(data, db, file):
    print(f"Processing user: {data['uuid']} - {data['first_name']} {data['last_name']} ({data['role']})")
    # Use a parameterized query for better syntax and security
    query = "SELECT * FROM user_entity WHERE uuid = '{uuid}'".format(uuid=data['uuid'])
    resource = db.execute_query(query)
    #check for only one resource otherwise print error
    if len(resource) == 1:
        print("This is what i got from db:")
        print(resource)
        write_seed_files_db(file, "users", resource[0])
    else:
        print("User  not found in database")


def handle_project(data, db, file):
    print(f"Processing project: {data['uuid']} - {data['name']}")
    # Add specific logic for handling a project here


def handle_document(data, db, file):
    print(f"Processing document: {data['uuid']} - {data['name']}")
    # Add specific logic for handling a document here


def handle_project_importer(data, db, file):
    print(f"Processing project importer: {data['id']} - {data['name']}")
    # Add specific logic for handling a project importer here


def handle_knowledge_model(data, db, file):
    print(f"Processing knowledge model: {data['id']} - {data['name']}")
    # Add specific logic for handling a knowledge model here


def handle_locale(data, db, file):
    print(f"Processing locale: {data['id']} - {data['name']} ({data['code']})")
    # Add specific logic for handling a locale here


def handle_document_template(data, db, file):
    print(f"Processing document template: {data['id']} - {data['name']}")
    # Add specific logic for handling a document template here

# Map resource types to handler functions
resource_handlers = {
    "users": handle_user,
    "projects": handle_project,
    "documents": handle_document,
    "project_importers": handle_project_importer,
    "knowledge_models": handle_knowledge_model,
    "locales": handle_locale,
    "document_templates": handle_document_template,
}

# Map resources to their table names
resource_tables = {
    "users": "user_entity",
    "projects": "questionnaire",
    "documents": "document",
    "project_importers": "questionnaire_importer",
    "knowledge_models": "package",
    "locales": "locale",
    "document_templates": "document_template",
}
