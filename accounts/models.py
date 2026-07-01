from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('HR', 'HR'),
        ('MANAGER', 'Manager'),
        ('PAYROLL_OFFICER', 'Payroll Officer'),
        ('EMPLOYEE', 'Employee'),
    ]

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.get_name_display()


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
        return self.email