from typing import Any, Dict
from database.db_handler import users
from .platforms import (
    StorageAction,
    CloudProviderType,
    AzureStorageServiceProvider,
    AWSStorageServiceProvider,
    GCPStorageServiceProvider,
    ServiceProvider)


def az(user_cloud: Dict[str,Any]) -> StorageAction:
    connection_string = user_cloud.get('connection_string')
    container_name = user_cloud.get('bucket_name')
    return AzureStorageServiceProvider(connection_string, container_name)


def aws(user_cloud: Dict[str,Any]) -> StorageAction:
    access_key_id = user_cloud.get('access_key')
    secret_access_key = user_cloud.get('secret_access_key')
    bucket_name = user_cloud.get('bucket_name')
    return AWSStorageServiceProvider(
        access_key_id,
        secret_access_key,
        bucket_name)


def gcp(user_cloud: users) -> None: pass
    # account_key_json = user_cloud.account_key_json
    # bucket_name = user_cloud.bucket_name
    # with tempfile.NamedTemporaryFile(suffix='.json') as key_json:
    #     key_json.write(account_key_json)
    #     return GCPStorageServiceProvider(
    #         account_key_json=key_json.name,
    #         bucket_name=bucket_name
    #         )


map_cloud_providers = {
    'aws': CloudProviderType.AWS,
    'gcp': CloudProviderType.GCP,
    'az': CloudProviderType.AZ
}

providers = {
    'gcp': gcp,
    'aws': aws,
    'az': az
}


def get_storage_provider(
    cloud_type: str,
    user_cloud: Dict[str,Any]) -> StorageAction:
    return providers.get(cloud_type)(user_cloud)


def get_service_provider_client(storage_provider: StorageAction)\
     -> ServiceProvider:
    serviceProvider: ServiceProvider = ServiceProvider(storage_provider)
    serviceProvider.create_client()
    return serviceProvider
