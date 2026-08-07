import logging

from celery import shared_task
from django.db import OperationalError
from django.utils import timezone

from payroll.models import PayrollRun
from payroll.services import PayrollProcessor

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_payroll(self, payroll_run_id):
    try:
        payroll_run = PayrollRun.objects.get(
            pk=payroll_run_id
        )
    except PayrollRun.DoesNotExist:
        logger.warning(
            "PayrollRun %s does not exist.",
            payroll_run_id,
        )
        return {
            "payroll_run_id": payroll_run_id,
            "status": "NOT_FOUND",
        }

    if payroll_run.status in {
        "APPROVED",
        "FINALIZED",
        "CANCELLED",
        "PENDING_APPROVAL",
    }:
        raise ValueError(
            f"Payroll run cannot be processed while status is "
            f"{payroll_run.status}."
        )

    payroll_run.status = "PROCESSING"
    payroll_run.started_at = timezone.now()
    payroll_run.completed_at = None
    payroll_run.error_message = ""

    payroll_run.save(
        update_fields=[
            "status",
            "started_at",
            "completed_at",
            "error_message",
        ]
    )

    def update_progress(
        processed,
        total,
        failed,
        percentage,
    ):
        self.update_state(
            state="PROGRESS",
            meta={
                "payroll_run_id": payroll_run.id,
                "processed": processed,
                "total": total,
                "failed": failed,
                "percentage": str(percentage),
            },
        )

    try:
        summary = PayrollProcessor.process(
            payroll_run,
            progress_callback=update_progress,
        )

        payroll_run.refresh_from_db()

        if summary["failed"] > 0:
            payroll_run.status = "COMPLETED_WITH_ERRORS"
            payroll_run.error_message = (
                f"{summary['failed']} employee payroll record(s) failed."
            )
        else:
            payroll_run.status = "COMPLETED"
            payroll_run.error_message = ""

        payroll_run.completed_at = timezone.now()
        payroll_run.processed_at = timezone.now()

        payroll_run.save(
            update_fields=[
                "status",
                "completed_at",
                "processed_at",
                "error_message",
            ]
        )

        summary["status"] = payroll_run.status

        return summary

    except OperationalError as exc:
        logger.exception(
            "Temporary database error while processing payroll run %s.",
            payroll_run.id,
        )

        if self.request.retries >= self.max_retries:
            payroll_run.status = "FAILED"
            payroll_run.completed_at = timezone.now()
            payroll_run.error_message = str(exc)

            payroll_run.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "error_message",
                ]
            )

            raise

        raise self.retry(
            exc=exc,
            countdown=30 * (2 ** self.request.retries),
        )

    except Exception as exc:
        logger.exception(
            "Payroll processing failed for payroll run %s.",
            payroll_run.id,
        )

        payroll_run.status = "FAILED"
        payroll_run.completed_at = timezone.now()
        payroll_run.error_message = str(exc)

        payroll_run.save(
            update_fields=[
                "status",
                "completed_at",
                "error_message",
            ]
        )

        raise
@shared_task(
    bind=True,
    max_retries=3,
)
def generate_payslip_pdf_task(
    self,
    payslip_id,
):
    from payroll.generators.payslip_pdf import (
        generate_payslip_pdf,
    )
    from payroll.models import Payslip

    try:
        payslip = Payslip.objects.get(
            pk=payslip_id
        )

        generate_payslip_pdf(payslip)

        return {
            "payslip_id": payslip.id,
            "status": "GENERATED",
        }

    except Payslip.DoesNotExist:
        return {
            "payslip_id": payslip_id,
            "status": "NOT_FOUND",
        }

    except Exception as exc:
        raise self.retry(
            exc=exc,
            countdown=30,
        )