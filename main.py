
from fastapi import FastAPI
from routers import airtable
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(airtable.router)
