import time

from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import CustomUser, Role
from employees.models import Employee
from employees.serializers import EmployeeSerializer


class EmployeeQueryPerformanceTests(TestCase):
    def setUp(self):
        role, _ = Role.objects.get_or_create(
            name="SUPER_ADMIN",
        )

        self.user = CustomUser.objects.create_superuser(
            username="performance_admin",
            email="performance@example.com",
            password="StrongPassword123!",
        )

        self.user.role = role
        self.user.is_approved = True
        self.user.save(
            update_fields=[
                "role",
                "is_approved",
            ]
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        users = [
            CustomUser(
                username=f"query_user{i}",
                email=f"query_user{i}@example.com",
                password="!",
                is_approved=True,
            )
            for i in range(1000)
        ]

        users = CustomUser.objects.bulk_create(users)

        employees = [
            Employee(
                employee_number=f"EMP-{i:03}",
                user=user,
                first_name=f"User{i}",
                last_name="Example",
                hire_date="2026-01-01",
                employment_status="ACTIVE",
            )
            for i, user in enumerate(users)
        ]

        Employee.objects.bulk_create(employees)

    def test_employee_list_query_count(self):
        url = reverse("employees-list")

        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)

        print(f"Status: {response.status_code}")
        print(f"Employees Returned: {response.data['count']}")
        print(f"Queries Executed: {len(captured)}")

        self.assertEqual(response.status_code, 200)


class EmployeeSerializationPerformanceTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        employees = [
            Employee(
                employee_number=f"SER-{i:04d}",
                first_name=f"Employee{i}",
                last_name="Test",
                personal_email=f"employee{i}@example.com",
                hire_date="2026-01-01",
                employment_status="ACTIVE",
            )
            for i in range(1000)
        ]

        Employee.objects.bulk_create(employees)

    def test_employee_serialization_performance(self):
        queryset = Employee.objects.all()

        start_time = time.perf_counter()

        serializer = EmployeeSerializer(queryset, many=True)
        serialized_data = serializer.data

        elapsed_time = time.perf_counter() - start_time

        print(f"\nSerialized records: {len(serialized_data)}")
        print(f"Serialization time: {elapsed_time:.4f} seconds")

        self.assertEqual(len(serialized_data), 1000)
        self.assertLess(
            elapsed_time,
            5,
            f"Serialization took too long: {elapsed_time:.4f} seconds",
        )


class EmployeeAPIPerformanceTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        role, _ = Role.objects.get_or_create(
            name="SUPER_ADMIN",
        )

        cls.user = CustomUser.objects.create_superuser(
            username="api_performance_admin",
            email="api_performance@example.com",
            password="StrongPassword123!",
        )

        cls.user.role = role
        cls.user.is_approved = True
        cls.user.save(
            update_fields=[
                "role",
                "is_approved",
            ]
        )

        employees = [
            Employee(
                employee_number=f"API-{i:04d}",
                first_name=f"Employee{i}",
                last_name="Test",
                personal_email=f"api_employee{i}@example.com",
                hire_date="2026-01-01",
                employment_status="ACTIVE",
            )
            for i in range(10000)
        ]

        Employee.objects.bulk_create(employees)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_employee_list_api_performance(self):
        start_time = time.perf_counter()

        response = self.client.get("/api/employees/")

        elapsed_time = time.perf_counter() - start_time

        print(f"\nStatus code: {response.status_code}")
        print(f"API response time: {elapsed_time:.4f} seconds")

        self.assertEqual(response.status_code, 200)

        self.assertLess(
            elapsed_time,
            5,
            f"Employee API response was too slow: {elapsed_time:.4f} seconds",
        )

    def test_employee_api_query_count(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/api/employees/")

        print(f"\nQueries executed: {len(queries)}")

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            len(queries),
            15,
            f"Too many database queries: {len(queries)}",
        )
