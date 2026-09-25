// AEGENTIX mcp-http Service
// Port: 7072
// Built by Sovereign Claw

const express = require("express");
const cors = require("cors");
const app = express();
const port = 7072;

app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => {
    res.json({
        status: "healthy",
        service: "mcp-http",
        version: "1.0.0",
        timestamp: new Date().toISOString(),
        built: "Complete System Build"
    });
});

app.get("/status", (req, res) => {
    res.json({
        service: "mcp-http",
        status: "running",
        uptime: process.uptime(),
        memory: process.memoryUsage()
    });
});

app.get("/ready", (req, res) => {
    res.json({ ready: true });
});

app.listen(port, () => {
    console.log("mcp-http running on port 7072");
    console.log("   http://localhost:7072/health");
});

process.on("SIGTERM", () => {
    console.log("mcp-http shutting down...");
    process.exit(0);
});