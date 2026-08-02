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


class ResourceRenewException(Exception):
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self.message = f"Resource {resource_id} cannot be renewed"
        super().__init__(self.message)


class ResourceLeaseValidationException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ResourceBlockException(Exception):
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self.message = f"Resource {resource_id} cannot be blocked"
        super().__init__(self.message)
