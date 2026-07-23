//go:build windows

package delivery

import (
	"context"
	"fmt"

	"desktop/domain"
)

type Executor struct {
	lockChecker domain.LockChecker
}

func NewExecutor(lc domain.LockChecker) *Executor {
	return &Executor{
		lockChecker: lc,
	}
}

// StartOrchestrator starts the workflow orchestrator via the aiwf native CLI.
// Uses: aiwf start --skill <skill> --command <command>
// Note: Setpgid is not available on Windows; process is started without a new process group.
func (e *Executor) StartOrchestrator(ctx context.Context, projectPath, skill, command string) (bool, error) {
	if err := e.lockChecker.CheckLock(projectPath); err != nil {
		return false, err
	}

	cmd, err := aiwfCommandContext(ctx,
		"start",
		"--skill", skill,
		"--command", command,
	)
	if err != nil {
		return false, err
	}
	cmd.Dir = projectPath

	if err := cmd.Start(); err != nil {
		return false, fmt.Errorf("failed to start orchestrator process: %w", err)
	}

	return true, nil
}

// StopOrchestrator stops the workflow orchestrator via the aiwf native CLI.
// Uses: aiwf state reset
func (e *Executor) StopOrchestrator(ctx context.Context, projectPath string) (bool, error) {
	cmd, err := aiwfCommandContext(ctx, "state", "reset")
	if err != nil {
		return false, err
	}
	cmd.Dir = projectPath

	if err := cmd.Run(); err != nil {
		return false, fmt.Errorf("failed to run stop orchestrator command: %w", err)
	}

	return true, nil
}
