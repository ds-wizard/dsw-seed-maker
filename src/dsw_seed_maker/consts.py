PACKAGE_NAME = 'dsw_seed_maker'
NICE_NAME = 'DSW Seed Maker'
PACKAGE_VERSION = '0.1.0'

_DEFAULT_BUILT_AT = 'BUILT_AT'
BUILT_AT = 'develop~c2f1ba2'
_DEFAULT_VERSION = 'VERSION'
VERSION = '2024-11-03 21:36:44Z'

DEFAULT_ENCODING = 'utf-8'
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FORMAT = '%(asctime)s | %(levelname)s | %(module)s: %(message)s'


BUILD_INFO = {
    'name': NICE_NAME,
    'packageVersion': PACKAGE_VERSION,
    'version': VERSION if VERSION != f'--{_DEFAULT_VERSION}--' else 'unknown',
    'builtAt': BUILT_AT if BUILT_AT != f'--{_DEFAULT_BUILT_AT}--' else 'unknown',
}
