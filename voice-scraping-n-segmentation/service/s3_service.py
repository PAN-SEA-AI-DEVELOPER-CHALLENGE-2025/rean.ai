"""
AWS S3 Service

This module provides functionality for uploading and managing audio files in AWS S3.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime
import mimetypes


class S3Service:
    """
    Service class for AWS S3 operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the S3 Service.
        
        Args:
            config: Configuration dictionary containing S3 settings
        """
        self.config = config
        self.bucket_name = config.get('s3_bucket_name', 'pansea-storage')
        self.region = config.get('s3_region', 'ap-southeast-1')
        self.prefix = config.get('s3_prefix', 'audio-extractions')
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize S3 client
        try:
            # Prepare S3 client configuration
            s3_config = {
                'region_name': self.region,
                'aws_access_key_id': config.get('aws_access_key_id'),
                'aws_secret_access_key': config.get('aws_secret_access_key')
            }
            
            # Add endpoint URL if specified (for S3-compatible services)
            if config.get('s3_endpoint_url'):
                s3_config['endpoint_url'] = config.get('s3_endpoint_url')
            
            # Configure SSL settings
            s3_config['use_ssl'] = config.get('s3_use_ssl', True)
            s3_config['verify'] = config.get('s3_verify_ssl', True)
            
            self.s3_client = boto3.client('s3', **s3_config)
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def _test_connection(self) -> bool:
        """
        Test S3 connection and bucket access.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                self.logger.error(f"S3 bucket not found: {self.bucket_name}")
            elif error_code == '403':
                self.logger.error(f"Access denied to S3 bucket: {self.bucket_name}")
            else:
                self.logger.error(f"S3 connection error: {e}")
            return False
        except NoCredentialsError:
            self.logger.error("AWS credentials not found")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected S3 error: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if S3 service is available and configured.
        
        Returns:
            bool: True if S3 is available
        """
        return self.s3_client is not None
    
    def upload_file(
        self,
        local_file_path: str,
        s3_key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to S3.
        
        Args:
            local_file_path: Path to the local file
            s3_key: S3 object key (if None, will be generated)
            metadata: Optional metadata to attach to the object
            tags: Optional tags to attach to the object
            
        Returns:
            Dict containing upload result
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'S3 service not available'
            }
        
        try:
            local_path = Path(local_file_path)
            
            if not local_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {local_file_path}'
                }
            
            # Generate S3 key if not provided
            if s3_key is None:
                timestamp = datetime.now().strftime('%Y/%m/%d')
                s3_key = f"{self.prefix}/{timestamp}/{local_path.name}"
            
            # Prepare upload arguments
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Filename': str(local_path)
            }
            
            # Add content type
            content_type, _ = mimetypes.guess_type(str(local_path))
            if content_type:
                upload_args['ExtraArgs'] = {'ContentType': content_type}
            else:
                upload_args['ExtraArgs'] = {'ContentType': 'audio/wav'}
            
            # Add metadata
            if metadata:
                if 'Metadata' not in upload_args['ExtraArgs']:
                    upload_args['ExtraArgs']['Metadata'] = {}
                upload_args['ExtraArgs']['Metadata'].update(metadata)
            
            # Perform upload
            self.s3_client.upload_file(**upload_args)
            
            # Add tags if provided
            if tags:
                tag_set = [{'Key': k, 'Value': v} for k, v in tags.items()]
                self.s3_client.put_object_tagging(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Tagging={'TagSet': tag_set}
                )
            
            # Get file info
            file_size = local_path.stat().st_size
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            self.logger.info(f"Successfully uploaded {local_path.name} to S3: {s3_key}")
            
            return {
                'success': True,
                'data': {
                    's3_key': s3_key,
                    's3_url': s3_url,
                    'bucket': self.bucket_name,
                    'region': self.region,
                    'file_size': file_size,
                    'content_type': content_type or 'audio/wav',
                    'local_path': str(local_path)
                }
            }
            
        except ClientError as e:
            self.logger.error(f"S3 upload failed: {e}")
            return {
                'success': False,
                'error': f'S3 upload error: {e.response["Error"]["Message"]}'
            }
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_files(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 100
    ) -> Dict[str, Any]:
        """
        List files in S3 bucket.
        
        Args:
            prefix: Optional prefix to filter objects
            max_keys: Maximum number of objects to return
            
        Returns:
            Dict containing list of files
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'S3 service not available'
            }
        
        try:
            list_args = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }
            
            if prefix:
                list_args['Prefix'] = prefix
            elif self.prefix:
                list_args['Prefix'] = self.prefix
            
            response = self.s3_client.list_objects_v2(**list_args)
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag'].strip('"'),
                        'storage_class': obj.get('StorageClass', 'STANDARD'),
                        'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                    })
            
            return {
                'success': True,
                'data': {
                    'files': files,
                    'total_count': len(files),
                    'is_truncated': response.get('IsTruncated', False),
                    'bucket': self.bucket_name,
                    'prefix': prefix or self.prefix
                }
            }
            
        except ClientError as e:
            self.logger.error(f"S3 list failed: {e}")
            return {
                'success': False,
                'error': f'S3 list error: {e.response["Error"]["Message"]}'
            }
        except Exception as e:
            self.logger.error(f"List failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_file(self, s3_key: str) -> Dict[str, Any]:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            Dict containing deletion result
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'S3 service not available'
            }
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            self.logger.info(f"Successfully deleted S3 object: {s3_key}")
            
            return {
                'success': True,
                'data': {
                    's3_key': s3_key,
                    'bucket': self.bucket_name
                }
            }
            
        except ClientError as e:
            self.logger.error(f"S3 delete failed: {e}")
            return {
                'success': False,
                'error': f'S3 delete error: {e.response["Error"]["Message"]}'
            }
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_info(self, s3_key: str) -> Dict[str, Any]:
        """
        Get information about an S3 object.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dict containing file information
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'S3 service not available'
            }
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'success': True,
                'data': {
                    's3_key': s3_key,
                    'size': response['ContentLength'],
                    'last_modified': response['LastModified'].isoformat(),
                    'etag': response['ETag'].strip('"'),
                    'content_type': response.get('ContentType'),
                    'metadata': response.get('Metadata', {}),
                    'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
                }
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return {
                    'success': False,
                    'error': 'File not found in S3'
                }
            else:
                self.logger.error(f"S3 head object failed: {e}")
                return {
                    'success': False,
                    'error': f'S3 error: {e.response["Error"]["Message"]}'
                }
        except Exception as e:
            self.logger.error(f"Get file info failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(
        self,
        s3_key: str,
        local_file_path: str
    ) -> Dict[str, Any]:
        """
        Download a file from S3 to local filesystem.
        
        Args:
            s3_key: S3 object key to download
            local_file_path: Local path where to save the file
            
        Returns:
            Dict containing download result
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'S3 service not available'
            }
        
        try:
            local_path = Path(local_file_path)
            
            # Create directory if it doesn't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file from S3
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                str(local_path)
            )
            
            # Verify file was downloaded
            if not local_path.exists():
                return {
                    'success': False,
                    'error': 'File download completed but file not found locally'
                }
            
            file_size = local_path.stat().st_size
            
            self.logger.info(f"Successfully downloaded S3 file {s3_key} to {local_path}")
            
            return {
                'success': True,
                'data': {
                    's3_key': s3_key,
                    'local_path': str(local_path),
                    'file_size': file_size,
                    'bucket': self.bucket_name
                }
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.error(f"S3 file not found: {s3_key}")
                return {
                    'success': False,
                    'error': f'File not found in S3: {s3_key}'
                }
            else:
                self.logger.error(f"S3 download failed: {e}")
                return {
                    'success': False,
                    'error': f'S3 download error: {e.response["Error"]["Message"]}'
                }
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        method: str = 'get_object'
    ) -> Dict[str, Any]:
        """
        Generate a presigned URL for S3 object access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds
            method: HTTP method ('get_object' or 'put_object')
            
        Returns:
            Dict containing presigned URL
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'S3 service not available'
            }
        
        try:
            url = self.s3_client.generate_presigned_url(
                method,
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            return {
                'success': True,
                'data': {
                    'presigned_url': url,
                    's3_key': s3_key,
                    'expires_in': expiration,
                    'method': method
                }
            }
            
        except ClientError as e:
            self.logger.error(f"Generate presigned URL failed: {e}")
            return {
                'success': False,
                'error': f'S3 error: {e.response["Error"]["Message"]}'
            }
        except Exception as e:
            self.logger.error(f"Generate presigned URL failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
