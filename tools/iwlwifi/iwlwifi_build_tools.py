import subprocess
import os
import re
import multiprocessing

from tools.iwlwifi.iwlwifi_bug_fix_tools import _run_check_kernel_version

# name/description are optional here now — SKILL.md is source of truth,
# but keep input_schema (and a fallback name/description) here.
SCHEMA = {
    "name": "build_backport_iwlwifi",
    "description": "Fallback description (overridden by SKILL.md if found)",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

def _run_command_normal(command):
    return subprocess.run(command, shell=True, capture_output=False)


def _run_command_with_output(command):
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = result.communicate()
    for line in out.splitlines():
        print(line.strip())

    return result


def build_backport_iwlwifi():
    """Build the backport-iwlwifi driver."""
    ##if not _run_check_kernel_version(subprocess.run("uname -r", shell=True, capture_output=True, text=True).stdout.strip()):
    ##    print("Kernel version mismatch, aborting build.")
    ##    return {
    ##        "returncode": 1,
    ##        "stdout": "",
    ##        "stderr": "Kernel version mismatch",
    ##        "success": False
    ##    }
    ##else:
    ##    print("Kernel version matches, proceeding with build.")


    _run_command_normal("cd backport-iwlwifi && git reset --hard HEAD")
    _run_command_normal("cp backport-iwlwifi-matt backport-iwlwifi/defconfigs/backport-iwlwifi-matt")
    _run_command_with_output("cd backport-iwlwifi && make defconfig-backport-iwlwifi-matt")

    ##subprocess.run("cd backport-iwlwifi && rm main main.o", shell=True, capture_output=True, text=True)
    jobs = multiprocessing.cpu_count() * 2
    command = f"cd backport-iwlwifi && make -j{jobs}"
    ##result = subprocess.run(command, shell=True, capture_output=True, text=True)
    result = _run_command_with_output(command)
    out, err = result.communicate()
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
    SCHEMA["name"]: build_backport_iwlwifi
}

if __name__ == "__main__":
    success = build_backport_iwlwifi()
    exit(0 if success in (True,) else 1)