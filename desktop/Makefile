VERSION := $(shell node -e "console.log(require('../MANIFEST.json').version)")
APP_NAME := aiwf-framework
DIST_DIR := dist
GITHUB_REPO ?= kyleit/AI-Agent-Workflow
TAG ?= v$(VERSION)
OS_NAME := $(shell uname -s | tr '[:upper:]' '[:lower:]')
ARCH_NAME := $(shell uname -m)
MAC_APP := build/bin/AIWF Framework.app
MAC_APP_ZIP := $(DIST_DIR)/$(APP_NAME)_$(VERSION)_darwin_universal.zip
MAC_DMG := $(DIST_DIR)/$(APP_NAME)_$(VERSION)_darwin_universal.dmg
MAC_PKG := $(DIST_DIR)/$(APP_NAME)_$(VERSION)_darwin_universal.pkg
MAC_ENTITLEMENTS := build/darwin/entitlements.plist
MAC_SIGN_IDENTITY ?=
MAC_INSTALLER_IDENTITY ?=
MAC_NOTARIZE ?= false
MAC_SIGNING_REQUIRED ?= false

.PHONY: all frontend build build-all dev test embed-aiwf package package-all package-mac package-mac-only package-windows package-windows-only package-linux package-linux-only release release-all release-dry-run release-dry release-all-dry-run release-all-dry clean clean-dist

all: build

# embed-aiwf — delegate to go-src/aiwf/Makefile.
# Cross-compiles aiwf for all 5 platforms and injects them into desktop/embedded/.
# Run this ONCE before 'make build' or 'make package' to bundle aiwf inside the app.
#
# Workflow:
#   (from desktop/)  make embed-aiwf   # inject all platform binaries
#   (from desktop/)  make build         # wails build (binary already contains aiwf)
#
# Or in one step:
#   (from go-src/aiwf/) make embed-aiwf && cd ../../desktop && make build
embed-aiwf:
ifeq ($(OS_NAME),darwin)
	$(MAKE) -C ../go-src/aiwf embed-aiwf
else ifeq ($(OS_NAME),linux)
	$(MAKE) -C ../go-src/aiwf embed-aiwf
else
	@cd ..\go-src\aiwf && $(MAKE) embed-aiwf
endif
	@echo "==> desktop/embedded/ updated — ready to build with: make build"

frontend:
	npm --prefix frontend run build

build:
ifeq ($(OS_NAME),darwin)
	wails build -platform darwin/universal -clean
else ifeq ($(OS_NAME),linux)
	wails build -platform linux/amd64 -clean
else
	wails build -platform windows/amd64 -clean
endif

build-all:
ifeq ($(OS_NAME),darwin)
	wails build -platform darwin/universal -clean
	wails build -platform windows/amd64
	@echo "Skipping linux/amd64 cross-build on macOS: Wails v2 does not support cross-compiling Linux from macOS."
else ifeq ($(OS_NAME),linux)
	wails build -platform linux/amd64 -clean
else
	wails build -platform windows/amd64 -clean
endif

dev:
	wails dev

test:
	go test ./...

clean-dist:
	rm -rf $(DIST_DIR)

package:
ifeq ($(OS_NAME),darwin)
	$(MAKE) package-mac
else ifeq ($(OS_NAME),linux)
	$(MAKE) package-linux
else
	$(MAKE) package-windows
endif

package-all: clean-dist
ifeq ($(OS_NAME),darwin)
	$(MAKE) package-mac
	$(MAKE) package-windows
	@echo "Skipping Linux package locally on macOS. Use the GitHub Actions release matrix or run make package on Linux to produce .tar.gz/.deb artifacts."
else ifeq ($(OS_NAME),linux)
	$(MAKE) package-linux
else
	$(MAKE) package-windows
endif

package-mac:
	wails build -platform darwin/universal -clean
	$(MAKE) package-mac-only

package-mac-only:
	mkdir -p $(DIST_DIR)
	@if [ -d "$(MAC_APP)" ]; then \
		if [ "$(MAC_SIGNING_REQUIRED)" = "true" ] && [ -z "$(MAC_SIGN_IDENTITY)" ]; then \
			echo "Error: MAC_SIGN_IDENTITY is required for a trusted macOS release."; \
			exit 1; \
		fi; \
		if [ "$(MAC_SIGNING_REQUIRED)" = "true" ] && [ -z "$(MAC_INSTALLER_IDENTITY)" ]; then \
			echo "Error: MAC_INSTALLER_IDENTITY is required for a trusted macOS pkg release."; \
			exit 1; \
		fi; \
		if [ -n "$(MAC_SIGN_IDENTITY)" ]; then \
			echo "Signing macOS App with Developer ID Application identity..."; \
			codesign --force --deep --options runtime --timestamp --entitlements "$(MAC_ENTITLEMENTS)" --sign "$(MAC_SIGN_IDENTITY)" "$(MAC_APP)"; \
			codesign --verify --deep --strict --verbose=2 "$(MAC_APP)"; \
		else \
			echo "Warning: MAC_SIGN_IDENTITY is not set. macOS artifacts will be unsigned and Gatekeeper may block them."; \
		fi; \
		if [ "$(MAC_NOTARIZE)" = "true" ]; then \
			if [ -z "$$APPLE_ID" ] || [ -z "$$APPLE_TEAM_ID" ] || [ -z "$$APPLE_APP_SPECIFIC_PASSWORD" ]; then \
				echo "Error: APPLE_ID, APPLE_TEAM_ID, and APPLE_APP_SPECIFIC_PASSWORD are required for notarization."; \
				exit 1; \
			fi; \
			echo "Notarizing and stapling macOS App before packaging..."; \
			rm -f "$(DIST_DIR)/$(APP_NAME)_$(VERSION)_darwin_universal_notary.zip"; \
			ditto -c -k --sequesterRsrc --keepParent "$(MAC_APP)" "$(DIST_DIR)/$(APP_NAME)_$(VERSION)_darwin_universal_notary.zip"; \
			xcrun notarytool submit "$(DIST_DIR)/$(APP_NAME)_$(VERSION)_darwin_universal_notary.zip" --apple-id "$$APPLE_ID" --team-id "$$APPLE_TEAM_ID" --password "$$APPLE_APP_SPECIFIC_PASSWORD" --wait; \
			xcrun stapler staple "$(MAC_APP)"; \
			rm -f "$(DIST_DIR)/$(APP_NAME)_$(VERSION)_darwin_universal_notary.zip"; \
		fi; \
		echo "Packaging macOS App into Universal PKG installer..."; \
		if [ -n "$(MAC_INSTALLER_IDENTITY)" ]; then \
			pkgbuild --component "$(MAC_APP)" --install-location "/Applications" --sign "$(MAC_INSTALLER_IDENTITY)" --timestamp "$(MAC_PKG)"; \
			pkgutil --check-signature "$(MAC_PKG)"; \
		else \
			pkgbuild --component "$(MAC_APP)" --install-location "/Applications" "$(MAC_PKG)"; \
		fi; \
		echo "Creating ZIP archive of macOS App..."; \
		ditto -c -k --sequesterRsrc --keepParent "$(MAC_APP)" "$(MAC_APP_ZIP)"; \
		echo "Creating DMG installer of macOS App..."; \
		hdiutil create -volname "AIWF Framework" -srcfolder "$(MAC_APP)" -ov -format UDZO "$(MAC_DMG)"; \
		if [ -n "$(MAC_SIGN_IDENTITY)" ]; then \
			echo "Signing macOS DMG with Developer ID Application identity..."; \
			codesign --force --timestamp --sign "$(MAC_SIGN_IDENTITY)" "$(MAC_DMG)"; \
			codesign --verify --verbose=2 "$(MAC_DMG)"; \
		fi; \
		if [ "$(MAC_NOTARIZE)" = "true" ]; then \
			echo "Notarizing and stapling macOS PKG and DMG..."; \
			xcrun notarytool submit "$(MAC_PKG)" --apple-id "$$APPLE_ID" --team-id "$$APPLE_TEAM_ID" --password "$$APPLE_APP_SPECIFIC_PASSWORD" --wait; \
			xcrun stapler staple "$(MAC_PKG)"; \
			xcrun notarytool submit "$(MAC_DMG)" --apple-id "$$APPLE_ID" --team-id "$$APPLE_TEAM_ID" --password "$$APPLE_APP_SPECIFIC_PASSWORD" --wait; \
			xcrun stapler staple "$(MAC_DMG)"; \
			spctl -a -vvv -t install "$(MAC_PKG)"; \
			spctl -a -vvv -t open --context context:primary-signature "$(MAC_DMG)"; \
		fi; \
	else \
		echo "Error: $(MAC_APP) not found."; \
		exit 1; \
	fi
	@ls -lah $(DIST_DIR)

package-windows:
	wails build -platform windows/amd64 -clean
	$(MAKE) package-windows-only

package-windows-only:
	mkdir -p $(DIST_DIR)
	@windows_exe="build/bin/$(APP_NAME).exe"; \
	if [ ! -f "$$windows_exe" ]; then \
		windows_exe="$$(find build/bin -maxdepth 1 -type f -name '*.exe' | head -n 1)"; \
	fi; \
	if [ -n "$$windows_exe" ] && [ -f "$$windows_exe" ]; then \
		windows_exe_name="$$(basename "$$windows_exe")"; \
		echo "Packaging Windows executable into ZIP..."; \
		if command -v zip >/dev/null 2>&1; then \
			(cd build/bin && zip -q "../../$(DIST_DIR)/$(APP_NAME)_$(VERSION)_windows_amd64.zip" "$$windows_exe_name"); \
		elif command -v powershell >/dev/null 2>&1; then \
			powershell -NoProfile -Command "Compress-Archive -Path '$$windows_exe' -DestinationPath '$(DIST_DIR)/$(APP_NAME)_$(VERSION)_windows_amd64.zip' -Force"; \
		elif command -v powershell.exe >/dev/null 2>&1; then \
			powershell.exe -NoProfile -Command "Compress-Archive -Path '$$windows_exe' -DestinationPath '$(DIST_DIR)/$(APP_NAME)_$(VERSION)_windows_amd64.zip' -Force"; \
		else \
			tar -czf "$(DIST_DIR)/$(APP_NAME)_$(VERSION)_windows_amd64.tar.gz" -C build/bin "$$windows_exe_name"; \
		fi; \
		if command -v ISCC >/dev/null 2>&1; then \
			echo "Compiling Inno Setup Installer..."; \
			ISCC /O"$(DIST_DIR)" /DAppVersion=$(VERSION) build/windows/installer.iss; \
		else \
			echo "ISCC compiler not found. Skipping Inno Setup installer compilation."; \
		fi; \
	else \
		echo "Error: no Windows executable found in build/bin."; \
		ls -lah build/bin || true; \
		exit 1; \
	fi
	@ls -lah $(DIST_DIR)

package-linux:
	wails build -platform linux/amd64 -clean
	$(MAKE) package-linux-only

package-linux-only:
	mkdir -p $(DIST_DIR)
	@if [ -f "build/bin/$(APP_NAME)" ]; then \
		echo "Packaging Linux binary into tar.gz..."; \
		tar -czf "$(DIST_DIR)/$(APP_NAME)_$(VERSION)_linux_amd64.tar.gz" -C build/bin "$(APP_NAME)"; \
		if command -v dpkg-deb >/dev/null 2>&1; then \
			echo "Building Debian Package (.deb)..."; \
			rm -rf build/linux_deb; \
			mkdir -p build/linux_deb/DEBIAN; \
			mkdir -p build/linux_deb/usr/bin; \
			mkdir -p build/linux_deb/usr/share/applications; \
			mkdir -p build/linux_deb/usr/share/pixmaps; \
			cp build/bin/$(APP_NAME) build/linux_deb/usr/bin/; \
			if [ -f "build/appicon.png" ]; then \
				cp build/appicon.png build/linux_deb/usr/share/pixmaps/$(APP_NAME).png; \
			fi; \
			echo "Package: $(APP_NAME)" > build/linux_deb/DEBIAN/control; \
			echo "Version: $(VERSION)" >> build/linux_deb/DEBIAN/control; \
			echo "Section: utils" >> build/linux_deb/DEBIAN/control; \
			echo "Priority: optional" >> build/linux_deb/DEBIAN/control; \
			echo "Architecture: amd64" >> build/linux_deb/DEBIAN/control; \
			echo "Maintainer: AIWF Team <info@aiwf.dev>" >> build/linux_deb/DEBIAN/control; \
			echo "Description: AI Engineering Workflow Framework Desktop App" >> build/linux_deb/DEBIAN/control; \
			echo "[Desktop Entry]" > build/linux_deb/usr/share/applications/$(APP_NAME).desktop; \
			echo "Name=AIWF Framework" >> build/linux_deb/usr/share/applications/$(APP_NAME).desktop; \
			echo "Comment=AI Engineering Workflow Framework Desktop App" >> build/linux_deb/usr/share/applications/$(APP_NAME).desktop; \
			echo "Exec=/usr/bin/$(APP_NAME)" >> build/linux_deb/usr/share/applications/$(APP_NAME).desktop; \
			echo "Icon=$(APP_NAME)" >> build/linux_deb/usr/share/applications/$(APP_NAME).desktop; \
			echo "Terminal=false" >> build/linux_deb/usr/share/applications/$(APP_NAME).desktop; \
			echo "Type=Application" >> build/linux_deb/usr/share/applications/$(APP_NAME).desktop; \
			echo "Categories=Development;" >> build/linux_deb/usr/share/applications/$(APP_NAME).desktop; \
			dpkg-deb --build build/linux_deb "$(DIST_DIR)/$(APP_NAME)_$(VERSION)_linux_amd64.deb"; \
			rm -rf build/linux_deb; \
		else \
			echo "dpkg-deb not found. Skipping Debian package creation."; \
		fi; \
	else \
		echo "Error: build/bin/$(APP_NAME) not found."; \
		exit 1; \
	fi
	@ls -lah $(DIST_DIR)

release-only:
	@if ! command -v gh >/dev/null 2>&1; then \
		echo "Error: GitHub CLI (gh) is not installed on this system."; \
		echo "Please install 'gh' (e.g. 'brew install gh' or https://cli.github.com) or upload artifacts manually."; \
		exit 1; \
	fi
	@echo "Creating GitHub Release for tag $(TAG) on repo $(GITHUB_REPO)..."
	gh release create $(TAG) --repo $(GITHUB_REPO) --title "AIWF Framework $(VERSION)" --notes "AIWF Framework desktop app release $(VERSION)" || echo "Release $(TAG) already exists."
	@echo "Uploading release artifacts in $(DIST_DIR) to GitHub..."
	@for file in $$(ls $(DIST_DIR)/* 2>/dev/null); do \
		echo "Uploading $$file..."; \
		gh release upload $(TAG) "$$file" --repo $(GITHUB_REPO) --clobber || \
		gh release upload $(TAG) "$$file" --repo $(GITHUB_REPO) || \
		echo "Warning: Failed to upload $$file to release $(TAG)"; \
	done

release:
	@if [ ! -d "$(DIST_DIR)" ] || [ ! "$$(ls -A $(DIST_DIR) 2>/dev/null)" ]; then \
		echo "$(DIST_DIR) is empty. Packaging current platform first..."; \
		$(MAKE) package; \
	fi
	$(MAKE) release-only

release-all:
	@echo "================================================================================"
	@echo "WARNING: Building all release packages locally will skip native installers"
	@echo "(like .deb or Inno Setup .exe) if their compilers are not present on this host."
	@echo "For official production releases, it is highly recommended to use GitHub Actions"
	@echo "CI matrix which automatically builds each platform native installer."
	@echo "================================================================================"
	@if [ ! -d "$(DIST_DIR)" ] || [ ! "$$(ls -A $(DIST_DIR) 2>/dev/null)" ]; then \
		echo "$(DIST_DIR) is empty. Packaging all platforms first..."; \
		$(MAKE) package-all; \
	fi
	$(MAKE) release-only

release-dry: release-dry-run

release-dry-run:
	@if [ ! -d "$(DIST_DIR)" ] || [ ! "$$(ls -A $(DIST_DIR) 2>/dev/null)" ]; then \
		echo "$(DIST_DIR) is empty. Packaging current platform first for dry-run..."; \
		$(MAKE) package; \
	fi
	@echo "[DRY-RUN] Simulating GitHub Release creation for tag $(TAG) on repo $(GITHUB_REPO)..."
	@echo "gh release create $(TAG) --repo $(GITHUB_REPO) --title \"AIWF Framework $(VERSION)\" --notes \"AIWF Framework desktop app release $(VERSION)\""
	@echo "[DRY-RUN] Simulating upload of release artifacts in $(DIST_DIR) to GitHub..."
	@for file in $$(ls $(DIST_DIR)/* 2>/dev/null); do \
		echo "gh release upload $(TAG) $$file --repo $(GITHUB_REPO) --clobber"; \
	done

release-all-dry: release-all-dry-run

release-all-dry-run:
	@echo "================================================================================"
	@echo "[DRY-RUN] WARNING: Native installers (like .deb or Inno Setup .exe) will be skipped"
	@echo "if their compilers are not present. Recommended to use GitHub Actions for official releases."
	@echo "================================================================================"
	@if [ ! -d "$(DIST_DIR)" ] || [ ! "$$(ls -A $(DIST_DIR) 2>/dev/null)" ]; then \
		echo "$(DIST_DIR) is empty. Packaging all platforms first for dry-run..."; \
		$(MAKE) package-all; \
	fi
	@echo "[DRY-RUN] Simulating GitHub Release creation for tag $(TAG) on repo $(GITHUB_REPO)..."
	@echo "gh release create $(TAG) --repo $(GITHUB_REPO) --title \"AIWF Framework $(VERSION)\" --notes \"AIWF Framework desktop app release $(VERSION)\""
	@echo "[DRY-RUN] Simulating upload of release artifacts in $(DIST_DIR) to GitHub..."
	@for file in $$(ls $(DIST_DIR)/* 2>/dev/null); do \
		echo "gh release upload $(TAG) $$file --repo $(GITHUB_REPO) --clobber"; \
	done

clean: clean-dist
	rm -rf build/bin frontend/dist
	@echo "Clean complete!"
