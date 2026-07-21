package infrastructure

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"time"

	"desktop/domain"

	"github.com/shirou/gopsutil/v3/process"
)

var ErrOrchestratorLocked = errors.New("orchestrator is currently locked by another active session")

type LockChecker struct{}

func NewLockChecker() *LockChecker {
	return &LockChecker{}
}

func (l *LockChecker) CheckLock(projectPath string) error {
	lockFilePath := filepath.Join(projectPath, ".agents", "runtime", "workflow.lock")
	leaseFilePath := filepath.Join(projectPath, ".agents", "runtime", "workflow-lease.json")

	if _, err := os.Stat(lockFilePath); os.IsNotExist(err) {
		return nil
	}

	leaseData, err := os.ReadFile(leaseFilePath)
	if err != nil {
		return ErrOrchestratorLocked
	}

	var lease domain.LeaseInfo
	if err := json.Unmarshal(leaseData, &lease); err != nil {
		return ErrOrchestratorLocked
	}

	if lease.PID > 0 {
		exists, err := process.PidExists(lease.PID)
		if err == nil && exists {
			t, err := time.Parse(time.RFC3339, lease.Timestamp)
			if err == nil {
				if time.Since(t) < 5*time.Minute {
					return ErrOrchestratorLocked
				}
			} else {
				return ErrOrchestratorLocked
			}
		}
	}

	return nil
}
