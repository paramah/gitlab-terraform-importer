"""GitLab client implementation (adapter)."""

from typing import Optional, List, Any
import logging
import gitlab
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from ...domain.entities import Group, Project
from ...domain.repositories import GitLabRepository
from ...config import GitLabConfig

logger = logging.getLogger(__name__)


class GitLabClient(GitLabRepository):
    """GitLab repository implementation using REST and GraphQL APIs."""

    def __init__(self, config: GitLabConfig):
        """Initialize GitLab client.

        Args:
            config: GitLab configuration
        """
        self.config = config

        # Initialize REST API client
        self.rest_client = gitlab.Gitlab(
            url=config.url,
            private_token=config.token,
            ssl_verify=config.verify_ssl,
            timeout=config.timeout
        )
        self.rest_client.auth()
        logger.info(f"Connected to GitLab: {config.url}")

        # Initialize GraphQL client
        transport = RequestsHTTPTransport(
            url=f"{config.url.rstrip('/')}/api/graphql",
            headers={
                "Authorization": f"Bearer {config.token}",
                "Content-Type": "application/json",
            },
            verify=config.verify_ssl,
            timeout=config.timeout,
        )
        self.graphql_client = Client(
            transport=transport,
            fetch_schema_from_transport=False,
        )

    def get_group(
        self,
        group_id: Optional[int] = None,
        group_path: Optional[str] = None
    ) -> Group:
        """Get a group by ID or path.

        Args:
            group_id: Group ID
            group_path: Group path

        Returns:
            Group entity
        """
        if group_id:
            gl_group = self.rest_client.groups.get(group_id)
        elif group_path:
            gl_group = self.rest_client.groups.get(group_path)
        else:
            raise ValueError("Either group_id or group_path must be provided")

        return self._map_group_to_entity(gl_group)

    def get_subgroups(self, group_id: int, include_archived: bool = False) -> List[Group]:
        """Get all subgroups of a group.

        Args:
            group_id: Parent group ID
            include_archived: Include archived groups

        Returns:
            List of subgroup entities
        """
        gl_group = self.rest_client.groups.get(group_id)
        subgroups = gl_group.subgroups.list(
            all=True,
            archived=include_archived,
        )

        return [self._map_group_to_entity(sg) for sg in subgroups]

    def get_group_projects(
        self,
        group_id: int,
        include_archived: bool = False
    ) -> List[Project]:
        """Get all projects in a group.

        Args:
            group_id: Group ID
            include_archived: Include archived projects

        Returns:
            List of project entities
        """
        gl_group = self.rest_client.groups.get(group_id)
        projects = gl_group.projects.list(
            all=True,
            archived=include_archived,
            include_subgroups=False,
        )

        return [self._map_project_to_entity(p) for p in projects]

    def get_project(self, project_id: int) -> Project:
        """Get a project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project entity
        """
        gl_project = self.rest_client.projects.get(project_id)
        return self._map_project_to_entity(gl_project)

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
        """
        # Get root group
        root_group = self.get_group(
            group_id=root_group_id,
            group_path=root_group_path
        )

        # Import hierarchy recursively
        self._import_hierarchy_recursive(
            root_group,
            depth=0,
            max_depth=max_depth,
            include_archived=include_archived
        )

        return root_group

    def _import_hierarchy_recursive(
        self,
        group: Group,
        depth: int,
        max_depth: Optional[int],
        include_archived: bool
    ) -> None:
        """Recursively import group hierarchy.

        Args:
            group: Group to import
            depth: Current depth
            max_depth: Maximum depth
            include_archived: Include archived resources
        """
        if max_depth is not None and depth >= max_depth:
            logger.debug(f"Max depth reached for group: {group.full_path}")
            return

        logger.debug(f"Importing group: {group.full_path} (depth: {depth})")

        # Import projects
        projects = self.get_group_projects(group.id, include_archived)
        for project in projects:
            group.add_project(project)
        logger.debug(f"  Found {len(projects)} projects")

        # Import subgroups
        subgroups = self.get_subgroups(group.id, include_archived)
        for subgroup in subgroups:
            group.add_subgroup(subgroup)
            # Recursively import subgroup
            self._import_hierarchy_recursive(
                subgroup,
                depth + 1,
                max_depth,
                include_archived
            )
        logger.debug(f"  Found {len(subgroups)} subgroups")

    def _map_group_to_entity(self, gl_group: Any) -> Group:
        """Map GitLab API group to domain entity.

        Args:
            gl_group: GitLab API group object

        Returns:
            Group domain entity
        """
        return Group(
            id=gl_group.id,
            name=gl_group.name,
            path=gl_group.path,
            full_path=gl_group.full_path,
            visibility=gl_group.visibility,
            description=getattr(gl_group, 'description', None),
            parent_id=getattr(gl_group, 'parent_id', None),
            web_url=getattr(gl_group, 'web_url', None),
        )

    def _map_project_to_entity(self, gl_project: Any) -> Project:
        """Map GitLab API project to domain entity.

        Args:
            gl_project: GitLab API project object

        Returns:
            Project domain entity
        """
        return Project(
            id=gl_project.id,
            name=gl_project.name,
            path=gl_project.path,
            full_path=gl_project.path_with_namespace,
            visibility=gl_project.visibility,
            namespace_id=gl_project.namespace['id'],
            description=getattr(gl_project, 'description', None),
            archived=getattr(gl_project, 'archived', False),
            http_url_to_repo=gl_project.http_url_to_repo,
            ssh_url_to_repo=gl_project.ssh_url_to_repo,
            web_url=getattr(gl_project, 'web_url', None),
            default_branch=getattr(gl_project, 'default_branch', None),
            topics=getattr(gl_project, 'topics', []) or [],
            issues_enabled=getattr(gl_project, 'issues_enabled', True),
            merge_requests_enabled=getattr(gl_project, 'merge_requests_enabled', True),
            wiki_enabled=getattr(gl_project, 'wiki_enabled', True),
            snippets_enabled=getattr(gl_project, 'snippets_enabled', True),
            container_registry_enabled=getattr(gl_project, 'container_registry_enabled', True),
        )
