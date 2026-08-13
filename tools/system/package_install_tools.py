import subprocess

# name/description are optional here — SKILL.md is source of truth,
# but keep input_schema (and a fallback name/description) here.
SCHEMA = {
    "name": "install_apt_packages",
    "description": (
        "Install one or more missing system packages with apt-get. Use this when "
        "a build fails due to a missing library or header (e.g. 'dbus/dbus.h: No "
        "such file or directory' -> libdbus-1-dev, or 'libnl-3.0 not found' -> "
        "libnl-3-dev). Provide the exact apt package names."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "packages": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of apt package names to install, e.g. ['libdbus-1-dev', 'libnl-3-dev'].",
            }
        },
        "required": ["packages"],
    },
}


def install_apt_packages(packages):
    if isinstance(packages, str):
        packages = [packages]
    if not packages:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": "No packages provided.",
            "success": False,
        }

    command = ["sudo", "apt-get", "install", "-y", *packages]
    result = subprocess.run(command, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print(f"Install stderr:\n{result.stderr}")

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }


TOOL_FUNCTIONS = {
    SCHEMA["name"]: install_apt_packages
}

if __name__ == "__main__":
    import sys
    outcome = install_apt_packages(sys.argv[1:])
    exit(0 if outcome.get("success") else 1)
