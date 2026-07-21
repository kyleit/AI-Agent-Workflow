package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"desktop/delivery"
	"desktop/infrastructure"
)

type MockLockChecker struct {
	shouldLock bool
}

func (m *MockLockChecker) CheckLock(projectPath string) error {
	if m.shouldLock {
		return infrastructure.ErrOrchestratorLocked
	}
	return nil
}

func TestExecutorStartLockEnforcement(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "exec_test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	os.MkdirAll(filepath.Join(tempDir, "skills", "workflow-runtime", "scripts"), 0755)
	os.WriteFile(filepath.Join(tempDir, "skills", "workflow-runtime", "scripts", "workflow_runtime.py"), []byte("# Mock python script"), 0644)

	lc := infrastructure.NewLockChecker()
	executor := delivery.NewExecutor(lc)

	lockDir := filepath.Join(tempDir, ".agents", "runtime")
	os.MkdirAll(lockDir, 0755)
	os.WriteFile(filepath.Join(lockDir, "workflow.lock"), []byte("locked"), 0644)
	leaseContent := fmt.Sprintf(`{"pid": %d, "timestamp": "%s"}`, os.Getpid(), time.Now().Format(time.RFC3339))
	os.WriteFile(filepath.Join(lockDir, "workflow-lease.json"), []byte(leaseContent), 0644)

	ctx := context.Background()
	success, err := executor.StartOrchestrator(ctx, tempDir, "brainstorming", "brainstorm")

	if success {
		t.Error("Expected StartOrchestrator to fail because of active lock, but got success")
	}

	if !errors.Is(err, infrastructure.ErrOrchestratorLocked) {
		t.Errorf("Expected ErrOrchestratorLocked, got: %v", err)
	}

	os.Remove(filepath.Join(lockDir, "workflow.lock")) // Release physical lock

	success, err = executor.StartOrchestrator(ctx, tempDir, "brainstorming", "brainstorm")
	if errors.Is(err, infrastructure.ErrOrchestratorLocked) {
		t.Error("Expected ErrOrchestratorLocked to be resolved, but still got it")
	}
}
