import boto3
import os
import uuid

def test_minio():
    print("Testing MinIO Connection...")
    try:
        s3_client = boto3.client('s3',
                                 endpoint_url="http://localhost:4000",
                                 aws_access_key_id='admin',
                                 aws_secret_access_key='paperai2026',
                                 region_name='auto')
        
        bucket_name = 'paperai-media'
        test_filename = f"test_file_{uuid.uuid4().hex[:6]}.txt"
        
        # Create a test file
        with open("test_upload.txt", "w") as f:
            f.write("Hello from PaperAI local testing!")
            
        print(f"Uploading {test_filename} to bucket '{bucket_name}'...")
        s3_client.upload_file("test_upload.txt", bucket_name, test_filename)
        
        url = f"http://localhost:4000/{bucket_name}/{test_filename}"
        print(f"✅ Upload successful!")
        print(f"✅ Access your file at: {url}")
        
    except Exception as e:
        print(f"❌ MinIO Error: {e}")

if __name__ == "__main__":
    test_minio()
