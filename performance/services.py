from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import (
    GoalProgress,
    PerformanceGoal,
    PerformanceReview,
)


def calculate_rating(score):
    """
    Determine the performance rating based on the overall score.
    """
    score = Decimal(score)

    if score >= Decimal("90"):
        return "Outstanding"

    if score >= Decimal("80"):
        return "Excellent"

    if score >= Decimal("70"):
        return "Very Good"

    if score >= Decimal("60"):
        return "Good"

    if score >= Decimal("50"):
        return "Average"

    return "Needs Improvement"


def calculate_review_score(review):
    """
    Calculate the overall review percentage.
    Each category is scored out of 10.
    """

    scores = [
        review.communication,
        review.teamwork,
        review.leadership,
        review.technical_skill,
        review.innovation,
        review.attendance,
        review.initiative,
        review.productivity,
        review.problem_solving,
        review.customer_service,
    ]

    total = sum(scores)

    average = total / Decimal("10")

    percentage = average * Decimal("10")

    return round(percentage, 2)


def validate_review_scores(data):
    """
    Ensure every score is between 0 and 10.
    """

    score_fields = [
        "communication",
        "teamwork",
        "leadership",
        "technical_skill",
        "innovation",
        "attendance",
        "initiative",
        "productivity",
        "problem_solving",
        "customer_service",
    ]

    for field in score_fields:
        score = data.get(field)

        if score is None:
            continue

        if score < 0 or score > 10:
            raise ValidationError(
                {
                    field: "Score must be between 0 and 10."
                }
            )


@transaction.atomic
def create_performance_review(
    *,
    validated_data,
):
    """
    Create a new performance review.
    """

    validate_review_scores(validated_data)

    review = PerformanceReview.objects.create(
        **validated_data
    )

    score = calculate_review_score(review)

    review.overall_score = score

    review.overall_rating = calculate_rating(score)

    review.save(
        update_fields=[
            "overall_score",
            "overall_rating",
            "updated_at",
        ]
    )

    return review


@transaction.atomic
def update_performance_review(
    *,
    review,
    validated_data,
):
    """
    Update an existing review.
    """

    validate_review_scores(validated_data)

    for field, value in validated_data.items():
        setattr(review, field, value)

    score = calculate_review_score(review)

    review.overall_score = score

    review.overall_rating = calculate_rating(score)

    review.save()

    return review


@transaction.atomic
def submit_review(review):
    """
    Submit a draft review.
    """

    if review.status != "DRAFT":
        raise ValidationError(
            {
                "status": "Only draft reviews can be submitted."
            }
        )

    review.status = "SUBMITTED"

    review.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return review


@transaction.atomic
def manager_approve(review):
    """
    Manager approves a submitted review.
    """

    if review.status != "SUBMITTED":
        raise ValidationError(
            {
                "status": "Review must be submitted first."
            }
        )

    review.status = "MANAGER_APPROVED"

    review.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return review


@transaction.atomic
def hr_approve(review):
    """
    HR approves the manager-approved review.
    """

    if review.status != "MANAGER_APPROVED":
        raise ValidationError(
            {
                "status": "Manager approval is required."
            }
        )

    review.status = "HR_APPROVED"

    review.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return review


@transaction.atomic
def finalize_review(review):
    """
    Finalize the review.
    """

    if review.status != "HR_APPROVED":
        raise ValidationError(
            {
                "status": "HR approval is required."
            }
        )

    review.status = "FINALIZED"

    review.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return review


@transaction.atomic
def submit_goal_progress(
    *,
    goal_id,
    progress_percentage,
    remarks,
    submitted_by,
):
    """
    Submit employee progress against a goal.
    """

    goal = get_object_or_404(
        PerformanceGoal,
        id=goal_id,
    )

    progress = GoalProgress.objects.create(
        goal=goal,
        progress_percentage=progress_percentage,
        remarks=remarks,
        submitted_by=submitted_by,
    )

    if progress_percentage >= 100:
        goal.status = "COMPLETED"

    elif progress_percentage > 0:
        goal.status = "IN_PROGRESS"

    goal.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return progress