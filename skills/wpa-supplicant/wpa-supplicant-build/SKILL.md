---
name: wpa-supplicant-build
description: Builds the wpa_supplicant binary from the hostap source tree. Use this when the user asks to build, compile, or make wpa_supplicant, or troubleshoot its build output.
---

# wpa_supplicant Build Skill

1. call build_wpa_supplicant tool to build the code.
2. Returns returncode/stdout/stderr/success.
3. If build success, then we are done.
4. If build fails, inspect the stderr/stdout for missing headers or packages and
   map them to the apt package that provides them, for example:
   - `dbus/dbus.h: No such file or directory` -> `libdbus-1-dev`
   - `libnl-3.0` not found -> `libnl-3-dev`
   - `libnl-genl-3.0` not found -> `libnl-genl-3-dev`
   - `libnl-route-3.0` not found -> `libnl-route-3-dev`
   - `openssl/ssl.h` not found -> `libssl-dev`
5. call install_apt_packages with the deduced package name(s) to install them.
6. call build_wpa_supplicant again and repeat until the build succeeds.




