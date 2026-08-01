from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx, time
from pathlib import Path

app = FastAPI(title='Sovereign Portal')
ROOT = Path(__file__).parent
UI = ROOT / 'ui'

OCS_URL = 'http://ocs-prime:8005'
RUNTIME_URL = 'http://runtime-prime:8004'

@app.get('/health')
def health():
    return {'status':'healthy','component':'portal','timestamp':time.time()}

@app.get('/api/ocs/registry')
async def ocs_registry():
    async with httpx.AsyncClient() as c:
        r = await c.get(f'{OCS_URL}/registry')
        r.raise_for_status()
        return r.json()

@app.get('/api/runtime/health')
async def runtime_health():
    async with httpx.AsyncClient() as c:
        r = await c.get(f'{RUNTIME_URL}/health')
        r.raise_for_status()
        return r.json()

app.mount('/static', StaticFiles(directory=UI/'static'), name='static')

@app.get('/')
def index():
    return FileResponse(UI/'index.html')
