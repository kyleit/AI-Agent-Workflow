package main

import (
	"fmt"
	"io"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// aiwfCommand returns an exec.Cmd configured to run the aiwf native CLI.
//
// Resolution order (cross-platform — macOS, Linux, Windows):
//  1. AIWF_BIN env var — use as-is if set.
//  2. PATH lookup for "aiwf" / "aiwf.exe".
//  3. Well-known OS install paths.
//  4. Embedded binary (extracted to ~/.aiwf/bin/) — injected at build time via "make embed-aiwf".
func aiwfCommand(args ...string) (*exec.Cmd, error) {
	bin, err := resolveAiwfBinary()
	if err != nil {
		return nil, err
	}
	return exec.Command(bin, args...), nil
}

// resolveAiwfBinary finds the aiwf binary path using the 4-step resolution chain.
func resolveAiwfBinary() (string, error) {
	// ── Step 1: explicit env override ────────────────────────────────────────
	if configured := strings.TrimSpace(os.Getenv("AIWF_BIN")); configured != "" {
		return configured, nil
	}

	// ── Step 2: PATH lookup ───────────────────────────────────────────────────
	exeName := "aiwf"
	if runtime.GOOS == "windows" {
		exeName = "aiwf.exe"
	}
	if path, err := exec.LookPath(exeName); err == nil {
		return path, nil
	}

	// ── Step 3: well-known OS install paths ──────────────────────────────────
	for _, c := range platformAiwfCandidates() {
		if _, err := os.Stat(c); err == nil {
			return c, nil
		}
	}

	// ── Step 4: embedded binary (extracted to ~/.aiwf/bin/) ──────────────────
	if path, err := extractEmbeddedAiwf(); err == nil {
		return path, nil
	}

	return "", fmt.Errorf(
		"aiwf CLI binary not found.\n"+
			"Options:\n"+
			"  1. Install: cd go-src/aiwf && make install\n"+
			"  2. Set AIWF_BIN=/path/to/aiwf in your environment\n"+
			"  3. Rebuild the desktop app with: make embed-aiwf && make build\n"+
			"Checked: PATH + %v + embedded bundle",
		platformAiwfCandidates(),
	)
}

// embeddedBinaryName returns the filename inside embedded/ for the current OS/ARCH.
func embeddedBinaryName() string {
	goos := runtime.GOOS
	goarch := runtime.GOARCH
	switch goos {
	case "windows":
		return fmt.Sprintf("aiwf_%s_%s.exe", goos, goarch)
	default:
		return fmt.Sprintf("aiwf_%s_%s", goos, goarch)
	}
}

// extractEmbeddedAiwf extracts the embedded aiwf binary to ~/.aiwf/bin/ and returns its path.
// Returns an error if the embedded binary is a stub (< 32 bytes) or missing.
func extractEmbeddedAiwf() (string, error) {
	name := embeddedBinaryName()
	fsPath := "embedded/" + name

	// Read from embed.FS
	data, err := fs.ReadFile(embeddedBinFS, fsPath)
	if err != nil {
		return "", fmt.Errorf("embedded binary %q not found in bundle", name)
	}

	// Detect stub files (committed placeholder, not a real binary)
	const minBinarySize = 32
	if len(data) < minBinarySize {
		return "", fmt.Errorf("embedded binary %q is a stub (%d bytes) — run 'make embed-aiwf' to inject real binary", name, len(data))
	}

	// Extract to ~/.aiwf/bin/
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("cannot determine home dir for extraction: %w", err)
	}
	binDir := filepath.Join(home, ".aiwf", "bin")
	if err := os.MkdirAll(binDir, 0755); err != nil {
		return "", fmt.Errorf("cannot create ~/.aiwf/bin/: %w", err)
	}

	destName := "aiwf"
	if runtime.GOOS == "windows" {
		destName = "aiwf.exe"
	}
	destPath := filepath.Join(binDir, destName)

	// Only overwrite if the embedded binary is newer (compare sizes as a proxy).
	if existing, err := os.Stat(destPath); err == nil {
		if existing.Size() == int64(len(data)) {
			// Assume same binary, skip re-extraction.
			return destPath, nil
		}
	}

	// Write atomically via temp file.
	tmp, err := os.CreateTemp(binDir, destName+".tmp.*")
	if err != nil {
		return "", fmt.Errorf("cannot create temp file for extraction: %w", err)
	}
	tmpPath := tmp.Name()

	if _, err := io.WriteString(tmp, string(data)); err != nil {
		tmp.Close()
		os.Remove(tmpPath)
		return "", fmt.Errorf("cannot write embedded binary: %w", err)
	}
	tmp.Close()

	// Make executable (no-op on Windows).
	if err := os.Chmod(tmpPath, 0755); err != nil {
		os.Remove(tmpPath)
		return "", fmt.Errorf("cannot chmod extracted binary: %w", err)
	}

	// Atomic rename.
	if err := os.Rename(tmpPath, destPath); err != nil {
		os.Remove(tmpPath)
		return "", fmt.Errorf("cannot move extracted binary to %s: %w", destPath, err)
	}

	return destPath, nil
}

// platformAiwfCandidates returns OS-specific well-known install paths.
func platformAiwfCandidates() []string {
	switch runtime.GOOS {
	case "windows":
		var paths []string
		if local := os.Getenv("LOCALAPPDATA"); local != "" {
			paths = append(paths, filepath.Join(local, "aiwf", "bin", "aiwf.exe"))
		}
		if profile := os.Getenv("USERPROFILE"); profile != "" {
			paths = append(paths, filepath.Join(profile, "AppData", "Local", "aiwf", "bin", "aiwf.exe"))
			paths = append(paths, filepath.Join(profile, "bin", "aiwf.exe"))
		}
		return paths

	default: // macOS, Linux, other Unix
		home, _ := os.UserHomeDir()
		paths := []string{
			"/usr/local/bin/aiwf",
			"/usr/bin/aiwf",
			"/opt/homebrew/bin/aiwf", // Homebrew — Apple Silicon
			"/opt/local/bin/aiwf",    // MacPorts
		}
		if home != "" {
			// Highest priority user paths prepended.
			paths = append([]string{
				filepath.Join(home, ".local", "bin", "aiwf"),
				filepath.Join(home, "bin", "aiwf"),
			}, paths...)
		}
		return paths
	}
}
