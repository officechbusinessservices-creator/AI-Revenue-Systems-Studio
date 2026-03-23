from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "AI Revenue Systems Studio API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)