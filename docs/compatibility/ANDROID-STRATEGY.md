# Android Compatibility Strategy

**Status:** DEFERRED. Target: far post-M7. **Not a 1.0 prerequisite.**

## Android is a platform, not "Linux apps with a touchscreen"

Android depends on Binder for essentially all process/service IPC, on ART, and on the Android
framework and HAL model — modern HALs are binderized interfaces running in separate processes.
None of that follows from Linux compatibility.

## Staging

### 1. Android VM (realistic)

```
APK → Android userspace → Android guest VM → Malrynth virtual GPU/input/audio/network
```

The compositor presents Android surfaces as ordinary Malrynth windows. This is the only path
that is credible within a reasonable horizon.

### 2. Tighter integration

Explicit bridges for clipboard, notifications, file picker, camera, microphone, location and
window sizing — each one a **capability**, not an ambient grant. An Android app in a VM must
not gain more authority than a native app.

### 3. Native Android personality (probably never)

Would require bionic, Binder semantics, ART, Android filesystem assumptions, graphics buffer
compatibility, SELinux expectations, the package framework and system services.

**This is an enormous project and must not become a 1.0 prerequisite.** It is recorded so the
option is understood, not planned.
