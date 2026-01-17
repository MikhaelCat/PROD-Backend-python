from fastapi import FastAPI
from solution.api import auth_router, users_router, transactions_router, fraud_rules_router
import uvicorn

app = FastAPI(title="Anti-fraud Service API", version="1.3.0")

# подключение маршрутов
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(fraud_rules_router, prefix="/api/v1")

@app.get("/api/v1/ping")
def ping():
    """эндпоинт проверки работоспособности"""
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)