"""Terraform configuration generator for GitLab resources."""

import os
from pathlib import Path
from typing import List, TextIO
import logging

from .importer import GroupInfo, ProjectInfo

logger = logging.getLogger(__name__)


class TerraformGenerator:
    """Generator for Terraform configuration files."""

    def __init__(self, output_dir: str):
        """Initialize the generator.

        Args:
            output_dir: Directory to write Terraform files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, root_group: GroupInfo) -> None:
        """Generate Terraform configuration files.

        Args:
            root_group: Root group with nested structure
        """
        logger.info(f"Generating Terraform files in {self.output_dir}")

        # Generate provider configuration
        self._generate_provider()

        # Generate groups and projects
        self._generate_resources(root_group)

        # Generate import script
        self._generate_import_script(root_group)

        logger.info("Terraform generation complete")

    def _generate_provider(self) -> None:
        """Generate provider configuration file."""
        provider_file = self.output_dir / "provider.tf"
        logger.debug(f"Generating provider configuration: {provider_file}")

        with open(provider_file, 'w') as f:
            f.write('''terraform {
  required_providers {
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "~> 17.0"
    }
  }
}

provider "gitlab" {
  # Configuration is expected via environment variables:
  # - GITLAB_TOKEN
  # - GITLAB_BASE_URL (optional, defaults to https://gitlab.com)
}
''')

    def _generate_resources(self, group: GroupInfo, parent_path: str = "") -> None:
        """Recursively generate resource files for groups and projects.

        Args:
            group: Group to generate resources for
            parent_path: Parent path for file organization
        """
        # Create directory for this group
        safe_path = self._sanitize_path(group.path)
        current_path = os.path.join(parent_path, safe_path) if parent_path else safe_path
        group_dir = self.output_dir / current_path
        group_dir.mkdir(parents=True, exist_ok=True)

        # Generate group resource
        group_file = group_dir / f"group_{safe_path}.tf"
        logger.debug(f"Generating group resource: {group_file}")

        with open(group_file, 'w') as f:
            self._write_group_resource(f, group)

        # Generate project resources
        if group.projects:
            projects_file = group_dir / f"projects_{safe_path}.tf"
            logger.debug(f"Generating projects file: {projects_file}")

            with open(projects_file, 'w') as f:
                for project in group.projects:
                    self._write_project_resource(f, project, group)
                    f.write('\n')

        # Recursively generate for subgroups
        for subgroup in group.subgroups:
            self._generate_resources(subgroup, current_path)

    def _write_group_resource(self, f: TextIO, group: GroupInfo) -> None:
        """Write a group resource to file.

        Args:
            f: File handle
            group: Group information
        """
        resource_name = self._get_resource_name(group.full_path)

        f.write(f'resource "gitlab_group" "{resource_name}" {{\n')
        f.write(f'  name        = "{self._escape_string(group.name)}"\n')
        f.write(f'  path        = "{group.path}"\n')
        f.write(f'  description = "{self._escape_string(group.description or "")}"\n')
        f.write(f'  visibility_level = "{group.visibility}"\n')

        if group.parent_id:
            parent_resource = self._get_parent_resource_reference(group.full_path)
            f.write(f'  parent_id   = {parent_resource}\n')

        f.write('}\n')

    def _write_project_resource(self, f: TextIO, project: ProjectInfo, group: GroupInfo) -> None:
        """Write a project resource to file.

        Args:
            f: File handle
            project: Project information
            group: Parent group
        """
        resource_name = self._get_resource_name(project.full_path)
        group_resource_name = self._get_resource_name(group.full_path)

        f.write(f'resource "gitlab_project" "{resource_name}" {{\n')
        f.write(f'  name        = "{self._escape_string(project.name)}"\n')
        f.write(f'  path        = "{project.path}"\n')
        f.write(f'  description = "{self._escape_string(project.description or "")}"\n')
        f.write(f'  namespace_id = gitlab_group.{group_resource_name}.id\n')
        f.write(f'  visibility_level = "{project.visibility}"\n')

        if project.default_branch:
            f.write(f'  default_branch = "{project.default_branch}"\n')

        if project.topics:
            topics_str = ", ".join([f'"{topic}"' for topic in project.topics])
            f.write(f'  topics = [{topics_str}]\n')

        f.write(f'  issues_enabled = {str(project.issues_enabled).lower()}\n')
        f.write(f'  merge_requests_enabled = {str(project.merge_requests_enabled).lower()}\n')
        f.write(f'  wiki_enabled = {str(project.wiki_enabled).lower()}\n')
        f.write(f'  snippets_enabled = {str(project.snippets_enabled).lower()}\n')
        f.write(f'  container_registry_enabled = {str(project.container_registry_enabled).lower()}\n')

        if project.archived:
            f.write(f'  archived = true\n')

        f.write('}\n')

    def _generate_import_script(self, root_group: GroupInfo) -> None:
        """Generate shell script for importing existing resources.

        Args:
            root_group: Root group with nested structure
        """
        import_file = self.output_dir / "import.sh"
        logger.debug(f"Generating import script: {import_file}")

        with open(import_file, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('# Terraform import script for GitLab resources\n')
            f.write('# This script imports existing GitLab resources into Terraform state\n\n')
            f.write('set -e\n\n')

            self._write_import_commands(f, root_group)

        # Make script executable
        os.chmod(import_file, 0o755)

    def _write_import_commands(self, f: TextIO, group: GroupInfo) -> None:
        """Write import commands for a group and its resources.

        Args:
            f: File handle
            group: Group to generate imports for
        """
        # Import group
        group_resource = self._get_resource_name(group.full_path)
        f.write(f'# Import group: {group.full_path}\n')
        f.write(f'terraform import gitlab_group.{group_resource} {group.id}\n\n')

        # Import projects
        for project in group.projects:
            project_resource = self._get_resource_name(project.full_path)
            f.write(f'# Import project: {project.full_path}\n')
            f.write(f'terraform import gitlab_project.{project_resource} {project.id}\n\n')

        # Recursively import subgroups
        for subgroup in group.subgroups:
            self._write_import_commands(f, subgroup)

    @staticmethod
    def _get_resource_name(full_path: str) -> str:
        """Convert a full path to a valid Terraform resource name.

        Args:
            full_path: GitLab full path (e.g., 'group/subgroup/project')

        Returns:
            Valid Terraform resource name
        """
        # Replace slashes and special characters with underscores
        return full_path.replace('/', '_').replace('-', '_').replace('.', '_')

    @staticmethod
    def _sanitize_path(path: str) -> str:
        """Sanitize a path component for filesystem use.

        Args:
            path: Path component

        Returns:
            Sanitized path
        """
        return path.replace('/', '_').replace('\\', '_')

    @staticmethod
    def _escape_string(s: str) -> str:
        """Escape a string for use in Terraform configuration.

        Args:
            s: String to escape

        Returns:
            Escaped string
        """
        if not s:
            return ""
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

    @staticmethod
    def _get_parent_resource_reference(full_path: str) -> str:
        """Get the Terraform reference to a parent group.

        Args:
            full_path: Full path to the group

        Returns:
            Terraform reference string
        """
        parts = full_path.split('/')
        if len(parts) <= 1:
            return ""

        parent_path = '/'.join(parts[:-1])
        parent_resource = TerraformGenerator._get_resource_name(parent_path)
        return f'gitlab_group.{parent_resource}.id'
