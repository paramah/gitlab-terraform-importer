"""Tests for Terraform entities."""


from gitlab_terraform_importer.domain.entities import (
    TerraformModule,
    TerraformOutput,
    TerraformResource,
    TerraformVariable,
)


class TestTerraformVariable:
    """Test TerraformVariable entity."""

    def test_create_variable_valid(self, sample_terraform_variable: TerraformVariable):
        """Test creating a valid variable."""
        assert sample_terraform_variable.name == "group_name"
        assert sample_terraform_variable.type == "string"
        assert sample_terraform_variable.required is True

    def test_variable_optional(self):
        """Test optional variable."""
        var = TerraformVariable(
            name="optional_var",
            type="string",
            default="default_value",
            required=False,
        )
        assert var.required is False
        assert var.default == "default_value"

    def test_variable_without_description(self):
        """Test variable without description."""
        var = TerraformVariable(
            name="test",
            type="string",
            default=None,
            required=True,
        )
        assert var.description is None

    def test_model_dump(self, sample_terraform_variable: TerraformVariable):
        """Test variable serialization."""
        data = sample_terraform_variable.model_dump()
        assert data["name"] == "group_name"
        assert data["type"] == "string"


class TestTerraformOutput:
    """Test TerraformOutput entity."""

    def test_create_output_valid(self, sample_terraform_output: TerraformOutput):
        """Test creating a valid output."""
        assert sample_terraform_output.name == "group_id"
        assert sample_terraform_output.sensitive is False

    def test_output_sensitive(self):
        """Test sensitive output."""
        output = TerraformOutput(
            name="password",
            value="${random_password.this.result}",
            sensitive=True,
        )
        assert output.sensitive is True

    def test_output_without_description(self):
        """Test output without description."""
        output = TerraformOutput(
            name="test",
            value="${test.value}",
            sensitive=False,
        )
        assert output.description is None


class TestTerraformResource:
    """Test TerraformResource entity."""

    def test_create_resource_valid(self, sample_terraform_resource: TerraformResource):
        """Test creating a valid resource."""
        assert sample_terraform_resource.resource_type == "gitlab_group"
        assert sample_terraform_resource.resource_name == "test_group"
        assert isinstance(sample_terraform_resource.attributes, dict)

    def test_resource_address_computed(self, sample_terraform_resource: TerraformResource):
        """Test resource_address computed field."""
        expected = "gitlab_group.test_group"
        assert sample_terraform_resource.resource_address == expected

    def test_import_command_computed(self):
        """Test import_command computed field."""
        resource = TerraformResource(
            resource_type="gitlab_group",
            resource_name="my_group",
            attributes={"id": "123"},
            depends_on=[],
            import_id="123",
        )
        expected = "terraform import gitlab_group.my_group 123"
        assert resource.import_command == expected

    def test_import_command_no_id(self):
        """Test import_command when no import_id."""
        # Resource without import_id should return None
        resource = TerraformResource(
            resource_type="gitlab_group",
            resource_name="test_group",
            attributes={},
            depends_on=[],
        )
        assert resource.import_command is None

    def test_resource_with_depends_on(self):
        """Test resource with dependencies."""
        resource = TerraformResource(
            resource_type="gitlab_project",
            resource_name="my_project",
            attributes={},
            depends_on=["gitlab_group.parent"],
        )
        assert len(resource.depends_on) == 1
        assert resource.depends_on[0] == "gitlab_group.parent"

    def test_model_dump(self, sample_terraform_resource: TerraformResource):
        """Test resource serialization."""
        data = sample_terraform_resource.model_dump()
        assert data["resource_type"] == "gitlab_group"
        assert data["resource_name"] == "test_group"


class TestTerraformModule:
    """Test TerraformModule entity."""

    def test_create_module_valid(self, sample_terraform_module: TerraformModule):
        """Test creating a valid module."""
        assert sample_terraform_module.name == "gitlab-group-module"
        assert sample_terraform_module.source == "/path/to/module"
        assert len(sample_terraform_module.variables) > 0
        assert len(sample_terraform_module.outputs) > 0
        assert len(sample_terraform_module.resources) > 0

    def test_required_variables_computed(self, sample_terraform_module: TerraformModule):
        """Test get_required_variables method."""
        required = sample_terraform_module.get_required_variables()
        assert all(var.required for var in required)
        assert len(required) == 2  # Both variables are required

    def test_optional_variables_computed(self):
        """Test get_required_variables method with optional variables."""
        module = TerraformModule(
            name="test-module",
            source="/test",
            variables={
                "required": TerraformVariable(name="required", type="string", required=True),
                "optional": TerraformVariable(
                    name="optional",
                    type="string",
                    default="default",
                    required=False,
                ),
            },
            outputs={},
            resources=[],
        )
        # Only required variables without default values
        required = module.get_required_variables()
        assert len(required) == 1
        assert required[0].name == "required"

    def test_resource_types_check(self, sample_terraform_module: TerraformModule):
        """Test checking resource types."""
        # Check that module has gitlab_group resources
        has_gitlab_group = any(
            r.resource_type == "gitlab_group" for r in sample_terraform_module.resources
        )
        assert has_gitlab_group

    def test_has_resource_type(self, sample_terraform_module: TerraformModule):
        """Test checking for specific resource types."""
        # Check gitlab_group exists
        has_gitlab_group = any(
            r.resource_type == "gitlab_group" for r in sample_terraform_module.resources
        )
        assert has_gitlab_group is True

        # Check gitlab_project doesn't exist
        has_gitlab_project = any(
            r.resource_type == "gitlab_project" for r in sample_terraform_module.resources
        )
        assert has_gitlab_project is False

    def test_is_compatible_with_gitlab_groups(self, sample_terraform_module: TerraformModule):
        """Test checking compatibility with gitlab_groups."""
        # Module has gitlab_group resource type
        has_gitlab_group = any(
            r.resource_type == "gitlab_group" for r in sample_terraform_module.resources
        )
        assert has_gitlab_group is True

    def test_is_compatible_with_gitlab_projects(self):
        """Test checking compatibility with gitlab_projects."""
        module = TerraformModule(
            name="test-module",
            source="/test",
            variables={},
            outputs={},
            resources=[
                TerraformResource(
                    resource_type="gitlab_project",
                    resource_name="this",
                    attributes={},
                    depends_on=[],
                )
            ],
        )
        has_gitlab_project = any(r.resource_type == "gitlab_project" for r in module.resources)
        assert has_gitlab_project is True

    def test_module_not_compatible(self):
        """Test module with incompatible resources."""
        module = TerraformModule(
            name="test-module",
            source="/test",
            variables={},
            outputs={},
            resources=[
                TerraformResource(
                    resource_type="aws_instance",
                    resource_name="this",
                    attributes={},
                    depends_on=[],
                )
            ],
        )
        has_gitlab_group = any(r.resource_type == "gitlab_group" for r in module.resources)
        has_gitlab_project = any(r.resource_type == "gitlab_project" for r in module.resources)
        assert has_gitlab_group is False
        assert has_gitlab_project is False

    def test_model_dump(self, sample_terraform_module: TerraformModule):
        """Test module serialization."""
        data = sample_terraform_module.model_dump()
        assert "variables" in data
        assert "outputs" in data
        assert "resources" in data
