import json
import os
import uuid
from datetime import datetime
from operator import index
from venv import create

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

# Create a copy of tmp.js to output_dir
def create_recipe_file(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open("recipe_tmp.json", 'r') as template_recipe:
        data = template_recipe.read()
    with open(os.path.join(output_dir, 'recipe.json'), 'w') as recipe:
        recipe.write(data)

def add_db_file_to_recipe(recipe_path, db_file_name):
    with open(recipe_path, 'r') as recipe_file:
        recipe_data = json.load(recipe_file)

        recipe_data["db"]["scripts"].append({"filename" : db_file_name})

    with open(recipe_path, 'w') as recipe_file:
        #recipe_file.write(str(recipe_data))
        json.dump(recipe_data, recipe_file, ensure_ascii=False, indent=4)


def process_input(data, output_dir):
    db = connect_to_db_logic()
    create_recipe_file(output_dir)
    for resource_type, items in data.items():
        handler = resource_handlers.get(resource_type)
        recipe_file = create_seed_files_db(resource_type, output_dir)
        add_db_file_to_recipe(output_dir + "/recipe.json", "add_" + resource_type + ".sql")
        if handler:
            # Call the handler for each item in the list associated with this resource type
            for item in items:
                handler(next(iter(item.values()), None), db, recipe_file, resource_type, output_dir)
        else:
            print(f"Unrecognized resource type: {resource_type}")


def format_for_sql(data_dict):
    sql_values = []
    for key, value in data_dict.items():
        if isinstance(value, uuid.UUID):
            # UUID should be wrapped in single quotes in the SQL query
            sql_values.append(f"'{str(value)}'")

        elif isinstance(value, datetime):
            # Format datetime as 'YYYY-MM-DD HH:MM:SS' (no timezone)
            sql_values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")

        elif isinstance(value, list):
            # Handle lists, convert to PostgreSQL-style array format (e.g., {'value1', 'value2'})
            formatted_list = '\'{' + ', '.join(
                [f"{item}" if isinstance(item, str) else str(item) for item in value]) + '}\''
            sql_values.append(formatted_list)

        elif value is None:
            sql_values.append('NULL')  # Convert None to SQL NULL

        elif isinstance(value, bool):
            # Convert boolean to SQL TRUE/FALSE (no quotes)
            sql_values.append('TRUE' if value else 'FALSE')

        else:
            # For any other data type (strings, numbers), ensure they are wrapped in single quotes
            sql_values.append(f"'{str(value)}'")
    return sql_values


def create_seed_files_db(resource_type, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"add_{resource_type}.sql")
    file = open(file_path, 'w', encoding='utf-8')
    return file

def write_seed_files_db(file, query):
    file.write(query + "\n")
    
    
def generate_insert_query(data, table):
    columns = ', '.join(data.keys())
    values = ", ".join(format_for_sql(data))
    return f"INSERT INTO {table} ({columns}) VALUES ({values});"

def generate_select_query(resource_type, attr, value):
    return "SELECT * FROM {table} WHERE {attr} = '{value}'".format(value=value, table=resource_tables[resource_type], attr=attr)


def handle_users(resource_id, db, recipe_file, resource_type, output_dir):
    query = generate_select_query(resource_type, "uuid", resource_id)
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
    else:
        print("User not found in database")

def handle_projects(resource_id, db, recipe_file, resource_type, output_dir):
    query = generate_select_query(resource_type, "uuid", resource_id )
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
        handle_knowledge_models(resource[0]['package_id'], db, recipe_file, "knowledge_models", output_dir)
        handle_document_templates(resource[0]['document_template_id'], db, recipe_file, "document_templates", output_dir)
    else:
        print("Project not found in database")

def handle_documents(resource_id, db, recipe_file, resource_type, output_dir):
    query = generate_select_query(resource_type, "uuid", resource_id)
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
        handle_document_templates(resource[0]['document_template_id'], db, recipe_file, "document_templates", output_dir)
        handle_projects(resource[0]['questionnaire_uuid'], db, recipe_file, "projects", output_dir)
    else:
        print("Document not found in database")

def handle_project_importers(resource_id, db, recipe_file, resource_type, output_dir):
    query = generate_select_query(resource_type, "id", resource_id)
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
    else:
        print("Project Importer not found in database")


def handle_knowledge_models(resource_id, db, recipe_file, resource_type, output_dir):
    query = generate_select_query(resource_type, "id", resource_id)
    resource = db.execute_query(query)
    if len(resource) == 1:
        if resource[0]['previous_package_id'] is None:
            insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
            write_seed_files_db(recipe_file, insert_query)
        else:
            # print("\n PRINT THE previous package id \n")
            # print(resource[0]['previous_package_id'])
            handle_knowledge_models(resource[0]['previous_package_id'], db, recipe_file, resource_type, output_dir)
            insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
            write_seed_files_db(recipe_file, insert_query)
    else:
        print("User not found in database")

def handle_locales(resource_id, db, recipe_file, resource_type,  output_dir):
    if resource_id != 'wizard:default:1.0.0':
        query = generate_select_query(resource_type, "id", resource_id )
        resource = db.execute_query(query)
        if len(resource) == 1:
            insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
            write_seed_files_db(recipe_file, insert_query)
            s3_locales = download_file_logic("locales/" + resource_id, output_dir + "/app" + "/locales/" + resource[0]['name'])
            if s3_locales:
                print("File downloaded")
            else:
                print("File not found")
        else:
            print("User not found in database")

def handle_document_templates(resource_id, db, recipe_file, resource_type, output_dir):
    query = generate_select_query(resource_type, "id" , resource_id )
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
        handle_document_templates_files(resource_id, db, recipe_file)
        handle_document_templates_assets(resource_id, db, recipe_file, output_dir)
    else:
        print("User not found in database")

def handle_document_templates_assets(doc_temp_id, db, recipe_file, output_dir):
    query = generate_select_query("document_template_asset", "document_template_id", doc_temp_id)
    resource = db.execute_query(query)
    for asset in resource:
        insert_query = generate_insert_query(asset, "document_template_asset")
        write_seed_files_db(recipe_file, insert_query)
        s3_assets = download_file_logic("templates/" + str(doc_temp_id) + "/" + str(asset['uuid']), output_dir + "/app" + "/document_templates/" + str(doc_temp_id).replace(":", "_") + "/asset_" + str(asset['uuid']) )
        if s3_assets:
            print("File downloaded")
        else:
            print("File not found")


def handle_document_templates_files(doc_temp_id, db, recipe_file):
    query = generate_select_query("document_template_file", "document_template_id", doc_temp_id)
    resource = db.execute_query(query)
    for file in resource:
        insert_query = generate_insert_query(file, "document_template_file")
        write_seed_files_db(recipe_file, insert_query)


# Map resource types to handler functions
resource_handlers = {
    "users": handle_users,
    "projects": handle_projects,
    "documents": handle_documents,
    "project_importers": handle_project_importers,
    "knowledge_models": handle_knowledge_models,
    "locales":handle_locales,
    "document_templates": handle_document_templates,
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
    "document_template_asset": "document_template_asset",
    "document_template_file": "document_template_file"
}