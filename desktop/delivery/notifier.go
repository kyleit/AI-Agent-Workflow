package delivery

import (
	"os/exec"
)

type Notifier struct{}

func NewNotifier() *Notifier {
	return &Notifier{}
}

func (n *Notifier) SendNotification(title, message string) error {
	psCmd := `[void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show("` + message + `", "` + title + `")`
	cmd := exec.Command("powershell", "-Command", psCmd)
	return cmd.Start()
}
