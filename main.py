from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from wakeup import SimpleWakeUpApplication
from sipsimple.storage import FileStorage


class CallInput(BaseModel):
    phone: str
    id: str


application = SimpleWakeUpApplication()
application.start(FileStorage("config"))
application.set_accounts(
    [{"id": "187188@sip.zadarma.com", "password": "GerDitOdalsvegen300Ja"}]
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/call")
async def call(call_input: CallInput):
    target_uri = f"sip:{call_input.phone}@sip.zadarma.com"
    application.call(target_uri)
    return {
        "message": f"Vekking igangsatt mot {target_uri} med provider: x og brukernavn: y."
    }
