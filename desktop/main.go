package main

import (
	"context"
	"embed"
	"log"
	"os"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
	wails_runtime "github.com/wailsapp/wails/v2/pkg/runtime"
)

//go:embed all:frontend/dist
var assets embed.FS

//go:embed build/trayicon.png
var trayIconBytes []byte

func main() {
	app := NewApp()

	// Extract embedded icon to a temporary file for Cocoa status bar
	tempIconPath := ""
	tempIconFile, err := os.CreateTemp("", "aiwf_tray_icon_*.png")
	if err == nil {
		_, _ = tempIconFile.Write(trayIconBytes)
		tempIconPath = tempIconFile.Name()
		tempIconFile.Close()
		defer os.Remove(tempIconPath)
	} else {
		log.Println("Warning: Failed to extract tray icon to temp file:", err)
	}

	err = wails.Run(&options.App{
		Title:         "AIWF Framework",
		Width:         1280,
		Height:        800,
		DisableResize: true,
		MinWidth:      1280,
		MinHeight:     800,
		MaxWidth:      1280,
		MaxHeight:     800,
		Frameless:     true,
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{R: 15, G: 23, B: 42, A: 255},
		SingleInstanceLock: &options.SingleInstanceLock{
			UniqueId: "com.kyleit.aiwf-framework",
			OnSecondInstanceLaunch: func(secondInstanceData options.SecondInstanceData) {
				if app != nil && app.ctx != nil {
					wails_runtime.WindowShow(app.ctx)
					wails_runtime.WindowUnminimise(app.ctx)
				}
			},
		},
		OnStartup: func(ctx context.Context) {
			app.startup(ctx)
			if tempIconPath != "" {
				InitTray(tempIconPath)
			}
		},
		OnBeforeClose: func(ctx context.Context) bool {
			if reallyQuit {
				return false // Allow actual quit
			}
			// Hide the window and prevent termination
			wails_runtime.WindowHide(ctx)
			return true // Prevent close
		},
		Bind: []interface{}{
			app,
		},
	})

	if err != nil {
		log.Fatal("Error starting Wails Desktop App:", err.Error())
	}
}
