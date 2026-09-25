import React, { useState } from 'react';
import { Mic, MicOff, Activity, Cpu, HardDrive, Terminal } from 'lucide-react';
import { queryLocalModel, LOCAL_AI_CONFIG } from '../apiConfig';

export const VRPortalVoiceOnly: React.FC = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [logs, setLogs] = useState<string[]>(['[System Initialized] - Fully Local Stack Active']);

  const addLog = (msg: string) => setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 15)]);

  const toggleVoice = () => {
    if (!isListening) {
      setIsListening(true);
      addLog('Voice input stream initialized.');
    } else {
      setIsListening(false);
      addLog('Processing captured local voice frame...');
      handlePromptExecute(transcript || 'Ping local engine status.');
    }
  };

  const handlePromptExecute = async (input: string) => {
    addLog(`Sending to local inference (${LOCAL_AI_CONFIG.baseUrl})...`);
    const result = await queryLocalModel(input);
    setAiResponse(result);
    addLog('Response rendered from local GGUF runtime.');
  };

  return (
    <div style={{ padding: '24px', backgroundColor: '#0f172a', color: '#f8fafc', minHeight: '100vh', fontFamily: 'monospace' }}>
      <header style={{ borderBottom: '1px solid #334155', paddingBottom: '16px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0, color: '#38bdf8' }}>SOVEREIGN OS // LOCAL PORTAL</h1>
          <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '14px' }}>Zero Cloud Dependencies • Pure Hardware Execution</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <span style={{ padding: '6px 12px', borderRadius: '4px', backgroundColor: '#1e293b', border: '1px solid #475569', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cpu size={14} color="#38bdf8" /> Port: 1234 (Local AI)
          </span>
          <span style={{ padding: '6px 12px', borderRadius: '4px', backgroundColor: '#1e293b', border: '1px solid #475569', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <HardDrive size={14} color="#4ade80" /> Path: C:\SovereignOS
          </span>
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '24px' }}>
        <main style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ backgroundColor: '#1e293b', padding: '24px', borderRadius: '8px', border: '1px solid #334155', textAlign: 'center' }}>
            <button
              onClick={toggleVoice}
              style={{
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                border: 'none',
                backgroundColor: isListening ? '#ef4444' : '#0284c7',
                color: '#fff',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: isListening ? '0 0 20px #ef4444' : '0 0 10px #0284c7'
              }}
            >
              {isListening ? <MicOff size={36} /> : <Mic size={36} />}
            </button>
            <h3 style={{ marginTop: '16px', color: isListening ? '#f87171' : '#38bdf8' }}>
              {isListening ? 'LISTENING TO LOCAL AUDIO STREAM...' : 'CLICK TO ENGAGE VOICE'}
            </h3>
            <input
              type="text"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Or type local command prompt here..."
              style={{ width: '100%', padding: '12px', backgroundColor: '#0f172a', border: '1px solid #475569', color: '#fff', borderRadius: '4px', marginTop: '12px', boxSizing: 'border-box' }}
            />
            <button
              onClick={() => handlePromptExecute(transcript)}
              style={{ marginTop: '12px', padding: '8px 16px', backgroundColor: '#334155', color: '#fff', border: '1px solid #475569', borderRadius: '4px', cursor: 'pointer' }}
            >
              Execute Local Prompt
            </button>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '20px', borderRadius: '8px', border: '1px solid #334155', flexGrow: 1 }}>
            <h3 style={{ marginTop: 0, color: '#4ade80', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={18} /> LOCAL MODEL RESPONSE STREAM
            </h3>
            <div style={{ backgroundColor: '#0f172a', padding: '16px', borderRadius: '4px', border: '1px solid #1e293b', minHeight: '150px', whiteSpace: 'pre-wrap', color: '#e2e8f0' }}>
              {aiResponse || '// Responses from your local LLM engine will stream here...'}
            </div>
          </div>
        </main>

        <aside style={{ backgroundColor: '#1e293b', padding: '20px', borderRadius: '8px', border: '1px solid #334155', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ marginTop: 0, color: '#f59e0b', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={18} /> LOCAL SYSTEM LOGS
          </h3>
          <div style={{ backgroundColor: '#0f172a', padding: '12px', borderRadius: '4px', flexGrow: 1, overflowY: 'auto', fontSize: '12px', color: '#94a3b8' }}>
            {logs.map((log, idx) => (
              <div key={idx} style={{ marginBottom: '6px' }}>{log}</div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
};
