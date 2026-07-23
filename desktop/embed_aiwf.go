package main

import "embed"

// embeddedBinFS holds the prebuilt aiwf binaries for all supported platforms.
//
// Platform binary filenames:
//   - embedded/aiwf_windows_amd64.exe  — Windows x86-64
//   - embedded/aiwf_darwin_arm64       — macOS Apple Silicon (M1/M2/M3)
//   - embedded/aiwf_darwin_amd64       — macOS Intel
//   - embedded/aiwf_linux_amd64        — Linux x86-64
//   - embedded/aiwf_linux_arm64        — Linux ARM64
//
// Stub files (4 bytes, "STUB") are committed to git so the build always compiles.
// Real binaries are injected by "make embed-aiwf" before packaging the desktop app.
// At runtime, resolveAiwfBinary() detects stubs (< 32 bytes) and skips extraction.
//
//go:embed embedded
var embeddedBinFS embed.FS
