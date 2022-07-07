import boto3
import logging
import tempfile
from uuid import uuid4
from typing import Any, Dict, List
from abc import ABC, abstractmethod
from enum import Enum
from google.cloud import storage
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from azure.storage.blob import (
    BlobServiceClient,
    ResourceTypes,
    AccountSasPermissions,
    generate_account_sas)


class AWSConnectionError(Exception):
    pass


class FileDownloadError(Exception):
    pass


class ItemNotFound(Exception):
    pass


class RequriedParameterMissing(Exception):
    pass


class FileUploadError(Exception):
    pass


class DeleteOperationError(Exception):
    pass


class AzureConnectionError(Exception):
    pass


class CloudProviderType(Enum):
    """Cloud Providers"""
    GCP = 'gcp'
    AWS = 'aws'
    AZ = 'az'


class StorageAction(ABC):
    """
    Storage Action interface:
    This interface provides actions like:
        get client object,
        download files from blob,
        list files in storage container/bucket,
        delete files from bucket/container,
        upload file to bucket/container
    """
    @abstractmethod
    def create_service_client(self) -> None: pass

    @abstractmethod
    def download_blob(self, name: str) -> Any: pass

    @abstractmethod
    def list_blob(self) -> List[Dict[str,Any]]: pass

    @abstractmethod
    def delete_blob(self, name: str) -> None: pass

    @abstractmethod
    def upload_blob(self, file_path: Any) -> None: pass

    @abstractmethod
    def upload_blob_public(self, file_path: Any) -> None: pass

    @abstractmethod
    def get_temp_blob_link(self, filename: str) -> str: pass


class AzureStorageServiceProvider(StorageAction):
    """Azure Blob Storage Service Provider"""
    conn: str
    container_name: str
    clt: Any

    def __init__(self, connection_string: str, container_name: str) -> None:
        self.conn = connection_string
        self.container_name = container_name

    def create_service_client(self) -> None:
        if not self.conn:
            raise RequriedParameterMissing('Required Connection \
                String Is Missing!')
        try:
            self.clt = BlobServiceClient.from_connection_string(
                self.conn
            )
        except AzureConnectionError as ace:
            logging.error(ace)
            raise AzureConnectionError('Connection string invalid, please check again')

    def get_container_client(self):
        # Checks for container
        # if not exists
        # creates one and returns container client
        return self.clt.get_container_client(self.container_name) \
            if self.clt.get_container_client(self.container_name)\
            else self.clt.create_container(self.container_name)

    def download_blob(self, name: str) -> Any:
        # Download the blob from storage
        blob_client = self.clt.get_blob_client(
            container=self.container_name,
            blob=name
        )
        if blob_client.exists():
            try:
                return str(blob_client.download_blob().readall())
            except Exception:
                raise FileDownloadError(
                    'Something went wrong while downloading!'
                )
        return f'Item: {name} does not found!'
        
    def parse_blob_list(self, blob_lists) -> List[Dict[str,Any]]:
        return [{"filename":blob.name,"bucket_name":blob.container} for blob in blob_lists]

    def list_blob(self) -> List[Dict[str,Any]]:
        # returns the list of items in container
        return self.parse_blob_list(self.get_container_client().list_blobs())

    def delete_blob(self, name: str) -> None:
        # Deletes the item from blob
        blob_client = self.clt.get_blob_client(
            container=self.container_name,
            blob=name
        )
        if blob_client.exists():
            blob_client.delete_blob()
            return True
        return False

    def upload_blob(self, file_path: Any) -> None:
        # Uploads a file to blob storage
        if file_path:
            filename = str(uuid4())+'.'+file_path.filename.split('.')[-1]
            blob_client = self.clt.get_blob_client(
                container=self.container_name,
                blob=filename
            )
            try:
                blob_client.upload_blob(file_path)
            except FileUploadError as e:
                logging.error(e)
                raise FileUploadError('Something went wrong while file upload!')
            logging.info('File: {} upload success'.format(filename))

    def upload_blob_public(self, file_path: Any) -> None:
        # Uploads a file to public blob storage
        if file_path:
            filename = str(uuid4())+'.'+file_path.filename.split('.')[-1]
            blob_client = self.clt.get_blob_client(
                container=self.container_name,
                blob=filename
            )
            try:
                blob_client.upload_blob(file_path)
            except FileUploadError as e:
                logging.error(e)
                raise FileUploadError('Something went wrong while file upload!')
            logging.info('File: {} upload success'.format(filename))

    def get_temp_blob_link(self, filename: str) -> str:
        sas_token = generate_account_sas(
            self.clt.account_name,
            account_key=self.clt.credential.account_key,
            blob_name=filename,
            resource_types=ResourceTypes(object=True),
            permission=AccountSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=10)
        )
        print(self.container_name)
        url = f'https://{self.clt.account_name}.blob.core.windows.net/{self.container_name}/{filename}?{sas_token}'
        return url


class GCPStorageServiceProvider(StorageAction):
    """GCP Storage Service Provider"""
    account_key_json: Any
    bucket_name: str
    clt: storage.Client

    def __init__(self, account_key_json: Any, bucket_name: str) -> None:
        self.account_key_json = account_key_json
        self.bucket_name = bucket_name

    def create_service_client(self) -> None:
        if not self.account_key_json:
            raise RequriedParameterMissing(
                'Required Connection String is Missing!'
            )
        self.clt = storage.Client.from_service_account_json(
            self.account_key_json)

    def download_blob(self, name: str) -> Any:
        self.check_bucket()
        bucket = self.clt.get_bucket(self.bucket_name)
        blob = bucket.get_blob(blob_name=name)
        return blob.download_as_bytes()

    def list_blob(self) -> List[str]:
        self.check_bucket()
        return list(self.clt.list_blobs(bucket_or_name=self.bucket_name))

    def delete_blob(self, name: str) -> None:
        self.check_bucket()
        bucket = self.clt.get_bucket(self.bucket_name)
        blob = bucket.get_blob(blob_name=name)
        try:
            blob.delete()
        except DeleteOperationError as e:
            logging.error(e)

    def upload_blob(self, file_path: Any) -> None:
        self.check_bucket()
        bucket = self.clt.get_bucket(self.bucket_name)
        filename = str(uuid4())+file_path.name.split('.')[-1]
        blob = bucket.blob(filename)
        try:
            with open(file_path, 'rb') as data:
                blob.upload_from_file(data)
        except FileUploadError as e:
            logging.error(e)

    def check_bucket(self):
        if not self.bucket_name:
            raise RequriedParameterMissing(
                    'Bucket Name missing!'
            )


class AWSStorageServiceProvider(StorageAction):
    """AWS Storage Service Provider"""
    access_key_id: str
    secret_access_key: str
    bucket_name: str
    _public_bucket_name: str = 'public_bucket'
    clt: Any

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        bucket_name: str
    ) -> None:
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name

    def create_service_client(self):
        if not (
            self.access_key and self.secret_key
            ):
            raise RequriedParameterMissing(
                'Required Secret key or access key is Missing!'
            )
        try:
            self.clt = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
        except AWSConnectionError as ace:
            raise AWSConnectionError('Secrets not valid, please check again!')

    def download_blob(self, name: str) -> Any:
        try:
            with tempfile.NamedTemporaryFile(suffix=name.split('.')[-1]) as data:
                self.clt.download_fileobj(self.bucket_name, name, data)
                data.seek(0)
                file_as_string = data.read()
                return str(file_as_string)
        except Exception as e:
            logging.error(e)
            raise FileDownloadError('Something went wrong while downloading!')

    def return_parsed_blob_list(self,blob_dict: Dict) -> Dict:
        return [ {'filename': item.get('Key'), 'bucket_name': blob_dict.get('Name') } for item in blob_dict.get('Contents')]
        

    def list_blob(self) -> List[Dict[str,Any]]:
        # Lists the existing buckets in AWS S3
        return self.return_parsed_blob_list(self.clt.list_objects_v2(Bucket=self.bucket_name, Delimiter=','))

    def delete_blob(self, name: str) -> bool:
        if not (name in [item.get('filename') for item in self.list_blob()]):
            return False
        try:
            self.clt.delete_object(Bucket=self.bucket_name, Key=name)
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def upload_blob(self, file_path: Any) -> None:
        if file_path:
            filename = str(uuid4())+'.'+file_path.filename.split('.')[-1]
            try:
                resp = self.clt.upload_fileobj(
                        file_path,
                        self.bucket_name,
                        filename)
            except ClientError as e:
                logging.error(e)
                raise FileUploadError(
                    f'Something went wrong while file uploading to S3 Bucket: {self.bucket_name}'
                    )
            logging.info('File: {} upload success'.format(filename))

    def upload_blob_public(self, file_path: Any) -> None:
        if file_path:
            filename = str(uuid4())+'.'+file_path.filename.split('.')[-1]
            try:
                resp = self.clt.upload_fileobj(
                    file_path,
                    self.bucket_name,
                    filename)
            except ClientError:
                raise FileUploadError(
                    f'Something went wrong while \
                        file uploading to\
                             S3 Bucket: {self._public_bucket_name}'
                    )
            logging.info('File: {} upload success'.format(filename))

    def get_temp_blob_link(self, filename: str) -> str:
        if filename:
            url = self.clt.generate_presigned_url(
                'get_object',
                Params = {
                    'Bucket': self.bucket_name,
                    'Key': filename
                },
                HttpMethod="GET",
                ExpiresIn=300)
            return url


class ServiceProvider:
    """ Common Service Provider for AWS, GCP and Azure Blob Storage"""
    def __init__(self, provider: StorageAction) -> None:
        self.provider = provider

    def create_client(self):
        self.provider.create_service_client()
