import contextlib
import io
import logging
import pathlib
import tempfile

import minio
import minio.error
import tenacity

LOG = logging.getLogger(__name__)

DOCUMENTS_DIR = 'documents'

RETRY_S3_MULTIPLIER = 0.5
RETRY_S3_TRIES = 3


@contextlib.contextmanager
def temp_binary_file(data: bytes):
    file = tempfile.TemporaryFile()
    file.write(data)
    file.seek(0)
    yield file
    file.close()


class S3Storage:

    def _get_endpoint(self):
        parts = self._url.split('://', maxsplit=1)
        return parts[0] if len(parts) == 1 else parts[1]

    def __init__(self, url: str, username: str, password: str,
                 bucket: str, region: str, multi_tenant: bool = True):
        self.multi_tenant = multi_tenant
        self._url = url
        self._username = username
        self._password = password
        self._bucket = bucket
        self._region = region

        self.client = minio.Minio(
            endpoint=self._get_endpoint(),
            access_key=self._username,
            secret_key=self._password,
            secure=self._url.startswith('https://'),
            region=self._region,
        )

    def __str__(self):
        return f'{self._url}/{self._bucket}'

    @tenacity.retry(
        reraise=True,
        wait=tenacity.wait_exponential(multiplier=RETRY_S3_MULTIPLIER),
        stop=tenacity.stop_after_attempt(RETRY_S3_TRIES),
        before=tenacity.before_log(LOG, logging.DEBUG),
        after=tenacity.after_log(LOG, logging.DEBUG),
    )
    def ensure_bucket(self):
        found = self.client.bucket_exists(self._bucket)
        if not found:
            self.client.make_bucket(self._bucket)

    @tenacity.retry(
        reraise=True,
        wait=tenacity.wait_exponential(multiplier=RETRY_S3_MULTIPLIER),
        stop=tenacity.stop_after_attempt(RETRY_S3_TRIES),
        before=tenacity.before_log(LOG, logging.DEBUG),
        after=tenacity.after_log(LOG, logging.DEBUG),
    )
    def download_file(self, file_name: str, target_path: pathlib.Path) -> bool:
        try:
            self.client.fget_object(
                bucket_name=self._bucket,
                object_name=file_name,
                file_path=str(target_path),
            )
        except minio.error.S3Error as e:
            if e.code != 'NoSuchKey':
                raise e
            return False
        return True

    @tenacity.retry(
        reraise=True,
        wait=tenacity.wait_exponential(multiplier=RETRY_S3_MULTIPLIER),
        stop=tenacity.stop_after_attempt(RETRY_S3_TRIES),
        before=tenacity.before_log(LOG, logging.DEBUG),
        after=tenacity.after_log(LOG, logging.DEBUG),
    )
    def store_object(self, tenant_uuid: str, object_name: str,
                     content_type: str, data: bytes,
                     metadata: dict | None = None):
        if self.multi_tenant:
            object_name = f'{tenant_uuid}/{object_name}'
        with io.BytesIO(data) as file:
            self.client.put_object(
                bucket_name=self._bucket,
                object_name=object_name,
                data=file,
                length=len(data),
                content_type=content_type,
                metadata=metadata,
            )

    @property
    def bucket(self):
        return self._bucket
