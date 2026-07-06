"""IngestionOperator (prototype stub).

Reads a DAG JSON config task entry and triggers the matching ingestion job.
Confirm Airflow version (2.x vs 3.x) before extending - base APIs differ.
"""


class IngestionOperator:
    def __init__(self, job_name: str):
        self.job_name = job_name
