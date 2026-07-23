from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import RequiredPermission
from audit.mixins import AuditViewSetMixin
from audit.services import log_activity
from audit.utils import get_client_ip

from .models import (
    GoalProgress,
    PerformanceAttachment,
    PerformanceCalibration,
    PerformanceComment,
    PerformanceCycle,
    PerformanceGoal,
    PerformanceReview,
)
from .serializers import (
    GoalProgressCreateSerializer,
    GoalProgressSerializer,
    PerformanceAttachmentSerializer,
    PerformanceCalibrationSerializer,
    PerformanceCommentSerializer,
    PerformanceCycleSerializer,
    PerformanceGoalSerializer,
    PerformanceReviewSerializer,
    ReviewActionSerializer,
)
from .services import (
    create_performance_review,
    finalize_review,
    hr_approve,
    manager_approve,
    submit_goal_progress,
    submit_review,
    update_performance_review,
)


class PerformanceCycleViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PERFORMANCE"

    queryset = PerformanceCycle.objects.all()
    serializer_class = PerformanceCycleSerializer
    permission_classes = [permissions.IsAuthenticated]


class PerformanceGoalViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PERFORMANCE"

    queryset = PerformanceGoal.objects.select_related(
        "employee",
        "cycle",
    )
    serializer_class = PerformanceGoalSerializer
    permission_classes = [permissions.IsAuthenticated]


class PerformanceReviewViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "PERFORMANCE"

    queryset = (
        PerformanceReview.objects
        .select_related(
            "employee",
            "reviewer",
            "cycle",
        )
    )

    serializer_class = PerformanceReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "overall_rating",
        "status",
    ]
    ordering_fields = "__all__"
    ordering = ["-created_at"]
    filterset_fields = [
        "employee",
        "reviewer",
        "cycle",
        "status",
        "review_date",
    ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_data["reviewer"] = request.user

        review = create_performance_review(
            validated_data=validated_data
        )

        log_activity(
            user=request.user,
            action="CREATE",
            module="Performance",
            description=f"Created performance review for {review.employee.employee_number}",
            object_id=review.id,
            ip_address=get_client_ip(request),
        )

        output = self.get_serializer(review)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        review = self.get_object()

        serializer = self.get_serializer(
            review,
            data=request.data,
            partial=False,
        )

        serializer.is_valid(raise_exception=True)

        review = update_performance_review(
            review=review,
            validated_data=serializer.validated_data,
        )

        log_activity(
            user=request.user,
            action="UPDATE",
            module="Performance",
            description=f"Updated performance review {review.id}",
            object_id=review.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            self.get_serializer(review).data
        )

    def partial_update(self, request, *args, **kwargs):
        review = self.get_object()

        serializer = self.get_serializer(
            review,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        review = update_performance_review(
            review=review,
            validated_data=serializer.validated_data,
        )

        return Response(
            self.get_serializer(review).data
        )
class SubmitPerformanceReviewView(APIView):
    permission_classes = [
        RequiredPermission(
            "performance.submit_review"
        )
    ]

    def post(self, request, review_id):
        review = get_object_or_404(
            PerformanceReview,
            id=review_id,
        )

        review = submit_review(review)

        log_activity(
            user=request.user,
            action="SUBMIT",
            module="Performance",
            description=f"Submitted review {review.id}",
            object_id=review.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": (
                    "Review submitted successfully."
                ),
                "status": review.status,
            }
        )


class ManagerApproveReviewView(APIView):
    permission_classes = [
        RequiredPermission(
            "performance.manager_approve"
        )
    ]

    def post(self, request, review_id):
        review = get_object_or_404(
            PerformanceReview,
            id=review_id,
        )

        review = manager_approve(review)

        log_activity(
            user=request.user,
            action="MANAGER_APPROVE",
            module="Performance",
            description=f"Manager approved review {review.id}",
            object_id=review.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": (
                    "Manager approval successful."
                ),
                "status": review.status,
            }
        )


class HRApproveReviewView(APIView):
    permission_classes = [
        RequiredPermission(
            "performance.hr_approve"
        )
    ]

    def post(self, request, review_id):
        review = get_object_or_404(
            PerformanceReview,
            id=review_id,
        )

        review = hr_approve(review)

        log_activity(
            user=request.user,
            action="HR_APPROVE",
            module="Performance",
            description=f"HR approved review {review.id}",
            object_id=review.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": (
                    "HR approval successful."
                ),
                "status": review.status,
            }
        )


class FinalizeReviewView(APIView):
    permission_classes = [
        RequiredPermission(
            "performance.finalize"
        )
    ]

    def post(self, request, review_id):
        review = get_object_or_404(
            PerformanceReview,
            id=review_id,
        )

        review = finalize_review(review)

        log_activity(
            user=request.user,
            action="FINALIZE",
            module="Performance",
            description=f"Finalized review {review.id}",
            object_id=review.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": (
                    "Review finalized."
                ),
                "status": review.status,
            }
        )


class GoalProgressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GoalProgress.objects.select_related(
        "goal",
        "submitted_by",
    )
    serializer_class = GoalProgressSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    request=GoalProgressCreateSerializer,
    responses={201: GoalProgressSerializer},
    tags=["Performance"],
)
class SubmitGoalProgressView(APIView):
    permission_classes = [
        RequiredPermission("performance.update_progress")
    ]

    def post(self, request):
        serializer = GoalProgressCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        progress = submit_goal_progress(
            goal_id=serializer.validated_data["goal_id"],
            progress_percentage=serializer.validated_data["progress_percentage"],
            remarks=serializer.validated_data["remarks"],
            submitted_by=request.user,
        )

        log_activity(
            user=request.user,
            action="UPDATE",
            module="Performance",
            description=(
                f"Updated progress for goal "
                f"{progress.goal.title}."
            ),
            object_id=progress.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Goal progress submitted successfully.",
                "progress": GoalProgressSerializer(progress).data,
            },
            status=status.HTTP_201_CREATED,
        )


class EmployeeGoalsView(APIView):
    permission_classes = [
        RequiredPermission("performance.view")
    ]

    def get(self, request, employee_id):
        goals = PerformanceGoal.objects.filter(
            employee_id=employee_id,
        ).select_related(
            "cycle",
        )

        serializer = PerformanceGoalSerializer(
            goals,
            many=True,
        )

        return Response(serializer.data)
