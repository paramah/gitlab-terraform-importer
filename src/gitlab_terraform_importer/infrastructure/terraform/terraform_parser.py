"""Terraform file parser."""

import hcl2
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from ...domain.entities import (
    TerraformModule,
    TerraformVariable,
    TerraformOutput,
    TerraformResource,
)

logger = logging.getLogger(__name__)


class TerraformParser:
    """Parser for Terraform configuration files."""

    def parse_terraform_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single Terraform file.

        Args:
            file_path: Path to .tf file

        Returns:
            Parsed HCL content

        Raises:
            FileNotFoundError: If file not found
            ParseError: If file cannot be parsed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Terraform file not found: {file_path}")

        try:
            with open(file_path, 'r') as f:
                content = hcl2.load(f)
            return content
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            raise ValueError(f"Failed to parse Terraform file: {e}")

    def parse_module_directory(self, module_path: Path) -> TerraformModule:
        """Parse all .tf files in a module directory.

        Args:
            module_path: Path to module directory

        Returns:
            TerraformModule entity

        Raises:
            FileNotFoundError: If module directory not found
        """
        if not module_path.exists() or not module_path.is_dir():
            raise FileNotFoundError(f"Module directory not found: {module_path}")

        logger.info(f"Parsing Terraform module: {module_path}")

        # Collect all .tf files
        tf_files = list(module_path.glob("*.tf"))
        if not tf_files:
            logger.warning(f"No .tf files found in {module_path}")

        # Parse all files and merge content
        all_content: Dict[str, List[Any]] = {}

        for tf_file in tf_files:
            try:
                content = self.parse_terraform_file(tf_file)
                # Merge content
                for key, value in content.items():
                    if key not in all_content:
                        all_content[key] = []
                    if isinstance(value, list):
                        all_content[key].extend(value)
                    else:
                        all_content[key].append(value)
            except Exception as e:
                logger.warning(f"Skipping {tf_file}: {e}")

        # Create module entity
        module = TerraformModule(
            name=module_path.name,
            source=str(module_path),
        )

        # Parse variables
        if 'variable' in all_content:
            for var_block in all_content['variable']:
                for var_name, var_def in var_block.items():
                    variable = self._parse_variable(var_name, var_def)
                    module.add_variable(variable)

        # Parse outputs
        if 'output' in all_content:
            for out_block in all_content['output']:
                for out_name, out_def in out_block.items():
                    output = self._parse_output(out_name, out_def)
                    module.add_output(output)

        # Parse resources
        if 'resource' in all_content:
            for res_block in all_content['resource']:
                for res_type, res_defs in res_block.items():
                    for res_name, res_attrs in res_defs.items():
                        resource = TerraformResource(
                            resource_type=res_type,
                            resource_name=res_name,
                            attributes=res_attrs if isinstance(res_attrs, dict) else {}
                        )
                        module.add_resource(resource)

        logger.info(
            f"Parsed module: {len(module.variables)} variables, "
            f"{len(module.outputs)} outputs, {len(module.resources)} resources"
        )

        return module

    def _parse_variable(self, name: str, definition: Any) -> TerraformVariable:
        """Parse a variable definition.

        Args:
            name: Variable name
            definition: Variable definition dict

        Returns:
            TerraformVariable entity
        """
        if not isinstance(definition, dict):
            definition = {}

        # Helper to extract value from HCL2 structure (which may wrap values in lists)
        def extract_value(value, default_value=None):
            if value is None:
                return default_value
            if isinstance(value, list) and len(value) > 0:
                return value[0]
            return value

        var_type = extract_value(definition.get('type'), 'string')
        description = extract_value(definition.get('description'), None)
        default = extract_value(definition.get('default'), None)
        sensitive = extract_value(definition.get('sensitive'), False)

        return TerraformVariable(
            name=name,
            type=var_type if isinstance(var_type, str) else str(var_type),
            description=description,
            default=default,
            required=(default is None),
            sensitive=sensitive,
        )

    def _parse_output(self, name: str, definition: Any) -> TerraformOutput:
        """Parse an output definition.

        Args:
            name: Output name
            definition: Output definition dict

        Returns:
            TerraformOutput entity
        """
        if not isinstance(definition, dict):
            definition = {}

        # Helper to extract value from HCL2 structure (which may wrap values in lists)
        def extract_value(value, default_value=None):
            if value is None:
                return default_value
            if isinstance(value, list) and len(value) > 0:
                return value[0]
            return value

        value = extract_value(definition.get('value'), '')
        description = extract_value(definition.get('description'), None)
        sensitive = extract_value(definition.get('sensitive'), False)

        return TerraformOutput(
            name=name,
            value=str(value),
            description=description,
            sensitive=sensitive,
        )

    def parse_json_plan(self, plan_file: Path) -> Dict[str, Any]:
        """Parse a Terraform plan JSON file.

        Args:
            plan_file: Path to plan JSON file

        Returns:
            Parsed plan data

        Raises:
            FileNotFoundError: If file not found
        """
        if not plan_file.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_file}")

        try:
            with open(plan_file, 'r') as f:
                plan_data = json.load(f)
            return plan_data
        except Exception as e:
            logger.error(f"Failed to parse plan file: {e}")
            raise ValueError(f"Failed to parse plan JSON: {e}")

    def parse_json_state(self, state_file: Path) -> Dict[str, Any]:
        """Parse a Terraform state JSON file.

        Args:
            state_file: Path to state JSON file

        Returns:
            Parsed state data

        Raises:
            FileNotFoundError: If file not found
        """
        if not state_file.exists():
            raise FileNotFoundError(f"State file not found: {state_file}")

        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            return state_data
        except Exception as e:
            logger.error(f"Failed to parse state file: {e}")
            raise ValueError(f"Failed to parse state JSON: {e}")
