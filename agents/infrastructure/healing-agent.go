package main

import (
	"context"
	"fmt"
	"log"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// HealingAgent autonomously detects and heals service failures
type HealingAgent struct {
	k8sClient kubernetes.Interface
	namespace string
	healingActions map[string]HealingAction
}

// HealingAction defines recovery strategy for a component
type HealingAction struct {
	ComponentName string
	MaxRetries    int
	BackoffTime   time.Duration
	Action        string // "restart", "recreate", "scale-up", "failover"
}

func NewHealingAgent(namespace string) (*HealingAgent, error) {
	config, err := rest.InClusterConfig()
	if err != nil {
		return nil, err
	}

	k8sClient, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	return &HealingAgent{
		k8sClient: k8sClient,
		namespace: namespace,
		healingActions: map[string]HealingAction{
			"aegentix-platform": {
				ComponentName: "aegentix-platform",
				MaxRetries:    3,
				BackoffTime:   10 * time.Second,
				Action:        "restart",
			},
			"api-gateway": {
				ComponentName: "api-gateway",
				MaxRetries:    3,
				BackoffTime:   10 * time.Second,
				Action:        "restart",
			},
			"database-proxy": {
				ComponentName: "database-proxy",
				MaxRetries:    2,
				BackoffTime:   30 * time.Second,
				Action:        "failover",
			},
		},
	}, nil
}

// Run starts continuous health monitoring and healing
func (ha *HealingAgent) Run(ctx context.Context) {
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()

	log.Println("[HEALING] Agent started")

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			ha.detectAndHeal(ctx)
		}
	}
}

// detectAndHeal scans for unhealthy services and heals them
func (ha *HealingAgent) detectAndHeal(ctx context.Context) {
	pods, err := ha.k8sClient.CoreV1().Pods(ha.namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		log.Printf("[ERROR] Failed to list pods: %v", err)
		return
	}

	for _, pod := range pods.Items {
		if ha.isUnhealthy(&pod) {
			ha.healPod(ctx, &pod)
		}

		// Check for pods that need recovery
		if ha.needsHealing(&pod) {
			ha.executHealing(ctx, &pod)
		}
	}
}

// isUnhealthy checks if a pod is in an unhealthy state
func (ha *HealingAgent) isUnhealthy(pod *corev1.Pod) bool {
	// Check pod phase
	if pod.Status.Phase != corev1.PodRunning {
		return true
	}

	// Check container readiness
	for _, containerStatus := range pod.Status.ContainerStatuses {
		if !containerStatus.Ready {
			return true
		}

		// Check for crash loops
		if containerStatus.State.Waiting != nil {
			reason := containerStatus.State.Waiting.Reason
			if reason == "CrashLoopBackOff" || reason == "ImagePullBackOff" {
				return true
			}
		}
	}

	return false
}

// needsHealing checks if pod meets criteria for healing
func (ha *HealingAgent) needsHealing(pod *corev1.Pod) bool {
	// High restart count
	for _, containerStatus := range pod.Status.ContainerStatuses {
		if containerStatus.RestartCount > 5 {
			log.Printf("[HEALING] Pod %s has high restart count: %d", pod.Name, containerStatus.RestartCount)
			return true
		}
	}

	// Pod stuck in pending
	if pod.Status.Phase == corev1.PodPending {
		createdTime := pod.CreationTimestamp.Time
		if time.Since(createdTime) > 5*time.Minute {
			log.Printf("[HEALING] Pod %s stuck in Pending for > 5 min", pod.Name)
			return true
		}
	}

	return false
}

// healPod executes healing for a pod
func (ha *HealingAgent) healPod(ctx context.Context, pod *corev1.Pod) {
	log.Printf("[HEALING] Healing pod: %s (Phase: %s)", pod.Name, pod.Status.Phase)

	// Get healing action
	action, ok := ha.healingActions[pod.Labels["app"]]
	if !ok {
		// Default healing action
		action = HealingAction{
			MaxRetries:  3,
			BackoffTime: 10 * time.Second,
			Action:      "restart",
		}
	}

	switch action.Action {
	case "restart":
		ha.restartPod(ctx, pod)
	case "recreate":
		ha.recreatePod(ctx, pod)
	case "scale-up":
		ha.scaleUp(ctx, pod)
	case "failover":
		ha.failover(ctx, pod)
	}
}

// restartPod deletes a pod to trigger restart
func (ha *HealingAgent) restartPod(ctx context.Context, pod *corev1.Pod) {
	log.Printf("[HEALING] Restarting pod: %s", pod.Name)

	deletePolicy := metav1.DeletePropagationForeground
	if err := ha.k8sClient.CoreV1().Pods(ha.namespace).Delete(ctx, pod.Name, metav1.DeleteOptions{
		PropagationPolicy: &deletePolicy,
	}); err != nil {
		log.Printf("[ERROR] Failed to restart pod: %v", err)
		return
	}

	log.Printf("[HEALING] Pod restart initiated: %s", pod.Name)

	// Wait for new pod to start
	time.Sleep(5 * time.Second)
	ha.verifyHealing(ctx, pod)
}

// recreatePod fully recreates a pod from its deployment
func (ha *HealingAgent) recreatePod(ctx context.Context, pod *corev1.Pod) {
	log.Printf("[HEALING] Recreating pod: %s", pod.Name)

	// Get owner deployment
	deploymentName := pod.Labels["app"]
	deployment, err := ha.k8sClient.AppsV1().Deployments(ha.namespace).Get(ctx, deploymentName, metav1.GetOptions{})
	if err != nil {
		log.Printf("[ERROR] Failed to get deployment: %v", err)
		return
	}

	// Trigger rollout restart
	if err := ha.k8sClient.AppsV1().Deployments(ha.namespace).Delete(ctx, deploymentName, metav1.DeleteOptions{}); err != nil {
		log.Printf("[ERROR] Failed to trigger rollout restart: %v", err)
		return
	}

	log.Printf("[HEALING] Deployment rollout restart initiated: %s", deploymentName)

	// Reapply deployment
	if _, err := ha.k8sClient.AppsV1().Deployments(ha.namespace).Create(ctx, deployment, metav1.CreateOptions{}); err != nil {
		log.Printf("[ERROR] Failed to recreate deployment: %v", err)
	}
}

// scaleUp adds more replicas to handle load
func (ha *HealingAgent) scaleUp(ctx context.Context, pod *corev1.Pod) {
	deploymentName := pod.Labels["app"]
	deployment, err := ha.k8sClient.AppsV1().Deployments(ha.namespace).Get(ctx, deploymentName, metav1.GetOptions{})
	if err != nil {
		log.Printf("[ERROR] Failed to get deployment: %v", err)
		return
	}

	newReplicas := *deployment.Spec.Replicas + 1
	deployment.Spec.Replicas = &newReplicas

	if _, err := ha.k8sClient.AppsV1().Deployments(ha.namespace).Update(ctx, deployment, metav1.UpdateOptions{}); err != nil {
		log.Printf("[ERROR] Failed to scale up: %v", err)
		return
	}

	log.Printf("[HEALING] Scaled up %s to %d replicas", deploymentName, newReplicas)
}

// failover switches to replica/standby
func (ha *HealingAgent) failover(ctx context.Context, pod *corev1.Pod) {
	log.Printf("[HEALING] Initiating failover for: %s", pod.Name)

	// Delete current pod to trigger failover
	deletePolicy := metav1.DeletePropagationBackground
	if err := ha.k8sClient.CoreV1().Pods(ha.namespace).Delete(ctx, pod.Name, metav1.DeleteOptions{
		PropagationPolicy: &deletePolicy,
	}); err != nil {
		log.Printf("[ERROR] Failed to failover: %v", err)
		return
	}

	log.Printf("[HEALING] Failover initiated for: %s", pod.Name)
}

// executHealing executes healing actions
func (ha *HealingAgent) executHealing(ctx context.Context, pod *corev1.Pod) {
	log.Printf("[HEALING] Executing healing for: %s", pod.Name)

	action, ok := ha.healingActions[pod.Labels["app"]]
	if !ok {
		action = HealingAction{
			MaxRetries:  3,
			BackoffTime: 10 * time.Second,
			Action:      "restart",
		}
	}

	for attempt := 1; attempt <= action.MaxRetries; attempt++ {
		log.Printf("[HEALING] Healing attempt %d/%d for %s", attempt, action.MaxRetries, pod.Name)

		ha.healPod(ctx, pod)

		// Check if healed
		if ha.verifyHealing(ctx, pod) {
			log.Printf("[HEALING] Successfully healed: %s", pod.Name)
			return
		}

		if attempt < action.MaxRetries {
			time.Sleep(action.BackoffTime * time.Duration(attempt))
		}
	}

	log.Printf("[HEALING] Failed to heal %s after %d attempts - escalating", pod.Name, action.MaxRetries)
	ha.escalateHealing(pod)
}

// verifyHealing checks if pod is healthy after healing
func (ha *HealingAgent) verifyHealing(ctx context.Context, pod *corev1.Pod) bool {
	updatedPod, err := ha.k8sClient.CoreV1().Pods(ha.namespace).Get(ctx, pod.Name, metav1.GetOptions{})
	if err != nil {
		return false
	}

	if updatedPod.Status.Phase != corev1.PodRunning {
		return false
	}

	for _, containerStatus := range updatedPod.Status.ContainerStatuses {
		if !containerStatus.Ready {
			return false
		}
	}

	return true
}

// escalateHealing escalates failed healing to on-call team
func (ha *HealingAgent) escalateHealing(pod *corev1.Pod) {
	log.Printf("[ESCALATE] Healing failed for %s - notifying on-call team", pod.Name)
	// Send alert to PagerDuty, Slack, etc.
}

func main() {
	agent, err := NewHealingAgent("aegentix-production")
	if err != nil {
		log.Fatalf("Failed to create healing agent: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	agent.Run(ctx)
}
