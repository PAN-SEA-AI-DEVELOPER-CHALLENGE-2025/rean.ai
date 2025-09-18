import boto3
import aioboto3
import asyncio
import logging
from typing import Optional, BinaryIO, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from app.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for AWS S3 operations"""
    
    def __init__(self):
        self.bucket_name = settings.aws_s3_bucket
        self.region = settings.aws_region
        self.endpoint_url = settings.aws_s3_endpoint_url
        self.use_ssl = settings.aws_s3_use_ssl
        self.verify_ssl = settings.aws_s3_verify_ssl
        
        # Prepare client kwargs
        client_kwargs = {
            'aws_access_key_id': settings.aws_access_key_id,
            'aws_secret_access_key': settings.aws_secret_access_key,
            'region_name': self.region,
            'use_ssl': self.use_ssl,
            'verify': self.verify_ssl
        }
        
        # Only add endpoint_url if it's not empty
        if self.endpoint_url and self.endpoint_url.strip():
            client_kwargs['endpoint_url'] = self.endpoint_url
        
        # Initialize synchronous client
        self.s3_client = boto3.client('s3', **client_kwargs)
        
        # Initialize async session
        self.session = aioboto3.Session()
    
    def _get_s3_resource(self):
        """Get S3 resource for synchronous operations"""
        resource_kwargs = {
            'aws_access_key_id': settings.aws_access_key_id,
            'aws_secret_access_key': settings.aws_secret_access_key,
            'region_name': self.region,
            'use_ssl': self.use_ssl,
            'verify': self.verify_ssl
        }
        
        # Only add endpoint_url if it's not empty
        if self.endpoint_url and self.endpoint_url.strip():
            resource_kwargs['endpoint_url'] = self.endpoint_url
            
        return boto3.resource('s3', **resource_kwargs)
    
    async def upload_file(
        self, 
        file_path: str, 
        s3_key: str, 
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """Upload a file to S3 asynchronously"""
        try:
            # Prepare client kwargs
            client_kwargs = {
                'aws_access_key_id': settings.aws_access_key_id,
                'aws_secret_access_key': settings.aws_secret_access_key,
                'region_name': self.region,
                'use_ssl': self.use_ssl,
                'verify': self.verify_ssl
            }
            
            # Only add endpoint_url if it's not empty
            if self.endpoint_url and self.endpoint_url.strip():
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            async with self.session.client('s3', **client_kwargs) as s3_client:

                extra_args = {"ACL": "private"}
                if content_type:
                    extra_args['ContentType'] = content_type
                if metadata:
                    extra_args['Metadata'] = metadata
                # Server-side encryption if configured
                try:
                    kms_key = getattr(settings, 'aws_kms_key_id', None)
                    if kms_key:
                        extra_args['ServerSideEncryption'] = 'aws:kms'
                        extra_args['SSEKMSKeyId'] = kms_key
                    else:
                        extra_args['ServerSideEncryption'] = 'AES256'
                except Exception:
                    pass
                
                await s3_client.upload_file(
                    file_path, 
                    self.bucket_name, 
                    s3_key,
                    ExtraArgs=extra_args
                )
                
                logger.info(f"Successfully uploaded {file_path} to S3 as {s3_key}")
                return True
                
        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return False
    
    async def upload_fileobj(
        self, 
        file_obj: BinaryIO, 
        s3_key: str, 
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """Upload a file object to S3 asynchronously"""
        try:
            # Prepare client kwargs
            client_kwargs = {
                'aws_access_key_id': settings.aws_access_key_id,
                'aws_secret_access_key': settings.aws_secret_access_key,
                'region_name': self.region,
                'use_ssl': self.use_ssl,
                'verify': self.verify_ssl
            }
            
            # Only add endpoint_url if it's not empty
            if self.endpoint_url and self.endpoint_url.strip():
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            async with self.session.client('s3', **client_kwargs) as s3_client:

                extra_args = {"ACL": "private"}
                if content_type:
                    extra_args['ContentType'] = content_type
                if metadata:
                    extra_args['Metadata'] = metadata
                # Server-side encryption if configured
                try:
                    kms_key = getattr(settings, 'aws_kms_key_id', None)
                    if kms_key:
                        extra_args['ServerSideEncryption'] = 'aws:kms'
                        extra_args['SSEKMSKeyId'] = kms_key
                    else:
                        extra_args['ServerSideEncryption'] = 'AES256'
                except Exception:
                    pass
                
                await s3_client.upload_fileobj(
                    file_obj, 
                    self.bucket_name, 
                    s3_key,
                    ExtraArgs=extra_args
                )
                
                logger.info(f"Successfully uploaded file object to S3 as {s3_key}")
                return True
                
        except Exception as e:
            logger.error(f"Error uploading file object to S3: {str(e)}")
            return False
    
    async def download_file(self, s3_key: str, local_path: str) -> bool:
        """Download a file from S3 asynchronously"""
        try:
            # Prepare client kwargs
            client_kwargs = {
                'aws_access_key_id': settings.aws_access_key_id,
                'aws_secret_access_key': settings.aws_secret_access_key,
                'region_name': self.region,
                'use_ssl': self.use_ssl,
                'verify': self.verify_ssl
            }
            
            # Only add endpoint_url if it's not empty
            if self.endpoint_url and self.endpoint_url.strip():
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            async with self.session.client('s3', **client_kwargs) as s3_client:
                
                await s3_client.download_file(
                    self.bucket_name, 
                    s3_key, 
                    local_path
                )
                
                logger.info(f"Successfully downloaded {s3_key} from S3 to {local_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error downloading file from S3: {str(e)}")
            return False
    
    async def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3 asynchronously"""
        try:
            # Prepare client kwargs
            client_kwargs = {
                'aws_access_key_id': settings.aws_access_key_id,
                'aws_secret_access_key': settings.aws_secret_access_key,
                'region_name': self.region,
                'use_ssl': self.use_ssl,
                'verify': self.verify_ssl
            }
            
            # Only add endpoint_url if it's not empty
            if self.endpoint_url and self.endpoint_url.strip():
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            async with self.session.client('s3', **client_kwargs) as s3_client:
                
                await s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                
                logger.info(f"Successfully deleted {s3_key} from S3")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
    
    def get_file_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a presigned URL for file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None
    
    def file_exists(self, s3_key: str) -> bool:
        """Check if a file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking if file exists: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error checking if file exists: {str(e)}")
            return False
    
    def get_file_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a file in S3"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            return None
    
    def list_files(self, prefix: str = "", max_keys: int = 1000) -> list:
        """List files in S3 with optional prefix"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag']
                    })
            
            return files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []


# Global S3 service instance
s3_service = S3Service()

