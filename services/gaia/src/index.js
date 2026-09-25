// AEGENTIX gaia Service
// Port: 8090
// Built by Sovereign Claw

const express = require("express");
const cors = require("cors");
const app = express();
const port = 8090;

app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => {
    res.json({
        status: "healthy",
        service: "gaia",
        version: "1.0.0",
        timestamp: new Date().toISOString(),
        built: "Complete System Build"
    });
});

app.get("/status", (req, res) => {
    res.json({
        service: "gaia",
        status: "running",
        uptime: process.uptime(),
        memory: process.memoryUsage()
    });
});

app.get("/ready", (req, res) => {
    res.json({ ready: true });
});

app.listen(port, () => {
    console.log("gaia running on port 8090");
    console.log("   http://localhost:8090/health");
});

process.on("SIGTERM", () => {
    console.log("gaia shutting down...");
    process.exit(0);
});