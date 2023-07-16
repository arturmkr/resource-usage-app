import uvicorn

from config.default import APP_PORT
from rest_api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
