import uvicorn

from api import app
from config.default import APP_PORT

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
