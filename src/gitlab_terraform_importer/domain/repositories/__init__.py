"""Domain repository interfaces."""

from .gitlab_repository import GitLabRepository
from .terraform_repository import TerraformRepository

__all__ = [
    "GitLabRepository",
    "TerraformRepository",
]
