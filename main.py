
from fastapi import FastAPI
from routers import airtable
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello from Team Autolinium, we are grinding"}

app.include_router(airtable.router)
