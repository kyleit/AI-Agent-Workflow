package domain

import "time"

// WorkflowStatus represents the current status of the AIWF runtime.
type WorkflowStatus string

const (
	StatusIdle       WorkflowStatus = "idle"
	StatusInProgress WorkflowStatus = "in_progress"
	StatusCompleted  WorkflowStatus = "completed"
	StatusWaiting    WorkflowStatus = "waiting_for_approval"
	StatusFailed     WorkflowStatus = "failed"
)

// RuntimeState holds the snapshot of .agents/state/runtime.json
type RuntimeState struct {
	CurrentSkill   string         `json:"current_skill"`   // Active skill name (e.g. quick-feature)
	CurrentCommand string         `json:"current_command"` // Active command
	CurrentStep    string         `json:"current_step"`    // Human-readable current step
	Status         WorkflowStatus `json:"status"`          // Current execution status
	Checkpoint     int            `json:"checkpoint"`      // Current workflow checkpoint (1-10)
	UpdatedAt      time.Time      `json:"updated_at"`      // Last update timestamp
}

// PromptGate holds pending prompt select user interaction request
type PromptGate struct {
	Question string   `json:"question"` // Question prompt (e.g. Approve Blueprint?)
	Options  []string `json:"options"`  // Options list (e.g. ["Continue", "Cancel"])
	Default  string   `json:"default"`  // Default fallback option
	Pending  bool     `json:"pending"`  // Whether prompt is currently active
}

// Project represents a workspace project managed by AIWF.
type Project struct {
	ID             string `json:"id"`
	Name           string `json:"name"`
	Path           string `json:"path"`
	Port           int    `json:"port"`
	RegisteredAt   string `json:"registered_at"`
	Active         bool   `json:"active"`
	AIWFVersion    string `json:"aiwf_version,omitempty"`
	Status         string `json:"status,omitempty"`
	TelegramChatID string `json:"telegram_chat_id,omitempty"`
	TelegramTitle  string `json:"telegram_title,omitempty"`
}

// ProjectCandidate represents a workspace discovered by folder scanning.
type ProjectCandidate struct {
	Name       string `json:"name"`
	Path       string `json:"path"`
	Kind       string `json:"kind"`
	Registered bool   `json:"registered"`
}

// GlobalConfig represents global AIWF settings stored outside a project.
type GlobalConfig struct {
	TelegramBotTokenConfigured bool   `json:"telegram_bot_token_configured"`
	TelegramProxy              string `json:"telegram_proxy"`
}

// CommandResult represents the outcome of running a subprocess command.
type CommandResult struct {
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
	ExitCode int    `json:"exit_code"`
	Success  bool   `json:"success"`
}

// MemoryMatch represents a RAG memory search result.
type MemoryMatch struct {
	File  string `json:"file"`
	Score string `json:"score"`
	Match string `json:"match"`
}

// DoctorReport represents the workspace doctor verification results.
type DoctorReport struct {
	Status      string            `json:"status"`
	Environment map[string]string `json:"environment"`
	Toolchain   map[string]any    `json:"toolchain"`
}

// FrameworkInfo describes the AIWF framework source managed by the desktop app.
type FrameworkInfo struct {
	Name             string `json:"name"`
	Version          string `json:"version"`
	Repository       string `json:"repository"`
	SourceRoot       string `json:"source_root"`
	Available        bool   `json:"available"`
	CLIInstalled     bool   `json:"cli_installed"`
	ProjectInstalled bool   `json:"project_installed"`
}

// TelegramConversation represents a conversation/group discovered for Telegram link selection.
type TelegramConversation struct {
	ChatID                 string `json:"chat_id"`
	Title                  string `json:"title"`
	Type                   string `json:"type,omitempty"`
	LastSeen               string `json:"last_seen,omitempty"`
	Source                 string `json:"source,omitempty"`
	LinkedProjectID        string `json:"linked_project_id,omitempty"`
	LinkedProjectName      string `json:"linked_project_name,omitempty"`
	LinkedProjectPath      string `json:"linked_project_path,omitempty"`
	LinkedToCurrentProject bool   `json:"linked_to_current_project"`
	LinkedToOtherProject   bool   `json:"linked_to_other_project"`
}
