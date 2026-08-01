import uvicorn

from src.config.default import get_settings
from src.rest_api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=get_settings().app_port)
