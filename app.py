from fastapi import FastAPI

app = FastAPI(title="DRAGON AI CORE", version="1.0.0")


@app.get("/")
def root():
    return {
        "system": "DRAGON AI CORE",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
