export const LOCAL_AI_CONFIG = {
  baseUrl: 'http://127.0.0.1:1234/v1',
  model: 'local-model',
  localServicePort: 8080,
  dxvrSocketPort: 9001
};

export async function queryLocalModel(prompt: string) {
  try {
    const response = await fetch(`${LOCAL_AI_CONFIG.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.7,
        max_tokens: 500
      })
    });
    if (!response.ok) throw new Error(`HTTP error ${response.status}`);
    const data = await response.json();
    return data.choices[0]?.message?.content || 'No response from local model.';
  } catch (err: any) {
    return `[Local AI Engine Offline]: Ensure LM Studio is active on port 1234. (${err.message})`;
  }
}
