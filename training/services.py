import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from employees.models import Employee
from performance.models import PerformanceReview

from .models import (
    TrainingAssessment,
    TrainingAttendance,
    TrainingCertificate,
    TrainingCourse,
    TrainingEnrollment,
    TrainingRecommendation,
    TrainingSession,
)


@transaction.atomic
def enroll_employee_in_training(
    *,
    employee_id,
    session_id,
    enrolled_by,
):
    employee = get_object_or_404(
        Employee,
        id=employee_id,
    )

    session = get_object_or_404(
        TrainingSession.objects.select_related("course"),
        id=session_id,
    )

    if session.status != "SCHEDULED":
        raise ValidationError(
            {
                "session_id": (
                    "Employees can only be enrolled in "
                    "scheduled training sessions."
                )
            }
        )

    existing_enrollment = TrainingEnrollment.objects.filter(
        employee=employee,
        session=session,
    ).exists()

    if existing_enrollment:
        raise ValidationError(
            {
                "employee_id": (
                    "This employee is already enrolled "
                    "in the selected session."
                )
            }
        )

    active_enrollments = session.enrollments.filter(
        status__in=["PENDING", "APPROVED", "COMPLETED"]
    ).count()

    if active_enrollments >= session.maximum_participants:
        raise ValidationError(
            {
                "session_id": (
                    "This training session has reached "
                    "its maximum participant capacity."
                )
            }
        )

    enrollment = TrainingEnrollment.objects.create(
        employee=employee,
        session=session,
        enrolled_by=enrolled_by,
        status="PENDING",
    )

    return enrollment


@transaction.atomic
def approve_training_enrollment(
    *,
    enrollment,
):
    if enrollment.status != "PENDING":
        raise ValidationError(
            {
                "status": (
                    "Only pending training enrollments "
                    "can be approved."
                )
            }
        )

    enrollment.status = "APPROVED"
    enrollment.save(update_fields=["status"])

    return enrollment


@transaction.atomic
def reject_training_enrollment(
    *,
    enrollment,
):
    if enrollment.status != "PENDING":
        raise ValidationError(
            {
                "status": (
                    "Only pending training enrollments "
                    "can be rejected."
                )
            }
        )

    enrollment.status = "REJECTED"
    enrollment.save(update_fields=["status"])

    return enrollment


@transaction.atomic
def record_training_attendance(
    *,
    enrollment_id,
    attendance_status,
    check_in=None,
    check_out=None,
):
    enrollment = get_object_or_404(
        TrainingEnrollment.objects.select_related(
            "employee",
            "session",
        ),
        id=enrollment_id,
    )

    if enrollment.status not in ["APPROVED", "COMPLETED"]:
        raise ValidationError(
            {
                "enrollment_id": (
                    "Attendance can only be recorded for "
                    "approved enrollments."
                )
            }
        )

    attendance, _ = TrainingAttendance.objects.update_or_create(
        enrollment=enrollment,
        defaults={
            "attendance_status": attendance_status,
            "check_in": check_in,
            "check_out": check_out,
        },
    )

    return attendance


@transaction.atomic
def record_training_assessment(
    *,
    enrollment_id,
    score,
    remarks="",
):
    enrollment = get_object_or_404(
        TrainingEnrollment.objects.select_related(
            "session__course",
        ),
        id=enrollment_id,
    )

    if enrollment.status != "APPROVED":
        raise ValidationError(
            {
                "enrollment_id": (
                    "Assessment can only be recorded for "
                    "an approved enrollment."
                )
            }
        )

    passing_score = enrollment.session.course.passing_score

    assessment, _ = TrainingAssessment.objects.update_or_create(
        enrollment=enrollment,
        defaults={
            "score": score,
            "passed": score >= passing_score,
            "remarks": remarks,
        },
    )

    if assessment.passed:
        enrollment.status = "COMPLETED"
        enrollment.save(update_fields=["status"])

        if enrollment.session.course.certificate_enabled:
            issue_training_certificate(
                enrollment=enrollment,
            )

    return assessment


@transaction.atomic
def issue_training_certificate(
    *,
    enrollment,
):
    if enrollment.status != "COMPLETED":
        raise ValidationError(
            {
                "status": (
                    "A certificate can only be issued after "
                    "the enrollment is completed."
                )
            }
        )

    try:
        assessment = enrollment.assessment
    except TrainingAssessment.DoesNotExist:
        raise ValidationError(
            {
                "assessment": (
                    "A passing assessment is required before "
                    "issuing a certificate."
                )
            }
        )

    if not assessment.passed:
        raise ValidationError(
            {
                "assessment": (
                    "The employee must pass the assessment "
                    "before receiving a certificate."
                )
            }
        )

    certificate, _ = TrainingCertificate.objects.get_or_create(
        enrollment=enrollment,
        defaults={
            "certificate_number": (
                f"TRN-{timezone.now().year}-"
                f"{uuid.uuid4().hex[:10].upper()}"
            ),
            "issued_date": timezone.localdate(),
        },
    )

    return certificate


@transaction.atomic
def create_training_recommendation(
    *,
    employee_id,
    performance_review_id,
    recommended_course_id,
    reason,
    recommended_by,
):
    employee = get_object_or_404(
        Employee,
        id=employee_id,
    )

    review = get_object_or_404(
        PerformanceReview,
        id=performance_review_id,
        employee=employee,
    )

    course = get_object_or_404(
        TrainingCourse,
        id=recommended_course_id,
        is_active=True,
    )

    existing_recommendation = TrainingRecommendation.objects.filter(
        employee=employee,
        performance_review=review,
        recommended_course=course,
        status__in=["PENDING", "ACCEPTED"],
    ).exists()

    if existing_recommendation:
        raise ValidationError(
            {
                "recommended_course_id": (
                    "An open recommendation already exists "
                    "for this employee and course."
                )
            }
        )

    recommendation = TrainingRecommendation.objects.create(
        employee=employee,
        performance_review=review,
        recommended_course=course,
        reason=reason,
        recommended_by=recommended_by,
        status="PENDING",
    )

    return recommendation


@transaction.atomic
def accept_training_recommendation(
    *,
    recommendation,
):
    if recommendation.status != "PENDING":
        raise ValidationError(
            {
                "status": (
                    "Only pending training recommendations "
                    "can be accepted."
                )
            }
        )

    recommendation.status = "ACCEPTED"
    recommendation.save(update_fields=["status"])

    return recommendation


@transaction.atomic
def decline_training_recommendation(
    *,
    recommendation,
):
    if recommendation.status != "PENDING":
        raise ValidationError(
            {
                "status": (
                    "Only pending training recommendations "
                    "can be declined."
                )
            }
        )

    recommendation.status = "DECLINED"
    recommendation.save(update_fields=["status"])

    return recommendation