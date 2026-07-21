package application

import (
	"context"
	"fmt"
	"log"
	"net/url"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	wailsRuntime "github.com/wailsapp/wails/v2/pkg/runtime"
)

type Connection struct {
	conn   *websocket.Conn
	cancel context.CancelFunc
}

type Supervisor struct {
	mu          sync.Mutex
	connections map[string]*Connection
	wailsCtx    context.Context
}

func NewSupervisor() *Supervisor {
	return &Supervisor{
		connections: make(map[string]*Connection),
	}
}

func (s *Supervisor) SetWailsContext(ctx context.Context) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.wailsCtx = ctx
}

func (s *Supervisor) ConnectProject(id string, port int) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.connections[id]; exists {
		return nil
	}

	ctx, cancel := context.WithCancel(context.Background())
	connCtx := &Connection{
		cancel: cancel,
	}
	s.connections[id] = connCtx

	go s.connectLoop(ctx, id, port)
	return nil
}

func (s *Supervisor) DisconnectProject(id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if conn, exists := s.connections[id]; exists {
		conn.cancel()
		if conn.conn != nil {
			conn.conn.Close()
		}
		delete(s.connections, id)
	}
	return nil
}

func (s *Supervisor) connectLoop(ctx context.Context, id string, port int) {
	u := url.URL{Scheme: "ws", Host: fmt.Sprintf("localhost:%d", port), Path: "/ws"}

	for {
		select {
		case <-ctx.Done():
			return
		default:
			log.Printf("Connecting to project %s via %s", id, u.String())
			conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
			if err != nil {
				log.Printf("Dial error on project %s: %v. Retrying in 1.5s...", id, err)
				s.emitEvent("status:"+id, map[string]string{"status": "connecting", "message": err.Error()})
				time.Sleep(1500 * time.Millisecond)
				continue
			}

			s.mu.Lock()
			if activeConn, exists := s.connections[id]; exists {
				activeConn.conn = conn
			}
			s.mu.Unlock()

			s.emitEvent("status:"+id, map[string]string{"status": "connected"})
			log.Printf("Connected successfully to project %s", id)

			// Read loop
			for {
				_, message, err := conn.ReadMessage()
				if err != nil {
					log.Printf("Read error on project %s: %v", id, err)
					conn.Close()
					break
				}
				s.emitEvent("telemetry:"+id, string(message))
			}

			s.emitEvent("status:"+id, map[string]string{"status": "disconnected"})
			time.Sleep(1500 * time.Millisecond)
		}
	}
}

func (s *Supervisor) emitEvent(eventName string, data interface{}) {
	s.mu.Lock()
	ctx := s.wailsCtx
	s.mu.Unlock()

	if ctx != nil {
		wailsRuntime.EventsEmit(ctx, eventName, data)
	}
}
