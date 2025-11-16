"""Tests for Project entity."""

import pytest
from pydantic import ValidationError

from gitlab_terraform_importer.domain.entities import Project


class TestProjectEntity:
    """Test Project entity."""

    def test_create_project_valid(self, sample_project: Project):
        """Test creating a valid project."""
        assert sample_project.id == 789
        assert sample_project.name == "Test Project"
        assert sample_project.path == "test-project"
        assert sample_project.namespace_id == 123

    def test_project_validation_invalid_id(self):
        """Test project validation with invalid ID."""
        with pytest.raises(ValidationError):
            Project(
                id="invalid",
                name="Test",
                path="test",
                full_path="test",
                namespace_id=123,
            )

    def test_project_validation_missing_required(self):
        """Test project validation with missing required fields."""
        with pytest.raises(ValidationError):
            Project(id=1)

    def test_terraform_resource_name_computed(self, sample_project: Project):
        """Test terraform_resource_name computed field."""
        assert (
            sample_project.terraform_resource_name
            == "org_test_group_test_project"
        )

    def test_terraform_resource_name_special_chars(self):
        """Test terraform resource name with special characters."""
        project = Project(
            id=1,
            name="Test",
            path="test",
            full_path="org/my-group.sub/my.project-name",
            namespace_id=123,
            visibility="private",
        )
        expected = "org_my_group_sub_my_project_name"
        assert project.terraform_resource_name == expected

    def test_group_path_computed(self, sample_project: Project):
        """Test group_path computed field."""
        # full_path: org/test-group/test-project -> group: org/test-group
        assert sample_project.group_path == "org/test-group"

    def test_group_path_root_project(self):
        """Test group_path for project in root."""
        project = Project(
            id=1,
            name="Test",
            path="test-project",
            full_path="test-project",
            namespace_id=123,
            visibility="private",
        )
        assert project.group_path == ""

    def test_topics_validator_none(self):
        """Test topics field validator with None."""
        project = Project(
            id=1,
            name="Test",
            path="test",
            full_path="test",
            namespace_id=123,
            visibility="private",
            topics=None,
        )
        assert project.topics == []

    def test_topics_validator_list(self):
        """Test topics field validator with list."""
        topics = ["python", "terraform", "gitlab"]
        project = Project(
            id=1,
            name="Test",
            path="test",
            full_path="test",
            namespace_id=123,
            visibility="private",
            topics=topics,
        )
        assert project.topics == topics

    def test_topics_validator_single_value(self):
        """Test topics field validator with single value."""
        project = Project(
            id=1,
            name="Test",
            path="test",
            full_path="test",
            namespace_id=123,
            visibility="private",
            topics="python",
        )
        assert project.topics == ["python"]

    def test_archived_default_false(self):
        """Test archived defaults to False."""
        project = Project(
            id=1,
            name="Test",
            path="test",
            full_path="test",
            namespace_id=123,
            visibility="private",
        )
        assert project.archived is False

    def test_model_dump(self, sample_project: Project):
        """Test model serialization."""
        data = sample_project.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == 789
        assert data["topics"] == ["terraform", "gitlab"]

    def test_model_dump_summary(self, sample_project: Project):
        """Test summary serialization."""
        summary = sample_project.model_dump_summary()
        assert isinstance(summary, dict)
        assert summary["id"] == 789
        assert summary["name"] == "Test Project"

    def test_visibility_values(self):
        """Test different visibility values."""
        for visibility in ["private", "internal", "public"]:
            project = Project(
                id=1,
                name="Test",
                path="test",
                full_path="test",
                namespace_id=123,
                visibility=visibility,
            )
            assert project.visibility == visibility

    def test_optional_fields_none(self):
        """Test optional fields can be None."""
        project = Project(
            id=1,
            name="Test",
            path="test",
            full_path="test",
            namespace_id=123,
            visibility="private",
            description=None,
            web_url=None,
            default_branch=None,
        )
        assert project.description is None
        assert project.web_url is None
        assert project.default_branch is None

    def test_model_validate(self, sample_project: Project):
        """Test model validation from dict."""
        data = sample_project.model_dump()
        validated = Project.model_validate(data)
        assert validated.id == sample_project.id
        assert validated.name == sample_project.name

    def test_legacy_methods(self, sample_project: Project):
        """Test backward compatibility methods."""
        assert (
            sample_project.get_terraform_resource_name()
            == sample_project.terraform_resource_name
        )
        assert sample_project.get_group_path() == sample_project.group_path
