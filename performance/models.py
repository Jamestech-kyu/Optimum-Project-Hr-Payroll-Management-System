from django.conf import settings
from django.db import models

from employees.models import Employee


class PerformanceCycle(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
        ("ARCHIVED", "Archived"),
    ]

    title = models.CharField(
        max_length=150,
        unique=True,
    )

    description = models.TextField(blank=True)

    start_date = models.DateField()

    end_date = models.DateField()

    review_deadline = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performance_cycles_created",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.title


class PerformanceGoal(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="performance_goals",
    )

    cycle = models.ForeignKey(
        PerformanceCycle,
        on_delete=models.CASCADE,
        related_name="goals",
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage weight of this goal",
    )

    target_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    measurement_unit = models.CharField(
        max_length=50,
        blank=True,
        help_text="Example: %, Tasks, Sales, Hours",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performance_goals_created",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee", "title"]

    def __str__(self):
        return f"{self.employee.employee_number} - {self.title}"


class GoalProgress(models.Model):
    goal = models.ForeignKey(
        PerformanceGoal,
        on_delete=models.CASCADE,
        related_name="progress_updates",
    )

    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    remarks = models.TextField(blank=True)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="goal_progress_submitted",
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return (
            f"{self.goal.title} "
            f"({self.progress_percentage}%)"
        )


class PerformanceReview(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("MANAGER_APPROVED", "Manager Approved"),
        ("HR_APPROVED", "HR Approved"),
        ("FINALIZED", "Finalized"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="performance_app_reviews",
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performance_app_reviews_conducted",
    )

    cycle = models.ForeignKey(
        PerformanceCycle,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    communication = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    teamwork = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    leadership = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    technical_skill = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    innovation = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    attendance = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    initiative = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    productivity = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    problem_solving = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    customer_service = models.DecimalField(max_digits=4, decimal_places=2, default=0)

    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    overall_rating = models.CharField(
        max_length=50,
        blank=True,
    )

    recommend_promotion = models.BooleanField(default=False)
    recommend_salary_increment = models.BooleanField(default=False)
    recommend_bonus = models.BooleanField(default=False)
    recommend_training = models.BooleanField(default=False)
    recommend_pip = models.BooleanField(default=False)

    manager_comments = models.TextField(blank=True)
    employee_comments = models.TextField(blank=True)
    hr_comments = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    review_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-review_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "cycle"],
                name="unique_employee_review_per_cycle",
            )
        ]

    def __str__(self):
        return f"{self.employee.employee_number} - {self.cycle.title}"


class PerformanceComment(models.Model):
    review = models.ForeignKey(
        PerformanceReview,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment #{self.pk}"


class PerformanceAttachment(models.Model):
    review = models.ForeignKey(
        PerformanceReview,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    file = models.FileField(
        upload_to="performance/",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name


class PerformanceCalibration(models.Model):
    review = models.OneToOneField(
        PerformanceReview,
        on_delete=models.CASCADE,
        related_name="calibration",
    )

    old_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    new_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    reason = models.TextField()

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    approved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Calibration {self.review_id}"
