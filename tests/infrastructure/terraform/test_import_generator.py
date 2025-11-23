"""Tests for ImportGenerator."""

import json
from pathlib import Path

import pytest

from gitlab_terraform_importer.infrastructure.terraform import ImportGenerator
from gitlab_terraform_importer.domain.entities import (
    Group,
    Project,
    TerraformResource,
)


class TestImportGenerator:
    """Test ImportGenerator."""

    @pytest.fixture
    def generator(self) -> ImportGenerator:
        """Create ImportGenerator instance."""
        return ImportGenerator()

    @pytest.fixture
    def generator_json(self) -> ImportGenerator:
        """Create ImportGenerator instance with JSON output format."""
        return ImportGenerator(output_format="json")

    def test_generate_import_commands(
        self,
        generator: ImportGenerator,
        sample_terraform_resource: TerraformResource,
        temp_dir: Path,
    ):
        """Test generate_import_commands."""
        # Execute
        output_file = temp_dir / "import.sh"
        result = generator.generate_import_commands(
            resources=[sample_terraform_resource],
            output_file=output_file,
        )

        # Verify
        assert len(result) > 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "terraform import" in content

    def test_generate_import_commands_multiple_resources(
        self,
        generator: ImportGenerator,
        temp_dir: Path,
    ):
        """Test generating commands for multiple resources."""
        resources = [
            TerraformResource(
                resource_type="gitlab_group",
                resource_name="group1",
                attributes={"id": "123"},
                depends_on=[],
                import_id="123",
            ),
            TerraformResource(
                resource_type="gitlab_group",
                resource_name="group2",
                attributes={"id": "456"},
                depends_on=[],
                import_id="456",
            ),
        ]

        # Execute
        output_file = temp_dir / "import.sh"
        result = generator.generate_import_commands(
            resources=resources,
            output_file=output_file,
        )

        # Verify
        assert len(result) == 2
        content = output_file.read_text()
        assert "gitlab_group.group1" in content
        assert "gitlab_group.group2" in content

    def test_generate_import_script_executable(
        self,
        generator: ImportGenerator,
        sample_terraform_resource: TerraformResource,
        temp_dir: Path,
    ):
        """Test generated script is executable."""
        # Execute
        output_file = temp_dir / "import.sh"
        generator.generate_import_commands(
            resources=[sample_terraform_resource],
            output_file=output_file,
        )

        # Verify
        import stat

        file_stat = output_file.stat()
        # Check if file has execute permission
        assert file_stat.st_mode & stat.S_IXUSR

    def test_generate_import_script_has_shebang(
        self,
        generator: ImportGenerator,
        sample_terraform_resource: TerraformResource,
        temp_dir: Path,
    ):
        """Test generated script has shebang."""
        # Execute
        output_file = temp_dir / "import.sh"
        generator.generate_import_commands(
            resources=[sample_terraform_resource],
            output_file=output_file,
        )

        # Verify
        content = output_file.read_text()
        assert content.startswith("#!/bin/bash")

    def test_generate_resource_configs_groups(
        self,
        generator: ImportGenerator,
        sample_group: Group,
        temp_dir: Path,
    ):
        """Test generate_resource_configs for groups."""
        # Execute
        result = generator.generate_resource_configs(
            groups=[sample_group],
            projects=[],
            output_dir=temp_dir,
        )

        # Verify
        assert len(result) > 0
        groups_tf = temp_dir / "groups.tf"
        assert groups_tf.exists()

        content = groups_tf.read_text()
        assert "resource" in content
        assert "gitlab_group" in content

    def test_generate_resource_configs_projects(
        self,
        generator: ImportGenerator,
        sample_project: Project,
        temp_dir: Path,
    ):
        """Test generate_resource_configs for projects."""
        # Execute
        result = generator.generate_resource_configs(
            groups=[],
            projects=[sample_project],
            output_dir=temp_dir,
        )

        # Verify
        assert len(result) > 0
        projects_tf = temp_dir / "projects.tf"
        assert projects_tf.exists()

        content = projects_tf.read_text()
        assert "resource" in content
        assert "gitlab_project" in content

    def test_generate_resource_configs_both(
        self,
        generator: ImportGenerator,
        sample_group: Group,
        sample_project: Project,
        temp_dir: Path,
    ):
        """Test generate_resource_configs for both groups and projects."""
        # Execute
        result = generator.generate_resource_configs(
            groups=[sample_group],
            projects=[sample_project],
            output_dir=temp_dir,
        )

        # Verify - expects 3 files: provider.tf, groups.tf, projects.tf
        assert len(result) == 3
        assert (temp_dir / "provider.tf").exists()
        assert (temp_dir / "groups.tf").exists()
        assert (temp_dir / "projects.tf").exists()

    def test_generate_resource_configs_creates_dir(
        self,
        generator: ImportGenerator,
        sample_group: Group,
        temp_dir: Path,
    ):
        """Test generate_resource_configs creates output directory."""
        # Setup - use non-existent subdirectory
        output_dir = temp_dir / "terraform" / "configs"

        # Execute
        generator.generate_resource_configs(
            groups=[sample_group],
            projects=[],
            output_dir=output_dir,
        )

        # Verify
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_generate_empty_lists(
        self,
        generator: ImportGenerator,
        temp_dir: Path,
    ):
        """Test generate_resource_configs with empty lists."""
        # Execute
        result = generator.generate_resource_configs(
            groups=[],
            projects=[],
            output_dir=temp_dir,
        )

        # Verify
        assert len(result) == 0

    def test_import_commands_empty_list(
        self,
        generator: ImportGenerator,
        temp_dir: Path,
    ):
        """Test generate_import_commands with empty resource list."""
        # Execute
        output_file = temp_dir / "import.sh"
        result = generator.generate_import_commands(
            resources=[],
            output_file=output_file,
        )

        # Verify
        assert len(result) == 0
        # File should still be created
        assert output_file.exists()

    # JSON Format Tests

    def test_generate_resource_configs_groups_json(
        self,
        generator_json: ImportGenerator,
        sample_group: Group,
        temp_dir: Path,
    ):
        """Test generate_resource_configs for groups in JSON format."""
        # Execute
        result = generator_json.generate_resource_configs(
            groups=[sample_group],
            projects=[],
            output_dir=temp_dir,
        )

        # Verify
        assert len(result) > 0
        groups_tf_json = temp_dir / "groups.tf.json"
        assert groups_tf_json.exists()

        # Verify it's valid JSON
        content = groups_tf_json.read_text()
        data = json.loads(content)
        assert "resource" in data
        assert "gitlab_group" in data["resource"]

    def test_generate_resource_configs_projects_json(
        self,
        generator_json: ImportGenerator,
        sample_project: Project,
        temp_dir: Path,
    ):
        """Test generate_resource_configs for projects in JSON format."""
        # Execute
        result = generator_json.generate_resource_configs(
            groups=[],
            projects=[sample_project],
            output_dir=temp_dir,
        )

        # Verify
        assert len(result) > 0
        projects_tf_json = temp_dir / "projects.tf.json"
        assert projects_tf_json.exists()

        # Verify it's valid JSON
        content = projects_tf_json.read_text()
        data = json.loads(content)
        assert "resource" in data
        assert "gitlab_project" in data["resource"]

    def test_generate_resource_configs_both_json(
        self,
        generator_json: ImportGenerator,
        sample_group: Group,
        sample_project: Project,
        temp_dir: Path,
    ):
        """Test generate_resource_configs for both groups and projects in JSON format."""
        # Execute
        result = generator_json.generate_resource_configs(
            groups=[sample_group],
            projects=[sample_project],
            output_dir=temp_dir,
        )

        # Verify - expects 3 files: provider.tf.json, groups.tf.json, projects.tf.json
        assert len(result) == 3
        assert (temp_dir / "provider.tf.json").exists()
        assert (temp_dir / "groups.tf.json").exists()
        assert (temp_dir / "projects.tf.json").exists()

        # Verify provider.tf.json is valid JSON
        provider_content = (temp_dir / "provider.tf.json").read_text()
        provider_data = json.loads(provider_content)
        assert "terraform" in provider_data
        assert "provider" in provider_data

    def test_json_format_validation(
        self,
        generator_json: ImportGenerator,
        sample_group: Group,
        temp_dir: Path,
    ):
        """Test that JSON output contains valid Terraform JSON structure."""
        # Execute
        generator_json.generate_resource_configs(
            groups=[sample_group],
            projects=[],
            output_dir=temp_dir,
        )

        # Read and parse JSON
        groups_file = temp_dir / "groups.tf.json"
        data = json.loads(groups_file.read_text())

        # Verify structure
        assert "resource" in data
        assert "gitlab_group" in data["resource"]

        # Get first group resource
        resource_name = list(data["resource"]["gitlab_group"].keys())[0]
        resource = data["resource"]["gitlab_group"][resource_name]

        # Verify required fields
        assert "name" in resource
        assert "path" in resource
        assert "visibility_level" in resource

    def test_invalid_output_format(self):
        """Test that invalid output format raises ValueError."""
        with pytest.raises(ValueError, match="output_format must be 'hcl' or 'json'"):
            ImportGenerator(output_format="xml")

    def test_json_format_escaping(
        self,
        generator_json: ImportGenerator,
        temp_dir: Path,
    ):
        """Test that JSON format properly handles special characters."""
        # Create group with special characters in description
        group = Group(
            id=123,
            name="Test Group",
            path="test-group",
            full_path="org/test-group",
            visibility="private",
            description='Description with "quotes" and \n newlines',
        )

        # Execute
        generator_json.generate_resource_configs(
            groups=[group],
            projects=[],
            output_dir=temp_dir,
        )

        # Read and verify JSON is valid
        groups_file = temp_dir / "groups.tf.json"
        data = json.loads(groups_file.read_text())

        # Verify description is properly stored
        resource_name = list(data["resource"]["gitlab_group"].keys())[0]
        resource = data["resource"]["gitlab_group"][resource_name]
        assert "description" in resource
