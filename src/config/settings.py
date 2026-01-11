import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """Central configuration for Kinetic Spark (Serverless Edition)."""
    
    # Core GCP Info
    PROJECT_ID = os.getenv("PROJECT_ID")
    REGION = os.getenv("REGION", "us-central1")
    
    # Storage (Required for Serverless logs/dependencies)
    GCS_BUCKET = os.getenv("GCS_BUCKET")
    
    # Serverless Network Configuration (Crucial for Batches)
    # Serverless jobs often fail if they can't access Private Google Access
    SUBNET_URI = os.getenv("SUBNET_URI", "default") 
    
    # Security
    SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")

    @classmethod
    def validate(cls):
        """Ensures critical variables are loaded."""
        required_vars = [cls.PROJECT_ID, cls.GCS_BUCKET]
        if not all(required_vars):
            raise ValueError("❌ Missing PROJECT_ID or GCS_BUCKET in .env file.")
        print(f"✅ Configuration Loaded: Serverless Batch Mode ({cls.REGION})")

if __name__ == "__main__":
    try:
        Config.validate()
    except ValueError as e:
        print(e)