package infrastructure

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"

	"desktop/domain"
)

type Config struct {
	Projects []domain.Project `json:"projects"`
}

type Registry struct {
	mu         sync.RWMutex
	ConfigPath string
}

func NewRegistry() (*Registry, error) {
	configDir, err := os.UserConfigDir()
	if err != nil {
		configDir = os.Getenv("USERPROFILE")
		if configDir == "" {
			configDir = "."
		}
	}

	aiwfDir := filepath.Join(configDir, "aiwf")
	if err := os.MkdirAll(aiwfDir, 0755); err != nil {
		return nil, err
	}

	return &Registry{
		ConfigPath: filepath.Join(aiwfDir, "projects.json"),
	}, nil
}

func (r *Registry) loadConfig() (Config, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var cfg Config
	if _, err := os.Stat(r.ConfigPath); os.IsNotExist(err) {
		cfg.Projects = []domain.Project{}
		return cfg, nil
	}

	data, err := os.ReadFile(r.ConfigPath)
	if err != nil {
		return cfg, err
	}

	if len(data) == 0 {
		cfg.Projects = []domain.Project{}
		return cfg, nil
	}

	if err := json.Unmarshal(data, &cfg); err != nil {
		return cfg, err
	}

	if cfg.Projects == nil {
		cfg.Projects = []domain.Project{}
	}

	return cfg, nil
}

func (r *Registry) saveConfig(cfg Config) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(r.ConfigPath, data, 0644)
}

func (r *Registry) RegisterProject(name, path string, port int) (domain.Project, error) {
	cfg, err := r.loadConfig()
	if err != nil {
		return domain.Project{}, err
	}

	id := name + "-" + string(rune(len(cfg.Projects)))

	project := domain.Project{
		ID:   id,
		Name: name,
		Path: path,
		Port: port,
	}

	cfg.Projects = append(cfg.Projects, project)
	if err := r.saveConfig(cfg); err != nil {
		return domain.Project{}, err
	}

	return project, nil
}

func (r *Registry) GetProjects() ([]domain.Project, error) {
	cfg, err := r.loadConfig()
	if err != nil {
		return nil, err
	}
	return cfg.Projects, nil
}

func (r *Registry) DeleteProject(id string) error {
	cfg, err := r.loadConfig()
	if err != nil {
		return err
	}

	newProjects := []domain.Project{}
	for _, p := range cfg.Projects {
		if p.ID != id {
			newProjects = append(newProjects, p)
		}
	}

	cfg.Projects = newProjects
	return r.saveConfig(cfg)
}

func (r *Registry) UnlinkTelegramConversation(chatID, projectID string) error {
	cfg, err := r.loadConfig()
	if err != nil {
		return err
	}

	for i, p := range cfg.Projects {
		if p.ID == projectID && p.TelegramChatID == chatID {
			cfg.Projects[i].TelegramChatID = ""
			cfg.Projects[i].TelegramTitle = ""
		}
	}

	return r.saveConfig(cfg)
}
