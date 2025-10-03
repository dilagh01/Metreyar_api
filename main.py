from api.v1.endpoints.main import app
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # پورت پیش‌فرض Render
    uvicorn.run(app, host="0.0.0.0", port=port)
