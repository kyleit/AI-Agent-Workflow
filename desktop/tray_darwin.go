//go:build darwin

package main

/*
#cgo LDFLAGS: -framework Cocoa
#include <stdlib.h>

void initSystray(const char* iconPath);
*/
import "C"
import (
	"log"
	"path/filepath"
	"unsafe"

	wails_runtime "github.com/wailsapp/wails/v2/pkg/runtime"
)

//export trayCallbackShow
func trayCallbackShow() {
	if globalApp != nil && globalApp.ctx != nil {
		wails_runtime.WindowShow(globalApp.ctx)
	}
}

//export trayCallbackHide
func trayCallbackHide() {
	if globalApp != nil && globalApp.ctx != nil {
		wails_runtime.WindowHide(globalApp.ctx)
	}
}

//export trayCallbackQuit
func trayCallbackQuit() {
	reallyQuit = true
	if globalApp != nil && globalApp.ctx != nil {
		wails_runtime.Quit(globalApp.ctx)
	}
}

func InitTray(iconPath string) {
	log.Printf("InitTray: starting systray with icon: %s\n", filepath.Base(iconPath))
	cIconPath := C.CString(iconPath)
	defer C.free(unsafe.Pointer(cIconPath))
	C.initSystray(cIconPath)
}
