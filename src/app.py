import uvicorn

from src.config.default import get_settings
from src.rest_api import app
from src.ui_app import install_ui

install_ui(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=get_settings().app_port)
