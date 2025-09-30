from unittest.mock import patch

from app.adapters.driver.worker.consumer import process_video_job


def test_process_video_job_calls_service():
    with patch(
        "app.adapters.driver.worker.consumer.get_process_service"
    ) as mock_service:
        fake_callable = mock_service.return_value
        job_id = "12345"

        process_video_job(job_id)

        mock_service.assert_called_once_with()
        fake_callable.assert_called_once_with(job_id=job_id)
