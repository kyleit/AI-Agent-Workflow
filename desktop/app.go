package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"

	infra_reg "desktop/infrastructure"
	"desktop/pkg/domain"
	"desktop/pkg/infra"

	"github.com/shirou/gopsutil/v3/process"
	wails_runtime "github.com/wailsapp/wails/v2/pkg/runtime"
)

var ErrProjectNotSelected = errors.New("no active project workspace selected")

const defaultFrameworkGitURL = "https://github.com/kyleit/AI-Agent-Workflow.git"

// App struct defines Wails bound methods for Frontend IPC calls.
type App struct {
	ctx                 context.Context
	workspaceRoot       string
	selectedProjectPath string
	registry            *infra_reg.Registry
}

var globalApp *App
var reallyQuit bool = false

// NewApp creates a new App application struct.
func NewApp() *App {
	reg, _ := infra_reg.NewRegistry()
	globalApp = &App{
		workspaceRoot: "..",
		registry:      reg,
	}
	return globalApp
}

// startup is called when the app starts.
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	abs, err := filepath.Abs(a.workspaceRoot)
	if err == nil {
		a.workspaceRoot = abs
	}
	if !isFrameworkSourceRoot(a.workspaceRoot) {
		if sourceRoot, err := globalFrameworkSourceRoot(); err == nil && isFrameworkSourceRoot(sourceRoot) {
			a.workspaceRoot = sourceRoot
		}
	}
}

// SelectProjectFolder opens a native folder dialog to let user select a folder.
func (a *App) SelectProjectFolder() (string, error) {
	options := wails_runtime.OpenDialogOptions{
		Title: "Select Project Directory",
	}
	dir, err := wails_runtime.OpenDirectoryDialog(a.ctx, options)
	if err != nil {
		return "", err
	}
	return dir, nil
}

func isDir(path string) bool {
	info, err := os.Stat(path)
	return err == nil && info.IsDir()
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func isFrameworkSourceRoot(path string) bool {
	if path == "" {
		return false
	}
	return fileExists(filepath.Join(path, "MANIFEST.json")) &&
		isDir(filepath.Join(path, "skills")) &&
		fileExists(filepath.Join(path, "bootstrap.sh"))
}

func globalFrameworkSourceRoot() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".aiwf", "framework-source"), nil
}

func projectCandidateKind(path string) string {
	if isDir(filepath.Join(path, ".agents")) {
		return "AIWF workspace"
	}
	if fileExists(filepath.Join(path, "AI_RULES.md")) || fileExists(filepath.Join(path, "AGENTS.md")) {
		return "Agent workspace"
	}
	if isDir(filepath.Join(path, ".git")) {
		return "Git project"
	}
	if fileExists(filepath.Join(path, "wails.json")) {
		return "Wails app"
	}
	if fileExists(filepath.Join(path, "go.mod")) {
		return "Go module"
	}
	if fileExists(filepath.Join(path, "package.json")) {
		return "Node project"
	}
	if fileExists(filepath.Join(path, "pyproject.toml")) {
		return "Python project"
	}
	return ""
}

func shouldSkipScanDir(path string, root string) bool {
	if path == root {
		return false
	}
	name := filepath.Base(path)
	if isTransientTempProject(path) {
		return true
	}
	switch name {
	case ".git", ".agents", "node_modules", "vendor", "dist", "build", ".svelte-kit", ".wails", "public_export", "_to_delete":
		return true
	}
	return strings.HasPrefix(name, ".") && name != ".config"
}

// ScanProjectFolders scans a selected root and returns likely project workspaces for user selection.
func (a *App) ScanProjectFolders(root string) ([]domain.ProjectCandidate, error) {
	if root == "" {
		return []domain.ProjectCandidate{}, nil
	}
	absRoot, err := filepath.Abs(root)
	if err != nil {
		return nil, fmt.Errorf("invalid scan root: %w", err)
	}
	if !isDir(absRoot) {
		return nil, fmt.Errorf("scan root is not a directory")
	}

	registered := map[string]bool{}
	projects, err := a.GetProjects()
	if err == nil {
		for _, project := range projects {
			registered[filepath.Clean(project.Path)] = true
		}
	}

	const maxDepth = 3
	candidates := []domain.ProjectCandidate{}
	seen := map[string]bool{}
	err = filepath.WalkDir(absRoot, func(path string, entry os.DirEntry, walkErr error) error {
		if walkErr != nil || !entry.IsDir() {
			return nil
		}
		cleanPath := filepath.Clean(path)
		if shouldSkipScanDir(cleanPath, absRoot) {
			return filepath.SkipDir
		}
		rel, err := filepath.Rel(absRoot, cleanPath)
		if err == nil && rel != "." {
			depth := len(strings.Split(rel, string(os.PathSeparator)))
			if depth > maxDepth {
				return filepath.SkipDir
			}
		}
		kind := projectCandidateKind(cleanPath)
		if kind == "" {
			return nil
		}
		if seen[cleanPath] {
			return filepath.SkipDir
		}
		seen[cleanPath] = true
		candidates = append(candidates, domain.ProjectCandidate{
			Name:       filepath.Base(cleanPath),
			Path:       cleanPath,
			Kind:       kind,
			Registered: registered[cleanPath],
		})
		return filepath.SkipDir
	})
	if err != nil {
		return nil, err
	}
	sort.Slice(candidates, func(i, j int) bool {
		if candidates[i].Registered != candidates[j].Registered {
			return !candidates[i].Registered
		}
		return strings.ToLower(candidates[i].Name) < strings.ToLower(candidates[j].Name)
	})
	return candidates, nil
}

// SelectProject sets the active project workspace.
func (a *App) SelectProject(path string) error {
	if path == "" {
		a.selectedProjectPath = ""
		return nil
	}
	absPath, err := filepath.Abs(path)
	if err != nil {
		return fmt.Errorf("invalid path: %w", err)
	}
	fi, err := os.Stat(absPath)
	if err != nil {
		return fmt.Errorf("project path does not exist: %w", err)
	}
	if !fi.IsDir() {
		return fmt.Errorf("project path is not a directory")
	}
	a.selectedProjectPath = absPath
	return nil
}

// GetSelectedProject returns the active project workspace path.
func (a *App) GetSelectedProject() (string, error) {
	return a.selectedProjectPath, nil
}

// GetWorkflowState fetches the latest runtime state from .agents/state/runtime.json in the selected project.
func (a *App) GetWorkflowState() (*domain.RuntimeState, error) {
	if a.selectedProjectPath == "" {
		return nil, ErrProjectNotSelected
	}
	targetPath := filepath.Join(a.selectedProjectPath, ".agents", "state", "runtime.json")
	data, err := infra.ReadStateFile(targetPath)
	if err != nil {
		// If file doesn't exist, return empty/idle state instead of failing, to let UI handle it gracefully
		if os.IsNotExist(err) {
			return &domain.RuntimeState{
				Status: domain.StatusIdle,
			}, nil
		}
		return nil, fmt.Errorf("failed to read runtime state file: %w", err)
	}

	var state domain.RuntimeState
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, fmt.Errorf("failed to parse runtime state JSON: %w", err)
	}

	return &state, nil
}

func (a *App) readManifestInfo() domain.FrameworkInfo {
	info := domain.FrameworkInfo{
		Name:       "AIWF Framework",
		Version:    "unknown",
		SourceRoot: a.workspaceRoot,
		Available:  isFrameworkSourceRoot(a.workspaceRoot),
	}
	if !info.Available {
		if sourceRoot, err := globalFrameworkSourceRoot(); err == nil {
			info.SourceRoot = sourceRoot
			info.Available = isFrameworkSourceRoot(sourceRoot)
		}
	}

	// Check if global CLI is installed
	_, err := exec.LookPath("aiwf")
	info.CLIInstalled = (err == nil)

	// Check if active project has AIWF installed
	if a.selectedProjectPath != "" {
		info.ProjectInstalled = isDir(filepath.Join(a.selectedProjectPath, ".agents"))
	} else {
		info.ProjectInstalled = false
	}

	if !info.Available {
		return info
	}
	manifestPath := filepath.Join(a.workspaceRoot, "MANIFEST.json")
	if !isFrameworkSourceRoot(a.workspaceRoot) {
		manifestPath = filepath.Join(info.SourceRoot, "MANIFEST.json")
	}
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return info
	}
	var manifest struct {
		Name       string `json:"name"`
		Version    string `json:"version"`
		Repository struct {
			URL string `json:"url"`
		} `json:"repository"`
	}
	if err := json.Unmarshal(data, &manifest); err != nil {
		return info
	}
	if manifest.Name != "" {
		info.Name = manifest.Name
	}
	if manifest.Version != "" {
		info.Version = manifest.Version
	}
	info.Repository = manifest.Repository.URL
	return info
}

// GetFrameworkInfo returns the installed AIWF framework source metadata.
func (a *App) GetFrameworkInfo() (domain.FrameworkInfo, error) {
	return a.readManifestInfo(), nil
}

func globalAIWFConfigPath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".aiwf", ".env.telegram-notify"), nil
}

func readTelegramEnv() map[string]string {
	cfg := map[string]string{}
	cfgPath, err := globalAIWFConfigPath()
	if err != nil {
		return cfg
	}
	data, err := os.ReadFile(cfgPath)
	if err != nil {
		return cfg
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") || !strings.Contains(line, "=") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		key := strings.TrimSpace(parts[0])
		value := strings.Trim(strings.TrimSpace(parts[1]), `"'`)
		cfg[key] = value
	}
	return cfg
}

// GetGlobalConfig returns global AIWF settings without exposing secret token values.
func (a *App) GetGlobalConfig() (domain.GlobalConfig, error) {
	cfg := readTelegramEnv()
	return domain.GlobalConfig{
		TelegramBotTokenConfigured: cfg["TELEGRAM_BOT_TOKEN"] != "",
		TelegramProxy:              cfg["TELEGRAM_PROXY"],
	}, nil
}

// SaveGlobalConfig updates global AIWF Telegram settings. Empty token preserves the current token.
func (a *App) SaveGlobalConfig(telegramBotToken string, telegramProxy string) (domain.GlobalConfig, error) {
	cfgPath, err := globalAIWFConfigPath()
	if err != nil {
		return domain.GlobalConfig{}, err
	}
	existing := readTelegramEnv()
	token := strings.TrimSpace(telegramBotToken)
	if token == "" {
		token = existing["TELEGRAM_BOT_TOKEN"]
	}
	proxy := strings.TrimSpace(telegramProxy)
	if token == "" {
		return domain.GlobalConfig{}, fmt.Errorf("telegram bot token is required")
	}
	if err := os.MkdirAll(filepath.Dir(cfgPath), 0700); err != nil {
		return domain.GlobalConfig{}, err
	}
	lines := []string{
		fmt.Sprintf("TELEGRAM_BOT_TOKEN=%q", token),
	}
	if proxy != "" {
		lines = append(lines, fmt.Sprintf("TELEGRAM_PROXY=%q", proxy))
	}
	if err := os.WriteFile(cfgPath, []byte(strings.Join(lines, "\n")+"\n"), 0600); err != nil {
		return domain.GlobalConfig{}, err
	}
	return a.GetGlobalConfig()
}

func (a *App) ensureFrameworkSource() (string, error) {
	if isFrameworkSourceRoot(a.workspaceRoot) {
		return a.workspaceRoot, nil
	}
	sourceRoot, err := globalFrameworkSourceRoot()
	if err != nil {
		return "", err
	}
	if isFrameworkSourceRoot(sourceRoot) {
		a.workspaceRoot = sourceRoot
		return sourceRoot, nil
	}
	if err := os.MkdirAll(filepath.Dir(sourceRoot), 0700); err != nil {
		return "", err
	}
	cmd := exec.Command("git", "clone", "--depth", "1", defaultFrameworkGitURL, sourceRoot)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("failed to clone AIWF framework source: %w (output: %s)", err, string(out))
	}
	if !isFrameworkSourceRoot(sourceRoot) {
		return "", fmt.Errorf("cloned source is missing required AIWF framework files")
	}
	a.workspaceRoot = sourceRoot
	return sourceRoot, nil
}

func scriptForPlatform(sourceRoot string, baseName string) (string, []string) {
	if strings.EqualFold(os.Getenv("OS"), "Windows_NT") {
		return "powershell", []string{"-NoProfile", "-ExecutionPolicy", "Bypass", "-File", filepath.Join(sourceRoot, baseName+".ps1")}
	}
	return "bash", []string{filepath.Join(sourceRoot, baseName+".sh")}
}

// InstallFramework bootstraps the global AIWF CLI and installs AIWF into the selected project when available.
func (a *App) InstallFramework() (*domain.CommandResult, error) {
	sourceRoot, err := a.ensureFrameworkSource()
	if err != nil {
		return nil, err
	}
	logs := []string{fmt.Sprintf("Framework source: %s", sourceRoot)}
	exitCode := 0
	success := true

	bootstrapBin, bootstrapArgs := scriptForPlatform(sourceRoot, "bootstrap")
	bootstrapCmd := exec.Command(bootstrapBin, bootstrapArgs...)
	bootstrapCmd.Dir = sourceRoot
	bootstrapOut, bootstrapErr := bootstrapCmd.CombinedOutput()
	logs = append(logs, string(bootstrapOut))
	if bootstrapErr != nil {
		success = false
		if exitErr, ok := bootstrapErr.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			exitCode = -1
		}
		return &domain.CommandResult{Stdout: strings.Join(logs, "\n"), ExitCode: exitCode, Success: success}, nil
	}

	if a.selectedProjectPath != "" {
		installBin, installArgs := scriptForPlatform(sourceRoot, "install")
		installArgs = append(installArgs, "--force")
		installCmd := exec.Command(installBin, installArgs...)
		installCmd.Dir = a.selectedProjectPath
		installOut, installErr := installCmd.CombinedOutput()
		logs = append(logs, string(installOut))
		if installErr != nil {
			success = false
			if exitErr, ok := installErr.(*exec.ExitError); ok {
				exitCode = exitErr.ExitCode()
			} else {
				exitCode = -1
			}
		}
	}
	return &domain.CommandResult{Stdout: strings.Join(logs, "\n"), ExitCode: exitCode, Success: success}, nil
}

// UpdateFrameworkSource updates the AIWF framework/skills source, not the desktop app.
func (a *App) UpdateFrameworkSource() (*domain.CommandResult, error) {
	sourceRoot, err := a.ensureFrameworkSource()
	if err != nil {
		return nil, err
	}
	scriptPath := filepath.Join(sourceRoot, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
	cmd, err := pythonCommand(scriptPath, "update-source", "--yes")
	if err != nil {
		return nil, err
	}
	cmd.Dir = sourceRoot
	out, err := cmd.CombinedOutput()
	exitCode := 0
	if err != nil {
		var exitErr *exec.ExitError
		if errors.As(err, &exitErr) {
			exitCode = exitErr.ExitCode()
		} else {
			exitCode = -1
		}
	}
	return &domain.CommandResult{
		Stdout:   string(out),
		Stderr:   "",
		ExitCode: exitCode,
		Success:  err == nil,
	}, nil
}

// RunCoordinatorTick triggers python coordinator.py tick in the selected project workspace.
func (a *App) RunCoordinatorTick(prompt string) (string, error) {
	if a.selectedProjectPath == "" {
		return "", ErrProjectNotSelected
	}
	scriptPath := filepath.Join(a.workspaceRoot, "skills", "workflow-coordinator", "scripts", "coordinator.py")
	cmd, err := pythonCommand(scriptPath, "tick", "--prompt", prompt)
	if err != nil {
		return "", err
	}
	cmd.Dir = a.selectedProjectPath
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("coordinator tick failed: %w (output: %s)", err, string(out))
	}
	return string(out), nil
}

// SubmitPromptResponse submits a response to the active AIWF prompt gate in the selected project workspace.
func (a *App) SubmitPromptResponse(response string) (string, error) {
	if a.selectedProjectPath == "" {
		return "", ErrProjectNotSelected
	}
	scriptPath := filepath.Join(a.workspaceRoot, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
	cmd, err := pythonCommand(scriptPath, "prompt", "response", "--value", response)
	if err != nil {
		return "", err
	}
	cmd.Dir = a.selectedProjectPath
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("prompt response submit failed: %w (output: %s)", err, string(out))
	}
	return string(out), nil
}

// RunGenericCommand runs a command via workflow_runtime.py in the selected project workspace.
func (a *App) RunGenericCommand(cmdGroup string, cmdSub string, extraArgs []string) (*domain.CommandResult, error) {
	// If it's a project registry action, we can bypass the project selection check or handle it in Go.
	if cmdGroup != "project/registry" && a.selectedProjectPath == "" {
		return nil, ErrProjectNotSelected
	}

	scriptPath := filepath.Join(a.workspaceRoot, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
	args := []string{scriptPath, cmdGroup, cmdSub}
	args = append(args, extraArgs...)

	cmd, err := pythonCommand(args...)
	if err != nil {
		return nil, err
	}
	if a.selectedProjectPath != "" {
		cmd.Dir = a.selectedProjectPath
	} else {
		cmd.Dir = a.workspaceRoot
	}

	out, err := cmd.CombinedOutput()
	exitCode := 0
	if err != nil {
		var exitErr *exec.ExitError
		if errors.As(err, &exitErr) {
			exitCode = exitErr.ExitCode()
		} else {
			exitCode = -1
		}
	}

	return &domain.CommandResult{
		Stdout:   string(out),
		Stderr:   "",
		ExitCode: exitCode,
		Success:  err == nil,
	}, nil
}

func isTransientTempProject(path string) bool {
	cleanPath := filepath.Clean(path)
	slashPath := filepath.ToSlash(cleanPath)
	baseName := filepath.Base(cleanPath)
	isMacTempRoot := strings.Contains(slashPath, "/private/var/folders/") || strings.Contains(slashPath, "/var/folders/")
	return isMacTempRoot && strings.Contains(slashPath, "/T/") && strings.HasPrefix(baseName, "tmp")
}

// GetProjects lists registered projects.
func (a *App) GetProjects() ([]domain.Project, error) {
	if a.registry == nil {
		var err error
		a.registry, err = infra_reg.NewRegistry()
		if err != nil {
			return nil, err
		}
	}
	projects, err := a.registry.GetProjects()
	if err != nil {
		return nil, err
	}
	groupTitles := a.loadDiscoveredTelegramGroups()
	domainProjects := make([]domain.Project, 0, len(projects))
	for _, p := range projects {
		if isTransientTempProject(p.Path) {
			continue
		}
		telegramTitle := ""
		if p.TelegramChatID != "" {
			telegramTitle = groupTitles[p.TelegramChatID]
		}
		domainProjects = append(domainProjects, domain.Project{
			ID:             p.ID,
			Name:           p.Name,
			Path:           p.Path,
			Port:           p.Port,
			RegisteredAt:   "Registered",
			Active:         p.Path == a.selectedProjectPath,
			AIWFVersion:    p.AIWFVersion,
			Status:         p.Status,
			TelegramChatID: p.TelegramChatID,
			TelegramTitle:  telegramTitle,
		})
	}
	return domainProjects, nil
}

func (a *App) loadDiscoveredTelegramGroups() map[string]string {
	home, err := os.UserHomeDir()
	if err != nil {
		return map[string]string{}
	}
	path := filepath.Join(home, ".aiwf", "discovered_groups.json")
	data, err := os.ReadFile(path)
	if err != nil {
		return map[string]string{}
	}
	var groups map[string]string
	if err := json.Unmarshal(data, &groups); err != nil {
		return map[string]string{}
	}
	return groups
}

// AddProject registers a project.
func (a *App) AddProject(name string, path string) error {
	if a.registry == nil {
		var err error
		a.registry, err = infra_reg.NewRegistry()
		if err != nil {
			return err
		}
	}
	absPath, err := filepath.Abs(path)
	if err != nil {
		return err
	}
	if isTransientTempProject(absPath) {
		return fmt.Errorf("temporary system directories cannot be registered as AIWF projects")
	}
	_, err = a.registry.RegisterProject(name, absPath, 9090)
	return err
}

// DeleteProject deletes a project from registry.
func (a *App) DeleteProject(id string) error {
	if a.registry == nil {
		var err error
		a.registry, err = infra_reg.NewRegistry()
		if err != nil {
			return err
		}
	}
	return a.registry.DeleteProject(id)
}

// SearchMemory searches the project RAG memory database.
func (a *App) SearchMemory(query string) ([]domain.MemoryMatch, error) {
	if a.selectedProjectPath == "" {
		return nil, ErrProjectNotSelected
	}
	scriptPath := filepath.Join(a.workspaceRoot, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
	cmd, err := pythonCommand(scriptPath, "memory", "search", query)
	if err != nil {
		return nil, err
	}
	cmd.Dir = a.selectedProjectPath
	out, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("memory search failed: %w (output: %s)", err, string(out))
	}

	var result map[string]interface{}
	if err := json.Unmarshal(out, &result); err == nil {
		if matchesRaw, ok := result["matches"]; ok {
			if matchesList, ok := matchesRaw.([]interface{}); ok {
				var matches []domain.MemoryMatch
				for _, item := range matchesList {
					if mObj, ok := item.(map[string]interface{}); ok {
						file, _ := mObj["file"].(string)
						score, _ := mObj["score"].(string)
						if score == "" {
							if scoreNum, ok := mObj["score"].(float64); ok {
								score = fmt.Sprintf("%.2f", scoreNum)
							}
						}
						match, _ := mObj["match"].(string)
						matches = append(matches, domain.MemoryMatch{
							File:  file,
							Score: score,
							Match: match,
						})
					}
				}
				return matches, nil
			}
		}
		summary, _ := result["summary"].(string)
		if summary == "" {
			summary = fmt.Sprintf("%v", result)
		}
		return []domain.MemoryMatch{
			{File: "Summary", Score: "1.00", Match: summary},
		}, nil
	}

	return []domain.MemoryMatch{
		{File: "Raw Output", Score: "0.00", Match: string(out)},
	}, nil
}

// RunDoctor calls live workspace doctor in active project.
func (a *App) RunDoctor() (*domain.DoctorReport, error) {
	if a.selectedProjectPath == "" {
		return nil, ErrProjectNotSelected
	}
	scriptPath := filepath.Join(a.workspaceRoot, "skills", "workflow-runtime", "scripts", "workspace_doctor.py")
	cmd, err := pythonCommand(scriptPath)
	if err != nil {
		return nil, err
	}
	cmd.Dir = a.selectedProjectPath
	out, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("doctor run failed: %w (output: %s)", err, string(out))
	}
	var report domain.DoctorReport
	if err := json.Unmarshal(out, &report); err != nil {
		return nil, fmt.Errorf("failed to parse doctor report: %w (raw output: %s)", err, string(out))
	}
	return &report, nil
}

// CheckDaemonStatus checks PID file & process status for telegram and runtime daemons.
func (a *App) CheckDaemonStatus(daemonType string) (string, error) {
	var pidFile string
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get home dir: %w", err)
	}

	if daemonType == "telegram" {
		pidFile = filepath.Join(home, ".aiwf", "telegram-daemon.pid")
	} else if daemonType == "runtime" {
		pidFile = filepath.Join(home, ".aiwf", "runtime.pid")
	} else {
		return "", fmt.Errorf("unknown daemon type: %s", daemonType)
	}

	if _, err := os.Stat(pidFile); os.IsNotExist(err) {
		return "STOPPED", nil
	}

	data, err := os.ReadFile(pidFile)
	if err != nil {
		return "STOPPED", nil
	}

	var pid int
	_, err = fmt.Sscanf(strings.TrimSpace(string(data)), "%d", &pid)
	if err != nil {
		return "STOPPED", nil
	}

	exists, err := process.PidExists(int32(pid))
	if err != nil || !exists {
		return "STOPPED", nil
	}

	return fmt.Sprintf("RUNNING (PID: %d)", pid), nil
}

// StartDaemon starts a daemon.
func (a *App) StartDaemon(daemonType string) (string, error) {
	if a.selectedProjectPath == "" {
		return "", ErrProjectNotSelected
	}
	scriptPath := filepath.Join(a.workspaceRoot, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
	cmd, err := pythonCommand(scriptPath, daemonType, "start")
	if err != nil {
		return "", err
	}
	cmd.Dir = a.selectedProjectPath
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("failed to start daemon: %w (output: %s)", err, string(out))
	}
	return string(out), nil
}

// StopDaemon stops a daemon.
func (a *App) StopDaemon(daemonType string) (string, error) {
	if a.selectedProjectPath == "" {
		return "", ErrProjectNotSelected
	}
	scriptPath := filepath.Join(a.workspaceRoot, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
	cmd, err := pythonCommand(scriptPath, daemonType, "stop")
	if err != nil {
		return "", err
	}
	cmd.Dir = a.selectedProjectPath
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("failed to stop daemon: %w (output: %s)", err, string(out))
	}
	return string(out), nil
}

// RestartDaemon restarts a daemon.
func (a *App) RestartDaemon(daemonType string) (string, error) {
	if a.selectedProjectPath == "" {
		return "", ErrProjectNotSelected
	}
	scriptPath := filepath.Join(a.workspaceRoot, "skills", "workflow-runtime", "scripts", "workflow_runtime.py")
	cmd, err := pythonCommand(scriptPath, daemonType, "restart")
	if err != nil {
		return "", err
	}
	cmd.Dir = a.selectedProjectPath
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("failed to restart daemon: %w (output: %s)", err, string(out))
	}
	return string(out), nil
}

// ScanTelegramConversations retrieves discovered groups and latest updates from Telegram Bot API.
func (a *App) ScanTelegramConversations() ([]domain.TelegramConversation, error) {
	cfg := readTelegramEnv()
	token := cfg["TELEGRAM_BOT_TOKEN"]
	if token == "" {
		return nil, fmt.Errorf("TELEGRAM_BOT_TOKEN is not configured. Please set it in System configuration")
	}

	// 1. Gộp cache đã lưu trước
	groups := map[string]domain.TelegramConversation{}
	discovered := a.loadDiscoveredTelegramGroups()
	for id, title := range discovered {
		groups[id] = domain.TelegramConversation{
			ChatID:   id,
			Title:    title,
			Type:     "group",
			LastSeen: "Daemon Cache",
			Source:   "Discovered Cache",
		}
	}

	// 2. Gọi API getUpdates của Telegram để phát hiện thêm
	client := &http.Client{Timeout: 5 * time.Second}
	if proxyStr := cfg["TELEGRAM_PROXY"]; proxyStr != "" {
		proxyURL, err := url.Parse(proxyStr)
		if err == nil {
			client.Transport = &http.Transport{
				Proxy: http.ProxyURL(proxyURL),
			}
		}
	}

	apiURL := fmt.Sprintf("https://api.telegram.org/bot%s/getUpdates?offset=-100&limit=100&timeout=2", token)
	resp, err := client.Get(apiURL)
	if err == nil {
		defer resp.Body.Close()
		var tgResp struct {
			Ok     bool `json:"ok"`
			Result []struct {
				Message *struct {
					Chat struct {
						ID        int64  `json:"id"`
						Title     string `json:"title"`
						Type      string `json:"type"`
						FirstName string `json:"first_name"`
						LastName  string `json:"last_name"`
						Username  string `json:"username"`
					} `json:"chat"`
					Date int64 `json:"date"`
				} `json:"message"`
				EditedMessage *struct {
					Chat struct {
						ID        int64  `json:"id"`
						Title     string `json:"title"`
						Type      string `json:"type"`
						FirstName string `json:"first_name"`
						LastName  string `json:"last_name"`
						Username  string `json:"username"`
					} `json:"chat"`
					Date int64 `json:"date"`
				} `json:"edited_message"`
				ChannelPost *struct {
					Chat struct {
						ID        int64  `json:"id"`
						Title     string `json:"title"`
						Type      string `json:"type"`
						FirstName string `json:"first_name"`
						LastName  string `json:"last_name"`
						Username  string `json:"username"`
					} `json:"chat"`
					Date int64 `json:"date"`
				} `json:"channel_post"`
				EditedChannelPost *struct {
					Chat struct {
						ID        int64  `json:"id"`
						Title     string `json:"title"`
						Type      string `json:"type"`
						FirstName string `json:"first_name"`
						LastName  string `json:"last_name"`
						Username  string `json:"username"`
					} `json:"chat"`
					Date int64 `json:"date"`
				} `json:"edited_channel_post"`
				MyChatMember *struct {
					Chat struct {
						ID        int64  `json:"id"`
						Title     string `json:"title"`
						Type      string `json:"type"`
						FirstName string `json:"first_name"`
						LastName  string `json:"last_name"`
						Username  string `json:"username"`
					} `json:"chat"`
					Date int64 `json:"date"`
				} `json:"my_chat_member"`
			} `json:"result"`
		}

		if errDec := json.NewDecoder(resp.Body).Decode(&tgResp); errDec == nil && tgResp.Ok {
			// Duyệt qua kết quả từ getUpdates
			for _, item := range tgResp.Result {
				var chatInfo struct {
					ID        int64
					Title     string
					Type      string
					FirstName string
					LastName  string
					Username  string
				}
				var hasChat bool
				var date int64

				if item.Message != nil {
					chatInfo.ID = item.Message.Chat.ID
					chatInfo.Title = item.Message.Chat.Title
					chatInfo.Type = item.Message.Chat.Type
					chatInfo.FirstName = item.Message.Chat.FirstName
					chatInfo.LastName = item.Message.Chat.LastName
					chatInfo.Username = item.Message.Chat.Username
					date = item.Message.Date
					hasChat = true
				} else if item.EditedMessage != nil {
					chatInfo.ID = item.EditedMessage.Chat.ID
					chatInfo.Title = item.EditedMessage.Chat.Title
					chatInfo.Type = item.EditedMessage.Chat.Type
					chatInfo.FirstName = item.EditedMessage.Chat.FirstName
					chatInfo.LastName = item.EditedMessage.Chat.LastName
					chatInfo.Username = item.EditedMessage.Chat.Username
					date = item.EditedMessage.Date
					hasChat = true
				} else if item.ChannelPost != nil {
					chatInfo.ID = item.ChannelPost.Chat.ID
					chatInfo.Title = item.ChannelPost.Chat.Title
					chatInfo.Type = item.ChannelPost.Chat.Type
					chatInfo.FirstName = item.ChannelPost.Chat.FirstName
					chatInfo.LastName = item.ChannelPost.Chat.LastName
					chatInfo.Username = item.ChannelPost.Chat.Username
					date = item.ChannelPost.Date
					hasChat = true
				} else if item.EditedChannelPost != nil {
					chatInfo.ID = item.EditedChannelPost.Chat.ID
					chatInfo.Title = item.EditedChannelPost.Chat.Title
					chatInfo.Type = item.EditedChannelPost.Chat.Type
					chatInfo.FirstName = item.EditedChannelPost.Chat.FirstName
					chatInfo.LastName = item.EditedChannelPost.Chat.LastName
					chatInfo.Username = item.EditedChannelPost.Chat.Username
					date = item.EditedChannelPost.Date
					hasChat = true
				} else if item.MyChatMember != nil {
					chatInfo.ID = item.MyChatMember.Chat.ID
					chatInfo.Title = item.MyChatMember.Chat.Title
					chatInfo.Type = item.MyChatMember.Chat.Type
					chatInfo.FirstName = item.MyChatMember.Chat.FirstName
					chatInfo.LastName = item.MyChatMember.Chat.LastName
					chatInfo.Username = item.MyChatMember.Chat.Username
					date = item.MyChatMember.Date
					hasChat = true
				}

				if hasChat {
					chatStrID := fmt.Sprintf("%d", chatInfo.ID)
					title := chatInfo.Title
					if title == "" {
						if chatInfo.FirstName != "" || chatInfo.LastName != "" {
							title = strings.TrimSpace(fmt.Sprintf("%s %s", chatInfo.FirstName, chatInfo.LastName))
						} else {
							title = chatInfo.Username
						}
					}
					if title == "" {
						title = fmt.Sprintf("Chat ID: %s", chatStrID)
					}

					lastSeen := "Active"
					if date > 0 {
						t := time.Unix(date, 0)
						lastSeen = t.Format("15:04:05 02/01/2006")
					}

					groups[chatStrID] = domain.TelegramConversation{
						ChatID:   chatStrID,
						Title:    title,
						Type:     chatInfo.Type,
						LastSeen: lastSeen,
						Source:   "Telegram API",
					}

					// Cập nhật lại cache file cho daemon (chỉ lưu các group chat)
					if chatInfo.Type == "group" || chatInfo.Type == "supergroup" {
						if discovered[chatStrID] != title {
							discovered[chatStrID] = title
						}
					}
				}
			}

			// Lưu lại cache đã cập nhật
			if len(discovered) > 0 {
				home, errH := os.UserHomeDir()
				if errH == nil {
					discPath := filepath.Join(home, ".aiwf", "discovered_groups.json")
					if data, errM := json.MarshalIndent(discovered, "", "  "); errM == nil {
						_ = os.WriteFile(discPath, data, 0644)
					}
				}
			}
		}
	}

	// 3. Enrich conversations with registered projects info
	projects, _ := a.GetProjects()
	for id, conv := range groups {
		for _, p := range projects {
			if p.TelegramChatID == conv.ChatID {
				conv.LinkedProjectID = p.ID
				conv.LinkedProjectName = p.Name
				conv.LinkedProjectPath = p.Path

				isCurrent := false
				if a.selectedProjectPath != "" && filepath.Clean(p.Path) == filepath.Clean(a.selectedProjectPath) {
					isCurrent = true
				}

				if isCurrent {
					conv.LinkedToCurrentProject = true
				} else {
					conv.LinkedToOtherProject = true
				}

				groups[id] = conv
				break
			}
		}
	}

	// 4. Trả về kết quả dưới dạng slice
	res := make([]domain.TelegramConversation, 0, len(groups))
	for _, conv := range groups {
		res = append(res, conv)
	}

	// Sắp xếp theo title
	sort.Slice(res, func(i, j int) bool {
		return res[i].Title < res[j].Title
	})

	return res, nil
}

// UnlinkTelegramConversation unlinks a Telegram conversation from a project.
func (a *App) UnlinkTelegramConversation(chatID string, projectID string) error {
	if a.registry == nil {
		var err error
		a.registry, err = infra_reg.NewRegistry()
		if err != nil {
			return err
		}
	}
	if err := a.registry.UnlinkTelegramConversation(chatID, projectID); err != nil {
		return err
	}
	return nil
}
