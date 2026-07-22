from django.conf import settings
from django.db import models

from employees.models import Employee
from performance.models import PerformanceReview


class TrainingCategory(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TrainingCourse(models.Model):
    category = models.ForeignKey(
        TrainingCategory,
        on_delete=models.PROTECT,
        related_name="courses",
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(blank=True)

    duration_hours = models.PositiveIntegerField()

    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50,
    )

    certificate_enabled = models.BooleanField(default=True)

    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class TrainingSession(models.Model):
    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("ONGOING", "Ongoing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="training_sessions",
    )

    venue = models.CharField(max_length=200)

    start_date = models.DateTimeField()

    end_date = models.DateTimeField()

    maximum_participants = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SCHEDULED",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.course.title} ({self.start_date.date()})"


class TrainingEnrollment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="training_app_enrollments",
    )

    session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="training_enrollments_created",
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "session"],
                name="unique_training_enrollment",
            )
        ]

    def __str__(self):
        return f"{self.employee.employee_number} - {self.session.course.title}"


class TrainingAttendance(models.Model):
    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
    ]

    enrollment = models.OneToOneField(
        TrainingEnrollment,
        on_delete=models.CASCADE,
        related_name="attendance",
    )

    attendance_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
    )

    check_in = models.DateTimeField(
        null=True,
        blank=True,
    )

    check_out = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.enrollment}"


class TrainingAssessment(models.Model):
    enrollment = models.OneToOneField(
        TrainingEnrollment,
        on_delete=models.CASCADE,
        related_name="assessment",
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    passed = models.BooleanField(default=False)

    remarks = models.TextField(blank=True)

    assessed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.enrollment}"


class TrainingCertificate(models.Model):
    enrollment = models.OneToOneField(
        TrainingEnrollment,
        on_delete=models.CASCADE,
        related_name="certificate",
    )

    certificate_number = models.CharField(
        max_length=100,
        unique=True,
    )

    issued_date = models.DateField()

    expiry_date = models.DateField(
        null=True,
        blank=True,
    )

    certificate_file = models.FileField(
        upload_to="training_certificates/",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.certificate_number


class TrainingRecommendation(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("DECLINED", "Declined"),
        ("COMPLETED", "Completed"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="training_recommendations",
    )

    performance_review = models.ForeignKey(
        PerformanceReview,
        on_delete=models.CASCADE,
        related_name="training_recommendations",
    )

    recommended_course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.PROTECT,
        related_name="recommendations",
    )

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    recommended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.employee_number} - {self.recommended_course.title}"
