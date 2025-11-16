"""Domain entity for GitLab Project."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Project:
    """GitLab Project domain entity."""

    id: int
    name: str
    path: str
    full_path: str
    visibility: str
    namespace_id: int
    description: Optional[str] = None
    archived: bool = False
    http_url_to_repo: Optional[str] = None
    ssh_url_to_repo: Optional[str] = None
    web_url: Optional[str] = None
    default_branch: Optional[str] = None
    topics: List[str] = field(default_factory=list)

    # Feature flags
    issues_enabled: bool = True
    merge_requests_enabled: bool = True
    wiki_enabled: bool = True
    snippets_enabled: bool = True
    container_registry_enabled: bool = True

    def get_terraform_resource_name(self) -> str:
        """Get Terraform resource name for this project.

        Returns:
            Terraform-safe resource name
        """
        return self.full_path.replace('/', '_').replace('-', '_').replace('.', '_')

    def get_group_path(self) -> str:
        """Get the group path from full path.

        Returns:
            Group path
        """
        parts = self.full_path.split('/')
        if len(parts) > 1:
            return '/'.join(parts[:-1])
        return ""
