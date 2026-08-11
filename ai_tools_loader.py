"""Dynamic discovery for tool modules under tools/.

Each tool module should expose:
  - SCHEMA (dict) or TOOLS_SCHEMA (list[dict])
  - TOOL_FUNCTIONS (dict[str, callable])
"""

from __future__ import annotations

import importlib.util
import os
from typing import Callable


def _load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module spec for {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_tools(tools_dir: str) -> dict:
    """Recursively scan tools_dir and return discovered tool schemas/functions."""
    tools_schema_by_name: dict[str, dict] = {}
    tool_functions: dict[str, Callable] = {}

    if not os.path.isdir(tools_dir):
        return {"tools_schema": [], "tool_functions": {}}

    tool_files: list[str] = []
    for root, dirnames, filenames in os.walk(tools_dir):
        dirnames.sort()
        for filename in sorted(filenames):
            if filename.endswith("_tools.py"):
                tool_files.append(os.path.join(root, filename))

    for file_path in sorted(tool_files):
        rel_path = os.path.relpath(file_path, tools_dir)
        module_name = (
            "tool_module_"
            + rel_path.replace("\\", "_").replace("/", "_").replace(".", "_")
        )

        try:
            module = _load_module_from_path(module_name, file_path)
        except Exception as exc:
            print(f"Skipping tool file '{file_path}': failed to import ({exc})")
            continue

        module_funcs = getattr(module, "TOOL_FUNCTIONS", {})
        if isinstance(module_funcs, dict):
            for name, fn in module_funcs.items():
                if callable(fn):
                    tool_functions[name] = fn

        module_schemas: list[dict] = []
        if hasattr(module, "TOOLS_SCHEMA") and isinstance(getattr(module, "TOOLS_SCHEMA"), list):
            module_schemas.extend(getattr(module, "TOOLS_SCHEMA"))
        elif hasattr(module, "SCHEMA") and isinstance(getattr(module, "SCHEMA"), dict):
            module_schemas.append(getattr(module, "SCHEMA"))

        for schema in module_schemas:
            if not isinstance(schema, dict):
                continue

            tool_name = schema.get("name")
            if not isinstance(tool_name, str) or not tool_name.strip():
                continue

            # Only expose schemas that have an executable function.
            if tool_name in tool_functions:
                tools_schema_by_name[tool_name] = schema

    tools_schema = [tools_schema_by_name[name] for name in sorted(tools_schema_by_name)]
    return {"tools_schema": tools_schema, "tool_functions": tool_functions}
