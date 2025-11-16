"""Domain entity for GitLab Project."""

from typing import Optional, List
from pydantic import BaseModel, Field, computed_field, field_validator


class Project(BaseModel):
    """GitLab Project domain entity using Pydantic."""

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    path: str = Field(..., description="Project path")
    full_path: str = Field(..., description="Full path to project")
    visibility: str = Field(..., description="Visibility level")
    namespace_id: int = Field(..., description="Namespace/Group ID")
    description: Optional[str] = Field(None, description="Project description")
    archived: bool = Field(default=False, description="Is project archived")
    http_url_to_repo: Optional[str] = Field(None, description="HTTP URL to repository")
    ssh_url_to_repo: Optional[str] = Field(None, description="SSH URL to repository")
    web_url: Optional[str] = Field(None, description="Web URL to project")
    default_branch: Optional[str] = Field(None, description="Default branch name")
    topics: List[str] = Field(default_factory=list, description="Project topics/tags")

    # Feature flags
    issues_enabled: bool = Field(default=True, description="Issues enabled")
    merge_requests_enabled: bool = Field(default=True, description="Merge requests enabled")
    wiki_enabled: bool = Field(default=True, description="Wiki enabled")
    snippets_enabled: bool = Field(default=True, description="Snippets enabled")
    container_registry_enabled: bool = Field(default=True, description="Container registry enabled")

    @field_validator('topics', mode='before')
    @classmethod
    def ensure_topics_list(cls, v):
        """Ensure topics is always a list.

        Args:
            v: Topics value

        Returns:
            Topics as list
        """
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [v]

    @computed_field
    @property
    def terraform_resource_name(self) -> str:
        """Get Terraform resource name for this project.

        Returns:
            Terraform-safe resource name
        """
        return self.full_path.replace('/', '_').replace('-', '_').replace('.', '_')

    @computed_field
    @property
    def group_path(self) -> str:
        """Get the group path from full path.

        Returns:
            Group path
        """
        parts = self.full_path.split('/')
        if len(parts) > 1:
            return '/'.join(parts[:-1])
        return ""

    def get_terraform_resource_name(self) -> str:
        """Get Terraform resource name for this project (legacy method).

        Returns:
            Terraform-safe resource name
        """
        return self.terraform_resource_name

    def get_group_path(self) -> str:
        """Get the group path from full path (legacy method).

        Returns:
            Group path
        """
        return self.group_path

    def model_dump_summary(self) -> dict:
        """Dump a summary of the project.

        Returns:
            Summary dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "full_path": self.full_path,
            "visibility": self.visibility,
            "archived": self.archived,
            "default_branch": self.default_branch,
            "topics": self.topics,
        }
