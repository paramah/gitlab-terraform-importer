"""Tests for ImportGitLabStructureUseCase."""

from unittest.mock import Mock

import pytest

from gitlab_terraform_importer.application.use_cases import ImportGitLabStructureUseCase
from gitlab_terraform_importer.domain.entities import Group


class TestImportGitLabStructureUseCase:
    """Test ImportGitLabStructureUseCase."""

    @pytest.fixture
    def use_case(self, mock_gitlab_repository: Mock) -> ImportGitLabStructureUseCase:
        """Create use case with mock repository."""
        return ImportGitLabStructureUseCase(gitlab_repository=mock_gitlab_repository)

    def test_execute_with_group_id(
        self,
        use_case: ImportGitLabStructureUseCase,
        mock_gitlab_repository: Mock,
        sample_group: Group,
    ):
        """Test execute with root_group_id."""
        # Setup mock
        mock_gitlab_repository.import_group_hierarchy.return_value = sample_group

        # Execute
        result = use_case.execute(root_group_id=123)

        # Verify
        assert result == sample_group
        mock_gitlab_repository.import_group_hierarchy.assert_called_once_with(
            root_group_id=123,
            root_group_path=None,
            max_depth=None,
            include_archived=False,
        )

    def test_execute_with_group_path(
        self,
        use_case: ImportGitLabStructureUseCase,
        mock_gitlab_repository: Mock,
        sample_group: Group,
    ):
        """Test execute with root_group_path."""
        # Setup mock
        mock_gitlab_repository.import_group_hierarchy.return_value = sample_group

        # Execute
        result = use_case.execute(root_group_path="org/test-group")

        # Verify
        assert result == sample_group
        mock_gitlab_repository.import_group_hierarchy.assert_called_once_with(
            root_group_id=None,
            root_group_path="org/test-group",
            max_depth=None,
            include_archived=False,
        )

    def test_execute_with_max_depth(
        self,
        use_case: ImportGitLabStructureUseCase,
        mock_gitlab_repository: Mock,
        sample_group: Group,
    ):
        """Test execute with max_depth."""
        # Setup mock
        mock_gitlab_repository.import_group_hierarchy.return_value = sample_group

        # Execute
        result = use_case.execute(root_group_id=123, max_depth=3)

        # Verify
        assert result == sample_group
        mock_gitlab_repository.import_group_hierarchy.assert_called_once_with(
            root_group_id=123,
            root_group_path=None,
            max_depth=3,
            include_archived=False,
        )

    def test_execute_with_include_archived(
        self,
        use_case: ImportGitLabStructureUseCase,
        mock_gitlab_repository: Mock,
        sample_group: Group,
    ):
        """Test execute with include_archived."""
        # Setup mock
        mock_gitlab_repository.import_group_hierarchy.return_value = sample_group

        # Execute
        result = use_case.execute(root_group_id=123, include_archived=True)

        # Verify
        assert result == sample_group
        mock_gitlab_repository.import_group_hierarchy.assert_called_once_with(
            root_group_id=123,
            root_group_path=None,
            max_depth=None,
            include_archived=True,
        )

    def test_execute_with_all_parameters(
        self,
        use_case: ImportGitLabStructureUseCase,
        mock_gitlab_repository: Mock,
        sample_group: Group,
    ):
        """Test execute with all parameters."""
        # Setup mock
        mock_gitlab_repository.import_group_hierarchy.return_value = sample_group

        # Execute
        result = use_case.execute(
            root_group_path="org/test",
            max_depth=5,
            include_archived=True,
        )

        # Verify
        assert result == sample_group
        mock_gitlab_repository.import_group_hierarchy.assert_called_once_with(
            root_group_id=None,
            root_group_path="org/test",
            max_depth=5,
            include_archived=True,
        )

    def test_execute_returns_nested_structure(
        self,
        use_case: ImportGitLabStructureUseCase,
        mock_gitlab_repository: Mock,
        sample_nested_group: Group,
    ):
        """Test execute returns nested group structure."""
        # Setup mock
        mock_gitlab_repository.import_group_hierarchy.return_value = sample_nested_group

        # Execute
        result = use_case.execute(root_group_id=123)

        # Verify
        assert result == sample_nested_group
        assert len(result.subgroups) == 1

    def test_execute_with_projects(
        self,
        use_case: ImportGitLabStructureUseCase,
        mock_gitlab_repository: Mock,
        sample_group_with_projects: Group,
    ):
        """Test execute returns group with projects."""
        # Setup mock
        mock_gitlab_repository.import_group_hierarchy.return_value = sample_group_with_projects

        # Execute
        result = use_case.execute(root_group_id=123)

        # Verify
        assert result == sample_group_with_projects
        assert len(result.projects) == 1
