"""Tests for TerraformParser."""

from pathlib import Path

import pytest

from gitlab_terraform_importer.infrastructure.terraform import TerraformParser
from gitlab_terraform_importer.domain.entities import TerraformModule


class TestTerraformParser:
    """Test TerraformParser."""

    @pytest.fixture
    def parser(self) -> TerraformParser:
        """Create TerraformParser instance."""
        return TerraformParser()

    def test_parse_module(
        self,
        parser: TerraformParser,
        sample_tf_module_dir: Path,
    ):
        """Test parse_module_directory with valid module."""
        # Execute
        result = parser.parse_module_directory(sample_tf_module_dir)

        # Verify
        assert isinstance(result, TerraformModule)
        assert result.source == str(sample_tf_module_dir)
        assert len(result.variables) > 0
        assert len(result.resources) > 0

    def test_parse_module_variables(
        self,
        parser: TerraformParser,
        sample_tf_module_dir: Path,
    ):
        """Test parsing module variables."""
        # Execute
        result = parser.parse_module_directory(sample_tf_module_dir)

        # Verify variables - variables is a Dict
        assert "group_name" in result.variables
        assert "group_path" in result.variables

        # Check variable details
        group_name_var = result.variables["group_name"]
        assert group_name_var.type == "string"
        assert group_name_var.required is True

    def test_parse_module_resources(
        self,
        parser: TerraformParser,
        sample_tf_module_dir: Path,
    ):
        """Test parsing module resources."""
        # Execute
        result = parser.parse_module_directory(sample_tf_module_dir)

        # Verify resources
        assert len(result.resources) > 0
        gitlab_resources = [r for r in result.resources if r.resource_type == "gitlab_group"]
        assert len(gitlab_resources) > 0

    def test_parse_module_outputs(
        self,
        parser: TerraformParser,
        sample_tf_module_dir: Path,
    ):
        """Test parsing module outputs."""
        # Execute
        result = parser.parse_module_directory(sample_tf_module_dir)

        # Verify outputs - outputs is a Dict
        assert "group_id" in result.outputs

    def test_parse_module_with_default_values(
        self,
        parser: TerraformParser,
        temp_dir: Path,
    ):
        """Test parsing variables with default values."""
        # Create module with default values
        module_dir = temp_dir / "module-with-defaults"
        module_dir.mkdir()

        tf_content = """
variable "required_var" {
  type        = string
  description = "Required variable"
}

variable "optional_var" {
  type        = string
  description = "Optional variable"
  default     = "default_value"
}

resource "gitlab_group" "test" {
  name = var.required_var
}
"""
        (module_dir / "main.tf").write_text(tf_content)

        # Execute
        result = parser.parse_module_directory(module_dir)

        # Verify - variables is a Dict
        required_vars = [v for v in result.variables.values() if v.required]
        optional_vars = [v for v in result.variables.values() if not v.required]

        assert len(required_vars) == 1
        assert len(optional_vars) == 1
        assert required_vars[0].name == "required_var"
        assert optional_vars[0].name == "optional_var"
        assert optional_vars[0].default == "default_value"

    def test_parse_module_nonexistent_dir(self, parser: TerraformParser):
        """Test parse_module_directory with nonexistent directory."""
        with pytest.raises(Exception):
            parser.parse_module_directory(Path("/nonexistent/path"))

    def test_parse_module_empty_dir(self, parser: TerraformParser, temp_dir: Path):
        """Test parse_module_directory with empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        # Execute
        result = parser.parse_module_directory(empty_dir)

        # Verify - should return module with empty lists
        assert isinstance(result, TerraformModule)
        assert len(result.variables) == 0
        assert len(result.resources) == 0
        assert len(result.outputs) == 0

    def test_parse_multiple_tf_files(self, parser: TerraformParser, temp_dir: Path):
        """Test parsing module with multiple .tf files."""
        module_dir = temp_dir / "multi-file"
        module_dir.mkdir()

        # Create variables.tf
        variables_tf = """
variable "var1" {
  type = string
}
"""
        (module_dir / "variables.tf").write_text(variables_tf)

        # Create main.tf
        main_tf = """
resource "gitlab_group" "test" {
  name = var.var1
}
"""
        (module_dir / "main.tf").write_text(main_tf)

        # Create outputs.tf
        outputs_tf = """
output "group_id" {
  value = gitlab_group.test.id
}
"""
        (module_dir / "outputs.tf").write_text(outputs_tf)

        # Execute
        result = parser.parse_module_directory(module_dir)

        # Verify - should combine all files
        assert len(result.variables) >= 1
        assert len(result.resources) >= 1
        assert len(result.outputs) >= 1
