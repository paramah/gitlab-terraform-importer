"""Tests for ModuleAnalyzer."""

import pytest

from gitlab_terraform_importer.infrastructure.terraform import ModuleAnalyzer
from gitlab_terraform_importer.domain.entities import TerraformModule


class TestModuleAnalyzer:
    """Test ModuleAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> ModuleAnalyzer:
        """Create ModuleAnalyzer instance."""
        return ModuleAnalyzer()

    def test_analyze_variables(
        self,
        analyzer: ModuleAnalyzer,
        sample_terraform_module: TerraformModule,
    ):
        """Test analyze_variables."""
        # Execute
        result = analyzer.analyze_variables(sample_terraform_module)

        # Verify
        assert "required_count" in result
        assert "optional_count" in result
        assert "total_count" in result
        assert result["total_count"] == len(sample_terraform_module.variables)

    def test_analyze_variables_required_count(
        self,
        analyzer: ModuleAnalyzer,
        sample_terraform_module: TerraformModule,
    ):
        """Test required variables count."""
        # Execute
        result = analyzer.analyze_variables(sample_terraform_module)

        # Verify - variables is a Dict
        required_vars = [v for v in sample_terraform_module.variables.values() if v.required]
        assert result["required_count"] == len(required_vars)

    def test_analyze_variables_optional_count(
        self,
        analyzer: ModuleAnalyzer,
        sample_terraform_module: TerraformModule,
    ):
        """Test optional variables count."""
        # Execute
        result = analyzer.analyze_variables(sample_terraform_module)

        # Verify - variables is a Dict
        optional_vars = [v for v in sample_terraform_module.variables.values() if not v.required]
        assert result["optional_count"] == len(optional_vars)

    def test_check_compatibility_gitlab_groups(
        self,
        analyzer: ModuleAnalyzer,
        sample_terraform_module: TerraformModule,
    ):
        """Test compatibility check for GitLab groups."""
        # Execute
        result = analyzer.check_compatibility(sample_terraform_module, "gitlab_group")

        # Verify
        assert isinstance(result, bool)
        assert result is True  # sample_terraform_module has gitlab_group resource

    def test_check_compatibility_gitlab_projects(
        self,
        analyzer: ModuleAnalyzer,
        sample_terraform_module: TerraformModule,
    ):
        """Test compatibility check for GitLab projects."""
        # Execute
        result = analyzer.check_compatibility(sample_terraform_module, "gitlab_project")

        # Verify
        assert result is False  # sample_terraform_module doesn't have gitlab_project

    def test_check_compatibility_case_insensitive(
        self,
        analyzer: ModuleAnalyzer,
        sample_terraform_module: TerraformModule,
    ):
        """Test compatibility check is case-insensitive."""
        # Execute
        result1 = analyzer.check_compatibility(sample_terraform_module, "gitlab_group")
        result2 = analyzer.check_compatibility(
            sample_terraform_module, "GITLAB_GROUP"
        )

        # Verify
        assert result1 == result2

    def test_analyze_empty_module(self, analyzer: ModuleAnalyzer):
        """Test analyzing module with no variables."""
        empty_module = TerraformModule(
            name="test-module",
            source="/test",
            variables={},
            outputs={},
            resources=[],
        )

        # Execute
        result = analyzer.analyze_variables(empty_module)

        # Verify
        assert result["required_count"] == 0
        assert result["optional_count"] == 0
        assert result["total_count"] == 0

    def test_check_compatibility_no_resources(self, analyzer: ModuleAnalyzer):
        """Test compatibility check with module without resources."""
        empty_module = TerraformModule(
            name="test-module",
            source="/test",
            variables={},
            outputs={},
            resources=[],
        )

        # Execute
        result = analyzer.check_compatibility(empty_module, "gitlab_group")

        # Verify
        assert result is False
