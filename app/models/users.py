from typing import Any, Dict
from cloud_providers.platforms import CloudProviderType
from database.db_handler import users

def create_user(public_id: str, name: str, email: str, password: str, cloud_provider: str):
    user_id = users.insert_one(
        {
            "public_id": public_id,
            "name": name,
            "email": email,
            "password": password,
            "cloud_provider": cloud_provider
        }
    ).inserted_id
    return user_id


def set_azure_cloud_details(
    public_id: str,
    az_connection_string: str,
    bucket_name: str
    ) -> Dict[str, Any]:
    cloud_info = users.update_one(filter={"public_id": public_id,'cloud_provider':'az'}, update={'$set': {'connection_string':az_connection_string,'bucket_name':bucket_name}})
    return cloud_info.raw_result


def set_aws_cloud_details(
    public_id: str,
    access_key_id: str,
    secret_access_key: str,
    bucket_name: str) -> Dict[str,Any]:
    cloud_info = users.update_one(filter={"public_id": public_id,'cloud_provider':'aws'}, update={'$set': {'access_key':access_key_id,'secret_access_key':secret_access_key, 'bucket_name':bucket_name}})
    return cloud_info.raw_result
