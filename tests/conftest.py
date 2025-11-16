"""Pytest configuration and shared fixtures."""

import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock

import pytest

from gitlab_terraform_importer.domain.entities import (
    Group,
    Project,
    TerraformModule,
    TerraformResource,
    TerraformVariable,
    TerraformOutput,
)
from gitlab_terraform_importer.domain.repositories import (
    GitLabRepository,
    TerraformRepository,
)


# ============================================================================
# Domain Entity Fixtures
# ============================================================================


@pytest.fixture
def sample_group() -> Group:
    """Create a sample Group entity."""
    return Group(
        id=123,
        name="Test Group",
        path="test-group",
        full_path="org/test-group",
        description="Test group description",
        visibility="private",
        parent_id=None,
        web_url="https://gitlab.example.com/org/test-group",
        subgroups=[],
        projects=[],
    )


@pytest.fixture
def sample_nested_group(sample_group: Group) -> Group:
    """Create a nested group structure."""
    subgroup = Group(
        id=456,
        name="Subgroup",
        path="subgroup",
        full_path="org/test-group/subgroup",
        description="Subgroup description",
        visibility="private",
        parent_id=123,
        web_url="https://gitlab.example.com/org/test-group/subgroup",
        subgroups=[],
        projects=[],
    )

    sample_group.subgroups = [subgroup]
    return sample_group


@pytest.fixture
def sample_project() -> Project:
    """Create a sample Project entity."""
    return Project(
        id=789,
        name="Test Project",
        path="test-project",
        full_path="org/test-group/test-project",
        description="Test project description",
        visibility="internal",
        namespace_id=123,
        web_url="https://gitlab.example.com/org/test-group/test-project",
        default_branch="main",
        topics=["terraform", "gitlab"],
        archived=False,
    )


@pytest.fixture
def sample_group_with_projects(sample_group: Group, sample_project: Project) -> Group:
    """Create a group with projects."""
    sample_group.projects = [sample_project]
    return sample_group


@pytest.fixture
def sample_terraform_variable() -> TerraformVariable:
    """Create a sample Terraform variable."""
    return TerraformVariable(
        name="group_name",
        type="string",
        description="Name of the GitLab group",
        default=None,
        required=True,
    )


@pytest.fixture
def sample_terraform_output() -> TerraformOutput:
    """Create a sample Terraform output."""
    return TerraformOutput(
        name="group_id",
        description="ID of the created group",
        value="${gitlab_group.this.id}",
        sensitive=False,
    )


@pytest.fixture
def sample_terraform_resource() -> TerraformResource:
    """Create a sample Terraform resource."""
    return TerraformResource(
        resource_type="gitlab_group",
        resource_name="test_group",
        attributes={
            "name": "Test Group",
            "path": "test-group",
            "visibility_level": "private",
        },
        depends_on=[],
        import_id="123",
    )


@pytest.fixture
def sample_terraform_module() -> TerraformModule:
    """Create a sample Terraform module."""
    return TerraformModule(
        name="gitlab-group-module",
        source="/path/to/module",
        variables={
            "group_name": TerraformVariable(
                name="group_name",
                type="string",
                description="Group name",
                default=None,
                required=True,
            ),
            "group_path": TerraformVariable(
                name="group_path",
                type="string",
                description="Group path",
                default=None,
                required=True,
            ),
        },
        outputs={
            "group_id": TerraformOutput(
                name="group_id",
                description="Group ID",
                value="${gitlab_group.this.id}",
                sensitive=False,
            )
        },
        resources=[
            TerraformResource(
                resource_type="gitlab_group",
                resource_name="this",
                attributes={},
                depends_on=[],
            )
        ],
    )


# ============================================================================
# Mock Repository Fixtures
# ============================================================================


@pytest.fixture
def mock_gitlab_repository() -> Mock:
    """Create a mock GitLab repository."""
    mock = Mock(spec=GitLabRepository)
    return mock


@pytest.fixture
def mock_terraform_repository() -> Mock:
    """Create a mock Terraform repository."""
    mock = Mock(spec=TerraformRepository)
    return mock


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def sample_env_vars() -> Dict[str, str]:
    """Sample environment variables for testing."""
    return {
        "GITLAB_URL": "https://gitlab.example.com",
        "GITLAB_TOKEN": "test-token-12345",
        "GITLAB_ROOT_GROUP_PATH": "test-org",
        "GITLAB_ROOT_GROUP_ID": "100",
        "GITLAB_INCLUDE_ARCHIVED": "false",
        "GITLAB_MAX_DEPTH": "5",
        "GITLAB_TIMEOUT": "60",
        "GITLAB_VERIFY_SSL": "true",
        "TERRAFORM_OUTPUT_DIR": "terraform",
    }


@pytest.fixture
def mock_env(sample_env_vars: Dict[str, str], monkeypatch):
    """Mock environment variables."""
    for key, value in sample_env_vars.items():
        monkeypatch.setenv(key, value)
    return sample_env_vars


# ============================================================================
# Terraform Module Fixtures
# ============================================================================


@pytest.fixture
def sample_tf_group_module_content() -> str:
    """Sample Terraform module for GitLab group."""
    return """
variable "group_name" {
  type        = string
  description = "Name of the GitLab group"
}

variable "group_path" {
  type        = string
  description = "Path of the GitLab group"
}

variable "visibility_level" {
  type        = string
  description = "Visibility level"
  default     = "private"
}

resource "gitlab_group" "this" {
  name             = var.group_name
  path             = var.group_path
  visibility_level = var.visibility_level
}

output "group_id" {
  value       = gitlab_group.this.id
  description = "ID of the created group"
}
"""


@pytest.fixture
def sample_tf_project_module_content() -> str:
    """Sample Terraform module for GitLab project."""
    return """
variable "project_name" {
  type        = string
  description = "Name of the GitLab project"
}

variable "project_path" {
  type        = string
  description = "Path of the GitLab project"
}

variable "namespace_id" {
  type        = number
  description = "Namespace ID"
}

resource "gitlab_project" "this" {
  name         = var.project_name
  path         = var.project_path
  namespace_id = var.namespace_id
}

output "project_id" {
  value       = gitlab_project.this.id
  description = "ID of the created project"
}
"""


@pytest.fixture
def sample_tf_module_dir(temp_dir: Path, sample_tf_group_module_content: str) -> Path:
    """Create a sample Terraform module directory."""
    module_dir = temp_dir / "modules" / "gitlab-group"
    module_dir.mkdir(parents=True)

    main_tf = module_dir / "main.tf"
    main_tf.write_text(sample_tf_group_module_content)

    return module_dir


# ============================================================================
# CLI Fixtures
# ============================================================================


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()
