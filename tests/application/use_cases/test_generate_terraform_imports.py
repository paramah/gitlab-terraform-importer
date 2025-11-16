"""Tests for GenerateTerraformImportsUseCase."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from gitlab_terraform_importer.application.use_cases import (
    GenerateTerraformImportsUseCase,
)
from gitlab_terraform_importer.domain.entities import (
    Group,
    TerraformModule,
    TerraformResource,
)


class TestGenerateTerraformImportsUseCase:
    """Test GenerateTerraformImportsUseCase."""

    @pytest.fixture
    def use_case(self, mock_terraform_repository: Mock) -> GenerateTerraformImportsUseCase:
        """Create use case with mock repository."""
        return GenerateTerraformImportsUseCase(terraform_repository=mock_terraform_repository)

    @pytest.fixture
    def sample_resources(self, sample_terraform_resource: TerraformResource):
        """Sample terraform resources."""
        return [sample_terraform_resource]

    def test_execute_basic(
        self,
        use_case: GenerateTerraformImportsUseCase,
        mock_terraform_repository: Mock,
        sample_group: Group,
        sample_terraform_module: TerraformModule,
        sample_resources: list,
        temp_dir: Path,
    ):
        """Test execute with basic parameters."""
        # Setup mocks
        mock_terraform_repository.map_module_to_gitlab_resources.return_value = sample_resources
        mock_terraform_repository.generate_resource_configs.return_value = [temp_dir / "groups.tf"]
        mock_terraform_repository.generate_import_commands.return_value = [
            "terraform import gitlab_group.test_group 123"
        ]

        # Execute
        result = use_case.execute(
            gitlab_structure=sample_group,
            group_module=sample_terraform_module,
            project_module=sample_terraform_module,
            output_dir=temp_dir,
        )

        # Verify
        assert result["resources_count"] == 1
        assert result["groups_count"] == 1
        assert result["projects_count"] == 0
        assert len(result["generated_files"]) == 1
        assert result["import_commands_count"] == 1

    def test_execute_with_projects(
        self,
        use_case: GenerateTerraformImportsUseCase,
        mock_terraform_repository: Mock,
        sample_group_with_projects: Group,
        sample_terraform_module: TerraformModule,
        sample_resources: list,
        temp_dir: Path,
    ):
        """Test execute with group containing projects."""
        # Setup mocks
        mock_terraform_repository.map_module_to_gitlab_resources.return_value = sample_resources
        mock_terraform_repository.generate_resource_configs.return_value = [
            temp_dir / "groups.tf",
            temp_dir / "projects.tf",
        ]
        mock_terraform_repository.generate_import_commands.return_value = [
            "terraform import gitlab_group.test 123",
            "terraform import gitlab_project.test 789",
        ]

        # Execute
        result = use_case.execute(
            gitlab_structure=sample_group_with_projects,
            group_module=sample_terraform_module,
            project_module=sample_terraform_module,
            output_dir=temp_dir,
        )

        # Verify
        assert result["groups_count"] == 1
        assert result["projects_count"] == 1
        assert len(result["generated_files"]) == 2

    def test_execute_without_import_script(
        self,
        use_case: GenerateTerraformImportsUseCase,
        mock_terraform_repository: Mock,
        sample_group: Group,
        sample_terraform_module: TerraformModule,
        sample_resources: list,
        temp_dir: Path,
    ):
        """Test execute without generating import script."""
        # Setup mocks
        mock_terraform_repository.map_module_to_gitlab_resources.return_value = sample_resources
        mock_terraform_repository.generate_resource_configs.return_value = []

        # Execute
        result = use_case.execute(
            gitlab_structure=sample_group,
            group_module=sample_terraform_module,
            project_module=sample_terraform_module,
            output_dir=temp_dir,
            generate_import_script=False,
        )

        # Verify
        assert result["import_script"] is None
        assert result["import_commands_count"] == 0
        mock_terraform_repository.generate_import_commands.assert_not_called()

    def test_execute_nested_groups(
        self,
        use_case: GenerateTerraformImportsUseCase,
        mock_terraform_repository: Mock,
        sample_nested_group: Group,
        sample_terraform_module: TerraformModule,
        sample_resources: list,
        temp_dir: Path,
    ):
        """Test execute with nested group structure."""
        # Setup mocks
        mock_terraform_repository.map_module_to_gitlab_resources.return_value = sample_resources
        mock_terraform_repository.generate_resource_configs.return_value = []
        mock_terraform_repository.generate_import_commands.return_value = []

        # Execute
        result = use_case.execute(
            gitlab_structure=sample_nested_group,
            group_module=sample_terraform_module,
            project_module=sample_terraform_module,
            output_dir=temp_dir,
        )

        # Verify - should collect all groups (root + subgroup)
        assert result["groups_count"] == 2

    def test_collect_all_groups(
        self,
        use_case: GenerateTerraformImportsUseCase,
        sample_nested_group: Group,
    ):
        """Test _collect_all_groups method."""
        groups = use_case._collect_all_groups(sample_nested_group)

        # Should include root group and subgroup
        assert len(groups) == 2
        assert groups[0].id == 123  # Root group
        assert groups[1].id == 456  # Subgroup

    def test_collect_all_projects(
        self,
        use_case: GenerateTerraformImportsUseCase,
        sample_group_with_projects: Group,
    ):
        """Test _collect_all_projects method."""
        projects = use_case._collect_all_projects(sample_group_with_projects)

        # Should include project
        assert len(projects) == 1
        assert projects[0].id == 789

    def test_execute_output_dir_in_result(
        self,
        use_case: GenerateTerraformImportsUseCase,
        mock_terraform_repository: Mock,
        sample_group: Group,
        sample_terraform_module: TerraformModule,
        sample_resources: list,
        temp_dir: Path,
    ):
        """Test execute includes output_dir in result."""
        # Setup mocks
        mock_terraform_repository.map_module_to_gitlab_resources.return_value = sample_resources
        mock_terraform_repository.generate_resource_configs.return_value = []
        mock_terraform_repository.generate_import_commands.return_value = []

        # Execute
        result = use_case.execute(
            gitlab_structure=sample_group,
            group_module=sample_terraform_module,
            project_module=sample_terraform_module,
            output_dir=temp_dir,
        )

        # Verify
        assert result["output_dir"] == str(temp_dir)
