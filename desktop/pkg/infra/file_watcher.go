package infra

import "os"

// ReadStateFile reads raw JSON state content safely from disk.
func ReadStateFile(path string) ([]byte, error) {
	return os.ReadFile(path)
}
