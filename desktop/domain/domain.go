package domain

import (
	"context"
)

// Project represents a workspace project managed by AIWF.
type Project struct {
	ID             string `json:"id"`
	Name           string `json:"name"`
	Path           string `json:"path"`
	Port           int    `json:"port"`
	AIWFVersion    string `json:"aiwf_version,omitempty"`
	Status         string `json:"status,omitempty"`
	TelegramChatID string `json:"telegram_chat_id,omitempty"`
	TelegramTitle  string `json:"telegram_title,omitempty"`
}

// LeaseInfo contains information about the active locks.
type LeaseInfo struct {
	Owner     string `json:"owner"`
	Skill     string `json:"skill"`
	Command   string `json:"command"`
	PID       int32  `json:"pid"`
	Timestamp string `json:"timestamp"`
}

// LockChecker defines the port for lock verification.
type LockChecker interface {
	CheckLock(projectPath string) error
}

// Registry defines the port for project registration storage.
type Registry interface {
	RegisterProject(name, path string, port int) (Project, error)
	GetProjects() ([]Project, error)
	DeleteProject(id string) error
}

// Notifier defines the port for local OS notifications.
type Notifier interface {
	SendNotification(title, message string) error
}

// Executor defines the port for starting and stopping workflow runtimes.
type Executor interface {
	StartOrchestrator(ctx context.Context, projectPath, skill, command string) (bool, error)
	StopOrchestrator(ctx context.Context, projectPath string) (bool, error)
}
