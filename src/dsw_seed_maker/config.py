import logging
import os
import pathlib
import dotenv

from .consts import DEFAULT_LOG_FORMAT, DEFAULT_LOG_LEVEL

LOG = logging.getLogger(__name__)

# Load the .env file
DOTENV_PATH = pathlib.Path(__file__).parent / '.env'  # Ensure the correct path
if DOTENV_PATH.exists():
    dotenv.load_dotenv(DOTENV_PATH)
    LOG.debug('Loaded environment variables from %s', DOTENV_PATH)
else:
    LOG.warning('No .env file found at %s', DOTENV_PATH)


class Config:
    API_ROOT_PATH = os.getenv('API_ROOT_PATH', '')
    DSW_DB_CONN_STR = os.getenv('DSW_DB_CONN_STR')
    DSW_S3_URL = os.getenv('DSW_S3_URL')
    DSW_S3_USERNAME = os.getenv('DSW_S3_USERNAME')
    DSW_S3_PASSWORD = os.getenv('DSW_S3_PASSWORD')
    DSW_S3_BUCKET = os.getenv('DSW_S3_BUCKET')
    DSW_S3_REGION = os.getenv('DSW_S3_REGION', 'eu-central-1')

    LOG_LEVEL = os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL)
    LOG_FORMAT = os.getenv('LOG_FORMAT', DEFAULT_LOG_FORMAT)

    @classmethod
    def check(cls):
        if cls.DSW_DB_CONN_STR == '':
            raise ValueError('DSW_DB_CONN_STR env variable is missing or empty!')
        if cls.DSW_S3_URL == '':
            raise ValueError('DSW_S3_URL env variable is missing or empty!')
        if cls.DSW_S3_USERNAME == '':
            raise ValueError('DSW_S3_USERNAME env variable is missing or empty!')
        if cls.DSW_S3_PASSWORD == '':
            raise ValueError('DSW_S3_PASSWORD env variable is missing or empty!')
        if cls.DSW_S3_BUCKET == '':
            raise ValueError('DSW_S3_BUCKET env variable is missing or empty!')

    @classmethod
    def apply_logging(cls):
        logging.basicConfig(
            level=cls.LOG_LEVEL,
            format=cls.LOG_FORMAT,
        )
        LOG.debug('Logging configured with level: %s', cls.LOG_LEVEL)
