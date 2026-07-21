package main

import (
	"os"
	"testing"

	"desktop/infrastructure"
)

func TestRegistryOperations(t *testing.T) {
	reg, err := infrastructure.NewRegistry()
	if err != nil {
		t.Fatalf("Failed to create registry: %v", err)
	}

	originalPath := reg.ConfigPath
	tempFile, err := os.CreateTemp("", "projects_test.json")
	if err != nil {
		t.Fatalf("Failed to create temp config: %v", err)
	}
	tempPath := tempFile.Name()
	tempFile.Close()
	defer os.Remove(tempPath)

	reg.ConfigPath = tempPath
	defer func() { reg.ConfigPath = originalPath }()

	p, err := reg.RegisterProject("Test-Project", "E:/MockPath", 9091)
	if err != nil {
		t.Errorf("RegisterProject returned error: %v", err)
	}

	if p.Name != "Test-Project" || p.Port != 9091 {
		t.Errorf("Unexpected registered project values: %+v", p)
	}

	projects, err := reg.GetProjects()
	if err != nil {
		t.Errorf("GetProjects returned error: %v", err)
	}

	if len(projects) != 1 {
		t.Errorf("Expected 1 project, got %d", len(projects))
	}

	err = reg.DeleteProject(p.ID)
	if err != nil {
		t.Errorf("DeleteProject returned error: %v", err)
	}

	projects, err = reg.GetProjects()
	if err != nil {
		t.Errorf("GetProjects after delete failed: %v", err)
	}

	if len(projects) != 0 {
		t.Errorf("Expected 0 projects after delete, got %d", len(projects))
	}
}
