from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import subprocess
import threading
import time
import uvicorn

app = FastAPI(title="Jupiter FAQ Bot", description="A conversational AI bot for Jupiter banking FAQs")

streamlit_process = None

def start_streamlit():
    """Start Streamlit server in background"""
    global streamlit_process
    try:
        streamlit_process = subprocess.Popen([
            "streamlit", "run", "demo/streamlit_app.py",
            "--server.port", "8502",
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ])
        print("Streamlit server started on port 8502")
    except Exception as e:
        print(f"Failed to start Streamlit: {e}")

@app.on_event("startup")
async def startup_event():
    """Start Streamlit when FastAPI starts"""
    streamlit_thread = threading.Thread(target=start_streamlit)
    streamlit_thread.daemon = True
    streamlit_thread.start()
    
    time.sleep(3)

@app.get("/")
async def root():
    """Redirect to Streamlit app"""
    return RedirectResponse(url="/streamlit")

@app.get("/streamlit")
async def streamlit_redirect():
    """Redirect to Streamlit app running on port 8502"""
    return RedirectResponse(url="http://localhost:8502")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Jupiter FAQ Bot"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
