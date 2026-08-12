---
name: iwlwifi-bug-fix
description: Get to debug iwlwifi build failure based on the result.stderr and result.returncode. 
---

# iwlwifi Build Skill

1. Check the result.stderr and result.returncode.
2. If the returncode is not 0, go with the following steps to fix the build failure:
   1. Check if the built kernel objects are not aligned with the source version code, if so, fix it by calling the tool `fix_kernel_version_align`.
   2. Check if the backport-iwlwifi branch can be compiled with the current kernel version.
3. After applying the fix, call the `build_backport_iwlwifi` to check if build is successful.
4. Inspect the returned returncode/stderr: if returncode is 0 the fix succeeded and you are done; otherwise repeat steps 1-3.


