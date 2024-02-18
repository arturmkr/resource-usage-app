import uvicorn

from src.rest_api import app
from src.config.default import APP_PORT

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
