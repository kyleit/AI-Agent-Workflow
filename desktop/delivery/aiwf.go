package delivery

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// aiwfCommandContext returns an exec.Cmd configured to run the aiwf native CLI with a context.
// Resolution order: AIWF_BIN env → PATH → well-known OS paths.
// Note: embedded extraction is handled in the main package (aiwf.go) and installs to ~/.aiwf/bin/,
// which is covered by the well-known OS paths checked here.
func aiwfCommandContext(ctx context.Context, args ...string) (*exec.Cmd, error) {
	bin, err := resolveAiwfBinary()
	if err != nil {
		return nil, err
	}
	return exec.CommandContext(ctx, bin, args...), nil
}

// resolveAiwfBinary finds the aiwf binary path (delivery package — no embed access).
func resolveAiwfBinary() (string, error) {
	// Step 1: explicit override.
	if configured := strings.TrimSpace(os.Getenv("AIWF_BIN")); configured != "" {
		return configured, nil
	}

	// Step 2: PATH lookup.
	exeName := "aiwf"
	if runtime.GOOS == "windows" {
		exeName = "aiwf.exe"
	}
	if path, err := exec.LookPath(exeName); err == nil {
		return path, nil
	}

	// Step 3: well-known OS paths (includes ~/.aiwf/bin/ where embedded extraction lands).
	candidates := platformAiwfCandidates()
	for _, c := range candidates {
		if _, err := os.Stat(c); err == nil {
			return c, nil
		}
	}

	return "", fmt.Errorf(
		"aiwf CLI binary not found. Install via 'make install' in go-src/aiwf/, "+
			"set AIWF_BIN env var, or rebuild the desktop app with embedded binaries. "+
			"Checked: PATH, %v", candidates,
	)
}

// platformAiwfCandidates returns OS-specific well-known install paths.
// Includes ~/.aiwf/bin/ where the embedded extraction from the main package lands.
func platformAiwfCandidates() []string {
	home, _ := os.UserHomeDir()

	switch runtime.GOOS {
	case "windows":
		var paths []string
		// ~/.aiwf/bin/ — where embedded extraction lands
		if home != "" {
			paths = append(paths, filepath.Join(home, ".aiwf", "bin", "aiwf.exe"))
		}
		if local := os.Getenv("LOCALAPPDATA"); local != "" {
			paths = append(paths, filepath.Join(local, "aiwf", "bin", "aiwf.exe"))
		}
		if profile := os.Getenv("USERPROFILE"); profile != "" {
			paths = append(paths, filepath.Join(profile, "AppData", "Local", "aiwf", "bin", "aiwf.exe"))
			paths = append(paths, filepath.Join(profile, "bin", "aiwf.exe"))
		}
		return paths

	default: // macOS, Linux, other Unix
		paths := []string{}
		if home != "" {
			paths = append(paths,
				filepath.Join(home, ".aiwf", "bin", "aiwf"), // embedded extraction target
				filepath.Join(home, ".local", "bin", "aiwf"),
				filepath.Join(home, "bin", "aiwf"),
			)
		}
		paths = append(paths,
			"/usr/local/bin/aiwf",
			"/usr/bin/aiwf",
			"/opt/homebrew/bin/aiwf", // Homebrew — Apple Silicon
			"/opt/local/bin/aiwf",    // MacPorts
		)
		return paths
	}
}
