from fastapi import FastAPI

app = FastAPI(title="Transmute Engine API")

@app.get("/")
async def root():
    return {"message": "Welcome to Transmute Engine"}
