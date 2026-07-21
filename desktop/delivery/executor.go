package delivery

import (
	"context"
	"fmt"
	"path/filepath"
	"syscall"

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

func (e *Executor) StartOrchestrator(ctx context.Context, projectPath, skill, command string) (bool, error) {
	if err := e.lockChecker.CheckLock(projectPath); err != nil {
		return false, err
	}

	scriptPath := filepath.Join(projectPath, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")

	cmdArgs := []string{
		scriptPath,
		"start",
		"--skill", skill,
		"--command", command,
	}

	cmd, err := pythonCommandContext(ctx, cmdArgs...)
	if err != nil {
		return false, err
	}
	cmd.Dir = projectPath

	cmd.SysProcAttr = &syscall.SysProcAttr{
		Setpgid: true,
	}

	if err := cmd.Start(); err != nil {
		return false, fmt.Errorf("failed to start orchestrator process: %w", err)
	}

	return true, nil
}

func (e *Executor) StopOrchestrator(ctx context.Context, projectPath string) (bool, error) {
	scriptPath := filepath.Join(projectPath, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
	cmdArgs := []string{
		scriptPath,
		"stop",
	}

	cmd, err := pythonCommandContext(ctx, cmdArgs...)
	if err != nil {
		return false, err
	}
	cmd.Dir = projectPath
	cmd.SysProcAttr = &syscall.SysProcAttr{
		Setpgid: true,
	}

	if err := cmd.Run(); err != nil {
		return false, fmt.Errorf("failed to run stop orchestrator command: %w", err)
	}

	return true, nil
}
