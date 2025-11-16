"""Tests for GitLabClient."""

from unittest.mock import Mock, MagicMock, patch

import pytest

from gitlab_terraform_importer.infrastructure.gitlab import GitLabClient
from gitlab_terraform_importer.domain.entities import Group, Project


class TestGitLabClient:
    """Test GitLabClient."""

    @pytest.fixture
    def mock_gitlab_client(self):
        """Create mock python-gitlab client."""
        with patch("gitlab.Gitlab") as mock:
            yield mock

    @pytest.fixture
    def mock_gql_client(self):
        """Create mock GQL client."""
        with patch("gql.Client") as mock:
            yield mock

    @pytest.fixture
    def gitlab_client(self, mock_env):
        """Create GitLabClient instance."""
        with patch("gitlab.Gitlab"), patch("gql.Client"):
            client = GitLabClient(
                gitlab_url="https://gitlab.example.com",
                token="test-token",
            )
            return client

    def test_init(self, mock_env):
        """Test GitLabClient initialization."""
        with patch("gitlab.Gitlab") as mock_gl:
            client = GitLabClient(
                gitlab_url="https://gitlab.example.com",
                token="test-token",
            )
            assert client is not None
            mock_gl.assert_called_once()

    def test_get_group_by_id(self, gitlab_client):
        """Test get_group by ID."""
        # Setup mock
        mock_group = Mock()
        mock_group.id = 123
        mock_group.name = "Test Group"
        mock_group.path = "test-group"
        mock_group.full_path = "org/test-group"
        mock_group.description = "Description"
        mock_group.visibility = "private"
        mock_group.parent_id = None
        mock_group.web_url = "https://gitlab.example.com/org/test-group"

        gitlab_client._gitlab_client.groups.get = Mock(return_value=mock_group)

        # Execute
        result = gitlab_client.get_group(group_id=123)

        # Verify
        assert isinstance(result, Group)
        assert result.id == 123
        assert result.name == "Test Group"
        gitlab_client._gitlab_client.groups.get.assert_called_once_with(123)

    def test_get_group_by_path(self, gitlab_client):
        """Test get_group by path."""
        # Setup mock
        mock_group = Mock()
        mock_group.id = 123
        mock_group.name = "Test Group"
        mock_group.path = "test-group"
        mock_group.full_path = "org/test-group"
        mock_group.description = "Description"
        mock_group.visibility = "private"
        mock_group.parent_id = None
        mock_group.web_url = "https://gitlab.example.com/org/test-group"

        gitlab_client._gitlab_client.groups.get = Mock(return_value=mock_group)

        # Execute
        result = gitlab_client.get_group(group_path="org/test-group")

        # Verify
        assert isinstance(result, Group)
        assert result.full_path == "org/test-group"
        gitlab_client._gitlab_client.groups.get.assert_called_once_with("org/test-group")

    def test_get_subgroups(self, gitlab_client):
        """Test get_subgroups."""
        # Setup mock
        mock_subgroup = Mock()
        mock_subgroup.id = 456
        mock_subgroup.name = "Subgroup"
        mock_subgroup.path = "subgroup"
        mock_subgroup.full_path = "org/test-group/subgroup"
        mock_subgroup.description = None
        mock_subgroup.visibility = "private"
        mock_subgroup.parent_id = 123
        mock_subgroup.web_url = "https://gitlab.example.com/org/test-group/subgroup"

        mock_parent = Mock()
        mock_parent.subgroups.list = Mock(return_value=[mock_subgroup])

        gitlab_client._gitlab_client.groups.get = Mock(return_value=mock_parent)

        # Execute
        result = gitlab_client.get_subgroups(parent_group_id=123)

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], Group)
        assert result[0].id == 456

    def test_get_group_projects(self, gitlab_client):
        """Test get_group_projects."""
        # Setup mock
        mock_project = Mock()
        mock_project.id = 789
        mock_project.name = "Test Project"
        mock_project.path = "test-project"
        mock_project.path_with_namespace = "org/test-group/test-project"
        mock_project.description = "Project description"
        mock_project.visibility = "internal"
        mock_project.namespace = {"id": 123}
        mock_project.web_url = "https://gitlab.example.com/org/test-group/test-project"
        mock_project.default_branch = "main"
        mock_project.topics = ["terraform"]
        mock_project.archived = False

        mock_group = Mock()
        mock_group.projects.list = Mock(return_value=[mock_project])

        gitlab_client._gitlab_client.groups.get = Mock(return_value=mock_group)

        # Execute
        result = gitlab_client.get_group_projects(group_id=123)

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], Project)
        assert result[0].id == 789

    def test_get_group_projects_exclude_archived(self, gitlab_client):
        """Test get_group_projects excluding archived."""
        # Setup mock
        mock_active_project = Mock()
        mock_active_project.id = 789
        mock_active_project.name = "Active Project"
        mock_active_project.path = "active"
        mock_active_project.path_with_namespace = "org/active"
        mock_active_project.description = None
        mock_active_project.visibility = "private"
        mock_active_project.namespace = {"id": 123}
        mock_active_project.web_url = "https://gitlab.example.com/org/active"
        mock_active_project.default_branch = "main"
        mock_active_project.topics = []
        mock_active_project.archived = False

        mock_archived_project = Mock()
        mock_archived_project.archived = True
        mock_archived_project.id = 790

        mock_group = Mock()
        mock_group.projects.list = Mock(
            return_value=[mock_active_project, mock_archived_project]
        )

        gitlab_client._gitlab_client.groups.get = Mock(return_value=mock_group)

        # Execute
        result = gitlab_client.get_group_projects(group_id=123, include_archived=False)

        # Verify
        assert len(result) == 1
        assert result[0].id == 789

    def test_import_group_hierarchy_simple(self, gitlab_client, sample_group: Group):
        """Test import_group_hierarchy with simple group."""
        # Setup mocks
        mock_group = Mock()
        mock_group.id = 123
        mock_group.name = "Test Group"
        mock_group.path = "test-group"
        mock_group.full_path = "org/test-group"
        mock_group.description = None
        mock_group.visibility = "private"
        mock_group.parent_id = None
        mock_group.web_url = "https://gitlab.example.com/org/test-group"
        mock_group.subgroups.list = Mock(return_value=[])
        mock_group.projects.list = Mock(return_value=[])

        gitlab_client._gitlab_client.groups.get = Mock(return_value=mock_group)

        # Execute
        result = gitlab_client.import_group_hierarchy(root_group_id=123)

        # Verify
        assert isinstance(result, Group)
        assert result.id == 123
        assert len(result.subgroups) == 0
        assert len(result.projects) == 0

    def test_import_group_hierarchy_with_max_depth(self, gitlab_client):
        """Test import_group_hierarchy respects max_depth."""
        # Setup mock
        mock_group = Mock()
        mock_group.id = 123
        mock_group.name = "Test"
        mock_group.path = "test"
        mock_group.full_path = "test"
        mock_group.description = None
        mock_group.visibility = "private"
        mock_group.parent_id = None
        mock_group.web_url = "https://gitlab.example.com/test"
        mock_group.subgroups.list = Mock(return_value=[])
        mock_group.projects.list = Mock(return_value=[])

        gitlab_client._gitlab_client.groups.get = Mock(return_value=mock_group)

        # Execute with max_depth=0 (should not recurse)
        result = gitlab_client.import_group_hierarchy(root_group_id=123, max_depth=0)

        # Verify
        assert isinstance(result, Group)
        # Should not call subgroups.list when max_depth=0
        assert len(result.subgroups) == 0
