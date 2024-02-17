**ToDo:**

- [ ] id and created_at generator
- [ ] add auth
- [ ] add gRPC
- [ ] add optional description for block operation
- [ ] add foreign keys
- [ ] add centralize error handling
- [ ] move tags to variables and search by them

```
==============================================
Centralize Error Handling:

# in rest_api.py
from fastapi import HTTPException, status

@app.exception_handler(ResourceNotFoundException)
def handle_resource_not_found_exception(request: Request, exc: ResourceNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": str(exc)},
    )

@app.exception_handler(ResourceReleaseException)
def handle_resource_release_exception(request: Request, exc: ResourceReleaseException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": str(exc)},
    )

@app.put("/resources/{resource_id}/release", status_code=200)
def release_resource(resource_id: str):
    resource_service.release_resource(resource_id)
    return {"message": f"Resource {resource_id} was released"}

==============================================
```