import pathlib
from typing import Any
from psycopg import sql

from .comm import S3Storage
from .models import ExampleRequestDTO, ExampleResponseDTO
from .comm.db import Database
import os
from dotenv import load_dotenv

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
        return {'projects_importers': list_project_importers_logic(db)}
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
    projects_importers = list_project_importers_logic(db)
    knowledge_models = list_knowledge_models_logic(db)
    locales = list_locales_logic(db)
    document_templates = list_document_templates_logic(db)
    projects = list_projects_logic(db)
    documents = list_documents_logic(db)
    resources = {
        'users': users,
        'project_importers': projects_importers,
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
