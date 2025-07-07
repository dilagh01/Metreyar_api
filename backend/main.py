from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# لیست دامنه‌هایی که اجازه دارند (برای همه: ['*'])
origins = [
    "http://localhost:3000",
    "https://dilagh01.github.io",
    "https://homkar.ir",
    "*"  # برای تست، ولی در Production پیشنهاد نمی‌شود
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # یا ['*']
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
def read_hello():
    return {"message": "Hello from FastAPI 🎉"}
