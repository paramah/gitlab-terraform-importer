"""Domain entity for GitLab Group."""

from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field, computed_field

if TYPE_CHECKING:
    from .project import Project


class Group(BaseModel):
    """GitLab Group domain entity using Pydantic."""

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(..., description="Group ID")
    name: str = Field(..., description="Group name")
    path: str = Field(..., description="Group path")
    full_path: str = Field(..., description="Full path to group")
    visibility: str = Field(..., description="Visibility level")
    description: Optional[str] = Field(None, description="Group description")
    parent_id: Optional[int] = Field(None, description="Parent group ID")
    web_url: Optional[str] = Field(None, description="Web URL to group")
    subgroups: List["Group"] = Field(default_factory=list, description="Subgroups")
    projects: List["Project"] = Field(default_factory=list, description="Projects in group")

    def add_subgroup(self, subgroup: "Group") -> None:
        """Add a subgroup to this group.

        Args:
            subgroup: Subgroup to add
        """
        self.subgroups.append(subgroup)

    def add_project(self, project: "Project") -> None:
        """Add a project to this group.

        Args:
            project: Project to add
        """
        self.projects.append(project)

    def count_all_groups(self) -> int:
        """Count total number of groups including subgroups.

        Returns:
            Total group count
        """
        count = 1
        for subgroup in self.subgroups:
            count += subgroup.count_all_groups()
        return count

    def count_all_projects(self) -> int:
        """Count total number of projects in group and subgroups.

        Returns:
            Total project count
        """
        count = len(self.projects)
        for subgroup in self.subgroups:
            count += subgroup.count_all_projects()
        return count

    @computed_field
    @property
    def terraform_resource_name(self) -> str:
        """Get Terraform resource name for this group.

        Returns:
            Terraform-safe resource name
        """
        return self.full_path.replace('/', '_').replace('-', '_').replace('.', '_')

    def get_terraform_resource_name(self) -> str:
        """Get Terraform resource name for this group (legacy method).

        Returns:
            Terraform-safe resource name
        """
        return self.terraform_resource_name

    def model_dump_summary(self) -> dict:
        """Dump a summary without nested subgroups/projects.

        Returns:
            Summary dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "full_path": self.full_path,
            "visibility": self.visibility,
            "description": self.description,
            "subgroups_count": len(self.subgroups),
            "projects_count": len(self.projects),
        }


# Forward reference resolution
from .project import Project

Group.model_rebuild()
