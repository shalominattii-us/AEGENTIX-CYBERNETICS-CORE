// AEGENTIX runtime Service
// Port: 8080
// Built by Sovereign Claw

const express = require("express");
const cors = require("cors");
const app = express();
const port = 8080;

app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => {
    res.json({
        status: "healthy",
        service: "runtime",
        version: "1.0.0",
        timestamp: new Date().toISOString(),
        built: "Complete System Build"
    });
});

app.get("/status", (req, res) => {
    res.json({
        service: "runtime",
        status: "running",
        uptime: process.uptime(),
        memory: process.memoryUsage()
    });
});

app.get("/ready", (req, res) => {
    res.json({ ready: true });
});

app.listen(port, () => {
    console.log("runtime running on port 8080");
    console.log("   http://localhost:8080/health");
});

process.on("SIGTERM", () => {
    console.log("runtime shutting down...");
    process.exit(0);
});