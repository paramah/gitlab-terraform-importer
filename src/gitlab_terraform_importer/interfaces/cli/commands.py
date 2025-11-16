"""CLI commands for GitLab Terraform Importer."""

import json
import logging
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

from ...application.use_cases import (
    AnalyzeTerraformModulesUseCase,
    GenerateTerraformImportsUseCase,
    ImportGitLabStructureUseCase,
)
from ...config import load_config
from ...domain.entities import Group
from ...infrastructure.gitlab import GitLabClient
from ...infrastructure.terraform import TerraformClient

console = Console()
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool) -> None:
    """Set up logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.option("--env-file", type=click.Path(exists=True), help="Path to .env file")
@click.pass_context
def cli(ctx, verbose: bool, env_file: str | None) -> None:
    """GitLab Terraform Importer - Clean Architecture Edition.

    Import GitLab structure and generate Terraform configurations with
    support for custom modules.
    """
    setup_logging(verbose)

    # Load environment variables
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    # Store context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.pass_context
def validate_config(ctx) -> None:
    """Validate environment configuration."""
    try:
        config = load_config()
        console.print("[green]✓[/green] Configuration is valid!")
        console.print("\n[bold]Settings:[/bold]")
        console.print(f"  GitLab URL:        {config.url}")
        console.print(f"  Token:             {'*' * 8} (set)")
        console.print(f"  Root Group ID:     {config.root_group_id or 'not set'}")
        console.print(f"  Root Group Path:   {config.root_group_path or 'not set'}")
        console.print(f"  Output Dir:        {config.output_dir}")
        console.print(f"  Max Depth:         {config.max_depth or 'unlimited'}")
        console.print(f"  Include Archived:  {config.include_archived}")

        console.print(f"  Terraform Binary:  {config.terraform_binary}")

    except Exception as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise click.Abort()


@cli.command()
@click.option("--format", "output_format", type=click.Choice(["tree", "json"]), default="tree")
@click.pass_context
def inspect(ctx, output_format: str) -> None:
    """Inspect GitLab structure without generating files."""
    try:
        config = load_config()

        # Create clients
        gitlab_client = GitLabClient(config)

        # Create use case
        import_use_case = ImportGitLabStructureUseCase(gitlab_client)

        # Execute import
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Importing GitLab structure...", total=None)

            root_group = import_use_case.execute(
                root_group_id=config.root_group_id,
                root_group_path=config.root_group_path,
                max_depth=config.max_depth,
                include_archived=config.include_archived,
            )

            progress.update(task, completed=True)

        # Display results
        if output_format == "json":
            _print_json(root_group)
        else:
            _print_tree(root_group)

        console.print("\n[green]Summary:[/green]")
        console.print(f"  Groups:   {root_group.count_all_groups()}")
        console.print(f"  Projects: {root_group.count_all_projects()}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if ctx.obj.get("verbose"):
            raise
        raise click.Abort()


@cli.command()
@click.option("--output-dir", type=click.Path(), help="Override output directory")
@click.option("--dry-run", is_flag=True, help="Perform a dry run")
@click.pass_context
def import_structure(ctx, output_dir: str | None, dry_run: bool) -> None:
    """Import GitLab structure and generate Terraform configuration."""
    try:
        config = load_config()

        if output_dir:
            config.output_dir = output_dir

        # Create clients
        gitlab_client = GitLabClient(config)
        terraform_client = TerraformClient(terraform_binary=config.terraform_binary)

        # Create use cases
        import_use_case = ImportGitLabStructureUseCase(gitlab_client)
        generate_use_case = GenerateTerraformImportsUseCase(terraform_client)

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            # Import GitLab structure
            task1 = progress.add_task("Importing GitLab structure...", total=None)
            root_group = import_use_case.execute(
                root_group_id=config.root_group_id,
                root_group_path=config.root_group_path,
                max_depth=config.max_depth,
                include_archived=config.include_archived,
            )
            progress.update(task1, completed=True)

            console.print("\n[green]Discovered:[/green]")
            console.print(f"  Groups:   {root_group.count_all_groups()}")
            console.print(f"  Projects: {root_group.count_all_projects()}")

            if dry_run:
                console.print("\n[yellow]Dry run - no files written[/yellow]")
                return

            # Generate Terraform files
            task2 = progress.add_task("Generating Terraform files...", total=None)

            # Create dummy modules for basic generation
            from ...domain.entities import TerraformModule

            group_module = TerraformModule(name="gitlab_group", source=".")
            project_module = TerraformModule(name="gitlab_project", source=".")

            result = generate_use_case.execute(
                gitlab_structure=root_group,
                group_module=group_module,
                project_module=project_module,
                output_dir=Path(config.output_dir),
                generate_import_script=True,
            )
            progress.update(task2, completed=True)

        console.print("\n[green]✓[/green] Success! Terraform files generated.")
        console.print("\n[bold]Generated:[/bold]")
        console.print(f"  Resources:     {result['resources_count']}")
        console.print(f"  Files:         {len(result['generated_files'])}")
        console.print(f"  Import Script: {result['import_script']}")

        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  1. cd {config.output_dir}")
        console.print(f"  2. {config.terraform_binary} init")
        console.print("  3. Review generated files")
        console.print("  4. Run ./import.sh to import resources")
        console.print(f"  5. {config.terraform_binary} plan")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if ctx.obj.get("verbose"):
            raise
        raise click.Abort()


@cli.command()
@click.argument("group_module_path", type=click.Path(exists=True))
@click.argument("project_module_path", type=click.Path(exists=True))
@click.pass_context
def analyze_modules(ctx, group_module_path: str, project_module_path: str) -> None:
    """Analyze Terraform modules for groups and projects."""
    try:
        config = load_config()
        terraform_client = TerraformClient(terraform_binary=config.terraform_binary)
        analyze_use_case = AnalyzeTerraformModulesUseCase(terraform_client)

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Analyzing modules...", total=None)

            analysis = analyze_use_case.execute(
                group_module_path=Path(group_module_path),
                project_module_path=Path(project_module_path),
            )

            progress.update(task, completed=True)

        console.print("\n[bold]Module Analysis:[/bold]\n")

        # Group module
        console.print("[cyan]Group Module:[/cyan]")
        gm = analysis["group_module"]
        console.print(f"  Name:              {gm['name']}")
        console.print(f"  Path:              {gm['path']}")
        console.print(f"  Variables:         {len(gm['variables'])}")
        console.print(f"  Required:          {len(gm['required_variables'])}")
        console.print(f"  Resources:         {gm['resource_count']}")
        console.print(f"  Compatible:        {'✓' if gm['compatible'] else '✗'}")

        # Project module
        console.print("\n[cyan]Project Module:[/cyan]")
        pm = analysis["project_module"]
        console.print(f"  Name:              {pm['name']}")
        console.print(f"  Path:              {pm['path']}")
        console.print(f"  Variables:         {len(pm['variables'])}")
        console.print(f"  Required:          {len(pm['required_variables'])}")
        console.print(f"  Resources:         {pm['resource_count']}")
        console.print(f"  Compatible:        {'✓' if pm['compatible'] else '✗'}")

        if ctx.obj.get("verbose"):
            console.print("\n[bold]Detailed Analysis:[/bold]")
            console.print(json.dumps(analysis, indent=2))

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if ctx.obj.get("verbose"):
            raise
        raise click.Abort()


@cli.command()
@click.argument("group_module_path", type=click.Path(exists=True))
@click.argument("project_module_path", type=click.Path(exists=True))
@click.option("--output-dir", type=click.Path(), help="Override output directory")
@click.pass_context
def import_with_modules(
    ctx, group_module_path: str, project_module_path: str, output_dir: str | None
) -> None:
    """Import GitLab structure using custom Terraform modules."""
    try:
        config = load_config()

        if output_dir:
            config.output_dir = output_dir

        # Create clients
        gitlab_client = GitLabClient(config)
        terraform_client = TerraformClient(terraform_binary=config.terraform_binary)

        # Create use cases
        import_use_case = ImportGitLabStructureUseCase(gitlab_client)
        analyze_use_case = AnalyzeTerraformModulesUseCase(terraform_client)
        generate_use_case = GenerateTerraformImportsUseCase(terraform_client)

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            # Analyze modules
            task1 = progress.add_task("Analyzing Terraform modules...", total=None)
            group_module, project_module = analyze_use_case.get_modules(
                group_module_path=Path(group_module_path),
                project_module_path=Path(project_module_path),
            )
            progress.update(task1, completed=True)

            # Import GitLab structure
            task2 = progress.add_task("Importing GitLab structure...", total=None)
            root_group = import_use_case.execute(
                root_group_id=config.root_group_id,
                root_group_path=config.root_group_path,
                max_depth=config.max_depth,
                include_archived=config.include_archived,
            )
            progress.update(task2, completed=True)

            console.print("\n[green]Discovered:[/green]")
            console.print(f"  Groups:   {root_group.count_all_groups()}")
            console.print(f"  Projects: {root_group.count_all_projects()}")

            # Generate Terraform files
            task3 = progress.add_task("Generating Terraform imports...", total=None)
            result = generate_use_case.execute(
                gitlab_structure=root_group,
                group_module=group_module,
                project_module=project_module,
                output_dir=Path(config.output_dir),
                generate_import_script=True,
            )
            progress.update(task3, completed=True)

        console.print("\n[green]✓[/green] Success! Terraform imports generated.")
        console.print("\n[bold]Generated:[/bold]")
        console.print(f"  Resources:     {result['resources_count']}")
        console.print(f"  Files:         {len(result['generated_files'])}")
        console.print(f"  Import Script: {result['import_script']}")

        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  1. cd {config.output_dir}")
        console.print(f"  2. {config.terraform_binary} init")
        console.print("  3. Run ./import.sh to import resources")
        console.print(f"  4. {config.terraform_binary} plan")

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if ctx.obj.get("verbose"):
            raise
        raise click.Abort()


def _print_tree(group: Group, tree: Tree | None = None, is_root: bool = True) -> None:
    """Print group structure as a tree.

    Args:
        group: Group to print
        tree: Rich tree object
        is_root: Whether this is the root group
    """
    if is_root:
        tree = Tree(f"[bold cyan]📁 {group.name}[/bold cyan] ({group.full_path})")
        console.print(tree)

    # Add projects
    for project in group.projects:
        archived = " [yellow][ARCHIVED][/yellow]" if project.archived else ""
        tree.add(f"[green]📄 {project.name}[/green]{archived}")

    # Add subgroups recursively
    for subgroup in group.subgroups:
        subtree = tree.add(f"[cyan]📁 {subgroup.name}[/cyan] ({subgroup.full_path})")
        _print_tree(subgroup, subtree, is_root=False)


def _print_json(group: Group) -> None:
    """Print group structure as JSON.

    Args:
        group: Group to print
    """

    def group_to_dict(g: Group) -> dict:
        return {
            "id": g.id,
            "name": g.name,
            "path": g.path,
            "full_path": g.full_path,
            "visibility": g.visibility,
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "path": p.path,
                    "full_path": p.full_path,
                    "archived": p.archived,
                }
                for p in g.projects
            ],
            "subgroups": [group_to_dict(sg) for sg in g.subgroups],
        }

    console.print_json(data=group_to_dict(group))


def main() -> None:
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
