"""Command-line interface for GitLab Terraform Importer."""

import logging
import sys
import json
from pathlib import Path

import click
from dotenv import load_dotenv

from .config import load_config, GitLabConfig
from .client import GitLabClient
from .importer import GitLabImporter
from .terraform_generator import TerraformGenerator


def setup_logging(verbose: bool) -> None:
    """Set up logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.group()
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--env-file', type=click.Path(exists=True), help='Path to .env file')
@click.pass_context
def cli(ctx, verbose: bool, env_file: str) -> None:
    """GitLab Terraform Importer - Import GitLab structure to Terraform.

    This tool imports GitLab group hierarchies and projects into Terraform
    configuration files, making it easy to manage your GitLab infrastructure
    as code.
    """
    setup_logging(verbose)

    # Load environment variables
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    # Store context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option(
    '--output-format',
    type=click.Choice(['json', 'tree']),
    default='tree',
    help='Output format for the structure'
)
@click.pass_context
def inspect(ctx, output_format: str) -> None:
    """Inspect GitLab structure without generating Terraform files.

    This command connects to GitLab and displays the group/project structure
    that would be imported, without actually generating any Terraform files.
    """
    try:
        # Load configuration
        config = load_config()

        # Create client and importer
        client = GitLabClient(config)
        importer = GitLabImporter(client, config)

        # Import structure
        click.echo("Importing GitLab structure...")
        root_group = importer.import_structure()

        # Display results
        if output_format == 'json':
            structure = importer.export_to_dict(root_group)
            click.echo(json.dumps(structure, indent=2))
        else:
            _print_tree(root_group)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get('verbose'):
            raise
        sys.exit(1)


@cli.command()
@click.option(
    '--output-dir',
    type=click.Path(),
    help='Override output directory from config'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Perform a dry run without writing files'
)
@click.pass_context
def import_structure(ctx, output_dir: str, dry_run: bool) -> None:
    """Import GitLab structure and generate Terraform configuration.

    This command imports the complete GitLab group hierarchy and generates
    Terraform configuration files that can be used to manage the infrastructure.
    """
    try:
        # Load configuration
        config = load_config()

        # Override output directory if specified
        if output_dir:
            config.output_dir = output_dir

        # Create client and importer
        client = GitLabClient(config)
        importer = GitLabImporter(client, config)

        # Import structure
        click.echo("Importing GitLab structure...")
        root_group = importer.import_structure()

        # Display summary
        group_count = importer._count_groups(root_group)
        project_count = importer._count_projects(root_group)
        click.echo(f"\nDiscovered:")
        click.echo(f"  Groups:   {group_count}")
        click.echo(f"  Projects: {project_count}")

        if dry_run:
            click.echo("\nDry run - no files written")
            return

        # Generate Terraform files
        click.echo(f"\nGenerating Terraform files in: {config.output_dir}")
        generator = TerraformGenerator(config.output_dir)
        generator.generate(root_group)

        click.echo("\nSuccess! Terraform files generated.")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. cd {config.output_dir}")
        click.echo(f"  2. terraform init")
        click.echo(f"  3. Review the generated files")
        click.echo(f"  4. Run ./import.sh to import existing resources")
        click.echo(f"  5. terraform plan")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get('verbose'):
            raise
        sys.exit(1)


@cli.command()
def validate_config() -> None:
    """Validate environment configuration.

    This command checks that all required environment variables are set
    and the configuration is valid.
    """
    try:
        config = load_config()
        click.echo("Configuration is valid!")
        click.echo(f"\nSettings:")
        click.echo(f"  GitLab URL:    {config.url}")
        click.echo(f"  Token:         {'*' * 8} (set)")
        click.echo(f"  Root Group ID: {config.root_group_id or 'not set'}")
        click.echo(f"  Root Group Path: {config.root_group_path or 'not set'}")
        click.echo(f"  Output Dir:    {config.output_dir}")
        click.echo(f"  Max Depth:     {config.max_depth or 'unlimited'}")
        click.echo(f"  Include Archived: {config.include_archived}")

    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)


def _print_tree(group, indent: int = 0) -> None:
    """Print group structure as a tree.

    Args:
        group: GroupInfo object
        indent: Current indentation level
    """
    prefix = "  " * indent
    click.echo(f"{prefix}📁 {group.name} ({group.full_path})")

    # Print projects
    for project in group.projects:
        project_prefix = "  " * (indent + 1)
        archived = " [ARCHIVED]" if project.archived else ""
        click.echo(f"{project_prefix}📄 {project.name}{archived}")

    # Print subgroups recursively
    for subgroup in group.subgroups:
        _print_tree(subgroup, indent + 1)


def main() -> None:
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
