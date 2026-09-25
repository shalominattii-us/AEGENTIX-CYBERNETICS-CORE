package slack

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

// Client handles Slack webhook communication
type Client struct {
	webhookURL string
	agent      string
	client     *http.Client
}

// Alert represents a Slack alert message
type Alert struct {
	Title       string
	Text        string
	Severity    string // critical, high, medium, low
	AgentAction string
	Timestamp   time.Time
	Metadata    map[string]string
}

// New creates a new Slack client
func New(agent string) *Client {
	webhookURL := os.Getenv("SLACK_WEBHOOK_URL")
	if webhookURL == "" {
		log.Println("[SLACK] Warning: SLACK_WEBHOOK_URL not set, Slack notifications disabled")
	}

	return &Client{
		webhookURL: webhookURL,
		agent:      agent,
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// PostAlert sends an alert to Slack
func (c *Client) PostAlert(alert Alert) error {
	if c.webhookURL == "" {
		return nil
	}

	color := c.getSeverityColor(alert.Severity)
	emoji := c.getSeverityEmoji(alert.Severity)

	payload := map[string]interface{}{
		"attachments": []map[string]interface{}{
			{
				"color": color,
				"title": fmt.Sprintf("%s %s | %s", emoji, alert.Title, c.agent),
				"text":  alert.Text,
				"fields": c.buildFields(alert),
				"ts":    alert.Timestamp.Unix(),
			},
		},
	}

	body, _ := json.Marshal(payload)

	resp, err := c.client.Post(c.webhookURL, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to post to Slack: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("Slack webhook returned status %d", resp.StatusCode)
	}

	return nil
}

// PostIncident posts an incident to Slack with escalation info
func (c *Client) PostIncident(title, description, severity, component string) error {
	if c.webhookURL == "" {
		return nil
	}

	color := c.getSeverityColor(severity)
	emoji := c.getSeverityEmoji(severity)

	payload := map[string]interface{}{
		"attachments": []map[string]interface{}{
			{
				"color": color,
				"title": fmt.Sprintf("%s [%s] %s", emoji, severity, title),
				"text":  description,
				"fields": []map[string]interface{}{
					{
						"title": "Agent",
						"value": c.agent,
						"short": true,
					},
					{
						"title": "Component",
						"value": component,
						"short": true,
					},
					{
						"title": "Timestamp",
						"value": time.Now().Format(time.RFC3339),
						"short": false,
					},
				},
			},
		},
	}

	body, _ := json.Marshal(payload)

	resp, err := c.client.Post(c.webhookURL, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to post incident: %w", err)
	}
	defer resp.Body.Close()

	return nil
}

// PostDeployment posts deployment status to Slack
func (c *Client) PostDeployment(appName, version, status, details string) error {
	if c.webhookURL == "" {
		return nil
	}

	var color string
	var emoji string

	switch status {
	case "started":
		color = "#0099ff"
		emoji = "🚀"
	case "canary":
		color = "#ffaa00"
		emoji = "⚠️"
	case "success":
		color = "#36a64f"
		emoji = "✅"
	case "failed":
		color = "#ff0000"
		emoji = "❌"
	case "rolled_back":
		color = "#ff6600"
		emoji = "⏮️"
	default:
		color = "#808080"
		emoji = "ℹ️"
	}

	payload := map[string]interface{}{
		"attachments": []map[string]interface{}{
			{
				"color": color,
				"title": fmt.Sprintf("%s Deployment %s | %s", emoji, status, c.agent),
				"fields": []map[string]interface{}{
					{
						"title": "Application",
						"value": appName,
						"short": true,
					},
					{
						"title": "Version",
						"value": version,
						"short": true,
					},
					{
						"title": "Details",
						"value": details,
						"short": false,
					},
					{
						"title": "Timestamp",
						"value": time.Now().Format(time.RFC3339),
						"short": false,
					},
				},
			},
		},
	}

	body, _ := json.Marshal(payload)

	resp, err := c.client.Post(c.webhookURL, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to post deployment: %w", err)
	}
	defer resp.Body.Close()

	return nil
}

// PostHealing posts healing action to Slack
func (c *Client) PostHealing(podName, action, result, reason string) error {
	if c.webhookURL == "" {
		return nil
	}

	var color string
	var emoji string

	switch result {
	case "success":
		color = "#36a64f"
		emoji = "✅"
	case "failed":
		color = "#ff0000"
		emoji = "❌"
	case "escalated":
		color = "#ff6600"
		emoji = "⚠️"
	default:
		color = "#0099ff"
		emoji = "ℹ️"
	}

	payload := map[string]interface{}{
		"attachments": []map[string]interface{}{
			{
				"color": color,
				"title": fmt.Sprintf("%s Healing %s | %s", emoji, result, c.agent),
				"fields": []map[string]interface{}{
					{
						"title": "Pod",
						"value": podName,
						"short": true,
					},
					{
						"title": "Action",
						"value": action,
						"short": true,
					},
					{
						"title": "Reason",
						"value": reason,
						"short": false,
					},
					{
						"title": "Timestamp",
						"value": time.Now().Format(time.RFC3339),
						"short": false,
					},
				},
			},
		},
	}

	body, _ := json.Marshal(payload)

	resp, err := c.client.Post(c.webhookURL, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to post healing alert: %w", err)
	}
	defer resp.Body.Close()

	return nil
}

// buildFields creates Slack message fields from alert metadata
func (c *Client) buildFields(alert Alert) []map[string]interface{} {
	fields := []map[string]interface{}{
		{
			"title": "Agent",
			"value": c.agent,
			"short": true,
		},
		{
			"title": "Severity",
			"value": alert.Severity,
			"short": true,
		},
	}

	if alert.AgentAction != "" {
		fields = append(fields, map[string]interface{}{
			"title": "Action",
			"value": alert.AgentAction,
			"short": false,
		})
	}

	for key, value := range alert.Metadata {
		fields = append(fields, map[string]interface{}{
			"title": key,
			"value": value,
			"short": true,
		})
	}

	return fields
}

// getSeverityColor returns Slack color for severity level
func (c *Client) getSeverityColor(severity string) string {
	switch severity {
	case "critical":
		return "#ff0000" // Red
	case "high":
		return "#ff6600" // Orange
	case "medium":
		return "#ffaa00" // Yellow
	case "low":
		return "#0099ff" // Blue
	default:
		return "#808080" // Gray
	}
}

// getSeverityEmoji returns emoji for severity level
func (c *Client) getSeverityEmoji(severity string) string {
	switch severity {
	case "critical":
		return "🚨"
	case "high":
		return "⚠️"
	case "medium":
		return "ℹ️"
	case "low":
		return "💡"
	default:
		return "📌"
	}
}
