//go:build !darwin

package main

func InitTray(iconPath string) {
	// No-op stub for non-darwin OS (Windows/Linux)
}
