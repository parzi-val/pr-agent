from fastapi import FastAPI
from pr_agent.api.routes import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PR Agent API", version="0.1.0")

app.include_router(router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
