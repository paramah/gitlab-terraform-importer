"""Tests for ImportGenerator."""

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

        # Verify
        assert len(result) == 2
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
