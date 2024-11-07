import json
import os
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv
import pathlib
from typing import Any

from .comm import S3Storage
from .models import ExampleRequestDTO, ExampleResponseDTO
from .comm.db import Database

load_dotenv()


def connect_to_db_logic() -> Database:
    return Database(name=os.getenv("DSW_DB_CONN_NAME"), dsn=os.getenv("DSW_DB_CONN_STR"))


processed_resources = set()
db = connect_to_db_logic()
output_dir = "-"


def example_logic(req_dto: ExampleRequestDTO) -> ExampleResponseDTO:
    return ExampleResponseDTO(
        message=req_dto.message.replace('server', 'client'),
    )


def connect_to_s3_logic() -> S3Storage:
    return S3Storage(
        url=os.getenv("DSW_S3_URL"),
        username=os.getenv("DSW_S3_USERNAME"),
        password=os.getenv("DSW_S3_PASSWORD"),
        bucket=os.getenv("DSW_S3_BUCKET"),
        region=os.getenv("DSW_S3_REGION"),
        multi_tenant=True
    )


def generate_insert_query(data, table):
    columns = ', '.join(data.keys())
    values = ", ".join(format_for_sql(data))
    return f"INSERT INTO {table} ({columns}) VALUES ({values})\;"


def generate_select_query(resource_type, attr, value):
    return "SELECT * FROM {table} WHERE {attr} = '{value}'".format(value=value, table=resource_tables[resource_type], attr=attr)


def generate_select_all_query(resource_type):
    return "SELECT * FROM {table}".format(table=resource_tables[resource_type])


def list_logic(resource_type: str) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
    if resource_type == "all":
        resource = {}
        for each in resource_attributes.keys():
            resource[each] = list_resource(each, resource_attributes[each])
        return resource
    else:
        return {resource_type: list_resource(resource_type, resource_attributes[resource_type])}


def list_resource(resource_type, attributes):
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


def download_file_s3(s3_path: str) -> bool:
    s3 = connect_to_s3_logic()
    s3.ensure_bucket()
    target_path = str(output_dir + "/app/" + s3_path).replace(":", "_")
    target = pathlib.Path(target_path)
    downloaded_file = s3.download_file(s3_path, target)

    if downloaded_file:
        return downloaded_file
    else:
      print(f"File '{s3_path}' not found in bucket.")


# Create a copy of tmp.js to output_dir
def create_recipe_file():
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    script_dir = pathlib.Path(__file__).parent
    recipe_file_path = script_dir / 'recipe_tmp.json'
    with open(recipe_file_path, 'r') as template_recipe:
        data = template_recipe.read()
    with open(os.path.join(output_dir, 'recipe.json'), 'w') as recipe:
        recipe.write(data)


# Add a seed file (its name) to the recipe (the structure)
def add_seed_file_to_recipe(recipe_path, db_file_name):
    with open(recipe_path, 'r') as recipe_file:
        recipe_data = json.load(recipe_file)

        if not any(script.get("filename") == db_file_name for script in recipe_data["db"]["scripts"]):
            # If not, append it to the scripts list
            recipe_data["db"]["scripts"].append({"filename": db_file_name})

    with open(recipe_path, 'w') as recipe_file:
        json.dump(recipe_data, recipe_file, ensure_ascii=False, indent=4)


def create_seed_files_db(resource_type, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"add_{resource_type}.sql")
    file = open(file_path, 'w', encoding='utf-8')
    return file


def process_input(data, output):
    global output_dir
    output_dir = output
    create_recipe_file()
    for resource_type, items in data.items():
        create_seed_files_db(resource_type, output_dir)
        for item in items:
            handle_resource(resource_type, item[resource_identification[resource_type]])


def write_seed_files_db(output_dir, resource_type, query):
    with open(os.path.join(output_dir, f"add_{resource_type}.sql"), 'a', encoding='utf-8') as file:
        if file is None:
           print("File not found")
        file.write(query + "\n")


def has_placeholder_in_s3_objects(resource_s3_objects):
    # Regular expression to match placeholders, e.g., "{some_placeholder}"
    placeholder_pattern = re.compile(r"{placeholder}")

    # Check if the input is a single string
    if placeholder_pattern.search(resource_s3_objects):
        return True

    return False


# TODO needs help a lot
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


def return_fkey_dependency(resource_type, dependent_resource_type):
    for dependency in resource_dependencies_keys.get(resource_type, []):
        if dependent_resource_type in dependency.keys():
            return str(dependency[dependent_resource_type])
    return None



def write_seed_files_db(file, query):
    file.write(query + "\n")


def generate_insert_query(data, table):
    columns = ', '.join(data.keys())
    values = ", ".join(format_for_sql(data))
    return f"INSERT INTO {table} ({columns}) VALUES ({values});"


def handle_resource(resource_type, resource_id):
    if resource_id not in processed_resources:
        processed_resources.add(resource_id)
        query = generate_select_query(resource_type, resource_identification[resource_type], resource_id)
        resources = db.execute_query(query)
        for resource in resources:
            # Dependencies
            for dependency in resource_dependencies.get(resource_type, []):
                dep_type = dependency
                dep_id_key = return_fkey_dependency(resource_type, dep_type)
                if dep_id_key in resource:
                    dep_id = resource[dep_id_key]
                    handle_resource(dep_type, dep_id)

            # S3 objects
            if resource_id != 'wizard:default:1.0.0' and resource_s3_objects[resource_type] != "":
                s3_object = resource_s3_objects[resource_type]
                # If the S3 object contains a placeholder, replace it with the dependent resource's value
                if has_placeholder_in_s3_objects(resource_s3_objects[resource_type]):
                    dependent_key = return_fkey_dependency(resource_type, resource_dependencies[resource_type][0])
                    dependent_value = resource.get(dependent_key)
                    s3_object = s3_object.format(placeholder=dependent_value)
                    download_file_s3(s3_object + str(resource_id))

                else:
                    download_file_s3(s3_object + str(resource_id))

            add_seed_file_to_recipe(output_dir + "/recipe.json", "add_" + resource_type + ".sql")
            insert_query = generate_insert_query(resource, resource_tables[resource_type])
            write_seed_files_db(output_dir, resource_type, insert_query)

            # Dependent resources of this one, that users can't see (document_template_asset, document_template_file)
            for dependent_resource_type in resources_part_of.get(resource_type, []):
                dependent_resource_id_key = return_fkey_dependency(dependent_resource_type, resource_type)
                query = generate_select_query(dependent_resource_type, dependent_resource_id_key,
                                              resource[resource_identification[resource_type]])
                dependent_resources = db.execute_query(query)
                for dependent_resource in dependent_resources:
                    handle_resource(dependent_resource_type, dependent_resource[resource_identification[dependent_resource_type]])
        return
    else:
        print("User not found in database")

def handle_id(data, db, file, resource_type):
    query = "SELECT * FROM {resource_type} WHERE id = '{id}'".format(id=data['id'], resource_type=resource_tables[resource_type])
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(file, insert_query)
    else:
        print("User  not found in database")

def log_and_write_query(resource, resource_type, recipe_file, db, file_dir):
    try:
        # Generate insert query
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        print(f"Generated insert query: {insert_query}")

        # Write to recipe file
        write_seed_files_db(recipe_file, insert_query)

        # Ensure recipe_file is a path string, not a file object
        if isinstance(recipe_file, str):
            file_path = recipe_file
        else:
            # If recipe_file is a file object, get the file path
            file_path = recipe_file.name  # .name gives the file path for file objects

        # Check if the file exists and is writable
        if not os.path.exists(file_path):  # Check if the file exists
            print(f"Error: The file path {file_path} does not exist.")
            return
        elif not os.access(file_path, os.W_OK):  # Check if the file is writable
            print(f"Error: {file_path} is not writable.")
            return

        # Open the file in append mode
        with open(file_path, 'a') as f:
            print(f"Writing query to {file_path}")
            f.write(insert_query + '\n')
            print(f"Successfully wrote query to {file_path}")

    except Exception as e:
        print(f"Error writing query to file: {e}")


def handle_users(input_data, db, recipe_file, resource_type, output_dir):
    query = "SELECT * FROM {resource_type} WHERE uuid = '{uuid}'".format(uuid=input_data['uuid'], resource_type=resource_tables[resource_type])
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
        log_and_write_query(resource, resource_type, recipe_file, db, output_dir)
    else:
        print("User not found in database/more than one record with that ID")

def handle_projects(input_data, db, recipe_file, resource_type, output_dir):
    query = "SELECT * FROM {resource_type} WHERE uuid = '{uuid}'".format(uuid=input_data['uuid'], resource_type=resource_tables[resource_type])
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
        log_and_write_query(resource, resource_type, recipe_file, db, output_dir)
    else:
        print("User not found in database")

def handle_documents(input_data, db, recipe_file, resource_type, output_dir):
    query = "SELECT * FROM {resource_type} WHERE uuid = '{uuid}'".format(uuid=input_data['uuid'], resource_type=resource_tables[resource_type])
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
        log_and_write_query(resource, resource_type, recipe_file, db, output_dir)
    else:
        print("User not found in database")

def handle_project_importers(input_data, db, recipe_file, resource_type, output_dir):
    query = "SELECT * FROM {resource_type} WHERE id = '{id}'".format(id=input_data['id'], resource_type=resource_tables[resource_type])
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
        log_and_write_query(resource, resource_type, recipe_file, db, output_dir)
    else:
        print("Project Importer not found in database")

def handle_knowledge_models(input_data, db, recipe_file, resource_type, output_dir):
    query = "SELECT * FROM {resource_type} WHERE id = '{id}'".format(id=input_data['id'], resource_type=resource_tables[resource_type])
    resource = db.execute_query(query)
    if len(resource) == 1:
        print("This is what i got from db:")
        print(resource)
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
        log_and_write_query(resource, resource_type, recipe_file, db, output_dir)
    else:
        print("User not found in database")

def handle_locales(input_data, db, recipe_file, resource_type,  output_dir):
    if input_data['id'] != 'wizard:default:1.0.0':
        print("\n" + input_data['id'] + "\n")
        query = "SELECT * FROM {resource_type} WHERE id = '{id}'".format(id=input_data['id'], resource_type=resource_tables[resource_type])
        resource = db.execute_query(query)
        if len(resource) == 1:
            insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
            write_seed_files_db(recipe_file, insert_query)
            log_and_write_query(resource, resource_type, recipe_file, db, output_dir)
            s3_locales = download_file_logic("locales/" + input_data['id'], output_dir + "/app" + "/locales/" + input_data['name'] )
            if s3_locales:
                print("File downloaded")
            else:
                print("File not found")
        else:
            print("User not found in database")

def handle_document_templates(input_data, db, recipe_file, resource_type, output_dir):
    query = "SELECT * FROM {resource_type} WHERE id = '{id}'".format(id=input_data['id'], resource_type=resource_tables[resource_type])
    resource = db.execute_query(query)
    if len(resource) == 1:
        insert_query = generate_insert_query(resource[0], resource_tables[resource_type])
        write_seed_files_db(recipe_file, insert_query)
        log_and_write_query(resource, resource_type, recipe_file, db, output_dir)
    else:
        print("User not found in database")


# Map resources to their dependencies
resources_part_of = {
    "users": [],
    "projects": [],
    "documents": [],
    "project_importers": [],
    "knowledge_models": [],
    "locales": [],
    "document_templates": ["document_template_asset", "document_template_file"],
    "document_template_asset": [],
    "document_template_file": []
}


# Map resources to their dependencies
resource_dependencies = {
    "users": [],
    "projects": ["knowledge_models", "document_templates"],
    "documents": ["document_templates", "projects"],
    "project_importers": [],
    "knowledge_models": ["knowledge_models"],
    "locales": [],
    "document_templates": [],
    "document_template_asset": ["document_templates"],
    "document_template_file": ["document_templates"]
}


# Map resources to their dependencies
resource_dependencies_keys = {
    "users": [],
    "projects": [
        {"knowledge_models": "package_id"},
        {"document_templates": "document_template_id"}
    ],
    "documents": [
        {"document_templates": "document_template_id"},
        {"projects": "questionnaire_uuid"}
    ],
    "project_importers" : [],
    "knowledge_models" : [
        {"knowledge_models": "previous_package_id"}
    ],
    "locales": [],
    "document_templates": [],
    "document_template_asset" : [
        {"document_templates": "document_template_id"}
    ],
    "document_template_file" : [
        {"document_templates": "document_template_id"}
    ]
}


# Map resources to their s3 objects
resource_s3_objects = {
    "users": "",
    "projects": "",
    "documents": "documents/",
    "project_importers": "",
    "knowledge_models": "",
    "locales": "locales/",
    "document_templates": "",
    "document_template_asset": "templates/{placeholder}/",
    "document_template_file": ""
}


# Map resources to their s3 objects' file names
resource_s3_objects_fileNames = {
    "locales": "name",
    "document_templates": [],
    "document_template_asset": ["templates/"],
    "document_template_file": ["templates/"]
}


# Map resources to their identification attribute
resource_identification = {
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


# Map resources to attributes visible to users
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
