// AEGENTIX hud Service
// Port: 3000
// Built by Sovereign Claw

const express = require("express");
const cors = require("cors");
const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => {
    res.json({
        status: "healthy",
        service: "hud",
        version: "1.0.0",
        timestamp: new Date().toISOString(),
        built: "Complete System Build"
    });
});

app.get("/status", (req, res) => {
    res.json({
        service: "hud",
        status: "running",
        uptime: process.uptime(),
        memory: process.memoryUsage()
    });
});

app.get("/ready", (req, res) => {
    res.json({ ready: true });
});

app.listen(port, () => {
    console.log("hud running on port 3000");
    console.log("   http://localhost:3000/health");
});

process.on("SIGTERM", () => {
    console.log("hud shutting down...");
    process.exit(0);
});