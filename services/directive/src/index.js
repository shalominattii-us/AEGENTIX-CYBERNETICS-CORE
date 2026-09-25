// AEGENTIX directive Service
// Port: 7070
// Built by Sovereign Claw

const express = require("express");
const cors = require("cors");
const app = express();
const port = 7070;

app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => {
    res.json({
        status: "healthy",
        service: "directive",
        version: "1.0.0",
        timestamp: new Date().toISOString(),
        built: "Complete System Build"
    });
});

app.get("/status", (req, res) => {
    res.json({
        service: "directive",
        status: "running",
        uptime: process.uptime(),
        memory: process.memoryUsage()
    });
});

app.get("/ready", (req, res) => {
    res.json({ ready: true });
});

app.listen(port, () => {
    console.log("directive running on port 7070");
    console.log("   http://localhost:7070/health");
});

process.on("SIGTERM", () => {
    console.log("directive shutting down...");
    process.exit(0);
});