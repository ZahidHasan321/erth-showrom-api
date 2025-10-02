
from fastapi import FastAPI
from routers import airtable
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

handler = Mangum(app)

origins = [
    "*", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # The list of allowed domains
    allow_credentials=True,           # Allow cookies/authorization headers
    allow_methods=["*"],              # Allow all standard methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],              # Allow all headers (Authorization, Content-Type, etc.)
)

@app.get("/")
def read_root():
    return {"Hello from Team Autolinium, we are grinding"}

app.include_router(airtable.router)
