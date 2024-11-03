# DSW Seed Maker

Maker for DSW data seeds (reproducible content packages)

## Usage

This application serves to create data seeding recipes for Data Stewardship Wizard, 
more specifically its [Data Seeder](https://github.com/ds-wizard/engine-tools/tree/develop/packages/dsw-data-seeder) tool.

### Installation

You can install it locally with Python in a standard way (preferably to a prepared
[virtual environment](https://docs.python.org/3/library/venv.html)). 

```shell
git clone git@github.com:ds-wizard/dsw-seed-maker.git
cd dsw-seed-maker
pip install .
```

### Configuration

All configuration is purely done via environment variables. For convenience, 
it is recommended to use a `.env` file in a standard way (see [`example.env`](example.env)) 
for details.

### Command Line Interface (CLI)

After installation, you can use the CLI:

```shell
dsw-seed-maker --help
dsw-seed-maker --version
dsw-seed-maker make-seed --help
```

### Web Application

A simple web application can be launched as this Python package contains 
[WSGI](https://wsgi.readthedocs.io/en/latest/index.html)-compliant application 
`app` exposed through the main module `dsw_seed_maker`, i.e. `dsw_seed_maker`.

There is a simple way to run the web application:

```shell
dsw-seed-maker run-web
```

## Development

There are some specifics to develop

### Environment

1. Clone the repository (eventually switch branch)
2. Setup a virtual environment (`python -m venv env`) and activate it
3. Install the package as editable (`pip install -e .`)
4. Prepare your local DSW instance with DB and S3 (see [`dsw/docker-compose.yml`](dsw/docker-compose.yml))
5. Create `.env` file (see [`example.env`](example.env))
6. Run CLI or web app (`./scripts/run-dev.sh`), develop and try it out

### Code Style and Best Practices

- Use type annotations in Python (`mypy` is used in GitHub Actions)
- Comply with PEP8 and other code style conventions (checked in GitHub Actions using `flake8` and `pylint`)
- Name variables, classes, and functions as sensible human being so it is understandable for others
- Use descriptive commit messages (short message = 3-7 words, but you can add then description if suitable)

### Resources

Within Python scripts:

- [Python (3.12+)](https://docs.python.org/3/)
- [Click](https://click.palletsprojects.com/en/stable/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Jinja](https://jinja.palletsprojects.com/en/stable/templates/)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [Psycopg 3](https://www.psycopg.org/psycopg3/)

For the web app simple frontend:

- [Boostrap](https://getbootstrap.com/)
- [jQuery](https://jquery.com/)

## License

This project is licensed under the Apache License v2.0 - see the 
[LICENSE](LICENSE) file for more details.

