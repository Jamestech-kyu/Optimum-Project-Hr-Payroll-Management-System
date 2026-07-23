import os

from locust import HttpUser, between, task


class HRPayrollAPIUser(HttpUser):
    wait_time = between(1, 3)

    email = os.getenv("LOAD_TEST_EMAIL", "your-admin-email@example.com")
    password = os.getenv("LOAD_TEST_PASSWORD", "your-password")

    def on_start(self):
        with self.client.post(
            "/api/auth/login/",
            json={
                "email": self.email,
                "password": self.password,
            },
            name="Login",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    f"Login failed: {response.status_code} {response.text}"
                )
                self.environment.runner.quit()
                return

            try:
                response_data = response.json()
            except ValueError:
                response.failure(f"Invalid login response: {response.text}")
                self.environment.runner.quit()
                return

            access_token = response_data.get("access")

            if not access_token:
                response.failure(
                    f"No access token returned: {response_data}"
                )
                self.environment.runner.quit()
                return

            self.client.headers.update(
                {
                    "Authorization": f"Bearer {access_token}",
                }
            )

            response.success()

    @task(5)
    def list_employees(self):
        self.client.get(
            "/api/employees/",
            name="List Employees",
        )

    @task(2)
    def search_employees(self):
        self.client.get(
            "/api/employees/?search=James",
            name="Search Employees",
        )

    @task(1)
    def filter_active_employees(self):
        self.client.get(
            "/api/employees/?employment_status=ACTIVE",
            name="Filter Active Employees",
        )
