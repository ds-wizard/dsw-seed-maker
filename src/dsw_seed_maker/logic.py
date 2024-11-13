import datetime
import json
import os
import pathlib
import re
import typing
import uuid

from .comm import Database, S3Storage
from .config import Config
from .consts import DEFAULT_ENCODING
from .models import ExampleRequestDTO, ExampleResponseDTO


def connect_to_db_logic() -> Database:
    return Database(
        name='main',
        dsn=Config.DSW_DB_CONN_STR,
    )


RECIPE_TEMPLATE = pathlib.Path(__file__).parent / 'recipe_template.json'


processed_resources = set()
db = connect_to_db_logic()


def example_logic(req_dto: ExampleRequestDTO) -> ExampleResponseDTO:
    return ExampleResponseDTO(
        message=req_dto.message.replace('server', 'client'),
    )


def connect_to_s3_logic() -> S3Storage:
    return S3Storage(
        url=Config.DSW_S3_URL,
        username=Config.DSW_S3_USERNAME,
        password=Config.DSW_S3_PASSWORD,
        bucket=Config.DSW_S3_BUCKET,
        region=Config.DSW_S3_REGION,
        multi_tenant=True
    )


def generate_insert_query(data, table):
    columns = ', '.join(data.keys())
    values = ', '.join(format_for_sql(data))
    return f'INSERT INTO {table} ({columns}) VALUES ({values})'


def generate_select_query(resource_type, attr, value):
    table = resource_tables[resource_type]
    return f'SELECT * FROM {table} WHERE {attr} = \'{value}\''


def generate_select_all_query(resource_type):
    table = resource_tables[resource_type]
    return f'SELECT * FROM {table}'


def list_logic(resource_type: str) -> dict[str, list[dict[str, typing.Any]]]:
    if resource_type == 'all':
        return {
            resource_key: list_resource(resource_key, attributes)
            for resource_key, attributes in resource_attributes.items()
        }
    return {
        resource_type: list_resource(resource_type, resource_attributes[resource_type])
    }


def list_resource(resource_type, attributes) -> list[dict[str, typing.Any]]:
    query = generate_select_all_query(resource_type)
    resources = db.execute_query(query)
    # Convert 'uuid' to string; others as-is
    parsed_resources = [
        {
            attr: str(row[attr]) if attr == 'uuid' else row[attr]
            for attr in attributes if attr in row
        }
        for row in resources
    ]

    return parsed_resources


def download_file_s3(s3_path: str) -> bool:
    s3 = connect_to_s3_logic()
    s3.ensure_bucket()
    target_path = (Config.OUT_DIR / 'app' / s3_path).as_posix().replace(':', '_')
    target = pathlib.Path(target_path)
    downloaded_file = s3.download_file(s3_path, target)

    if not downloaded_file:
        print(f'File \'{s3_path}\' not found.')
    return downloaded_file


# Create a copy of tmp.js to output_dir
def create_recipe_file():
    Config.ensure_out_dir()

    data = RECIPE_TEMPLATE.read_text(encoding=DEFAULT_ENCODING)
    recipe_file = Config.OUT_DIR / 'recipe.json'
    recipe_file.write_text(data, encoding=DEFAULT_ENCODING)


# Add a seed file (its name) to the recipe (the structure)
def add_seed_file_to_recipe(recipe_path, db_file_name):
    with open(recipe_path, 'r', encoding=DEFAULT_ENCODING) as recipe_file:
        recipe_data = json.load(recipe_file)

        if not any(script.get('filename') == db_file_name
                   for script in recipe_data['db']['scripts']):
            # If not, append it to the scripts list
            recipe_data['db']['scripts'].append({'filename': db_file_name})

    with open(recipe_path, 'w', encoding=DEFAULT_ENCODING) as recipe_file:
        json.dump(recipe_data, recipe_file, ensure_ascii=False, indent=4)


def create_seed_files_db(resource_type, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f'add_{resource_type}.sql')
    with open(file_path, 'w', encoding=DEFAULT_ENCODING) as _:
        pass


def process_input(data, output):
    Config.OUT_DIR = output
    create_recipe_file()
    for resource_type, items in data.items():
        create_seed_files_db(resource_type, Config.OUT_DIR)
        for item in items:
            handle_resource(resource_type, item[resource_identification[resource_type]])


def write_seed_files_db(output_dir: pathlib.Path, resource_type: str, query: str):
    with open(
            file=output_dir / f'add_{resource_type}.sql',
            mode='a',
            encoding=DEFAULT_ENCODING
    ) as file:
        if file is None:
            print('File not found')
        file.write(query + '\n')


def has_placeholder_in_s3_objects(x_resource_s3_objects):
    # Regular expression to match placeholders, e.g., '{some_placeholder}'
    placeholder_pattern = re.compile(r'{placeholder}')

    # Check if the input is a single string
    if placeholder_pattern.search(x_resource_s3_objects):
        return True

    return False


# TODO needs help a lot
def format_for_sql(data_dict):
    sql_values = []
    for value in data_dict.values():
        if isinstance(value, uuid.UUID):
            # UUID should be wrapped in single quotes in the SQL query
            sql_values.append(f'\'{str(value)}\'')

        elif isinstance(value, datetime.datetime):
            # Format datetime as 'YYYY-MM-DD HH:MM:SS' (no timezone)
            sql_values.append(f'\'{value.strftime('%Y-%m-%d %H:%M:%S')}\'')

        elif isinstance(value, list):
            # Handle lists, convert to PostgreSQL-style array format (e.g., {'value1', 'value2'})
            formatted_list = '\'{' + ', '.join([str(item) for item in value]) + '}\''
            sql_values.append(formatted_list)

        elif value is None:
            sql_values.append('NULL')  # Convert None to SQL NULL

        elif isinstance(value, bool):
            # Convert boolean to SQL TRUE/FALSE (no quotes)
            sql_values.append('TRUE' if value else 'FALSE')

        else:
            # For any other data type (strings, numbers), ensure they are wrapped in single quotes
            sql_values.append(f'\'{str(value)}\'')
    return sql_values


def return_fkey_dependency(resource_type, dependent_resource_type):
    for dependency in resource_dependencies_keys.get(resource_type, []):
        if dependent_resource_type in dependency.keys():
            return str(dependency[dependent_resource_type])
    return None


def handle_resource(resource_type, resource_id):
    if resource_id in processed_resources:
        return

    processed_resources.add(resource_id)
    query = generate_select_query(
        resource_type,
        resource_identification[resource_type],
        resource_id,
    )
    resources = db.execute_query(query)

    for resource in resources:
        process_resource(resource, resource_id, resource_type)


def process_resource(resource, resource_id, resource_type):
    # Dependencies
    for dependency in resource_dependencies.get(resource_type, []):
        dep_type = dependency
        dep_id_key = return_fkey_dependency(
            resource_type=resource_type,
            dependent_resource_type=dep_type,
        )
        if dep_id_key in resource:
            dep_id = resource[dep_id_key]
            handle_resource(dep_type, dep_id)

    process_resource_s3(resource, resource_id, resource_type)

    add_seed_file_to_recipe(Config.OUT_DIR / 'recipe.json', f'add_{resource_type}.sql')
    insert_query = generate_insert_query(resource, resource_tables[resource_type])
    write_seed_files_db(Config.OUT_DIR, resource_type, insert_query)

    # Dependent resources of this one, that users can't
    # see (document_template_asset, document_template_file)
    for dependent_resource_type in resources_part_of.get(resource_type, []):
        dependent_resource_id_key = return_fkey_dependency(
            resource_type=dependent_resource_type,
            dependent_resource_type=resource_type,
        )
        query = generate_select_query(dependent_resource_type, dependent_resource_id_key,
                                      resource[resource_identification[resource_type]])
        dependent_resources = db.execute_query(query)
        for dependent_resource in dependent_resources:
            handle_resource(
                dependent_resource_type,
                dependent_resource[resource_identification[dependent_resource_type]],
            )


def process_resource_s3(resource, resource_id, resource_type):
    if resource_id != 'wizard:default:1.0.0' and resource_s3_objects[resource_type] != '':
        s3_object = resource_s3_objects[resource_type]
        # If the S3 object contains a placeholder, replace
        # it with the dependent resource's value
        if has_placeholder_in_s3_objects(resource_s3_objects[resource_type]):
            dependent_key = return_fkey_dependency(
                resource_type=resource_type,
                dependent_resource_type=resource_dependencies[resource_type][0],
            )
            dependent_value = resource.get(dependent_key)
            s3_object = s3_object.format(placeholder=dependent_value)
            download_file_s3(s3_object + str(resource_id))

        else:
            download_file_s3(s3_object + str(resource_id))


# Map resources to their dependencies
resources_part_of: dict[str, list] = {
    'users': [],
    'projects': [],
    'documents': [],
    'project_importers': [],
    'knowledge_models': [],
    'locales': [],
    'document_templates': ['document_template_asset', 'document_template_file'],
    'document_template_asset': [],
    'document_template_file': []
}


# Map resources to their dependencies
resource_dependencies: dict[str, list] = {
    'users': [],
    'projects': ['knowledge_models', 'document_templates'],
    'documents': ['document_templates', 'projects'],
    'project_importers': [],
    'knowledge_models': ['knowledge_models'],
    'locales': [],
    'document_templates': [],
    'document_template_asset': ['document_templates'],
    'document_template_file': ['document_templates']
}


# Map resources to their dependencies
resource_dependencies_keys: dict[str, list] = {
    'users': [],
    'projects': [
        {'knowledge_models': 'package_id'},
        {'document_templates': 'document_template_id'}
    ],
    'documents': [
        {'document_templates': 'document_template_id'},
        {'projects': 'questionnaire_uuid'}
    ],
    'project_importers': [],
    'knowledge_models': [
        {'knowledge_models': 'previous_package_id'}
    ],
    'locales': [],
    'document_templates': [],
    'document_template_asset': [
        {'document_templates': 'document_template_id'}
    ],
    'document_template_file': [
        {'document_templates': 'document_template_id'}
    ]
}


# Map resources to their s3 objects
resource_s3_objects = {
    'users': '',
    'projects': '',
    'documents': 'documents/',
    'project_importers': '',
    'knowledge_models': '',
    'locales': 'locales/',
    'document_templates': '',
    'document_template_asset': 'templates/{placeholder}/',
    'document_template_file': ''
}


# Map resources to their s3 objects' file names
resource_s3_objects_fileNames = {
    'locales': 'name',
    'document_templates': [],
    'document_template_asset': ['templates/'],
    'document_template_file': ['templates/']
}


# Map resources to their identification attribute
resource_identification = {
    'users': 'uuid',
    'projects': 'uuid',
    'documents': 'uuid',
    'project_importers': 'id',
    'knowledge_models': 'id',
    'locales': 'id',
    'document_templates': 'id',
    'document_template_asset': 'uuid',
    'document_template_file': 'uuid'
}


# Map resources to their table names
resource_tables = {
    'users': 'user_entity',
    'projects': 'questionnaire',
    'documents': 'document',
    'project_importers': 'questionnaire_importer',
    'knowledge_models': 'package',
    'locales': 'locale',
    'document_templates': 'document_template',
    'document_template_asset': 'document_template_asset',
    'document_template_file': 'document_template_file'
}


# Map resources to attributes visible to users
resource_attributes = {
    'users': ['uuid', 'first_name', 'last_name', 'role', 'email'],
    'projects': ['uuid', 'name'],
    'documents': ['uuid', 'name'],
    'project_importers': ['id', 'name', 'description'],
    'knowledge_models': ['id', 'name', 'km_id', 'description'],
    'locales': ['id', 'name', 'code', 'description'],
    'document_templates': ['id', 'name', 'template_id'],
    'document_template_asset': ['uuid', 'document_template_id'],
    'document_template_file': ['uuid', 'document_template_id']
}
