"""Domain entities for Terraform resources."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class ResourceType(Enum):
    """Terraform resource types."""

    GROUP = "gitlab_group"
    PROJECT = "gitlab_project"
    UNKNOWN = "unknown"


@dataclass
class TerraformVariable:
    """Terraform variable definition."""

    name: str
    type: str
    description: Optional[str] = None
    default: Any = None
    required: bool = True
    sensitive: bool = False


@dataclass
class TerraformOutput:
    """Terraform output definition."""

    name: str
    value: str
    description: Optional[str] = None
    sensitive: bool = False


@dataclass
class TerraformResource:
    """Terraform resource definition."""

    resource_type: str
    resource_name: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    import_id: Optional[str] = None

    def get_resource_address(self) -> str:
        """Get full Terraform resource address.

        Returns:
            Resource address (e.g., 'gitlab_group.my_group')
        """
        return f"{self.resource_type}.{self.resource_name}"

    def get_import_command(self) -> Optional[str]:
        """Get Terraform import command.

        Returns:
            Import command or None if no import_id
        """
        if not self.import_id:
            return None
        return f"terraform import {self.get_resource_address()} {self.import_id}"


@dataclass
class TerraformModule:
    """Terraform module definition."""

    name: str
    source: str
    version: Optional[str] = None
    variables: Dict[str, TerraformVariable] = field(default_factory=dict)
    outputs: Dict[str, TerraformOutput] = field(default_factory=dict)
    resources: List[TerraformResource] = field(default_factory=list)

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
        return [var for var in self.variables.values() if var.required and var.default is None]


@dataclass
class TerraformPlan:
    """Terraform plan representation."""

    format_version: str
    terraform_version: str
    planned_values: Dict[str, Any] = field(default_factory=dict)
    resource_changes: List[Dict[str, Any]] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)

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
        # Resources that exist but are not in state
        return [
            change for change in self.resource_changes
            if 'import' in change.get('change', {}).get('actions', [])
        ]


@dataclass
class TerraformState:
    """Terraform state representation."""

    version: int
    terraform_version: str
    resources: List[Dict[str, Any]] = field(default_factory=list)

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
