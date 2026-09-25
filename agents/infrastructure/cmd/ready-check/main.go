package main

import (
	"fmt"
	"os"
)

func main() {
	port := os.Getenv("HEALTH_CHECK_PORT")
	if port == "" {
		port = "8080"
	}

	// Simple readiness check
	resp, err := http.Get(fmt.Sprintf("http://localhost:%s/ready", port))
	if err != nil {
		fmt.Printf("FAILED: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		fmt.Printf("FAILED: status %d\n", resp.StatusCode)
		os.Exit(1)
	}

	fmt.Println("OK")
	os.Exit(0)
}
