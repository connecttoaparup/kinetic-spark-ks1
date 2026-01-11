import time
from google.cloud import dataproc_v1
from src.config.settings import Config

class DataprocClient:
    """Handles interaction with Dataproc Serverless."""

    def __init__(self):
        self.project_id = Config.PROJECT_ID
        self.region = Config.REGION
        self.client_endpoint = f"{self.region}-dataproc.googleapis.com:443"
        
        # Connect to the specific region's controller
        self.batch_client = dataproc_v1.BatchControllerClient(
            client_options={"api_endpoint": self.client_endpoint}
        )

    def submit_pyspark_job(self, python_file_uri, job_id=None):
        """Submits a Serverless Spark Batch Job."""
        
        if not job_id:
            job_id = f"ks1-job-{int(time.time())}"

        batch = dataproc_v1.Batch()
        batch.pyspark_batch.main_python_file_uri = python_file_uri
        
        # Serverless Configuration
        batch.environment_config.execution_config.service_account = Config.SERVICE_ACCOUNT_EMAIL
        batch.environment_config.execution_config.subnetwork_uri = Config.SUBNET_URI

        # Construct the Request
        parent = f"projects/{self.project_id}/locations/{self.region}"
        request = dataproc_v1.CreateBatchRequest(
            parent=parent,
            batch=batch,
            batch_id=job_id
        )

        print(f"🚀 Submitting Batch Job: {job_id}...")
        operation = self.batch_client.create_batch(request=request)
        return operation

if __name__ == "__main__":
    try:
        # 1. Initialize
        client = DataprocClient()
        print("✅ Client Initialized.")
        
        # 2. Define where the script lives in the Cloud
        # (Make sure this matches where you uploaded it in Step 2!)
        gcs_script_path = f"gs://{Config.GCS_BUCKET}/test_dp.py"
        
        # 3. Submit
        print(f"🚀 Submitting job using script: {gcs_script_path}")
        operation = client.submit_pyspark_job(gcs_script_path)
        
        print(f"⏳ Job Submitted! Operation Full Name: {operation.operation.name}")
        print("Go to Google Cloud Console > Dataproc > Batches to watch it run.")
        
    except Exception as e:
        print(f"❌ Error: {e}")