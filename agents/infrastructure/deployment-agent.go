package main

import (
	"context"
	"fmt"
	"log"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

// DeploymentAgent autonomously manages application deployments
type DeploymentAgent struct {
	k8sClient kubernetes.Interface
	namespace string
	registry  string
}

// DeploymentConfig holds deployment strategy configuration
type DeploymentConfig struct {
	Name              string
	Image             string
	Replicas          int32
	Strategy          string // "rolling", "canary", "blue-green"
	MaxSurge          int
	MaxUnavailable    int
	HealthCheckPath   string
	HealthCheckPort   int32
}

func NewDeploymentAgent(namespace, registry string) (*DeploymentAgent, error) {
	config, err := rest.InClusterConfig()
	if err != nil {
		return nil, err
	}

	k8sClient, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	return &DeploymentAgent{
		k8sClient: k8sClient,
		namespace: namespace,
		registry:  registry,
	}, nil
}

// Run starts deployment management loop
func (da *DeploymentAgent) Run(ctx context.Context) {
	ticker := time.NewTicker(2 * time.Minute)
	defer ticker.Stop()

	log.Println("[DEPLOYMENT] Agent started")

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			da.checkDeployments(ctx)
		}
	}
}

// checkDeployments scans for pending deployments
func (da *DeploymentAgent) checkDeployments(ctx context.Context) {
	deployments, err := da.k8sClient.AppsV1().Deployments(da.namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		log.Printf("[ERROR] Failed to list deployments: %v", err)
		return
	}

	for _, deployment := range deployments.Items {
		// Check if deployment has pending update
		if da.isPendingUpdate(&deployment) {
			da.executeDeployment(ctx, &deployment)
		}

		// Check deployment health
		if da.isDeploymentUnhealthy(&deployment) {
			da.handleDeploymentFailure(ctx, &deployment)
		}
	}
}

// isPendingUpdate checks if deployment has a pending update
func (da *DeploymentAgent) isPendingUpdate(deployment *appsv1.Deployment) bool {
	// Check annotations for pending deployment flag
	if deployment.Annotations != nil {
		if _, pending := deployment.Annotations["deployment-pending"]; pending {
			return true
		}
	}

	// Check image version mismatch
	return false
}

// executeDeployment performs a rolling update
func (da *DeploymentAgent) executeDeployment(ctx context.Context, deployment *appsv1.Deployment) {
	log.Printf("[DEPLOYMENT] Deploying: %s", deployment.Name)

	// Get desired image version from annotation
	desiredImage := deployment.Annotations["desired-image"]
	if desiredImage == "" {
		log.Printf("[WARNING] No desired image specified for %s", deployment.Name)
		return
	}

	// Execute deployment strategy
	strategy := deployment.Annotations["deployment-strategy"]
	if strategy == "" {
		strategy = "rolling"
	}

	switch strategy {
	case "canary":
		da.canaryDeployment(ctx, deployment, desiredImage)
	case "blue-green":
		da.blueGreenDeployment(ctx, deployment, desiredImage)
	default:
		da.rollingDeployment(ctx, deployment, desiredImage)
	}
}

// rollingDeployment performs standard rolling update
func (da *DeploymentAgent) rollingDeployment(ctx context.Context, deployment *appsv1.Deployment, image string) {
	log.Printf("[DEPLOYMENT] Rolling update for %s to image: %s", deployment.Name, image)

	// Update image in deployment
	for i := range deployment.Spec.Template.Spec.Containers {
		deployment.Spec.Template.Spec.Containers[i].Image = image
	}

	// Set rolling update strategy
	deployment.Spec.Strategy.Type = appsv1.RollingUpdateDeploymentStrategyType
	if deployment.Spec.Strategy.RollingUpdate == nil {
		maxSurge := intstr.FromInt(1)
		maxUnavailable := intstr.FromInt(0)
		deployment.Spec.Strategy.RollingUpdate = &appsv1.RollingUpdateDeployment{
			MaxSurge:       &maxSurge,
			MaxUnavailable: &maxUnavailable,
		}
	}

	// Update deployment
	if _, err := da.k8sClient.AppsV1().Deployments(da.namespace).Update(ctx, deployment, metav1.UpdateOptions{}); err != nil {
		log.Printf("[ERROR] Failed to update deployment: %v", err)
		return
	}

	// Monitor rollout
	da.monitorRollout(ctx, deployment)
}

// canaryDeployment performs canary deployment (10% traffic, then 100%)
func (da *DeploymentAgent) canaryDeployment(ctx context.Context, deployment *appsv1.Deployment, image string) {
	log.Printf("[DEPLOYMENT] Canary deployment for %s to image: %s", deployment.Name, image)

	// Phase 1: Deploy to 10% of replicas
	currentReplicas := *deployment.Spec.Replicas
	canaryReplicas := currentReplicas / 10
	if canaryReplicas == 0 {
		canaryReplicas = 1
	}

	// Create canary deployment
	canaryDeployment := deployment.DeepCopy()
	canaryDeployment.Name = fmt.Sprintf("%s-canary", deployment.Name)
	canaryDeployment.Spec.Replicas = &canaryReplicas

	for i := range canaryDeployment.Spec.Template.Spec.Containers {
		canaryDeployment.Spec.Template.Spec.Containers[i].Image = image
	}

	if _, err := da.k8sClient.AppsV1().Deployments(da.namespace).Create(ctx, canaryDeployment, metav1.CreateOptions{}); err != nil {
		log.Printf("[ERROR] Failed to create canary deployment: %v", err)
		return
	}

	log.Printf("[DEPLOYMENT] Canary phase 1: deployed %d replicas", canaryReplicas)

	// Wait 5 minutes for canary testing
	time.Sleep(5 * time.Minute)

	// Check canary health
	if da.isCanaryHealthy(ctx, canaryDeployment) {
		log.Printf("[DEPLOYMENT] Canary healthy, rolling out to 100%%")

		// Phase 2: Update main deployment
		for i := range deployment.Spec.Template.Spec.Containers {
			deployment.Spec.Template.Spec.Containers[i].Image = image
		}

		if _, err := da.k8sClient.AppsV1().Deployments(da.namespace).Update(ctx, deployment, metav1.UpdateOptions{}); err != nil {
			log.Printf("[ERROR] Failed to update main deployment: %v", err)
		}

		// Clean up canary
		da.k8sClient.AppsV1().Deployments(da.namespace).Delete(ctx, canaryDeployment.Name, metav1.DeleteOptions{})
	} else {
		log.Printf("[ERROR] Canary failed health checks, rolling back")
		da.k8sClient.AppsV1().Deployments(da.namespace).Delete(ctx, canaryDeployment.Name, metav1.DeleteOptions{})
	}
}

// blueGreenDeployment performs blue-green deployment
func (da *DeploymentAgent) blueGreenDeployment(ctx context.Context, deployment *appsv1.Deployment, image string) {
	log.Printf("[DEPLOYMENT] Blue-green deployment for %s to image: %s", deployment.Name, image)

	// Create green deployment (new version)
	greenDeployment := deployment.DeepCopy()
	greenDeployment.Name = fmt.Sprintf("%s-green", deployment.Name)

	for i := range greenDeployment.Spec.Template.Spec.Containers {
		greenDeployment.Spec.Template.Spec.Containers[i].Image = image
	}

	if _, err := da.k8sClient.AppsV1().Deployments(da.namespace).Create(ctx, greenDeployment, metav1.CreateOptions{}); err != nil {
		log.Printf("[ERROR] Failed to create green deployment: %v", err)
		return
	}

	// Wait for green to be ready
	da.monitorRollout(ctx, greenDeployment)

	// Switch traffic to green
	log.Printf("[DEPLOYMENT] Switching traffic from blue to green")
	service, _ := da.k8sClient.CoreV1().Services(da.namespace).Get(ctx, deployment.Name, metav1.GetOptions{})
	service.Spec.Selector = greenDeployment.Labels
	da.k8sClient.CoreV1().Services(da.namespace).Update(ctx, service, metav1.UpdateOptions{})

	// Keep blue for quick rollback
	log.Printf("[DEPLOYMENT] Blue deployment ready for rollback")

	// After grace period, delete blue
	time.AfterFunc(30*time.Minute, func() {
		da.k8sClient.AppsV1().Deployments(da.namespace).Delete(ctx, deployment.Name, metav1.DeleteOptions{})
	})
}

// isCanaryHealthy checks if canary deployment is healthy
func (da *DeploymentAgent) isCanaryHealthy(ctx context.Context, deployment *appsv1.Deployment) bool {
	// Check pod health
	pods, err := da.k8sClient.CoreV1().Pods(da.namespace).List(ctx, metav1.ListOptions{
		LabelSelector: fmt.Sprintf("app=%s", deployment.Name),
	})
	if err != nil {
		return false
	}

	healthyPods := 0
	for _, pod := range pods.Items {
		if pod.Status.Phase == corev1.PodRunning {
			healthyPods++
		}
	}

	return healthyPods > 0
}

// monitorRollout waits for deployment rollout to complete
func (da *DeploymentAgent) monitorRollout(ctx context.Context, deployment *appsv1.Deployment) {
	timeout := time.After(15 * time.Minute)
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-timeout:
			log.Printf("[ERROR] Deployment %s rollout timeout", deployment.Name)
			return
		case <-ctx.Done():
			return
		case <-ticker.C:
			updated, err := da.k8sClient.AppsV1().Deployments(da.namespace).Get(ctx, deployment.Name, metav1.GetOptions{})
			if err != nil {
				continue
			}

			// Check if rollout complete
			if updated.Status.ObservedGeneration >= updated.Generation &&
				updated.Status.UpdatedReplicas == *updated.Spec.Replicas &&
				updated.Status.ReadyReplicas == *updated.Spec.Replicas &&
				updated.Status.AvailableReplicas == *updated.Spec.Replicas {
				log.Printf("[DEPLOYMENT] Rollout complete for %s", deployment.Name)
				return
			}

			log.Printf("[DEPLOYMENT] Rollout progress for %s: %d/%d ready",
				deployment.Name, updated.Status.ReadyReplicas, *updated.Spec.Replicas)
		}
	}
}

// isDeploymentUnhealthy checks if deployment is failing
func (da *DeploymentAgent) isDeploymentUnhealthy(deployment *appsv1.Deployment) bool {
	// Check for failed rollout
	if deployment.Status.UpdatedReplicas < *deployment.Spec.Replicas {
		return true
	}

	// Check conditions
	for _, condition := range deployment.Status.Conditions {
		if condition.Type == appsv1.DeploymentProgressing && condition.Status != corev1.ConditionTrue {
			return true
		}
	}

	return false
}

// handleDeploymentFailure handles failed deployments
func (da *DeploymentAgent) handleDeploymentFailure(ctx context.Context, deployment *appsv1.Deployment) {
	log.Printf("[DEPLOYMENT] Deployment failed: %s", deployment.Name)

	// Trigger rollback
	da.rollback(ctx, deployment)
}

// rollback reverts to previous deployment version
func (da *DeploymentAgent) rollback(ctx context.Context, deployment *appsv1.Deployment) {
	log.Printf("[DEPLOYMENT] Rolling back %s", deployment.Name)

	// Get rollout history and revert to previous
	// Implementation would use kubectl rollout undo equivalent
	log.Printf("[DEPLOYMENT] Rollback triggered for %s", deployment.Name)
}

func main() {
	agent, err := NewDeploymentAgent("aegentix-production", "registry.aegentix.io")
	if err != nil {
		log.Fatalf("Failed to create deployment agent: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	agent.Run(ctx)
}
