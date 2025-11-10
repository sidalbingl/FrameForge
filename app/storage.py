"""
FrameForge - Google Cloud Storage Integration
Handles uploading and downloading files to/from GCS, and generating signed URLs.
"""

import os
from datetime import timedelta
from typing import Optional

# Try to import Google Cloud Storage, provide stub if not available
try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    print("Warning: google-cloud-storage not available. Using stub implementation.")


def get_storage_client():
    """
    Get a Google Cloud Storage client.
    Uses default credentials (service account or user credentials).
    
    Returns:
        storage.Client instance or None if GCS not available
    """
    if not GCS_AVAILABLE:
        return None
    
    try:
        return storage.Client()
    except Exception as e:
        print(f"Error creating GCS client: {e}")
        print("Make sure GOOGLE_APPLICATION_CREDENTIALS is set or running on GCP")
        return None


def upload_to_gcs(
    local_file_path: str,
    bucket_name: str,
    gcs_blob_name: str,
    content_type: Optional[str] = None
) -> bool:
    """
    Upload a local file to Google Cloud Storage.
    
    Args:
        local_file_path: Path to local file to upload
        bucket_name: Name of GCS bucket
        gcs_blob_name: Destination path/name in GCS (e.g., "videos/my_video.mp4")
        content_type: Optional MIME type (auto-detected if None)
        
    Returns:
        True if successful, False otherwise
    """
    if not GCS_AVAILABLE:
        print(f"Stub: Would upload {local_file_path} to gs://{bucket_name}/{gcs_blob_name}")
        return True
    
    client = get_storage_client()
    if client is None:
        print("GCS client not available. Stub upload.")
        return False
    
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_blob_name)
        
        # Auto-detect content type if not provided
        if content_type is None:
            if local_file_path.endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            elif local_file_path.endswith('.png'):
                content_type = 'image/png'
            elif local_file_path.endswith('.mp4'):
                content_type = 'video/mp4'
            else:
                content_type = 'application/octet-stream'
        
        blob.content_type = content_type
        
        # Upload file
        blob.upload_from_filename(local_file_path)
        print(f"✅ Uploaded {local_file_path} to gs://{bucket_name}/{gcs_blob_name}")
        
        # Make blob public immediately after upload
        try:
            blob.make_public()
            print(f"✅ Made blob public")
        except Exception as e:
            print(f"⚠️ Could not make blob public (may need bucket permissions): {e}")
        
        return True
    
    except NotFound:
        print(f"❌ Bucket {bucket_name} not found. Please create it first.")
        return False
    except Exception as e:
        print(f"❌ Error uploading to GCS: {e}")
        return False


def download_from_gcs(
    bucket_name: str,
    gcs_blob_name: str,
    local_file_path: str
) -> bool:
    """
    Download a file from Google Cloud Storage to local filesystem.
    
    Args:
        bucket_name: Name of GCS bucket
        gcs_blob_name: Source path in GCS
        local_file_path: Destination path on local filesystem
        
    Returns:
        True if successful, False otherwise
    """
    if not GCS_AVAILABLE:
        print(f"Stub: Would download gs://{bucket_name}/{gcs_blob_name} to {local_file_path}")
        return True
    
    client = get_storage_client()
    if client is None:
        print("GCS client not available. Stub download.")
        return False
    
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_blob_name)
        
        blob.download_to_filename(local_file_path)
        print(f"Downloaded gs://{bucket_name}/{gcs_blob_name} to {local_file_path}")
        return True
    
    except NotFound:
        print(f"Blob gs://{bucket_name}/{gcs_blob_name} not found")
        return False
    except Exception as e:
        print(f"Error downloading from GCS: {e}")
        return False


def get_signed_url(
    bucket_name: str,
    gcs_blob_name: str,
    expiration_minutes: int = 60
) -> str:
    """
    Generate a signed URL for accessing a GCS blob without authentication.
    Falls back to public URL if signed URL generation fails.
    
    Args:
        bucket_name: Name of GCS bucket
        gcs_blob_name: Path to blob in GCS
        expiration_minutes: URL expiration time in minutes (default: 60)
        
    Returns:
        Signed URL string (or public URL if signed URL fails)
    """
    if not GCS_AVAILABLE:
        # Return a public URL for local development
        public_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_blob_name}"
        print(f"⚠️ GCS not available, using public URL: {public_url}")
        return public_url
    
    client = get_storage_client()
    if client is None:
        public_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_blob_name}"
        print(f"⚠️ GCS client unavailable, using public URL: {public_url}")
        return public_url
    
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_blob_name)
        
        # Try to generate signed URL
        try:
            url = blob.generate_signed_url(
                expiration=timedelta(minutes=expiration_minutes),
                method='GET'
            )
            print(f"✅ Generated signed URL for {gcs_blob_name}")
            return url
        except Exception as sign_error:
            print(f"⚠️ Signed URL failed ({sign_error}), using public URL instead")
            # Fallback to public URL
            public_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_blob_name}"
            return public_url
    
    except Exception as e:
        print(f"❌ Error in get_signed_url: {e}")
        # Fallback to public URL
        return f"https://storage.googleapis.com/{bucket_name}/{gcs_blob_name}"


def delete_from_gcs(bucket_name: str, gcs_blob_name: str) -> bool:
    """
    Delete a blob from Google Cloud Storage.
    
    Args:
        bucket_name: Name of GCS bucket
        gcs_blob_name: Path to blob to delete
        
    Returns:
        True if successful, False otherwise
    """
    if not GCS_AVAILABLE:
        print(f"Stub: Would delete gs://{bucket_name}/{gcs_blob_name}")
        return True
    
    client = get_storage_client()
    if client is None:
        return False
    
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_blob_name)
        blob.delete()
        print(f"Deleted gs://{bucket_name}/{gcs_blob_name}")
        return True
    
    except NotFound:
        print(f"Blob gs://{bucket_name}/{gcs_blob_name} not found")
        return False
    except Exception as e:
        print(f"Error deleting from GCS: {e}")
        return False


def list_gcs_files(bucket_name: str, prefix: str = "") -> list[str]:
    """
    List all files in a GCS bucket with optional prefix filter.
    
    Args:
        bucket_name: Name of GCS bucket
        prefix: Optional prefix to filter files (e.g., "videos/")
        
    Returns:
        List of blob names
    """
    if not GCS_AVAILABLE:
        return []
    
    client = get_storage_client()
    if client is None:
        return []
    
    try:
        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    
    except Exception as e:
        print(f"Error listing GCS files: {e}")
        return []