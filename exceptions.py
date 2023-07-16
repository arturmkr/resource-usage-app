class ResourceNotFoundException(Exception):
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self.message = f"Resource {resource_id} not found"
        super().__init__(self.message)


class ResourceReleaseException(Exception):
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self.message = f"Resource {resource_id} cannot be released"
        super().__init__(self.message)


class ResourceBlockException(Exception):
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self.message = f"Resource {resource_id} cannot be blocked"
        super().__init__(self.message)
