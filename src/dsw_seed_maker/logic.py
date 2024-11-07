import json
import os
import uuid
from datetime import datetime

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
    if resource_type== "all":
        resource = {}
        for each in resource_attributes.keys():
            resource[each] = list_resource(each,db, resource_attributes[each])
        return resource
    else:
        return {resource_type : list_resource(resource_type, db, resource_attributes[resource_type])}


def generate_insert_query(data, table):
    columns = ', '.join(data.keys())
    values = ", ".join(format_for_sql(data))
    return f"INSERT INTO {table} ({columns}) VALUES ({values});"


def generate_select_query(resource_type, attr, value):
    return "SELECT * FROM {table} WHERE {attr} = '{value}'".format(value=value, table=resource_tables[resource_type], attr=attr)


def generate_select_all_query(resource_type):
    return "SELECT * FROM {table}".format(table=resource_tables[resource_type])


def list_resource(resource_type, db, attributes):
    query = generate_select_all_query(resource_type)
    resources = db.execute_query(query)
    parsed_resources = [
        {
            attr: str(row[attr]) if attr == 'uuid' else row[attr]  # Convert 'uuid' to string; others as-is
            for attr in attributes if attr in row
        }
        for row in resources
    ]

    return parsed_resources


def download_file_logic(s3_path: str, target_dir: str, target_path) -> bool:
    s3 = connect_to_s3_logic()
    s3.ensure_bucket()
    target = pathlib.Path(target_dir + "/app/" + target_path)
    downloaded_file = s3.download_file(s3_path, target)

    if downloaded_file:
        print(f"File '{s3_path}' downloaded to '{target}'.")
    else:
        print(f"File '{s3_path}' not found in bucket.")

    return downloaded_file

# Create a copy of tmp.js to output_dir
def create_recipe_file(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open("recipe_tmp.json", 'r') as template_recipe:
        data = template_recipe.read()
    with open(os.path.join(output_dir, 'recipe.json'), 'w') as recipe:
        recipe.write(data)

def add_seed_file_to_recipe(recipe_path, db_file_name):
    with open(recipe_path, 'r') as recipe_file:
        recipe_data = json.load(recipe_file)

        recipe_data["db"]["scripts"].append({"filename" : db_file_name})

    with open(recipe_path, 'w') as recipe_file:
        #recipe_file.write(str(recipe_data))
        json.dump(recipe_data, recipe_file, ensure_ascii=False, indent=4)

def create_seed_files_db(resource_type, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"add_{resource_type}.sql")
    file = open(file_path, 'w', encoding='utf-8')
    return file

def process_input(data, output_dir):
    db = connect_to_db_logic()
    create_recipe_file(output_dir)
    for resource_type, items in data.items():
        create_seed_files_db(resource_type, output_dir)
        add_seed_file_to_recipe(output_dir + "/recipe.json", "add_" + resource_type + ".sql")
        for item in items:
            handle_resource(resource_type, item[resource_idenificators[resource_type]], db, output_dir)

def write_seed_files_db(output_dir, resource_type, query):
    with open(os.path.join(output_dir, f"add_{resource_type}.sql"), 'a') as file:
        if file is None:
            print("File not found")
        file.write(query + "\n")
        print("Query added to file" + resource_type)


def format_for_sql(data_dict): # needs help a lot
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

def return_fkey_dependency(resource_type, dependent_resource_type):
    for dependency in resource_dependencies.get(resource_type, []):
        if dependency == dependent_resource_type:
            return dependency[dependent_resource_type]

def handle_resource(resource_type, resource_id, db, output_dir):
    query = generate_select_query(resource_type, resource_idenificators[resource_type], resource_id)
    resource = db.execute_query(query)
    # dependencies
    for dependency in resource_dependencies.get(resource_type, []):
        if isinstance(dependency, dict):
            dep_type = list(dependency.keys())[0]
            dep_id = return_fkey_dependency(resource_type, dep_type)
            handle_resource(dep_type, dep_id, db, output_dir)

        # s3 objects
    for s3_object in resource_s3_objects[resource_type]:
        if resource_id != 'wizard:default:1.0.0':
            download_file_logic(s3_object + resource_id, output_dir, s3_object + "/" + resource[0][resource_s3_objects_fileNames[resource_type]])

    insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
    write_seed_files_db(output_dir, resource_type, insert_query)

    #TODO dependent resources - document_template assetes and files

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

resource_dependencies = {
    "users": [],
    "projects": ["knowledge_models", "document_templates"],
    "documents": ["document_templates", "projects"],
    "project_importers": [],
    "knowledge_models": ["knowledge_models"],
    "locales": [],
    "document_templates": ["document_template_asset", "document_template_file"],
    "document_template_asset": ["document_templates"],
    "document_template_file": ["document_templates"]
}

resource_dependencies_keys = {
    "users": [],
    "projects": [
        { "knowledge_models" : "package_id"},
        { "document_templates" : "document_template_id"}
    ],
    "documents": [
        { "document_templates" : "document_template_id"},
        { "projects" : "questionnaire_uuid"}
    ],
    "project_importers": [],
    "knowledge_models": [
        { "knowledge_models" : "previous_package_id"}
    ],
    "locales": [],
    "document_templates": [],
    "document_template_asset": [
        { "document_templates" : "document_template_id"}
    ],
    "document_template_file": [
        { "document_templates" : "document_template_id"}
    ]
}

# Map resources to their s3 objects
resource_s3_objects = {
    "users": [],
    "projects": [],
    "documents": [],
    "project_importers": [],
    "knowledge_models": [],
    "locales": ["locales/"],
    "document_templates": [],
    "document_template_asset": ["templates/"],
    "document_template_file": ["templates/"]
}

resource_s3_objects_fileNames = {
    "locales": "name",
    "document_templates": [],
    "document_template_asset": ["templates/"],
    "document_template_file": ["templates/"]
}

resource_idenificators = {
    "users": "uuid",
    "projects": "uuid",
    "documents": "uuid",
    "project_importers": "id",
    "knowledge_models": "id",
    "locales": "id",
    "document_templates": "id",
    "document_template_asset": "uuid",
    "document_template_file": "uuid"
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

# Map resources to attributes
resource_attributes = {
    "users": ['uuid', 'first_name', 'last_name', 'role', 'email'],
    "projects": ['uuid', 'name'],
    "documents": ['uuid', 'name'],
    "project_importers": ['id', 'name', 'description'],
    "knowledge_models": ['id', 'name', 'km_id', 'description'],
    "locales": ['id', 'name', 'code', 'description'],
    "document_templates": ['id', 'name', 'template_id'],
    "document_template_asset": ['uuid', 'document_template_id'],
    "document_template_file": ['uuid', 'document_template_id']
}