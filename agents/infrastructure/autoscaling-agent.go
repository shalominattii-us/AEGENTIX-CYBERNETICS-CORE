package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	metricsv1beta1 "k8s.io/metrics/pkg/apis/metrics/v1beta1"
	"k8s.io/metrics/pkg/client/clientset/versioned"
)

// AutoScalingAgent autonomously scales deployments based on metrics
type AutoScalingAgent struct {
	k8sClient      kubernetes.Interface
	metricsClient  versioned.Interface
	namespace      string
	scalingRules   map[string]ScalingRule
}

// ScalingRule defines when and how to scale a deployment
type ScalingRule struct {
	DeploymentName string
	MinReplicas    int32
	MaxReplicas    int32
	CPUThreshold   int64  // percentage
	MemoryThreshold int64 // percentage
	TargetReplicas int32
}

func NewAutoScalingAgent(namespace string) (*AutoScalingAgent, error) {
	config, err := rest.InClusterConfig()
	if err != nil {
		return nil, err
	}

	k8sClient, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	metricsClient, err := versioned.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	return &AutoScalingAgent{
		k8sClient:     k8sClient,
		metricsClient: metricsClient,
		namespace:     namespace,
		scalingRules: map[string]ScalingRule{
			"aegentix-platform": {
				DeploymentName:    "aegentix-platform",
				MinReplicas:       3,
				MaxReplicas:       20,
				CPUThreshold:      70,
				MemoryThreshold:   80,
			},
			"api-gateway": {
				DeploymentName:    "api-gateway",
				MinReplicas:       2,
				MaxReplicas:       10,
				CPUThreshold:      75,
				MemoryThreshold:   85,
			},
			"worker-service": {
				DeploymentName:    "worker-service",
				MinReplicas:       5,
				MaxReplicas:       50,
				CPUThreshold:      60,
				MemoryThreshold:   70,
			},
		},
	}, nil
}

// Run starts continuous scaling monitoring
func (asa *AutoScalingAgent) Run(ctx context.Context) {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	log.Println("[AUTO-SCALING] Agent started")

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			asa.evaluateScaling(ctx)
		}
	}
}

// evaluateScaling checks metrics and scales deployments
func (asa *AutoScalingAgent) evaluateScaling(ctx context.Context) {
	for _, rule := range asa.scalingRules {
		metrics := asa.getDeploymentMetrics(ctx, rule.DeploymentName)
		if metrics == nil {
			continue
		}

		currentReplicas := asa.getCurrentReplicas(ctx, rule.DeploymentName)
		decision := asa.makeScalingDecision(metrics, rule, currentReplicas)

		if decision != currentReplicas {
			log.Printf("[AUTO-SCALING] Scaling %s from %d to %d replicas (CPU: %d%%, Memory: %d%%)",
				rule.DeploymentName, currentReplicas, decision, metrics.AvgCPU, metrics.AvgMemory)
			asa.scaleDeployment(ctx, rule.DeploymentName, decision)
		}
	}
}

// getDeploymentMetrics retrieves current metrics for a deployment
func (asa *AutoScalingAgent) getDeploymentMetrics(ctx context.Context, deploymentName string) *DeploymentMetrics {
	// Get pod metrics
	podMetrics, err := asa.metricsClient.MetricsV1beta1().PodMetricses(asa.namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		log.Printf("[ERROR] Failed to get pod metrics: %v", err)
		return nil
	}

	var totalCPU, totalMemory int64
	var podCount int

	for _, pm := range podMetrics.Items {
		for _, container := range pm.Containers {
			cpu := container.Usage.Cpu().MilliValue()
			memory := container.Usage.Memory().Value()
			totalCPU += cpu
			totalMemory += memory
			podCount++
		}
	}

	if podCount == 0 {
		return nil
	}

	// Get deployment info for limits
	deployment, err := asa.k8sClient.AppsV1().Deployments(asa.namespace).Get(ctx, deploymentName, metav1.GetOptions{})
	if err != nil {
		return nil
	}

	// Calculate limits from deployment spec
	var cpuLimit, memoryLimit int64
	if len(deployment.Spec.Template.Spec.Containers) > 0 {
		limits := deployment.Spec.Template.Spec.Containers[0].Resources.Limits
		cpuLimit = limits.Cpu().MilliValue()
		memoryLimit = limits.Memory().Value()
	}

	avgCPU := (totalCPU / int64(podCount) / cpuLimit) * 100
	avgMemory := (totalMemory / int64(podCount) / memoryLimit) * 100

	return &DeploymentMetrics{
		AvgCPU:    avgCPU,
		AvgMemory: avgMemory,
		PodCount:  int32(podCount),
	}
}

// DeploymentMetrics holds current resource metrics
type DeploymentMetrics struct {
	AvgCPU    int64
	AvgMemory int64
	PodCount  int32
}

// getCurrentReplicas gets current replica count
func (asa *AutoScalingAgent) getCurrentReplicas(ctx context.Context, deploymentName string) int32 {
	deployment, err := asa.k8sClient.AppsV1().Deployments(asa.namespace).Get(ctx, deploymentName, metav1.GetOptions{})
	if err != nil {
		log.Printf("[ERROR] Failed to get deployment: %v", err)
		return 0
	}

	if deployment.Spec.Replicas != nil {
		return *deployment.Spec.Replicas
	}
	return 1
}

// makeScalingDecision determines target replica count
func (asa *AutoScalingAgent) makeScalingDecision(metrics *DeploymentMetrics, rule ScalingRule, current int32) int32 {
	// Scale up if either CPU or memory exceed thresholds
	if metrics.AvgCPU > rule.CPUThreshold || metrics.AvgMemory > rule.MemoryThreshold {
		target := current + 2 // Add 2 pods
		if target > rule.MaxReplicas {
			target = rule.MaxReplicas
		}
		return target
	}

	// Scale down if both CPU and memory are low (with hysteresis)
	if metrics.AvgCPU < (rule.CPUThreshold - 20) && metrics.AvgMemory < (rule.MemoryThreshold - 20) {
		target := current - 1 // Remove 1 pod
		if target < rule.MinReplicas {
			target = rule.MinReplicas
		}
		// Only scale down if we've been low for a while (implement debounce in production)
		return target
	}

	return current
}

// scaleDeployment updates replica count
func (asa *AutoScalingAgent) scaleDeployment(ctx context.Context, deploymentName string, replicas int32) error {
	deployment, err := asa.k8sClient.AppsV1().Deployments(asa.namespace).Get(ctx, deploymentName, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get deployment: %w", err)
	}

	deployment.Spec.Replicas = &replicas

	if _, err := asa.k8sClient.AppsV1().Deployments(asa.namespace).Update(ctx, deployment, metav1.UpdateOptions{}); err != nil {
		return fmt.Errorf("failed to update deployment: %w", err)
	}

	log.Printf("[AUTO-SCALING] Successfully scaled %s to %d replicas", deploymentName, replicas)
	return nil
}

func main() {
	agent, err := NewAutoScalingAgent("aegentix-production")
	if err != nil {
		log.Fatalf("Failed to create auto-scaling agent: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	agent.Run(ctx)
}
