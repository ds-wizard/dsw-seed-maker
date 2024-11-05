from .models import ExampleRequestDTO, ExampleResponseDTO
from .comm.db import Database, DatabaseConnection
from psycopg import sql
from typing import List, Dict, Any
import json

def example_logic(req_dto: ExampleRequestDTO) -> ExampleResponseDTO:
    return ExampleResponseDTO(
        message=req_dto.message.replace('server', 'client'),
    )

def list_resources_users_logic() -> list[dict[str, Any]]:
    db = Database(name='postgres', dsn='postgresql://postgres:postgres@localhost:15432/wizard')
    query = sql.SQL('SELECT * FROM user_entity')
    users_resources = db.execute_query(query)
    # Parse the dictionaries into UserDTO instances
    parsed_resources = [
        {
            'uuid': str(row['uuid']),  # Convert UUID to string
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'role': row['role']
        }
        for row in users_resources
    ]

    return parsed_resources