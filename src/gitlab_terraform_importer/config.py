"""Configuration module for GitLab Terraform Importer.

This module handles environment-based configuration using pydantic-settings.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitLabConfig(BaseSettings):
    """GitLab configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='GITLAB_',
        case_sensitive=False,
        extra='ignore'
    )

    # GitLab instance configuration
    url: str = Field(
        default="https://gitlab.com",
        description="GitLab instance URL"
    )

    token: str = Field(
        ...,
        description="GitLab personal access token with API access"
    )

    # Import configuration
    root_group_id: Optional[int] = Field(
        default=None,
        description="Root group ID to start importing from (optional)"
    )

    root_group_path: Optional[str] = Field(
        default=None,
        description="Root group path to start importing from (optional)"
    )

    # Output configuration
    output_dir: str = Field(
        default="./terraform",
        description="Output directory for Terraform files"
    )

    # API configuration
    timeout: int = Field(
        default=60,
        description="API request timeout in seconds"
    )

    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates"
    )

    # Import options
    include_archived: bool = Field(
        default=False,
        description="Include archived projects"
    )

    max_depth: Optional[int] = Field(
        default=None,
        description="Maximum group depth to import (None for unlimited)"
    )

    def validate_config(self) -> None:
        """Validate configuration consistency."""
        if not self.root_group_id and not self.root_group_path:
            raise ValueError(
                "Either root_group_id or root_group_path must be specified"
            )


def load_config() -> GitLabConfig:
    """Load and validate configuration from environment."""
    config = GitLabConfig()
    config.validate_config()
    return config
