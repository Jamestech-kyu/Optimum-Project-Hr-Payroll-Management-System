from django.contrib import admin

from .models import (
    BenefitPlan,
    EmployeeBenefit,
    BenefitContributionHistory,
    EnrollmentWindow,
)


admin.site.register(BenefitPlan)
admin.site.register(EmployeeBenefit)
admin.site.register(BenefitContributionHistory)
admin.site.register(EnrollmentWindow)