from .models import ExampleRequestDTO, ExampleResponseDTO
from .comm.db import Database, DatabaseConnection
from psycopg import sql
from .models import UserDTO
from typing import List
import json

def example_logic(req_dto: ExampleRequestDTO) -> ExampleResponseDTO:
    return ExampleResponseDTO(
        message=req_dto.message.replace('server', 'client'),
    )

def list_resources_users_logic() -> List[UserDTO]:
    db = Database(name='postgres', dsn='postgresql://postgres:postgres@localhost:15432/wizard')
    query = sql.SQL('SELECT * FROM user_entity')
    users_resources = db.execute_query(query)
    # Parse the dictionaries into UserDTO instances
    users = []
    for row in users_resources:
        user_dto = UserDTO(
            uuid=row.get('uuid'),
            first_name=row.get('firstName', ''),
            last_name=row.get('lastName', '')
        )
        users.append(user_dto.dict())  # Pydantic handles UUID serialization here

    return users