"""Domain entities for Terraform resources."""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, computed_field


class ResourceType(Enum):
    """Terraform resource types."""

    GROUP = "gitlab_group"
    PROJECT = "gitlab_project"
    UNKNOWN = "unknown"


class TerraformVariable(BaseModel):
    """Terraform variable definition using Pydantic."""

    model_config = {"arbitrary_types_allowed": True}

    name: str = Field(..., description="Variable name")
    type: str = Field(..., description="Variable type")
    description: Optional[str] = Field(None, description="Variable description")
    default: Any = Field(None, description="Default value")
    required: bool = Field(default=True, description="Is variable required")
    sensitive: bool = Field(default=False, description="Is variable sensitive")


class TerraformOutput(BaseModel):
    """Terraform output definition using Pydantic."""

    name: str = Field(..., description="Output name")
    value: str = Field(..., description="Output value expression")
    description: Optional[str] = Field(None, description="Output description")
    sensitive: bool = Field(default=False, description="Is output sensitive")


class TerraformResource(BaseModel):
    """Terraform resource definition using Pydantic."""

    model_config = {"arbitrary_types_allowed": True}

    resource_type: str = Field(..., description="Resource type (e.g., 'gitlab_group')")
    resource_name: str = Field(..., description="Resource name")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Resource attributes")
    depends_on: List[str] = Field(default_factory=list, description="Dependencies")
    import_id: Optional[str] = Field(None, description="ID for terraform import")

    @computed_field
    @property
    def resource_address(self) -> str:
        """Get full Terraform resource address.

        Returns:
            Resource address (e.g., 'gitlab_group.my_group')
        """
        return f"{self.resource_type}.{self.resource_name}"

    @computed_field
    @property
    def import_command(self) -> Optional[str]:
        """Get Terraform import command.

        Returns:
            Import command or None if no import_id
        """
        if not self.import_id:
            return None
        return f"terraform import {self.resource_address} {self.import_id}"

    def get_resource_address(self) -> str:
        """Get full Terraform resource address (legacy method).

        Returns:
            Resource address
        """
        return self.resource_address

    def get_import_command(self) -> Optional[str]:
        """Get Terraform import command (legacy method).

        Returns:
            Import command or None if no import_id
        """
        return self.import_command


class TerraformModule(BaseModel):
    """Terraform module definition using Pydantic."""

    model_config = {"arbitrary_types_allowed": True}

    name: str = Field(..., description="Module name")
    source: str = Field(..., description="Module source path")
    version: Optional[str] = Field(None, description="Module version")
    variables: Dict[str, TerraformVariable] = Field(
        default_factory=dict,
        description="Module variables"
    )
    outputs: Dict[str, TerraformOutput] = Field(
        default_factory=dict,
        description="Module outputs"
    )
    resources: List[TerraformResource] = Field(
        default_factory=list,
        description="Module resources"
    )

    def add_variable(self, variable: TerraformVariable) -> None:
        """Add a variable to the module.

        Args:
            variable: Variable to add
        """
        self.variables[variable.name] = variable

    def add_output(self, output: TerraformOutput) -> None:
        """Add an output to the module.

        Args:
            output: Output to add
        """
        self.outputs[output.name] = output

    def add_resource(self, resource: TerraformResource) -> None:
        """Add a resource to the module.

        Args:
            resource: Resource to add
        """
        self.resources.append(resource)

    def get_required_variables(self) -> List[TerraformVariable]:
        """Get list of required variables.

        Returns:
            List of required variables
        """
        return [
            var for var in self.variables.values()
            if var.required and var.default is None
        ]

    @computed_field
    @property
    def required_variables_count(self) -> int:
        """Get count of required variables.

        Returns:
            Number of required variables
        """
        return len(self.get_required_variables())


class TerraformPlan(BaseModel):
    """Terraform plan representation using Pydantic."""

    model_config = {"arbitrary_types_allowed": True}

    format_version: str = Field(..., description="Plan format version")
    terraform_version: str = Field(..., description="Terraform version")
    planned_values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Planned values"
    )
    resource_changes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Resource changes"
    )
    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration"
    )

    def get_resources_to_create(self) -> List[Dict[str, Any]]:
        """Get resources that will be created.

        Returns:
            List of resources to create
        """
        return [
            change for change in self.resource_changes
            if change.get('change', {}).get('actions') == ['create']
        ]

    def get_resources_to_import(self) -> List[Dict[str, Any]]:
        """Get resources that need to be imported.

        Returns:
            List of resources to import
        """
        return [
            change for change in self.resource_changes
            if 'import' in change.get('change', {}).get('actions', [])
        ]

    @computed_field
    @property
    def creates_count(self) -> int:
        """Get count of resources to create.

        Returns:
            Number of resources to create
        """
        return len(self.get_resources_to_create())

    @computed_field
    @property
    def imports_count(self) -> int:
        """Get count of resources to import.

        Returns:
            Number of resources to import
        """
        return len(self.get_resources_to_import())


class TerraformState(BaseModel):
    """Terraform state representation using Pydantic."""

    model_config = {"arbitrary_types_allowed": True}

    version: int = Field(..., description="State version")
    terraform_version: str = Field(..., description="Terraform version")
    resources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Resources in state"
    )

    def has_resource(self, resource_type: str, resource_name: str) -> bool:
        """Check if resource exists in state.

        Args:
            resource_type: Type of resource
            resource_name: Name of resource

        Returns:
            True if resource exists
        """
        for resource in self.resources:
            if (resource.get('type') == resource_type and
                resource.get('name') == resource_name):
                return True
        return False

    @computed_field
    @property
    def resources_count(self) -> int:
        """Get count of resources in state.

        Returns:
            Number of resources
        """
        return len(self.resources)

    def get_resources_by_type(self, resource_type: str) -> List[Dict[str, Any]]:
        """Get all resources of a specific type.

        Args:
            resource_type: Resource type to filter by

        Returns:
            List of matching resources
        """
        return [
            resource for resource in self.resources
            if resource.get('type') == resource_type
        ]
