from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('EXECUTIVE', 'Executive'),
        ('HR', 'HR'),
        ('DEPARTMENT_HEAD', 'Department Head'),
        ('MANAGER', 'Manager'),
        ('FINANCE', 'Finance'),
        ('PAYROLL_OFFICER', 'Payroll Officer'),
        ('EMPLOYEE', 'Employee'),
    ]

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.get_name_display()


class Permission(models.Model):
    MODULE_CHOICES = [
        ("ACCOUNTS", "Accounts"),
        ("EMPLOYEES", "Employees"),
        ("ATTENDANCE", "Attendance"),
        ("LEAVE", "Leave"),
        ("PAYROLL", "Payroll"),
        ("BENEFITS", "Benefits"),
        ("PERFORMANCE", "Performance"),
        ("DISCIPLINARY", "Disciplinary"),
        ("REPORTS", "Reports"),
        ("AUDIT", "Audit"),
        ("SETTINGS", "Settings"),
    ]

    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.module} - {self.name}"
class PermissionGroup(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True,
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupPermission(models.Model):
    group = models.ForeignKey(
        PermissionGroup,
        on_delete=models.CASCADE,
        related_name="permissions",
    )

    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="groups",
    )

    class Meta:
        unique_together = (
            "group",
            "permission",
        )

    def __str__(self):
        return f"{self.group.name} → {self.permission.codename}"


class RolePermissionGroup(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="permission_groups",
    )

    group = models.ForeignKey(
        PermissionGroup,
        on_delete=models.CASCADE,
        related_name="roles",
    )

    class Meta:
        unique_together = (
            "role",
            "group",
        )

    def __str__(self):
        return f"{self.role} → {self.group}"


class RolePermission(models.Model):
    DATA_SCOPE_CHOICES = [
        ("OWN", "Own Records"),
        ("DEPARTMENT", "Department"),
        ("BRANCH", "Branch"),
        ("ORGANIZATION", "Entire Organization"),
    ]

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    data_scope = models.CharField(
        max_length=20,
        choices=DATA_SCOPE_CHOICES,
        default="OWN",
    )

    class Meta:
        unique_together = ("role", "permission")

    def __str__(self):
        return (
            f"{self.role} - {self.permission.codename} "
            f"({self.data_scope})"
        )


class UserDelegation(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delegations_given",
    )

    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delegations_received",
    )

    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.from_user} → {self.to_user}"


class ApprovalWorkflow(models.Model):
    MODULE_CHOICES = [
        ("LEAVE", "Leave"),
        ("PAYROLL", "Payroll"),
        ("BENEFITS", "Benefits"),
        ("PERFORMANCE", "Performance"),
        ("DISCIPLINARY", "Disciplinary"),
    ]

    name = models.CharField(max_length=150)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.module}"


class ApprovalStep(models.Model):
    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        related_name="steps",
    )

    step_order = models.PositiveIntegerField()
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="approval_steps",
    )

    permission_required = models.ForeignKey(
        Permission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approval_steps",
    )

    class Meta:
        unique_together = ("workflow", "step_order")
        ordering = ["step_order"]

    def __str__(self):
        return f"{self.workflow.name} Step {self.step_order} - {self.role}"


class CustomUser(AbstractUser):
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    email = models.EmailField(unique=True)
    is_approved = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_users',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_users',
        blank=True
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username
