import logging
import psycopg
import psycopg.connection
import psycopg.conninfo
import psycopg.rows
import psycopg.types.json
import tenacity


LOG = logging.getLogger(__name__)

RETRY_QUERY_MULTIPLIER = 0.5
RETRY_QUERY_TRIES = 3

RETRY_CONNECT_MULTIPLIER = 0.2
RETRY_CONNECT_TRIES = 10


def wrap_json_data(data: dict):
    return psycopg.types.json.Json(data)


class Database:

    def __init__(self, name: str, dsn: str, timeout: int = 30000,
                 autocommit: bool = False):
        self._db = DatabaseConnection(
            name=name,
            dsn=dsn,
            timeout=timeout,
            autocommit=autocommit,
        )
        self._db.connect()

    def __str__(self):
        return f'DB[{self._db.name}]'

    @tenacity.retry(
        reraise=True,
        wait=tenacity.wait_exponential(multiplier=RETRY_QUERY_MULTIPLIER),
        stop=tenacity.stop_after_attempt(RETRY_QUERY_TRIES),
        before=tenacity.before_log(LOG, logging.DEBUG),
        after=tenacity.after_log(LOG, logging.DEBUG),
    )
    def execute_query(self, query: psycopg.connection.Query, **kwargs):
        with self._db.new_cursor(use_dict=True) as cursor:
            cursor.execute(query=query, params=kwargs)


class DatabaseConnection:

    def __init__(self, name: str, dsn: str, timeout: int, autocommit: bool):
        self.name = name
        self.dsn = psycopg.conninfo.make_conninfo(
            conninfo=dsn,
            connect_timeout=timeout,
        )
        self.autocommit = autocommit
        self._connection: psycopg.Connection | None = None

    @tenacity.retry(
        reraise=True,
        wait=tenacity.wait_exponential(multiplier=RETRY_CONNECT_MULTIPLIER),
        stop=tenacity.stop_after_attempt(RETRY_CONNECT_TRIES),
        before=tenacity.before_log(LOG, logging.DEBUG),
        after=tenacity.after_log(LOG, logging.DEBUG),
    )
    def _connect_db(self):
        LOG.info('Creating connection to PostgreSQL database "%s"', self.name)
        try:
            connection: psycopg.Connection = psycopg.connect(
                conninfo=self.dsn,
                autocommit=self.autocommit,
            )
        except Exception as e:
            LOG.error('Failed to connect to PostgreSQL database "%s": %s', self.name, e)
            raise e
        # test connection
        cursor = connection.cursor()
        cursor.execute(query='SELECT 1;')
        result = cursor.fetchone()
        if result is None:
            raise RuntimeError('Failed to verify DB connection')
        LOG.debug('DB connection verified (result=%s)', result[0])
        cursor.close()
        connection.commit()
        self._connection = connection

    def connect(self):
        if not self._connection or self._connection.closed != 0:
            self._connect_db()

    @property
    def connection(self):
        self.connect()
        return self._connection

    def new_cursor(self, use_dict: bool = False):
        return self.connection.cursor(
            row_factory=psycopg.rows.dict_row if use_dict else psycopg.rows.tuple_row,
        )

    def reset(self):
        self.close()
        self.connect()

    def close(self):
        if self._connection:
            LOG.info('Closing connection to PostgreSQL database "%s"', self.name)
            self._connection.close()
        self._connection = None
