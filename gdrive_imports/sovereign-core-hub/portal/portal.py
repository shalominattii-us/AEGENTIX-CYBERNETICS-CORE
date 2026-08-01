from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>Sovereign Portal Online</h1><p>RSN Docker Layer Active</p>"
