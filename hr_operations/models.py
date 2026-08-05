
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from employees.models import Employee
from accounts.models import Role


# =========================================================
# PERFORMANCE
# =========================================================

class PerformanceReview(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("ACKNOWLEDGED", "Acknowledged"),
        ("CLOSED", "Closed"),
    ]
    RATING_CHOICES = [
        (1, "Poor"),
        (2, "Below Average"),
        (3, "Average"),
        (4, "Good"),
        (5, "Excellent"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="performance_reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reviews_conducted",
    )
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    overall_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    reviewer_comments = models.TextField(blank=True)
    employee_comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-review_period_end"]

    def clean(self):
        if self.review_period_end < self.review_period_start:
            raise ValidationError("Review period end date must be after the start date.")

    def __str__(self):
        return f"{self.employee.full_name} Review ({self.review_period_start} - {self.review_period_end})"


class PerformanceGoal(models.Model):
    STATUS_CHOICES = [
        ("NOT_STARTED", "Not Started"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("MISSED", "Missed"),
    ]

    # Goals are set for an employee, optionally within a review or a cycle. The
    # client creates them per employee before any review exists, so `review` is
    # optional and `employee` carries the ownership.
    review = models.ForeignKey(
        PerformanceReview,
        on_delete=models.CASCADE,
        related_name="goals",
        null=True,
        blank=True,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="hr_performance_goals",
        null=True,
        blank=True,
    )
    cycle = models.ForeignKey(
        "PerformanceCycle",
        on_delete=models.SET_NULL,
        related_name="goals",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    weight_percentage = models.PositiveSmallIntegerField(
        default=0, help_text="Weight of this goal in the overall review (%)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NOT_STARTED")
    progress_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ["target_date", "id"]

    @property
    def owner(self):
        return self.employee or (self.review.employee if self.review_id else None)

    def __str__(self):
        owner = self.owner
        return f"{self.title} ({owner.full_name if owner else 'unassigned'})"


class PerformanceCycle(models.Model):
    STATUS_CHOICES = [
        ("NOT_STARTED", "Not Started"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    ]
    SCOPE_CHOICES = [
        ("ORG_WIDE", "Organization wide"),
        ("BRANCH", "Branch"),
        ("DEPARTMENT", "Department"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    review_period = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NOT_STARTED")
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default="ORG_WIDE")
    scope_id = models.CharField(max_length=100, blank=True)
    rating_scale = models.JSONField(default=list, blank=True)
    has_360_feedback = models.BooleanField(default=False)
    reminder_frequency = models.PositiveIntegerField(default=7)
    employees = models.ManyToManyField(Employee, related_name="appraisal_cycles", blank=True)
    employee_status = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="hr_performance_cycles_created",
    )

    class Meta:
        ordering = ["-start_date", "-created_at"]


# =========================================================
# DISCIPLINARY
# =========================================================

class DisciplinaryCase(models.Model):
    SEVERITY_CHOICES = [
        ("MINOR", "Minor"),
        ("MODERATE", "Moderate"),
        ("MAJOR", "Major"),
        ("GROSS_MISCONDUCT", "Gross Misconduct"),
    ]
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("UNDER_INVESTIGATION", "Under Investigation"),
        ("HEARING_SCHEDULED", "Hearing Scheduled"),
        ("RESOLVED", "Resolved"),
        ("APPEALED", "Appealed"),
        ("CLOSED", "Closed"),
    ]
    ACTION_CHOICES = [
        ("VERBAL_WARNING", "Verbal Warning"),
        ("WRITTEN_WARNING", "Written Warning"),
        ("SUSPENSION", "Suspension"),
        ("TERMINATION", "Termination"),
        ("NONE", "No Action"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="disciplinary_cases",
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="cases_reported",
    )
    incident_date = models.DateField()
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="MINOR")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="OPEN")
    action_taken = models.CharField(max_length=30, choices=ACTION_CHOICES, default="NONE")
    resolution_notes = models.TextField(blank=True)
    hearing_date = models.DateField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-incident_date"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_severity_display()} ({self.status})"


class OffboardingCase(models.Model):
    EXIT_TYPE_CHOICES = [
        ("RESIGNATION", "Resignation"),
        ("TERMINATION", "Termination"),
        ("END_OF_CONTRACT", "End of contract"),
        ("RETIREMENT", "Retirement"),
    ]
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("IN_PROGRESS", "In progress"),
        ("COMPLETED", "Completed"),
        ("OVERDUE", "Overdue"),
        ("CANCELLED", "Cancelled"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="offboarding_cases")
    exit_type = models.CharField(max_length=30, choices=EXIT_TYPE_CHOICES)
    reason = models.TextField()
    last_working_day = models.DateField()
    notice_period_status = models.CharField(max_length=20, default="FULL")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="offboarding_cases_initiated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class OffboardingChecklistItem(models.Model):
    case = models.ForeignKey(OffboardingCase, on_delete=models.CASCADE, related_name="checklist_items")
    category = models.CharField(max_length=40)
    item = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="PENDING")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)


class OffboardingExitInterview(models.Model):
    case = models.OneToOneField(OffboardingCase, on_delete=models.CASCADE, related_name="exit_interview")
    primary_reason = models.CharField(max_length=255, blank=True)
    feedback = models.JSONField(default=list, blank=True)
    overall_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    would_recommend = models.CharField(max_length=10, blank=True)
    additional_comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_confidential = models.BooleanField(default=True)


class OffboardingFinalSettlement(models.Model):
    case = models.OneToOneField(OffboardingCase, on_delete=models.CASCADE, related_name="final_settlement")
    pro_rated_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    leave_encashment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pending_reimbursements = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    asset_non_return_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default="DRAFT")
    notes = models.TextField(blank=True)


# =========================================================
# ANNOUNCEMENTS
# =========================================================

class Announcement(models.Model):
    AUDIENCE_CHOICES = [
        ("ALL", "All Employees"),
        ("DEPARTMENT", "Specific Department"),
        ("BRANCH", "Specific Branch"),
        ("ROLE", "Specific Role"),
    ]

    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default="ALL")
    target_department = models.CharField(max_length=100, blank=True)
    target_branch = models.CharField(max_length=100, blank=True)
    target_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="announcements_posted",
    )
    is_pinned = models.BooleanField(default=False)
    publish_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-publish_at"]

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        if self.expires_at:
            return self.publish_at <= now <= self.expires_at
        return self.publish_at <= now


# =========================================================
# BRANCH OPERATIONS
# =========================================================

class BranchTask(models.Model):
    """Task assigned to an employee, shown on the branch dashboard board."""

    PRIORITY_CHOICES = [
        ("HIGH", "High"),
        ("MEDIUM", "Medium"),
        ("LOW", "Low"),
    ]
    STATUS_CHOICES = [
        ("TODO", "Todo"),
        ("IN_PROGRESS", "In Progress"),
        ("DONE", "Done"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="MEDIUM")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="TODO")
    due_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="branch_tasks",
        null=True,
        blank=True,
    )
    branch = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=150, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="branch_tasks_created",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "due_date", "-created_at"]

    def __str__(self):
        return self.title


class EmployeeNote(models.Model):
    """Free-text note recorded against an employee's record."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    note = models.TextField()
    category = models.CharField(max_length=50, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="employee_notes_written",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.employee.full_name}"


# =========================================================
# TRAINING
# =========================================================

class Training(models.Model):
    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("ONGOING", "Ongoing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trainer_name = models.CharField(max_length=150, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=200, blank=True)
    is_mandatory = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SCHEDULED")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="trainings_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before the start date.")

    def __str__(self):
        return self.title


class TrainingEnrollment(models.Model):
    """Join table: which employees are enrolled in / completed which training."""

    STATUS_CHOICES = [
        ("ENROLLED", "Enrolled"),
        ("ATTENDED", "Attended"),
        ("ABSENT", "Absent"),
        ("COMPLETED", "Completed"),
    ]

    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name="enrollments")
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="training_enrollments",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ENROLLED")
    certificate = models.FileField(upload_to="training_certificates/", null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("training", "employee")
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.training}"
