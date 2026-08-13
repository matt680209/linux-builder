import os
import subprocess

# name/description are optional here — SKILL.md is source of truth,
# but keep input_schema (and a fallback name/description) here.
SCHEMA = {
    "name": "build_wpa_supplicant",
    "description": "Fallback description (overridden by SKILL.md if found)",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

# wpa_supplicant lives in the hostap source tree checked out under test_assert/.
BUILD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "test_assert", "hostap", "wpa_supplicant",
)


def build_wpa_supplicant():
    subprocess.run("make clean", shell=True, cwd=BUILD_DIR, capture_output=False)
    command = "make -j20"
    result = subprocess.Popen(
        command,
        shell=True,
        cwd=BUILD_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = result.communicate()
    for line in out.splitlines():
        print(line.strip())

    result.stderr = err
    result.stdout = out
    print(f"Build stderr:\n{result.stderr}")

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0
    }

TOOL_FUNCTIONS = {
    SCHEMA["name"]: build_wpa_supplicant
}

if __name__ == "__main__":
    outcome = build_wpa_supplicant()
    exit(0 if outcome.get("success") else 1)
