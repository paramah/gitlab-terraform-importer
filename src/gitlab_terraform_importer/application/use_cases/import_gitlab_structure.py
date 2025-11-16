"""Use case for importing GitLab structure."""

from typing import Optional
import logging

from ...domain.entities import Group
from ...domain.repositories import GitLabRepository

logger = logging.getLogger(__name__)


class ImportGitLabStructureUseCase:
    """Use case for importing GitLab group hierarchy."""

    def __init__(self, gitlab_repository: GitLabRepository):
        """Initialize use case.

        Args:
            gitlab_repository: GitLab repository implementation
        """
        self.gitlab_repository = gitlab_repository

    def execute(
        self,
        root_group_id: Optional[int] = None,
        root_group_path: Optional[str] = None,
        max_depth: Optional[int] = None,
        include_archived: bool = False
    ) -> Group:
        """Execute the import use case.

        Args:
            root_group_id: Root group ID to import from
            root_group_path: Root group path to import from
            max_depth: Maximum depth to traverse
            include_archived: Include archived resources

        Returns:
            Root group with complete hierarchy

        Raises:
            ValueError: If neither group_id nor group_path provided
        """
        logger.info("Starting GitLab structure import")

        if not root_group_id and not root_group_path:
            raise ValueError("Either root_group_id or root_group_path must be provided")

        # Import the hierarchy
        root_group = self.gitlab_repository.import_group_hierarchy(
            root_group_id=root_group_id,
            root_group_path=root_group_path,
            max_depth=max_depth,
            include_archived=include_archived
        )

        logger.info(
            f"Import complete: {root_group.count_all_groups()} groups, "
            f"{root_group.count_all_projects()} projects"
        )

        return root_group
