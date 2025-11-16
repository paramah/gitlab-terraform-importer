"""Tests for AnalyzeTerraformModulesUseCase."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from gitlab_terraform_importer.application.use_cases import (
    AnalyzeTerraformModulesUseCase,
)
from gitlab_terraform_importer.domain.entities import TerraformModule
from gitlab_terraform_importer.domain.repositories import TerraformRepository


class TestAnalyzeTerraformModulesUseCase:
    """Test AnalyzeTerraformModulesUseCase."""

    @pytest.fixture
    def use_case(self, mock_terraform_repository: Mock) -> AnalyzeTerraformModulesUseCase:
        """Create use case with mock repository."""
        return AnalyzeTerraformModulesUseCase(
            terraform_repository=mock_terraform_repository
        )

    def test_execute_single_module(
        self,
        use_case: AnalyzeTerraformModulesUseCase,
        mock_terraform_repository: Mock,
        sample_terraform_module: TerraformModule,
    ):
        """Test execute with single module."""
        # Setup mock
        mock_terraform_repository.parse_module.return_value = sample_terraform_module
        mock_terraform_repository.analyze_module_variables.return_value = {
            "required_count": 2,
            "optional_count": 1,
            "total_count": 3,
        }

        # Execute
        module_path = Path("/path/to/module")
        result = use_case.execute(module_paths=[module_path])

        # Verify
        assert len(result["modules"]) == 1
        assert result["modules"][0]["module"] == sample_terraform_module
        mock_terraform_repository.parse_module.assert_called_once_with(module_path)

    def test_execute_multiple_modules(
        self,
        use_case: AnalyzeTerraformModulesUseCase,
        mock_terraform_repository: Mock,
        sample_terraform_module: TerraformModule,
    ):
        """Test execute with multiple modules."""
        # Setup mock
        mock_terraform_repository.parse_module.return_value = sample_terraform_module
        mock_terraform_repository.analyze_module_variables.return_value = {
            "required_count": 2,
            "optional_count": 0,
            "total_count": 2,
        }

        # Execute
        module_paths = [Path("/module1"), Path("/module2")]
        result = use_case.execute(module_paths=module_paths)

        # Verify
        assert len(result["modules"]) == 2
        assert mock_terraform_repository.parse_module.call_count == 2

    def test_execute_module_analysis_details(
        self,
        use_case: AnalyzeTerraformModulesUseCase,
        mock_terraform_repository: Mock,
        sample_terraform_module: TerraformModule,
    ):
        """Test execute returns detailed module analysis."""
        # Setup mock
        mock_terraform_repository.parse_module.return_value = sample_terraform_module
        analysis = {
            "required_count": 2,
            "optional_count": 1,
            "total_count": 3,
            "variable_names": ["group_name", "group_path", "visibility"],
        }
        mock_terraform_repository.analyze_module_variables.return_value = analysis

        # Execute
        result = use_case.execute(module_paths=[Path("/module")])

        # Verify
        module_result = result["modules"][0]
        assert module_result["analysis"] == analysis
        assert module_result["path"] == Path("/module")

    def test_execute_summary_statistics(
        self,
        use_case: AnalyzeTerraformModulesUseCase,
        mock_terraform_repository: Mock,
        sample_terraform_module: TerraformModule,
    ):
        """Test execute returns summary statistics."""
        # Setup mock
        mock_terraform_repository.parse_module.return_value = sample_terraform_module
        mock_terraform_repository.analyze_module_variables.return_value = {
            "required_count": 2,
            "optional_count": 1,
            "total_count": 3,
        }

        # Execute
        result = use_case.execute(module_paths=[Path("/module")])

        # Verify
        assert "summary" in result
        summary = result["summary"]
        assert summary["total_modules"] == 1

    def test_execute_empty_module_list(
        self,
        use_case: AnalyzeTerraformModulesUseCase,
        mock_terraform_repository: Mock,
    ):
        """Test execute with empty module list."""
        # Execute
        result = use_case.execute(module_paths=[])

        # Verify
        assert result["modules"] == []
        assert result["summary"]["total_modules"] == 0
        mock_terraform_repository.parse_module.assert_not_called()

    def test_execute_compatibility_check(
        self,
        use_case: AnalyzeTerraformModulesUseCase,
        mock_terraform_repository: Mock,
        sample_terraform_module: TerraformModule,
    ):
        """Test execute includes compatibility check."""
        # Setup mock
        mock_terraform_repository.parse_module.return_value = sample_terraform_module
        mock_terraform_repository.analyze_module_variables.return_value = {
            "required_count": 2,
            "optional_count": 0,
            "total_count": 2,
        }

        # Execute
        result = use_case.execute(module_paths=[Path("/module")])

        # Verify
        module_result = result["modules"][0]
        assert "compatible_with_gitlab" in module_result
