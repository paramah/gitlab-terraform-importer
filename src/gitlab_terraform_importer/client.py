"""GitLab client wrapper supporting both REST and GraphQL APIs."""

from typing import Dict, List, Optional, Any
import gitlab
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from .config import GitLabConfig


class GitLabClient:
    """Wrapper for GitLab API client supporting both REST and GraphQL."""

    def __init__(self, config: GitLabConfig):
        """Initialize GitLab clients.

        Args:
            config: GitLab configuration
        """
        self.config = config

        # Initialize REST API client (python-gitlab)
        self.rest_client = gitlab.Gitlab(
            url=config.url,
            private_token=config.token,
            ssl_verify=config.verify_ssl,
            timeout=config.timeout
        )
        self.rest_client.auth()

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

    def get_group(self, group_id: Optional[int] = None, group_path: Optional[str] = None) -> Any:
        """Get group by ID or path using REST API.

        Args:
            group_id: Group ID
            group_path: Group path

        Returns:
            Group object

        Raises:
            ValueError: If neither group_id nor group_path is provided
        """
        if group_id:
            return self.rest_client.groups.get(group_id)
        elif group_path:
            return self.rest_client.groups.get(group_path)
        else:
            raise ValueError("Either group_id or group_path must be provided")

    def get_subgroups(self, group_id: int, include_archived: bool = False) -> List[Any]:
        """Get all subgroups of a group using REST API.

        Args:
            group_id: Parent group ID
            include_archived: Include archived groups

        Returns:
            List of subgroup objects
        """
        group = self.rest_client.groups.get(group_id)
        subgroups = group.subgroups.list(
            all=True,
            archived=include_archived,
        )
        return subgroups

    def get_group_projects(self, group_id: int, include_archived: bool = False) -> List[Any]:
        """Get all projects in a group using REST API.

        Args:
            group_id: Group ID
            include_archived: Include archived projects

        Returns:
            List of project objects
        """
        group = self.rest_client.groups.get(group_id)
        projects = group.projects.list(
            all=True,
            archived=include_archived,
            include_subgroups=False,  # We'll handle subgroups recursively
        )
        return projects

    def get_project(self, project_id: int) -> Any:
        """Get project details using REST API.

        Args:
            project_id: Project ID

        Returns:
            Project object
        """
        return self.rest_client.projects.get(project_id)

    def query_graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Query result
        """
        result = self.graphql_client.execute(
            gql(query),
            variable_values=variables
        )
        return result

    def get_group_hierarchy_graphql(self, group_path: str) -> Dict[str, Any]:
        """Get group hierarchy using GraphQL.

        Args:
            group_path: Full path to the group

        Returns:
            Group hierarchy data
        """
        query = """
        query GetGroupHierarchy($fullPath: ID!) {
          group(fullPath: $fullPath) {
            id
            name
            fullPath
            description
            visibility
            path
            descendantGroups {
              nodes {
                id
                name
                fullPath
                description
                visibility
                path
              }
            }
            projects {
              nodes {
                id
                name
                path
                fullPath
                description
                visibility
                archived
                httpUrlToRepo
                sshUrlToRepo
              }
            }
          }
        }
        """
        return self.query_graphql(query, {"fullPath": group_path})

    def get_project_details_graphql(self, project_path: str) -> Dict[str, Any]:
        """Get project details using GraphQL.

        Args:
            project_path: Full path to the project

        Returns:
            Project details
        """
        query = """
        query GetProject($fullPath: ID!) {
          project(fullPath: $fullPath) {
            id
            name
            path
            fullPath
            description
            visibility
            archived
            httpUrlToRepo
            sshUrlToRepo
            defaultBranch
            topics
            issuesEnabled
            mergeRequestsEnabled
            wikiEnabled
            snippetsEnabled
            containerRegistryEnabled
          }
        }
        """
        return self.query_graphql(query, {"fullPath": project_path})
