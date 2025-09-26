
from fastapi import FastAPI
from routers import airtable
from mangum import Mangum


app = FastAPI()

handler = Mangum(app)

@app.get("/")
def read_root():
    return {"Hello from Team Autolinium, we are grinding"}

app.include_router(airtable.router)
