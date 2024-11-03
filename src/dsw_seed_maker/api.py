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
from .logic import example_logic


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
    if req_dto.magic_code != 'example':
        raise fastapi.HTTPException(status_code=400, detail='Magic code is not correct :-(')
    return example_logic(req_dto)


@app.get('/api/resources', response_class=fastapi.responses.JSONResponse)
async def get_resources():
    # TODO: implement
    return fastapi.responses.JSONResponse(content={'resources': []})


@app.post('/api/seed-package', response_class=fastapi.responses.JSONResponse)
async def post_seed():
    # TODO: implement
    return fastapi.responses.JSONResponse(content={'status': 'ok'})
