from src.models.db_models import Resource, ResourceVariable
from src.models.pydantic_models import ResourceLeaseOut, ResourceOut


def resource_db_model_to_pydantic(resource_db_obj: Resource) -> ResourceOut:
    resource_dict = resource_db_obj.to_dict()
    resource_dict.pop("lease_token", None)
    resource_dict["variables"] = [var.to_dict() for var in resource_db_obj.variables]
    return ResourceOut(**resource_dict)


def resource_db_model_to_lease_pydantic(resource_db_obj: Resource) -> ResourceLeaseOut:
    resource_dict = resource_db_obj.to_dict()
    resource_dict["variables"] = [var.to_dict() for var in resource_db_obj.variables]
    return ResourceLeaseOut(**resource_dict)


def resource_pydantic_to_db_model(resource_out: ResourceOut) -> Resource:
    resource_data: dict = resource_out.model_dump()

    variables_data = resource_data.pop("variables", [])
    variables_instances = [ResourceVariable(**var) for var in variables_data]

    return Resource(**resource_data, variables=variables_instances)
