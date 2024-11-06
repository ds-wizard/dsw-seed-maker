import contextlib
import logging
import pathlib

import fastapi
import fastapi.responses
import fastapi.staticfiles
import fastapi.templating

from .config import Config
from .consts import NICE_NAME, VERSION
from .models import ExampleRequestDTO, ExampleResponseDTO
from .logic import example_logic, list_logic

LOG = logging.getLogger('uvicorn.error')
ROOT = pathlib.Path(__file__).parent
STATIC_DIR = ROOT / 'static'
TEMPLATES_DIR = ROOT / 'templates'


@contextlib.asynccontextmanager
async def lifespan(fastapi_app: fastapi.FastAPI):
    Config.apply_logging()
    Config.check()
    LOG.debug('Configured logging when starting app "%s"', repr(fastapi_app))
    yield


app = fastapi.FastAPI(
    title=NICE_NAME,
    version=VERSION,
    lifespan=lifespan,
    root_path=Config.API_ROOT_PATH,
)

app.mount('/static', fastapi.staticfiles.StaticFiles(directory=STATIC_DIR), name='static')
templates = fastapi.templating.Jinja2Templates(directory=TEMPLATES_DIR)


# HTML endpoints / controllers
@app.get('/', response_class=fastapi.responses.HTMLResponse)
async def get_example(request: fastapi.Request):
    return templates.TemplateResponse(
        name='index.html.j2',
        request=request,
    )


# API/JSON endpoints / controllers
@app.post('/api/example', response_model=ExampleResponseDTO)
async def post_example(req_dto: ExampleRequestDTO, request: fastapi.Request):
    LOG.debug('Handling example request...')
    LOG.debug('Host: %s', request.client.host if request.client else 'unknown')
    return example_logic(req_dto)


@app.get("/api/resources")
async def list_resources():
    resources = [
        {"name": "Users", "endpoint": "/api/users"},
        {"name": "Project Importers", "endpoint": "/api/project_importers"},
        {"name": "Knowledge Models", "endpoint": "/api/knowledge_models"},
        {"name": "Locale", "endpoint": "/api/locale"},
        {"name": "Document Templates", "endpoint": "/api/document_templates"},
        {"name": "Projects", "endpoint": "/api/projects"},
        {"name": "Documents", "endpoint": "/api/documents"},
    ]
    return resources


@app.get('/api/users')
async def get_users():
    LOG.debug('Fetching users...')
    try:
        users = list_logic("users")
        return users
    except Exception as e:
        LOG.error('Error fetching users: %s', str(e))
        raise fastapi.HTTPException(status_code=500, detail='Could not fetch users')


@app.get('/api/project_importers')
async def get_project_importers():
    LOG.debug('Fetching pproject importers...')
    try:
        project_importers = list_logic("project_importers")
        return project_importers
    except Exception as e:
        LOG.error('Error fetching project_importers: %s', str(e))
        raise fastapi.HTTPException(status_code=500, detail='Could not fetch project_importers')


@app.get('/api/knowledge_models')
async def get_knowledge_models():
    LOG.debug('Fetching knowledge models...')
    try:
        knowledge_models = list_logic("knowledge_models")
        return knowledge_models
    except Exception as e:
        LOG.error('Error fetching knowledge models: %s', str(e))
        raise fastapi.HTTPException(status_code=500, detail='Could not fetch knowledge models')


@app.get('/api/locales')
async def get_locales():
    LOG.debug('Fetching locales...')
    try:
        locales = list_logic("locales")
        return locales
    except Exception as e:
        LOG.error('Error fetching locales: %s', str(e))
        raise fastapi.HTTPException(status_code=500, detail='Could not fetch locales')


@app.get('/api/document_templates')
async def get_document_templates():
    LOG.debug('Fetching document templates...')
    try:
        document_templates = list_logic("document_templates")
        return document_templates
    except Exception as e:
        LOG.error('Error fetching document templates: %s', str(e))
        raise fastapi.HTTPException(status_code=500, detail='Could not fetch document templates')


@app.get('/api/projects')
async def get_projects():
    LOG.debug('Fetching projects...')
    try:
        projects = list_logic("projects")
        return projects
    except Exception as e:
        LOG.error('Error fetching projects: %s', str(e))
        raise fastapi.HTTPException(status_code=500, detail='Could not fetch projects')


@app.get('/api/documents')
async def get_documents():
    LOG.debug('Fetching documents...')
    try:
        documents = list_logic("documents")
        return documents
    except Exception as e:
        LOG.error('Error fetching documents: %s', str(e))
        raise fastapi.HTTPException(status_code=500, detail='Could not fetch documents')


@app.post('/api/seed-package', response_class=fastapi.responses.JSONResponse)
async def post_seed():
    # TODO: implement
    return fastapi.responses.JSONResponse(content={'status': 'ok'})
