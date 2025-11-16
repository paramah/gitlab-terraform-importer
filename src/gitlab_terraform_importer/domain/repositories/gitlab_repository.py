"""GitLab repository interface (port)."""

from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities import Group, Project


class GitLabRepository(ABC):
    """Abstract repository for GitLab operations."""

    @abstractmethod
    def get_group(self, group_id: Optional[int] = None, group_path: Optional[str] = None) -> Group:
        """Get a group by ID or path.

        Args:
            group_id: Group ID
            group_path: Group path

        Returns:
            Group entity

        Raises:
            ValueError: If neither group_id nor group_path provided
            NotFoundError: If group not found
        """
        pass

    @abstractmethod
    def get_subgroups(self, group_id: int, include_archived: bool = False) -> List[Group]:
        """Get all subgroups of a group.

        Args:
            group_id: Parent group ID
            include_archived: Include archived groups

        Returns:
            List of subgroup entities
        """
        pass

    @abstractmethod
    def get_group_projects(self, group_id: int, include_archived: bool = False) -> List[Project]:
        """Get all projects in a group.

        Args:
            group_id: Group ID
            include_archived: Include archived projects

        Returns:
            List of project entities
        """
        pass

    @abstractmethod
    def get_project(self, project_id: int) -> Project:
        """Get a project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project entity

        Raises:
            NotFoundError: If project not found
        """
        pass

    @abstractmethod
    def import_group_hierarchy(
        self,
        root_group_id: Optional[int] = None,
        root_group_path: Optional[str] = None,
        max_depth: Optional[int] = None,
        include_archived: bool = False
    ) -> Group:
        """Import complete group hierarchy.

        Args:
            root_group_id: Root group ID
            root_group_path: Root group path
            max_depth: Maximum depth to import
            include_archived: Include archived resources

        Returns:
            Root group with nested structure

        Raises:
            ValueError: If neither ID nor path provided
        """
        pass
