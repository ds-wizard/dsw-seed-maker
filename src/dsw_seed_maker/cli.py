import json
import pathlib

import click

from .config import Config
from .consts import DEFAULT_ENCODING, PACKAGE_VERSION
from .logic import list_logic, download_file_logic


class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        if len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        return ctx.fail(f'Too many matches: {", ".join(sorted(matches))}')


@click.group(cls=AliasedGroup)
@click.version_option(version=PACKAGE_VERSION, message=f'%(prog)s v{PACKAGE_VERSION}')
def cli():
    Config.apply_logging()


@cli.command(help='Run the web application', name='run-web')
@click.option('-h', '--host', default='0.0.0.0',
              help='Host address to bind to')
@click.option('-p', '--port', default=8000,
              help='Port to bind to')
def run_web(host: str, port: int):
    import uvicorn  # pylint: disable=import-outside-toplevel
    from .api import app  # pylint: disable=import-outside-toplevel
    Config.check()
    uvicorn.run(app, host=host, port=port)


@cli.command(help='Example command', name='example')
def example():
    click.echo('Hello, world!')


@cli.command(help='List all available seed resources', name='list')
@click.option('-o', '--output',
              type=click.File('w', encoding=DEFAULT_ENCODING), default='-',
              help='Output file to write to (JSON)')
@click.option('-t', '--resource_type',
              type=click.Choice(['all', 'users', 'projects_importers',
                                 'knowledge_models', 'locale', 'document_templates', 'projects', 'documents']), default='all',
              help='Specify the type of resource to list '
                   '(all, users, projects_importers, knowledge_models, locales, document_templates, projects, documents)')
def list_resources(output, resource_type):
    Config.check()
    # TODO: Implement list command (do it in logic, import & use here)
    resources = list_logic(resource_type)
    json_output = json.dumps({'resources': resources}, indent=4)
    output.write(json_output)

#just for testing the download
#@cli.command(help='List all available seed resources', name='download')
#def download_resources():
#    Config.check()
#    # TODO: Implement list command (do it in logic, import & use here)
#    download_file_logic("documents/1034a4b0-d867-4b4b-b2a0-a3956b43cf95", "test.pdf")


@cli.command(help='Create a seed package from input', name='make-seed')
@click.option('-i', '--input',
              type=click.File('r', encoding=DEFAULT_ENCODING), default='-',
              help='Input file to read from (JSON)')
@click.option('-o', '--output-dir',
              type=click.Path(dir_okay=True, file_okay=False), default='-',
              help='Output directory to write to')
def make_seed(input_fp, output_dir):
    Config.check()
    data = json.load(input_fp)
    out_dir = pathlib.Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # TODO: Implement list command (do it in logic, import & use here)
    print(data)
