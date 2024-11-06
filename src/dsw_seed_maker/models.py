import pydantic

class ExampleRequestDTO(pydantic.BaseModel):
    magic_code: str = pydantic.Field(alias='magicCode')
    message: str = pydantic.Field(alias='message')


class ExampleResponseDTO(pydantic.BaseModel):
    message: str = pydantic.Field(alias='message')
