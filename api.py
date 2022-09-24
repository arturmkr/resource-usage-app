import fastapi

app = fastapi.FastAPI(title="resource-usage-app")


@app.get("/healthcheck", status_code=200)
async def healthcheck():
    return "OK"
