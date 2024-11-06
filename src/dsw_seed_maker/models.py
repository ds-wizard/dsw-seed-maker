import pydantic

class ExampleRequestDTO(pydantic.BaseModel):
    magic_code: str = pydantic.Field(alias='magicCode')
    message: str = pydantic.Field(alias='message')


class ExampleResponseDTO(pydantic.BaseModel):
    message: str = pydantic.Field(alias='message')


class UserDTO(pydantic.BaseModel):
    uuid: str  # UUID as a string
    first_name: str
    last_name: str
    role: str

    class Config:
        # Allows us to use camelCase when sending data to the client
        allow_population_by_field_name = True
