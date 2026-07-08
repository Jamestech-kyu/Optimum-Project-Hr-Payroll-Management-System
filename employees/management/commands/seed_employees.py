from django.core.management.base import BaseCommand
from faker import Faker
from random import choice, randint
from decimal import Decimal

from departments.models import Branch, Department, Designation
from employees.models import Employee


fake = Faker("en_GB")


class Command(BaseCommand):
    help = "Seed realistic HR employee data"

    def handle(self, *args, **kwargs):
        branches = [
            ("Nairobi Head Office", "NBO", "Nairobi"),
            ("Mombasa Branch", "MSA", "Mombasa"),
            ("Kisumu Branch", "KSM", "Kisumu"),
            ("Nakuru Branch", "NKR", "Nakuru"),
            ("Eldoret Branch", "ELD", "Eldoret"),
        ]

        departments = [
            "Human Resources",
            "Finance",
            "Payroll",
            "ICT",
            "Operations",
            "Procurement",
            "Sales",
            "Marketing",
            "Legal",
            "Compliance",
        ]

        designations = [
            "HR Manager",
            "HR Officer",
            "Payroll Officer",
            "Finance Manager",
            "Accountant",
            "Software Engineer",
            "System Administrator",
            "Procurement Officer",
            "Operations Manager",
            "Branch Manager",
        ]

        banks = [
            "Equity Bank",
            "KCB Bank",
            "Co-operative Bank",
            "NCBA Bank",
            "Absa Bank Kenya",
            "Stanbic Bank",
        ]

        created_branches = []
        for name, code, location in branches:
            branch, _ = Branch.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "location": location,
                    "phone_number": fake.phone_number(),
                    "email": f"{code.lower()}@company.co.ke",
                },
            )
            created_branches.append(branch)

        created_departments = []
        for branch in created_branches:
            for dept_name in departments:
                dept, _ = Department.objects.get_or_create(
                    branch=branch,
                    code=dept_name[:3].upper(),
                    defaults={"name": dept_name},
                )
                created_departments.append(dept)

        created_designations = []
        for dept in created_departments:
            for title in designations:
                designation, _ = Designation.objects.get_or_create(
                    department=dept,
                    title=title,
                )
                created_designations.append(designation)

        for i in range(1, 101):
            first_name = fake.first_name()
            last_name = fake.last_name()
            branch = choice(created_branches)
            department = choice(created_departments)
            designation = choice(created_designations)

            Employee.objects.get_or_create(
                employee_number=f"EMP{i:04d}",
                defaults={
                    "branch": branch,
                    "department": department,
                    "designation": designation,
                    "first_name": first_name,
                    "last_name": last_name,
                    "gender": choice(["MALE", "FEMALE"]),
                    "date_of_birth": fake.date_of_birth(minimum_age=22, maximum_age=58),
                    "marital_status": choice(["SINGLE", "MARRIED", "DIVORCED"]),
                    "nationality": "Kenyan",
                    "phone_number": f"+2547{randint(10000000, 99999999)}",
                    "personal_email": f"{first_name.lower()}.{last_name.lower()}@gmail.com",
                    "work_email": f"{first_name.lower()}.{last_name.lower()}@company.co.ke",
                    "address": fake.address(),
                    "national_id_number": str(randint(20000000, 39999999)),
                    "tax_pin": f"A{randint(100000000, 999999999)}K",
                    "social_security_number": str(randint(10000000, 99999999)),
                    "health_insurance_number": str(randint(10000000, 99999999)),
                    "hire_date": fake.date_between(start_date="-8y", end_date="-1m"),
                    "employment_type": choice(["PERMANENT", "CONTRACT", "INTERN"]),
                    "employment_status": choice(["ACTIVE", "PROBATION", "ONBOARDING"]),
                    "work_location": branch.location,
                    "bank_name": choice(banks),
                    "bank_branch": branch.location,
                    "bank_account_name": f"{first_name} {last_name}",
                    "bank_account_number": str(randint(1000000000, 9999999999)),
                    "basic_salary": Decimal(randint(40000, 250000)),
                    "house_allowance": Decimal(randint(5000, 50000)),
                    "transport_allowance": Decimal(randint(3000, 30000)),
                    "medical_allowance": Decimal(randint(2000, 25000)),
                    "other_allowance": Decimal(randint(0, 20000)),
                    "emergency_contact_name": fake.name(),
                    "emergency_contact_relationship": choice(["Spouse", "Parent", "Sibling"]),
                    "emergency_contact_phone": f"+2547{randint(10000000, 99999999)}",
                },
            )

        self.stdout.write(self.style.SUCCESS("Seeded realistic HR employee data successfully."))