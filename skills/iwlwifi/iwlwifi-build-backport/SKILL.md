---
name: iwlwifi-build-backport
description: Builds the backport-iwlwifi driver. Use this when the user asks to build, compile, or make the backport-iwlwifi project, or troubleshoot its build output.
---

# iwlwifi Build Skill

1. call run_backport_iwlwifi_build_shell tool to build the code.
2. Returns returncode/stdout/stderr/success.
3. If build success, then we are done.
4. If build fails, Need to invoke iwlwifi_bug_fix skill to debug the build failure based on the result.stderr and result.returncode.


