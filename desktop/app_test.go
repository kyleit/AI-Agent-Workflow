package main

import (
	"testing"
)

func TestAppInitialization(t *testing.T) {
	app := NewApp()
	if app == nil {
		t.Fatal("NewApp() returned nil")
	}
}
