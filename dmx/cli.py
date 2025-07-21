"""Command line interface for dmx."""

import click
import sys
from pathlib import Path

from dmx.config import Config
from dmx.interactive import InteractiveSession
from dmx.music_client import MusicClient


@click.group(invoke_without_command=True)
@click.option('--config-dir', help='Configuration directory path')
@click.pass_context
def cli(ctx, config_dir):
    """dmx - Simple music downloader using deemix."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config(config_dir)
    
    # If no subcommand is provided, start interactive mode
    if ctx.invoked_subcommand is None:
        try:
            session = InteractiveSession(ctx.obj['config'])
            session.start("")
        except Exception as e:
            print(f"Error starting session: {e}")
            sys.exit(1)


@cli.command()
@click.argument('query', required=False, default="")
@click.pass_obj
def search(obj, query):
    """Start interactive search session."""
    config = obj['config']
    
    try:
        session = InteractiveSession(config)
        if not session.start(query):
            sys.exit(1)
    except Exception as e:
        print(f"Error starting session: {e}")
        sys.exit(1)


@cli.group()
def config():
    """Configuration management."""
    pass


@config.command('show')
@click.pass_obj
def config_show(obj):
    """Show current configuration."""
    config = obj['config']
    
    click.echo("Current configuration:")
    click.echo(f"  ARL: {'*' * len(config.arl) if config.arl else 'Not set'}")
    click.echo(f"  Quality: {config.quality}")
    click.echo(f"  Output directory: {config.output_dir}")
    click.echo(f"  Search limit: {config.search_limit}")
    click.echo(f"  Config file: {config.config_file}")


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_obj
def config_set(obj, key, value):
    """Set configuration value."""
    config = obj['config']
    
    if key == 'arl':
        config.arl = value
        click.echo("ARL token updated")
    elif key == 'quality':
        try:
            config.quality = value
            click.echo(f"Quality set to {value}")
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    elif key == 'output':
        config.output_dir = value
        click.echo(f"Output directory set to {value}")
    elif key == 'search_limit':
        try:
            config.search_limit = int(value)
            click.echo(f"Search limit set to {value}")
        except ValueError:
            click.echo("Error: Search limit must be a number", err=True)
            sys.exit(1)
    else:
        click.echo(f"Error: Unknown configuration key '{key}'", err=True)
        click.echo("Available keys: arl, quality, output, search_limit")
        sys.exit(1)
    
    config.save()


@config.command('init')
@click.pass_obj
def config_init(obj):
    """Initialize configuration with default values."""
    config = obj['config']
    
    click.echo("Initializing configuration...")
    
    # Ask for ARL token
    arl = click.prompt("Enter your Deezer ARL token (optional)", default="", show_default=False)
    if arl:
        config.arl = arl
    
    # Ask for quality
    quality = click.prompt("Download quality", 
                          type=click.Choice(['128', '320', 'FLAC']), 
                          default='320')
    config.quality = quality
    
    # Ask for output directory
    default_output = str(Path.home() / "Downloads" / "Music")
    output = click.prompt("Output directory", default=default_output)
    config.output_dir = output
    
    config.save()
    click.echo("Configuration saved!")


@cli.command()
@click.argument('url')
@click.pass_obj
def download(obj, url):
    """Download a track, album, or playlist by URL."""
    config = obj['config']
    client = MusicClient(
        arl=config.arl,
        quality=config.quality,
        output_dir=config.output_dir
    )
    
    if not client.is_available():
        click.echo("Error: Music client not available. Please check your configuration.", err=True)
        sys.exit(1)
    
    click.echo(f"Downloading: {url}")
    
    try:
        success = client.download(url)
        if success:
            click.echo("✓ Download completed successfully")
        else:
            click.echo("✗ Download failed", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Download error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_obj  
def status(obj):
    """Show system status."""
    config = obj['config']
    client = MusicClient(arl=config.arl)
    
    click.echo("dmx Status:")
    click.echo(f"  Configuration: {'✓' if config.config_file.exists() else '✗'}")
    click.echo(f"  Music client available: {'✓' if client.is_available() else '✗'}")
    click.echo(f"  ARL configured: {'✓' if config.arl else '✗'}")
    
    status_info = client.get_status()
    if status_info['clients']['deemix_client']:
        click.echo("  ✓ Deemix client: Available")
    else:
        click.echo("  ✗ Deemix client: Not available")
    
    if status_info['clients']['api_client']:
        click.echo("  ✓ Search API: Available")
    else:
        click.echo("  ✗ Search API: Will be initialized when needed")
    
    if client.is_available():
        click.echo(f"  Supported qualities: {', '.join(client.get_supported_qualities())}")
        click.echo(f"  Download capable: {'✓' if status_info['download_capable'] else '✗'}")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()