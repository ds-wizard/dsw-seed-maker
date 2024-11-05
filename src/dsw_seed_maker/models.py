from datetime import datetime
from typing import Optional, List

#import jsonb
import pydantic
import uuid


class ExampleRequestDTO(pydantic.BaseModel):
    magic_code: str = pydantic.Field(alias='magicCode')
    message: str = pydantic.Field(alias='message')


class ExampleResponseDTO(pydantic.BaseModel):
    message: str = pydantic.Field(alias='message')

class UserDTO(pydantic.BaseModel):
    user_uuid: uuid = pydantic.Field(alias='uuid')
    first_name: str = pydantic.Field(alias='firstName')
    last_name: str = pydantic.Field(alias='LastName')
    email: str = pydantic.Field(alias='email')
    password_hash: str = pydantic.Field(alias='password')
    affiliation: Optional[str] = pydantic.Field(alias='affiliation')
    sources: str = pydantic.Field(alias='sources')
    role: str = pydantic.Field(alias='role')
    permissions: List[str] = pydantic.Field(alias='permissions')
    active: bool = pydantic.Field(alias='active')
    #submission_props: jsonb = pydantic.Field(alias='submissionProps')
    image_url: Optional[str] = pydantic.Field(alias='imageUrl')
    last_visited_at: Optional[datetime] = pydantic.Field(alias='lastVisitedAt')
    created_at: datetime = pydantic.Field(alias='createdAt')
    updated_at: datetime = pydantic.Field(alias='updatedAt')
    tenant_uuid: uuid = pydantic.Field(alias='tenantUuid')
    machine: bool = pydantic.Field(alias='machine')

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {uuid.UUID: str}
    }
