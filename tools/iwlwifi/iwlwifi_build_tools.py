import subprocess

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

def build_backport_iwlwifi():
    subprocess.run("cd backport-iwlwifi && make clean", shell=True, capture_output=False)
    ##subprocess.run("cd backport-iwlwifi &&git reset --hard HEAD", shell=True, capture_output=False)
    ##subprocess.run("cp .config backport-iwlwifi", shell=True, capture_output=True, text=True)
    ##subprocess.run("cd backport-iwlwifi && rm main main.o", shell=True, capture_output=True, text=True)
    command = "cd backport-iwlwifi && make -j20"
    ##result = subprocess.run(command, shell=True, capture_output=True, text=True)
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
    SCHEMA["name"]: build_backport_iwlwifi
}

if __name__ == "__main__":
    success = build_backport_iwlwifi()
    exit(0 if success in (True,) else 1)