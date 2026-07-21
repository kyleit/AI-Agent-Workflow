package delivery

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

func pythonCommandContext(ctx context.Context, args ...string) (*exec.Cmd, error) {
	if configured := strings.TrimSpace(os.Getenv("AIWF_PYTHON")); configured != "" {
		return exec.CommandContext(ctx, configured, args...), nil
	}

	candidates := []struct {
		name      string
		extraArgs []string
	}{
		{name: "python3"},
		{name: "python"},
		{name: "py", extraArgs: []string{"-3"}},
	}

	for _, candidate := range candidates {
		path, err := exec.LookPath(candidate.name)
		if err != nil {
			continue
		}
		fullArgs := append([]string{}, candidate.extraArgs...)
		fullArgs = append(fullArgs, args...)
		return exec.CommandContext(ctx, path, fullArgs...), nil
	}

	return nil, fmt.Errorf("Python 3 runtime was not found. Install Python 3 and ensure python3/python is available in PATH, or set AIWF_PYTHON to the Python executable path")
}
