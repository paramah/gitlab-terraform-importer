"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from gitlab_terraform_importer.interfaces.cli.commands import (
    cli,
)


class TestCLI:
    """Test CLI commands."""

    def test_cli_help(self, cli_runner: CliRunner):
        """Test CLI help command."""
        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "GitLab Terraform Importer" in result.output
        assert "Commands:" in result.output

    def test_cli_verbose_flag(self, cli_runner: CliRunner):
        """Test CLI verbose flag."""
        result = cli_runner.invoke(cli, ["-v", "--help"])

        assert result.exit_code == 0


class TestValidateConfig:
    """Test validate-config command."""

    def test_validate_config_success(self, cli_runner: CliRunner, mock_env):
        """Test validate-config with valid environment."""
        result = cli_runner.invoke(cli, ["validate-config"])

        assert result.exit_code == 0
        assert "Configuration is valid" in result.output or "valid" in result.output.lower()

    def test_validate_config_missing_token(self, cli_runner: CliRunner, monkeypatch):
        """Test validate-config with missing GITLAB_TOKEN."""
        # Remove GITLAB_TOKEN
        monkeypatch.delenv("GITLAB_TOKEN", raising=False)

        result = cli_runner.invoke(cli, ["validate-config"])

        # Should fail validation
        assert result.exit_code != 0 or "error" in result.output.lower()

    def test_validate_config_with_env_file(
        self, cli_runner: CliRunner, temp_dir: Path, sample_env_vars
    ):
        """Test validate-config with custom .env file."""
        # Create .env file
        env_file = temp_dir / ".env"
        env_content = "\n".join(f"{k}={v}" for k, v in sample_env_vars.items())
        env_file.write_text(env_content)

        result = cli_runner.invoke(cli, ["--env-file", str(env_file), "validate-config"])

        assert result.exit_code == 0


class TestInspect:
    """Test inspect command."""

    @patch("gitlab_terraform_importer.interfaces.cli.commands.GitLabClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.ImportGitLabStructureUseCase")
    def test_inspect_tree_format(
        self,
        mock_use_case_class,
        mock_client_class,
        cli_runner: CliRunner,
        mock_env,
        sample_group,
    ):
        """Test inspect with tree format."""
        # Setup mocks
        mock_use_case = Mock()
        mock_use_case.execute.return_value = sample_group
        mock_use_case_class.return_value = mock_use_case

        result = cli_runner.invoke(cli, ["inspect"])

        # Should succeed
        assert result.exit_code == 0

    @patch("gitlab_terraform_importer.interfaces.cli.commands.GitLabClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.ImportGitLabStructureUseCase")
    def test_inspect_json_format(
        self,
        mock_use_case_class,
        mock_client_class,
        cli_runner: CliRunner,
        mock_env,
        sample_group,
    ):
        """Test inspect with JSON format."""
        # Setup mocks
        mock_use_case = Mock()
        mock_use_case.execute.return_value = sample_group
        mock_use_case_class.return_value = mock_use_case

        result = cli_runner.invoke(cli, ["inspect", "--format", "json"])

        # Should succeed and output JSON
        assert result.exit_code == 0
        # JSON output should contain group data
        assert "{" in result.output  # JSON object marker


class TestImportStructure:
    """Test import-structure command."""

    @patch("gitlab_terraform_importer.interfaces.cli.commands.GitLabClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.TerraformClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.ImportGitLabStructureUseCase")
    def test_import_structure_basic(
        self,
        mock_import_use_case_class,
        mock_terraform_client_class,
        mock_gitlab_client_class,
        cli_runner: CliRunner,
        mock_env,
        sample_group,
        temp_dir: Path,
    ):
        """Test import-structure basic execution."""
        # Setup mocks
        mock_import_use_case = Mock()
        mock_import_use_case.execute.return_value = sample_group
        mock_import_use_case_class.return_value = mock_import_use_case

        mock_terraform_client = Mock()
        mock_terraform_client.map_module_to_gitlab_resources.return_value = []
        mock_terraform_client.generate_resource_configs.return_value = []
        mock_terraform_client.generate_import_commands.return_value = ([], None)
        mock_terraform_client_class.return_value = mock_terraform_client

        # Create a temporary output directory
        output_dir = temp_dir / "terraform"

        result = cli_runner.invoke(cli, ["import-structure", "--output-dir", str(output_dir)])

        # Should succeed
        if result.exit_code != 0:
            print(f"Output: {result.output}")
            if result.exception:
                import traceback

                traceback.print_exception(
                    type(result.exception), result.exception, result.exception.__traceback__
                )
        assert result.exit_code == 0

    @patch("gitlab_terraform_importer.interfaces.cli.commands.GitLabClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.TerraformClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.ImportGitLabStructureUseCase")
    def test_import_structure_dry_run(
        self,
        mock_import_use_case_class,
        mock_terraform_client_class,
        mock_gitlab_client_class,
        cli_runner: CliRunner,
        mock_env,
        sample_group,
    ):
        """Test import-structure with dry-run flag."""
        # Setup mocks
        mock_import_use_case = Mock()
        mock_import_use_case.execute.return_value = sample_group
        mock_import_use_case_class.return_value = mock_import_use_case

        result = cli_runner.invoke(cli, ["import-structure", "--dry-run"])

        # Should succeed
        assert result.exit_code == 0
        # Should mention dry-run in output
        assert "dry" in result.output.lower() or "Dry run" in result.output

    @patch("gitlab_terraform_importer.interfaces.cli.commands.GitLabClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.TerraformClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.ImportGitLabStructureUseCase")
    def test_import_structure_custom_output_dir(
        self,
        mock_import_use_case_class,
        mock_terraform_client_class,
        mock_gitlab_client_class,
        cli_runner: CliRunner,
        mock_env,
        sample_group,
        temp_dir: Path,
    ):
        """Test import-structure with custom output directory."""
        # Setup mocks
        mock_import_use_case = Mock()
        mock_import_use_case.execute.return_value = sample_group
        mock_import_use_case_class.return_value = mock_import_use_case

        mock_terraform_client = Mock()
        mock_terraform_client.map_module_to_gitlab_resources.return_value = []
        mock_terraform_client.generate_resource_configs.return_value = []
        mock_terraform_client.generate_import_commands.return_value = ([], None)
        mock_terraform_client_class.return_value = mock_terraform_client

        custom_output = temp_dir / "my-terraform"

        result = cli_runner.invoke(cli, ["import-structure", "--output-dir", str(custom_output)])

        # Should succeed
        if result.exit_code != 0:
            print(f"Output: {result.output}")
            if result.exception:
                import traceback

                traceback.print_exception(
                    type(result.exception), result.exception, result.exception.__traceback__
                )
        assert result.exit_code == 0


class TestAnalyzeModules:
    """Test analyze-modules command."""

    @patch("gitlab_terraform_importer.interfaces.cli.commands.TerraformClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.AnalyzeTerraformModulesUseCase")
    def test_analyze_modules_basic(
        self,
        mock_use_case_class,
        mock_client_class,
        cli_runner: CliRunner,
        mock_env,
        sample_tf_module_dir: Path,
    ):
        """Test analyze-modules command."""
        # Setup mocks
        mock_use_case = Mock()
        # The CLI expects the old format with group_module and project_module
        mock_use_case.execute.return_value = {
            "group_module": {
                "name": "test-group-module",
                "path": str(sample_tf_module_dir),
                "variables": {},
                "required_variables": [],
                "outputs": [],
                "resource_count": 1,
                "compatible": True,
            },
            "project_module": {
                "name": "test-project-module",
                "path": str(sample_tf_module_dir),
                "variables": {},
                "required_variables": [],
                "outputs": [],
                "resource_count": 1,
                "compatible": True,
            },
        }
        mock_use_case_class.return_value = mock_use_case

        # The CLI expects two paths: group_module_path and project_module_path
        result = cli_runner.invoke(
            cli, ["analyze-modules", str(sample_tf_module_dir), str(sample_tf_module_dir)]
        )

        # Should succeed
        if result.exit_code != 0:
            print(f"Output: {result.output}")
            if result.exception:
                import traceback

                traceback.print_exception(
                    type(result.exception), result.exception, result.exception.__traceback__
                )
        assert result.exit_code == 0


class TestImportWithModules:
    """Test import-with-modules command."""

    @patch("gitlab_terraform_importer.interfaces.cli.commands.GitLabClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.TerraformClient")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.ImportGitLabStructureUseCase")
    @patch("gitlab_terraform_importer.interfaces.cli.commands.GenerateTerraformImportsUseCase")
    def test_import_with_modules_basic(
        self,
        mock_generate_use_case_class,
        mock_import_use_case_class,
        mock_terraform_client_class,
        mock_gitlab_client_class,
        cli_runner: CliRunner,
        mock_env,
        sample_group,
        sample_tf_module_dir: Path,
        temp_dir: Path,
    ):
        """Test import-with-modules command."""
        # Setup mocks
        mock_import_use_case = Mock()
        mock_import_use_case.execute.return_value = sample_group
        mock_import_use_case_class.return_value = mock_import_use_case

        mock_generate_use_case = Mock()
        mock_generate_use_case.execute.return_value = {
            "resources_count": 1,
            "groups_count": 1,
            "projects_count": 0,
            "generated_files": [],
            "import_commands_count": 1,
            "import_script": None,
            "output_dir": str(temp_dir),
        }
        mock_generate_use_case_class.return_value = mock_generate_use_case

        mock_terraform_client = Mock()
        mock_terraform_client.parse_module.return_value = Mock()
        mock_terraform_client_class.return_value = mock_terraform_client

        output_dir = temp_dir / "terraform"

        result = cli_runner.invoke(
            cli,
            [
                "import-with-modules",
                str(sample_tf_module_dir),
                str(sample_tf_module_dir),
                "--output-dir",
                str(output_dir),
            ],
        )

        # Should succeed
        assert result.exit_code == 0
