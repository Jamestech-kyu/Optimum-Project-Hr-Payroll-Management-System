from django.db import models
from django.conf import settings
from departments.models import Branch, Department, Designation


class Employee(models.Model):
    EMPLOYMENT_STATUS_CHOICES = [
        ("ONBOARDING", "Onboarding"),
        ("PROBATION", "Probation"),
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("TERMINATED", "Terminated"),
        ("OFFBOARDED", "Offboarded"),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ("PERMANENT", "Permanent"),
        ("CONTRACT", "Contract"),
        ("INTERN", "Intern"),
        ("CASUAL", "Casual"),
        ("CONSULTANT", "Consultant"),
    ]

    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    ]

    MARITAL_STATUS_CHOICES = [
        ("SINGLE", "Single"),
        ("MARRIED", "Married"),
        ("DIVORCED", "Divorced"),
        ("WIDOWED", "Widowed"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        related_name="employees",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name="employees",
    )

    designation = models.ForeignKey(
        Designation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )

    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
    )

    employee_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)

    profile_photo = models.ImageField(
        upload_to="employees/photos/",
        null=True,
        blank=True,
    )

    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
    )
    nationality = models.CharField(max_length=100, blank=True)
    disability_status = models.BooleanField(default=False)
    disability_description = models.TextField(blank=True)

    phone_number = models.CharField(max_length=20, blank=True)
    alternative_phone = models.CharField(max_length=20, blank=True)
    personal_email = models.EmailField(blank=True)
    work_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    postal_address = models.CharField(max_length=255, blank=True)

    national_id_number = models.CharField(max_length=100, blank=True)
    passport_number = models.CharField(max_length=100, blank=True)
    tax_pin = models.CharField(max_length=100, blank=True)
    social_security_number = models.CharField(max_length=100, blank=True)
    health_insurance_number = models.CharField(max_length=100, blank=True)

    hire_date = models.DateField()
    confirmation_date = models.DateField(null=True, blank=True)
    probation_end_date = models.DateField(null=True, blank=True)

    employment_type = models.CharField(
        max_length=30,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default="PERMANENT",
    )

    employment_status = models.CharField(
        max_length=30,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default="ONBOARDING",
    )

    work_location = models.CharField(max_length=150, blank=True)
    job_grade = models.CharField(max_length=50, blank=True)
    job_level = models.CharField(max_length=50, blank=True)

    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_address = models.TextField(blank=True)

    bank_name = models.CharField(max_length=150, blank=True)
    bank_branch = models.CharField(max_length=150, blank=True)
    bank_account_number = models.CharField(max_length=100, blank=True)
    bank_account_name = models.CharField(max_length=150, blank=True)
    swift_code = models.CharField(max_length=50, blank=True)

    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    house_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["employment_status"],
                name="emp_status_idx",
            ),
            models.Index(
                fields=["department", "employment_status"],
                name="emp_dept_status_idx",
            ),
            models.Index(
                fields=["branch", "employment_status"],
                name="emp_branch_status_idx",
            ),
            models.Index(
                fields=["manager"],
                name="emp_manager_idx",
            ),
        ]

    @property
    def gross_salary(self):
        return (
            self.basic_salary
            + self.house_allowance
            + self.transport_allowance
            + self.medical_allowance
            + self.other_allowance
        )


class EmployeeDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ("CONTRACT", "Contract"),
        ("NATIONAL_ID", "National ID"),
        ("PASSPORT", "Passport"),
        ("CV", "CV"),
        ("ACADEMIC_CERTIFICATE", "Academic Certificate"),
        ("PROFESSIONAL_CERTIFICATE", "Professional Certificate"),
        ("TAX_DOCUMENT", "Tax Document"),
        ("BANK_DOCUMENT", "Bank Document"),
        ("OTHER", "Other"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    document_name = models.CharField(max_length=150)
    file = models.FileField(upload_to="employees/documents/")
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_employee_documents",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.employee.employee_number} - {self.document_name}"


class EmployeeEducation(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="education",
    )

    institution_name = models.CharField(max_length=200)
    qualification = models.CharField(max_length=200)
    course = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=100, blank=True)

    certificate = models.FileField(
        upload_to="employees/education/",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-end_date"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.qualification}"


class EmployeeWorkExperience(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="work_experiences",
    )

    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    responsibilities = models.TextField(blank=True)
    reason_for_leaving = models.TextField(blank=True)
    reference_contact = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ["-end_date"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.position}"


class EmployeeDependant(models.Model):
    RELATIONSHIP_CHOICES = [
        ("SPOUSE", "Spouse"),
        ("CHILD", "Child"),
        ("PARENT", "Parent"),
        ("SIBLING", "Sibling"),
        ("OTHER", "Other"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="dependants",
    )

    full_name = models.CharField(max_length=200)

    relationship = models.CharField(
        max_length=30,
        choices=RELATIONSHIP_CHOICES,
    )

    date_of_birth = models.DateField(null=True, blank=True)

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    is_beneficiary = models.BooleanField(default=False)

    beneficiary_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.relationship})"


class EmployeeCertification(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="certifications",
    )

    certification_name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    certificate_file = models.FileField(
        upload_to="employees/certifications/",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.certification_name}"


class EmployeeSkill(models.Model):
    SKILL_LEVEL_CHOICES = [
        ("BEGINNER", "Beginner"),
        ("INTERMEDIATE", "Intermediate"),
        ("ADVANCED", "Advanced"),
        ("EXPERT", "Expert"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="skills",
    )

    skill_name = models.CharField(max_length=150)

    skill_level = models.CharField(
        max_length=20,
        choices=SKILL_LEVEL_CHOICES,
        default="BEGINNER",
    )

    years_of_experience = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["skill_name"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.skill_name}"


class EmployeeBankAccount(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="bank_accounts",
    )

    bank_name = models.CharField(max_length=150)
    branch_name = models.CharField(max_length=150)
    account_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=100)

    swift_code = models.CharField(max_length=50, blank=True)

    is_primary = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.bank_name}"


class EmployeeAsset(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="assets",
    )

    asset_name = models.CharField(max_length=150)
    asset_code = models.CharField(max_length=100, unique=True)

    serial_number = models.CharField(max_length=100, blank=True)

    issue_date = models.DateField()

    return_date = models.DateField(
        null=True,
        blank=True,
    )

    is_returned = models.BooleanField(default=False)

    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asset_name} - {self.employee.full_name}"
from django.conf import settings
from django.db import models


class SalaryHistory(models.Model):
    ADJUSTMENT_TYPE_CHOICES = [
        ("INITIAL", "Initial Salary"),
        ("INCREMENT", "Salary Increment"),
        ("DECREMENT", "Salary Decrement"),
        ("PROMOTION", "Promotion"),
        ("CONTRACT_RENEWAL", "Contract Renewal"),
        ("CORRECTION", "Salary Correction"),
        ("OTHER", "Other"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="salary_history",
    )

    previous_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    new_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    adjustment_type = models.CharField(
        max_length=30,
        choices=ADJUSTMENT_TYPE_CHOICES,
        default="OTHER",
    )

    effective_date = models.DateField()

    reason = models.TextField()

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salary_changes_made",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [
            "-effective_date",
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.employee.employee_number}: "
            f"{self.previous_salary} → {self.new_salary}"
        )   
