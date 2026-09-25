package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"sync"
	"time"
)

// HealthStatus tracks agent health
type HealthStatus struct {
	Status    string    `json:"status"`
	Agent     string    `json:"agent"`
	Timestamp time.Time `json:"timestamp"`
	Uptime    string    `json:"uptime"`
	Metrics   map[string]interface{} `json:"metrics"`
	mu        sync.RWMutex
}

var health = &HealthStatus{
	Status:    "healthy",
	Agent:     "monitoring-agent",
	Timestamp: time.Now(),
	Metrics:   make(map[string]interface{}),
	mu:        sync.RWMutex{},
}

var startTime = time.Now()

// UpdateMetric safely updates a health metric
func UpdateMetric(key string, value interface{}) {
	health.mu.Lock()
	defer health.mu.Unlock()
	health.Metrics[key] = value
	health.Timestamp = time.Now()
}

// SetStatus sets overall health status
func SetStatus(status string) {
	health.mu.Lock()
	defer health.mu.Unlock()
	health.Status = status
	health.Timestamp = time.Now()
}

// HealthHandler responds to health checks
func HealthHandler(w http.ResponseWriter, r *http.Request) {
	health.mu.RLock()
	defer health.mu.RUnlock()

	health.Timestamp = time.Now()
	health.Uptime = time.Since(startTime).String()

	w.Header().Set("Content-Type", "application/json")

	if health.Status != "healthy" {
		w.WriteHeader(http.StatusServiceUnavailable)
	} else {
		w.WriteHeader(http.StatusOK)
	}

	json.NewEncoder(w).Encode(health)
}

// ReadyHandler responds to readiness checks
func ReadyHandler(w http.ResponseWriter, r *http.Request) {
	health.mu.RLock()
	isReady := health.Status == "healthy"
	health.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")

	if !isReady {
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{
			"status": "not_ready",
			"reason": "agent starting up",
		})
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status": "ready",
	})
}

// MetricsHandler exposes Prometheus metrics
func MetricsHandler(w http.ResponseWriter, r *http.Request) {
	health.mu.RLock()
	defer health.mu.RUnlock()

	w.Header().Set("Content-Type", "text/plain; version=0.0.4")

	// Basic metrics
	metrics := `# HELP agent_health_status Agent health status (1=healthy, 0=degraded)
# TYPE agent_health_status gauge
agent_health_status{agent="monitoring"} 1

# HELP agent_uptime_seconds Agent uptime in seconds
# TYPE agent_uptime_seconds gauge
agent_uptime_seconds ` + fmt.Sprintf("%.0f\n", time.Since(startTime).Seconds())

	// Add custom metrics
	for key, value := range health.Metrics {
		metrics += `# HELP agent_` + key + ` Custom agent metric
# TYPE agent_` + key + ` gauge
agent_` + key + ` ` + fmt.Sprintf("%v\n", value)
	}

	w.Write([]byte(metrics))
}

// StartHealthServer starts the health check HTTP server
func StartHealthServer(port string) {
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/health", HealthHandler)
	http.HandleFunc("/ready", ReadyHandler)
	http.HandleFunc("/metrics", MetricsHandler)

	log.Printf("[HEALTH] Server starting on port %s", port)

	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Printf("[ERROR] Health server failed: %v", err)
		os.Exit(1)
	}
}

// StartHealthServerAsync starts health server in background
func StartHealthServerAsync(port string) {
	go StartHealthServer(port)
}
