"""Tests for Group entity."""

import pytest
from pydantic import ValidationError

from gitlab_terraform_importer.domain.entities import Group


class TestGroupEntity:
    """Test Group entity."""

    def test_create_group_valid(self, sample_group: Group):
        """Test creating a valid group."""
        assert sample_group.id == 123
        assert sample_group.name == "Test Group"
        assert sample_group.path == "test-group"
        assert sample_group.full_path == "org/test-group"

    def test_group_validation_invalid_id(self):
        """Test group validation with invalid ID."""
        with pytest.raises(ValidationError):
            Group(
                id="invalid",  # Should be int
                name="Test",
                path="test",
                full_path="test",
                visibility="private",
            )

    def test_group_validation_missing_required_fields(self):
        """Test group validation with missing required fields."""
        with pytest.raises(ValidationError):
            Group(id=123)  # Missing required fields

    def test_terraform_resource_name_computed_field(self, sample_group: Group):
        """Test terraform_resource_name computed field."""
        assert sample_group.terraform_resource_name == "org_test_group"

    def test_terraform_resource_name_with_special_chars(self):
        """Test terraform_resource_name with special characters."""
        group = Group(
            id=1,
            name="Test",
            path="test",
            full_path="org/test-group.subgroup",
            visibility="private",
        )
        # Should replace /, -, . with _
        assert group.terraform_resource_name == "org_test_group_subgroup"

    def test_get_terraform_resource_name_legacy(self, sample_group: Group):
        """Test legacy get_terraform_resource_name method."""
        # Backward compatibility
        assert sample_group.get_terraform_resource_name() == sample_group.terraform_resource_name

    def test_model_dump(self, sample_group: Group):
        """Test model serialization."""
        data = sample_group.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == 123
        assert data["name"] == "Test Group"
        assert "subgroups" in data
        assert "projects" in data

    def test_model_dump_json(self, sample_group: Group):
        """Test JSON serialization."""
        json_str = sample_group.model_dump_json()
        assert isinstance(json_str, str)
        assert "Test Group" in json_str

    def test_model_dump_summary(self, sample_group: Group):
        """Test summary serialization."""
        summary = sample_group.model_dump_summary()
        assert isinstance(summary, dict)
        assert summary["id"] == 123
        # Summary should exclude nested objects
        assert "subgroups" not in summary or summary["subgroups"] == []

    def test_nested_group_structure(self, sample_nested_group: Group):
        """Test nested group structure."""
        assert len(sample_nested_group.subgroups) == 1
        subgroup = sample_nested_group.subgroups[0]
        assert subgroup.parent_id == 123
        assert subgroup.full_path == "org/test-group/subgroup"

    def test_group_with_projects(self, sample_group_with_projects: Group):
        """Test group with projects."""
        assert len(sample_group_with_projects.projects) == 1
        project = sample_group_with_projects.projects[0]
        assert project.namespace_id == 123

    def test_visibility_values(self):
        """Test different visibility values."""
        for visibility in ["private", "internal", "public"]:
            group = Group(
                id=1,
                name="Test",
                path="test",
                full_path="test",
                visibility=visibility,
            )
            assert group.visibility == visibility

    def test_optional_fields(self):
        """Test optional fields can be None."""
        group = Group(
            id=1,
            name="Test",
            path="test",
            full_path="test",
            visibility="private",
            description=None,
            parent_id=None,
            web_url=None,
        )
        assert group.description is None
        assert group.parent_id is None
        assert group.web_url is None

    def test_default_empty_lists(self):
        """Test default empty lists for subgroups and projects."""
        group = Group(
            id=1,
            name="Test",
            path="test",
            full_path="test",
            visibility="private",
        )
        assert group.subgroups == []
        assert group.projects == []

    def test_model_validate(self, sample_group: Group):
        """Test model validation from dict."""
        data = sample_group.model_dump()
        validated_group = Group.model_validate(data)
        assert validated_group.id == sample_group.id
        assert validated_group.name == sample_group.name
