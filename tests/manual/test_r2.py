import boto3
import os
import uuid
from dotenv import load_dotenv

def test_r2():
    load_dotenv()
    
    print("Testing Cloudflare R2 Connection...")
    try:
        s3_client = boto3.client('s3',
                                 endpoint_url=os.getenv("R2_ENDPOINT"),
                                 aws_access_key_id=os.getenv('R2_ACCESS_KEY'),
                                 aws_secret_access_key=os.getenv('R2_SECRET_KEY'),
                                 region_name='auto')
        
        bucket_name = os.getenv('R2_BUCKET')
        public_url_base = "https://imgr2.aidocx.us.ci"
        test_filename = f"test_r2_{uuid.uuid4().hex[:6]}.txt"
        
        # Create a test file
        with open("test_r2_upload.txt", "w") as f:
            f.write("Hello from PaperAI R2 testing!")
            
        print(f"Uploading {test_filename} to R2 bucket '{bucket_name}'...")
        s3_client.upload_file("test_r2_upload.txt", bucket_name, test_filename)
        
        url = f"{public_url_base}/{test_filename}"
        print(f"✅ Upload successful!")
        print(f"✅ Public URL: {url}")
        
    except Exception as e:
        print(f"❌ R2 Error: {e}")

if __name__ == "__main__":
    test_r2()
