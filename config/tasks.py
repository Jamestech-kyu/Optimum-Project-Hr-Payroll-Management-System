import time

from celery import shared_task


@shared_task
def test_background_task(name):
    time.sleep(5)
    return f"Hello {name}, the background task completed successfully."