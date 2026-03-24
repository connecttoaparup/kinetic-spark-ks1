---
applyTo: "airflow_plugins/service/**/*.py"
---

# Service Layer Instructions

> Scoped to: `airflow_plugins/service/**/*.py`
> Covers: `bigquery.py`, `dataproc.py`, `airflow_gcs_*.py`, `flow.py` and all other service scripts.

The `service/` layer is where **all business logic lives**. It is called by operators and sensors — never by DAGs directly. Files here must be pure Python classes/functions with no Airflow task constructs.

---

## ✅ Mandatory Structure for Every Service Class

```python
from __future__ import annotations

import logging
from typing import Any

import google.api_core.exceptions
from google.cloud import storage  # or bigquery, dataproc_v1, etc.

from airflow_plugins.utility.exceptions import airflowServiceError
from airflow_plugins.utility.gcs_client_singleton import get_gcs_client  # use singletons

logger = logging.getLogger(__name__)


class GcsFileCopyService:
    """Handles GCS file copy/move operations for airflow ingestion pipelines.

    Args:
        project_id: GCP project ID to run operations against.
        timeout: Timeout in seconds for GCP API calls. Defaults to 300.
    """

    def __init__(self, project_id: str, timeout: int = 300) -> None:
        self._project_id = project_id
        self._timeout = timeout
        self._client: storage.Client | None = None  # lazy init — NOT at module level

    @property
    def client(self) -> storage.Client:
        """Lazily initialise GCS client on first use."""
        if self._client is None:
            self._client = get_gcs_client(project=self._project_id)
        return self._client

    def copy_file(self, source_uri: str, destination_uri: str) -> bool:
        """Copy a file from source to destination GCS path.

        Args:
            source_uri: Full GCS URI (gs://bucket/path/file.csv).
            destination_uri: Full GCS URI for the destination.

        Returns:
            True if copy succeeded.

        Raises:
            airflowServiceError: If the GCP operation fails.
        """
        logger.info("Copying %s → %s", source_uri, destination_uri)
        try:
            src_bucket, src_blob = self._parse_gcs_uri(source_uri)
            dst_bucket, dst_blob = self._parse_gcs_uri(destination_uri)

            source = self.client.bucket(src_bucket).blob(src_blob)
            destination_bucket = self.client.bucket(dst_bucket)

            self.client.copy_blob(
                source, destination_bucket, new_name=dst_blob, timeout=self._timeout
            )
            logger.info("Copy complete")
            return True
        except google.api_core.exceptions.GoogleAPICallError as exc:
            raise airflowServiceError(
                f"GCS copy failed from {source_uri} to {destination_uri}: {exc}"
            ) from exc

    @staticmethod
    def _parse_gcs_uri(uri: str) -> tuple[str, str]:
        """Parse gs://bucket/blob into (bucket, blob)."""
        if not uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {uri!r}")
        _, _, path = uri.partition("gs://")
        bucket, _, blob = path.partition("/")
        return bucket, blob
```

---

## 📋 Service Layer Rules

### GCP Client Rules
- **Never instantiate GCP clients at module level** — Airflow imports all DAG/wheel modules at parse time; a module-level client call will fail in environments without credentials and slow down the scheduler.
- Use **lazy initialisation** via a `@property` or `get_*_client()` singleton from `utility/gcs_client_singleton.py`.
- Always pass an explicit `project` — never rely on the environment default.
- Always pass `timeout` to every GCP API call — never leave it as `None` (infinite).

```python
# ✅ Correct — lazy client
@property
def client(self) -> bigquery.Client:
    if self._client is None:
        self._client = bigquery.Client(project=self._project_id)
    return self._client

# ❌ Wrong — module-level client
client = bigquery.Client()  # fails at import time in CI/CD
```

### GCS-Specific Rules (for `airflow_gcs_*.py` files)
- Always filter `list_blobs()` with a `prefix` — never list an entire bucket.
- Use `match_glob` or `prefix` to narrow results: `client.list_blobs(bucket, prefix=folder_path)`.
- Always handle `google.api_core.exceptions.NotFound` explicitly for blob existence checks — do not use try/except as a flow control substitute.
- GCS URIs must always be validated before use (check `gs://` prefix, non-empty bucket/blob).

### BigQuery-Specific Rules (for `bigquery.py`)
- Always set `job_config` explicitly — never rely on BQ defaults for schema, write disposition, or location.
- Always call `.result()` on query/load jobs to wait for completion and surface errors.
- Use `QueryJobConfig(use_legacy_sql=False)` — standard SQL only.
- For large result sets, use `to_dataframe()` with caution — prefer server-side processing.

### Dataproc-Specific Rules (for `dataproc.py`)
- Always use `dataproc_v1` client — not the deprecated `dataproc_v1beta2`.
- Always wait for job completion with explicit polling — never fire-and-forget.
- Always log the Dataproc job ID so it is traceable in Cloud Logging.

### REST API Rules (for `file_download_rest_api.py`, `json_rest_api_extractor.py`)
- Always set `timeout` on `requests.get/post` — never leave it as the default `None`.
- Always call `response.raise_for_status()` before consuming response body.
- Implement retry logic with exponential backoff for transient HTTP 5xx errors.
- Never log full API responses — they may contain PII or secrets; log only status codes and record counts.

### Error Handling in Service Layer
- Raise `airflowServiceError` (from `utility/exceptions.py`) for all service-level failures — do not raise raw GCP exceptions to operators.
- Always use `raise airflowServiceError("context") from exc` to preserve the original traceback.
- Log the error before raising: `logger.error("Operation failed: %s", exc)`.

### No Airflow Imports in Service Layer
- `from airflow...` imports are **forbidden** in `service/`.
- Services must be independently testable without an Airflow environment.
- If you need Airflow context (e.g., execution date), accept it as a plain string/datetime parameter — do not import `Context`.

```python
# ❌ Forbidden in service/
from airflow.exceptions import AirflowException
from airflow.models import Variable

# ✅ Correct — raise domain exceptions, accept plain params
from airflow_plugins.utility.exceptions import airflowServiceError
```

---

## 🧪 Testing Requirements for Service Layer

```python
# unit_test/service/test_gcs_file_copy_service.py
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from airflow_plugins.service.airflow_gcs_file_copy_move import GcsFileCopyService
from airflow_plugins.utility.exceptions import airflowServiceError


@pytest.fixture
def service():
    return GcsFileCopyService(project_id="test-project")


def test_copy_file_calls_gcs_copy_blob(service):
    with patch.object(type(service), "client", new_callable=PropertyMock) as mock_client:
        mock_gcs = MagicMock()
        mock_client.return_value = mock_gcs
        service.copy_file("gs://src-bucket/file.csv", "gs://dst-bucket/file.csv")
        mock_gcs.copy_blob.assert_called_once()


def test_copy_file_raises_airflow_service_error_on_gcp_failure(service):
    import google.api_core.exceptions
    with patch.object(type(service), "client", new_callable=PropertyMock) as mock_client:
        mock_gcs = MagicMock()
        mock_gcs.copy_blob.side_effect = google.api_core.exceptions.ServiceUnavailable("down")
        mock_client.return_value = mock_gcs
        with pytest.raises(airflowServiceError, match="GCS copy failed"):
            service.copy_file("gs://src/f.csv", "gs://dst/f.csv")


def test_parse_gcs_uri_raises_on_invalid_uri(service):
    with pytest.raises(ValueError, match="Invalid GCS URI"):
        service._parse_gcs_uri("s3://wrong-scheme/path")


def test_client_is_not_instantiated_at_import_time():
    """GCP client must not be created until first use."""
    svc = GcsFileCopyService(project_id="test-project")
    assert svc._client is None  # lazy — not yet created
```
