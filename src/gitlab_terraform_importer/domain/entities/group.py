"""Domain entity for GitLab Group."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Group:
    """GitLab Group domain entity."""

    id: int
    name: str
    path: str
    full_path: str
    visibility: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    web_url: Optional[str] = None
    subgroups: List["Group"] = field(default_factory=list)
    projects: List["Project"] = field(default_factory=list)

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

    def get_terraform_resource_name(self) -> str:
        """Get Terraform resource name for this group.

        Returns:
            Terraform-safe resource name
        """
        return self.full_path.replace('/', '_').replace('-', '_').replace('.', '_')


# Forward reference resolution
from .project import Project
