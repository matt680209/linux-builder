"""Diagnostic tool for iwlwifi backport build failures.

Corresponds to skills/iwlwifi/iwlwifi-bug-fix/SKILL.md:
  1. Check result.stderr and result.returncode.
  2. Check the running kernel version and the backport-iwlwifi branch to see
     if the branch meets the requirement.
  3. Point at the kernel source / offending files parsed from the build output.
  4. If the build succeeded, report that nothing needs fixing.

The module exposes SCHEMA + TOOL_FUNCTIONS so it is compatible with the
discovery mechanism in ai_tools_loader.py.
"""

from __future__ import annotations

import os
import re
import subprocess

# name/description are optional here — SKILL.md is the source of truth — but
# keep input_schema (and a fallback name/description) here for tool discovery.
SCHEMA = {
    "name": "diagnose_backport_iwlwifi_build",
    "description": (
        "Fallback description (overridden by SKILL.md if found). Diagnose an "
        "iwlwifi backport build failure from its returncode/stderr, report the "
        "running kernel version and backport-iwlwifi branch, and list the "
        "offending files/errors parsed from the build output."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "returncode": {
                "type": "integer",
                "description": "Exit code from the build (0 means success).",
            },
            "stderr": {
                "type": "string",
                "description": "Captured stderr text from the build command.",
            },
            "stdout": {
                "type": "string",
                "description": "Optional captured stdout text from the build command.",
            },
        },
        "required": ["returncode", "stderr"],
    },
}

# Directory holding the backport-iwlwifi source tree, relative to repo root.
_BACKPORT_DIR = "backport-iwlwifi"

# Match typical GCC/Clang diagnostics:  path/file.c:123:45: error: message
_DIAG_RE = re.compile(
    r"^(?P<file>[^\s:]+):(?P<line>\d+):(?:(?P<col>\d+):)?\s*"
    r"(?P<level>error|warning|fatal error):\s*(?P<message>.*)$"
)


def _run(command: str) -> str:
    """Run a shell command and return its stripped stdout ('' on failure)."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
    except (subprocess.SubprocessError, OSError):
        return ""
    return (result.stdout or "").strip()


def _kernel_version() -> str:
    """Return the running kernel version (uname -r)."""
    return _run("uname -r") or "unknown"


def _backport_branch() -> dict:
    """Return git branch/describe info for the backport-iwlwifi tree."""
    if not os.path.isdir(_BACKPORT_DIR):
        return {"available": False}

    branch = _run(f"cd {_BACKPORT_DIR} && git rev-parse --abbrev-ref HEAD")
    describe = _run(f"cd {_BACKPORT_DIR} && git describe --tags --always --dirty")
    commit = _run(f"cd {_BACKPORT_DIR} && git rev-parse --short HEAD")
    return {
        "available": True,
        "branch": branch or "unknown",
        "describe": describe or "unknown",
        "commit": commit or "unknown",
    }


def _run_command_with_output(command):
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = result.communicate()
    for line in out.splitlines():
        print(line.strip())
    return result


def _major_minor(version):
    # Extract leading MAJOR.MINOR (e.g. "6.19" from "6.19.3-arch1-1").
    match = re.match(r"(\d+)\.(\d+)", version)
    return match.group(0) if match else version.strip()

def _run_check_kernel_version(kernel_version):
    # Check if the kernel version is equal to /lib/modules/`uname -r`/build/source/Makefile
    print(f"Checking kernel version: {kernel_version}")
    result = _run_command_with_output(f"cd /lib/modules/{kernel_version}/build/source/ && make kernelversion")
    out, err = result.communicate()
    if result.returncode != 0:
        print(f"Error checking kernel version: {result.stderr}")
        return False
        
    if _major_minor(kernel_version) != _major_minor(out):
        print(f"Kernel version mismatch: {kernel_version} != {out.strip()}")
        return False

    ## Strongly compare current kernel and latest commit in source tree.
    if kernel_version != out.strip():
        print(f"Kernel version mismatch: {kernel_version} != {out.strip()}")
        print(f"Suggest to get aligned kernel source latest commit, but we can still try to build.")

    return True 
 
   
def _fix_kernel_version_align(kernel_version):
    """Enter the kernel source dir, check the current git branch, and if it is
    not similar to kernel_version, checkout a branch that matches it.
    """
    source_dir = f"/lib/modules/{kernel_version}/build/source"
    if not os.path.isdir(source_dir):
        print(f"Kernel source dir not found: {source_dir}")
        return False


    current_branch = _run(f"cd {source_dir} && git rev-parse --abbrev-ref HEAD")
    base_version = _major_minor(kernel_version)
    print(f"Current branch in {source_dir}: {current_branch or 'unknown'}")

    ## From here to look for existing branch can fit kernel_version, and checkout it if found. If not found, return False.
    ## If found, git check out the branch, and return True.

    if current_branch and (base_version in current_branch or kernel_version in current_branch):
        print(f"Branch '{current_branch}' already matches kernel {kernel_version}.")
        return True

    branches = _run(
        f"cd {source_dir} && git branch -a --format='%(refname:short)'"
    )
    candidates = [
        b.strip()
        for b in branches.splitlines()
        if b.strip() and (base_version in b or kernel_version in b)
    ]
    if not candidates:
        print(f"No branch similar to '{kernel_version}' found in {source_dir}.")
        return False

    # Prefer a local branch (fewest '/' segments) over a remote one.
    target = min(candidates, key=lambda b: (b.count("/"), len(b)))
    print(f"Checking out branch '{target}' in {source_dir}.")
    _run(f"cd {source_dir} && git checkout {target}")

    new_branch = _run(f"cd {source_dir} && git rev-parse --abbrev-ref HEAD")
    print(f"Now on branch '{new_branch or 'unknown'}' in {source_dir}.")
    return bool(new_branch) and (base_version in new_branch or kernel_version in new_branch)
    

def diagnose_backport_iwlwifi_build(
    returncode: int, stderr: str = "", stdout: str = ""
) -> dict:
    """Diagnose an iwlwifi backport build failure.

    Follows the iwlwifi-bug-fix skill: inspect returncode/stderr, report the
    kernel version and backport branch, and surface the offending files.
    """
    kernel_version = _kernel_version()
    if not _run_check_kernel_version(kernel_version):
        print("Kernel version mismatch, attempt to fix it.")
        success = _fix_kernel_version_align(kernel_version)   
        if success:
            return {
                "success": True,
                "returncode": returncode,
                "summary": "Kernel version is fixed.",
            }
        else :
            return {
                "success": False,
                "returncode": returncode,
                "summary": "Kernel version mismatch and failed to fix it.",
            }


    success = returncode == 0
    return {
        "success": success,
        "returncode": returncode,
        "summary": "Build succeeded; nothing to fix.",
    }

    backport = _backport_branch()

    summary_parts = [
        f"Build failed (returncode={returncode}).",
        f"Running kernel: {kernel}.",
    ]
    if backport.get("available"):
        summary_parts.append(
            f"backport-iwlwifi branch: {backport['branch']} "
            f"({backport['describe']})."
        )
    else:
        summary_parts.append(
            f"backport-iwlwifi tree not found under '{_BACKPORT_DIR}'."
        )
    if error_diags:
        summary_parts.append(
            f"{len(error_diags)} compiler error(s) across "
            f"{len(affected_files)} file(s)."
        )
    else:
        summary_parts.append("No structured compiler errors were parsed from output.")

    return {
        "success": False,
        "returncode": returncode,
        "kernel_version": kernel,
        "backport": backport,
        "errors": error_diags,
        "warnings": [d for d in diagnostics if d["level"] == "warning"],
        "affected_files": affected_files,
        "summary": " ".join(summary_parts),
    }


TOOL_FUNCTIONS = {
    SCHEMA["name"]: diagnose_backport_iwlwifi_build
}

if __name__ == "__main__":
    import json

    sample_stderr = (
        "backport-iwlwifi/main.c:42:5: error: implicit declaration of "
        "function 'foo'\n"
    )
    print(json.dumps(diagnose_backport_iwlwifi_build(2, sample_stderr), indent=2))
