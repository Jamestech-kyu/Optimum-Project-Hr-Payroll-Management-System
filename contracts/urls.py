from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EmploymentContractViewSet,
    ContractRenewalViewSet,
    ContractTerminationViewSet,
    ExpiringContractsView,
    RenewContractView,
    TerminateContractView,
    EmployeeContractsView,
)


router = DefaultRouter()

router.register(
    "contracts",
    EmploymentContractViewSet,
    basename="contracts",
)

router.register(
    "contract-renewals",
    ContractRenewalViewSet,
    basename="contract-renewals",
)

router.register(
    "contract-terminations",
    ContractTerminationViewSet,
    basename="contract-terminations",
)


urlpatterns = [
    # Custom routes must come before router.urls.
    path(
        "contracts/expiring/",
        ExpiringContractsView.as_view(),
        name="expiring-contracts",
    ),

    path(
        "contracts/<int:contract_id>/renew/",
        RenewContractView.as_view(),
        name="renew-contract",
    ),

    path(
        "contracts/<int:contract_id>/terminate/",
        TerminateContractView.as_view(),
        name="terminate-contract",
    ),

    path(
        "employees/<int:employee_id>/contracts/",
        EmployeeContractsView.as_view(),
        name="employee-contracts",
    ),

    path("", include(router.urls)),
]
