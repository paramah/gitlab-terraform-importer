"""GitLab structure importer for groups and projects."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging

from .client import GitLabClient
from .config import GitLabConfig

logger = logging.getLogger(__name__)


@dataclass
class ProjectInfo:
    """Information about a GitLab project."""

    id: int
    name: str
    path: str
    full_path: str
    description: Optional[str]
    visibility: str
    archived: bool
    http_url: str
    ssh_url: str
    default_branch: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    issues_enabled: bool = True
    merge_requests_enabled: bool = True
    wiki_enabled: bool = True
    snippets_enabled: bool = True
    container_registry_enabled: bool = True

    @classmethod
    def from_rest_api(cls, project: Any) -> "ProjectInfo":
        """Create ProjectInfo from REST API project object.

        Args:
            project: Project object from python-gitlab

        Returns:
            ProjectInfo instance
        """
        return cls(
            id=project.id,
            name=project.name,
            path=project.path,
            full_path=project.path_with_namespace,
            description=getattr(project, 'description', None),
            visibility=project.visibility,
            archived=getattr(project, 'archived', False),
            http_url=project.http_url_to_repo,
            ssh_url=project.ssh_url_to_repo,
            default_branch=getattr(project, 'default_branch', None),
            topics=getattr(project, 'topics', []) or [],
            issues_enabled=getattr(project, 'issues_enabled', True),
            merge_requests_enabled=getattr(project, 'merge_requests_enabled', True),
            wiki_enabled=getattr(project, 'wiki_enabled', True),
            snippets_enabled=getattr(project, 'snippets_enabled', True),
            container_registry_enabled=getattr(project, 'container_registry_enabled', True),
        )


@dataclass
class GroupInfo:
    """Information about a GitLab group."""

    id: int
    name: str
    path: str
    full_path: str
    description: Optional[str]
    visibility: str
    parent_id: Optional[int] = None
    subgroups: List["GroupInfo"] = field(default_factory=list)
    projects: List[ProjectInfo] = field(default_factory=list)

    @classmethod
    def from_rest_api(cls, group: Any) -> "GroupInfo":
        """Create GroupInfo from REST API group object.

        Args:
            group: Group object from python-gitlab

        Returns:
            GroupInfo instance
        """
        return cls(
            id=group.id,
            name=group.name,
            path=group.path,
            full_path=group.full_path,
            description=getattr(group, 'description', None),
            visibility=group.visibility,
            parent_id=getattr(group, 'parent_id', None),
        )


class GitLabImporter:
    """Importer for GitLab group and project structure."""

    def __init__(self, client: GitLabClient, config: GitLabConfig):
        """Initialize the importer.

        Args:
            client: GitLab client instance
            config: Configuration
        """
        self.client = client
        self.config = config
        self._current_depth = 0

    def import_structure(self) -> GroupInfo:
        """Import the complete group structure.

        Returns:
            Root group with nested subgroups and projects

        Raises:
            ValueError: If root group cannot be found
        """
        logger.info("Starting GitLab structure import")

        # Get the root group
        if self.config.root_group_id:
            logger.info(f"Fetching root group by ID: {self.config.root_group_id}")
            root_group = self.client.get_group(group_id=self.config.root_group_id)
        elif self.config.root_group_path:
            logger.info(f"Fetching root group by path: {self.config.root_group_path}")
            root_group = self.client.get_group(group_path=self.config.root_group_path)
        else:
            raise ValueError("No root group specified")

        # Convert to GroupInfo and import recursively
        group_info = GroupInfo.from_rest_api(root_group)
        self._import_group_recursive(group_info, depth=0)

        logger.info(
            f"Import complete. Found {self._count_groups(group_info)} groups "
            f"and {self._count_projects(group_info)} projects"
        )

        return group_info

    def _import_group_recursive(self, group_info: GroupInfo, depth: int) -> None:
        """Recursively import a group's subgroups and projects.

        Args:
            group_info: Group to import
            depth: Current recursion depth
        """
        # Check max depth
        if self.config.max_depth is not None and depth >= self.config.max_depth:
            logger.debug(f"Skipping group {group_info.full_path} - max depth reached")
            return

        logger.info(f"Importing group: {group_info.full_path} (depth: {depth})")

        # Import projects in this group
        logger.debug(f"Fetching projects for group {group_info.id}")
        projects = self.client.get_group_projects(
            group_info.id,
            include_archived=self.config.include_archived
        )

        for project in projects:
            project_info = ProjectInfo.from_rest_api(project)
            group_info.projects.append(project_info)
            logger.debug(f"  Added project: {project_info.full_path}")

        # Import subgroups recursively
        logger.debug(f"Fetching subgroups for group {group_info.id}")
        subgroups = self.client.get_subgroups(
            group_info.id,
            include_archived=self.config.include_archived
        )

        for subgroup in subgroups:
            subgroup_info = GroupInfo.from_rest_api(subgroup)
            group_info.subgroups.append(subgroup_info)

            # Recursively import the subgroup
            self._import_group_recursive(subgroup_info, depth + 1)

    def _count_groups(self, group: GroupInfo) -> int:
        """Count total number of groups including subgroups.

        Args:
            group: Root group

        Returns:
            Total group count
        """
        count = 1  # Count this group
        for subgroup in group.subgroups:
            count += self._count_groups(subgroup)
        return count

    def _count_projects(self, group: GroupInfo) -> int:
        """Count total number of projects in group and subgroups.

        Args:
            group: Root group

        Returns:
            Total project count
        """
        count = len(group.projects)
        for subgroup in group.subgroups:
            count += self._count_projects(subgroup)
        return count

    def export_to_dict(self, group: GroupInfo) -> Dict[str, Any]:
        """Export group structure to dictionary.

        Args:
            group: Group to export

        Returns:
            Dictionary representation
        """
        return {
            "id": group.id,
            "name": group.name,
            "path": group.path,
            "full_path": group.full_path,
            "description": group.description,
            "visibility": group.visibility,
            "parent_id": group.parent_id,
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "path": p.path,
                    "full_path": p.full_path,
                    "description": p.description,
                    "visibility": p.visibility,
                    "archived": p.archived,
                    "http_url": p.http_url,
                    "ssh_url": p.ssh_url,
                    "default_branch": p.default_branch,
                    "topics": p.topics,
                }
                for p in group.projects
            ],
            "subgroups": [
                self.export_to_dict(subgroup)
                for subgroup in group.subgroups
            ],
        }
