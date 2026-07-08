import click
import sys
import os

@click.group()
def cli():
    pass

@cli.command()
@click.option('--config', default='config.yaml', help='Path to configuration file')
def start(config):
    from honeypot.core.honeypot import Honeypot
    
    try:
        honeypot = Honeypot(config)
        honeypot.start()
    except Exception as e:
        click.echo(f"Error starting honeypot: {e}")
        sys.exit(1)

@cli.command()
@click.option('--config', default='config.yaml', help='Path to configuration file')
def gui(config):
    from honeypot.gui.main_window import main
    
    try:
        main(config)
    except Exception as e:
        click.echo(f"Error starting GUI: {e}")
        sys.exit(1)

@cli.command()
@click.option('--config', default='config.yaml', help='Path to configuration file')
def api(config):
    from honeypot.core.honeypot import Honeypot
    from honeypot.api.server import APIServer
    
    try:
        honeypot = Honeypot(config)
        api_server = APIServer(honeypot)
        api_server.start()
    except Exception as e:
        click.echo(f"Error starting API: {e}")
        sys.exit(1)

@cli.command()
def status():
    click.echo("Honeypot status command - requires running honeypot")

@cli.command()
def version():
    click.echo("CyberHoney v1.0.4")

if __name__ == '__main__':
    cli()