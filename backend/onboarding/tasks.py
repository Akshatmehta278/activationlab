from celery import shared_task

from .services import process_customer_import


@shared_task(bind=True)
def process_customer_import_task(self, import_id: int):
    """Process one durable import job. Worker-loss redelivery is configured in Django settings."""
    job = process_customer_import(import_id)
    return {"id": job.id, "status": job.status, "imported_rows": job.imported_rows}
