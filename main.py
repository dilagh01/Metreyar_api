import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'api')))

from v1.endpoints.main import app
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
