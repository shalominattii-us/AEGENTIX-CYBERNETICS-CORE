const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');

const app = express();
const PORT = 5174;

app.use(cors());
app.use(express.json());

app.post('/api/execute', (req, res) => {
    const { command } = req.body;
    if (!command) {
        return res.status(400).json({ error: 'No command string provided' });
    }
    console.log(`[CYBERDECK BRIDGE] Executing command: ${command}`);
    exec(command, (error, stdout, stderr) => {
        res.json({
            output: stdout || '',
            error: stderr || (error ? error.message : '')
        });
    });
});

app.listen(PORT, () => {
    console.log("=======================================================");
    console.log(" ? CYBERDECK BACKEND BRIDGE RUNNING ON PORT 5174 ");
    console.log("=======================================================");
});
