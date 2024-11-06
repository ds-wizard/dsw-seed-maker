from psycopg import sql
from typing import Any

from .models import ExampleRequestDTO, ExampleResponseDTO
from .comm.db import Database


def example_logic(req_dto: ExampleRequestDTO) -> ExampleResponseDTO:
    return ExampleResponseDTO(
        message=req_dto.message.replace('server', 'client'),
    )


def list_resources_users_logic() -> list[dict[str, Any]]:
    db = Database(name='postgres', dsn='postgresql://postgres:postgres@localhost:15432/wizard')
    query = sql.SQL('SELECT * FROM user_entity')
    users_resources = db.execute_query(query)
    parsed_resources = [
        {
            'uuid': str(row['uuid']),
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'role': row['role']
        }
        for row in users_resources
    ]

    return parsed_resources
