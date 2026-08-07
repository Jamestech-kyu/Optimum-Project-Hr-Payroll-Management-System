from django.shortcuts import get_object_or_404

from rest_framework import filters, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from config.filters import SchemaCompatibleDjangoFilterBackend

from drf_spectacular.utils import extend_schema

from accounts.permissions import RequiredPermission
from audit.mixins import AuditViewSetMixin
from audit.services import log_activity
from audit.utils import get_client_ip

from .models import (
    TrainingAssessment,
    TrainingAttendance,
    TrainingCategory,
    TrainingCertificate,
    TrainingCourse,
    TrainingEnrollment,
    TrainingRecommendation,
    TrainingSession,
)

from .serializers import (
    TrainingAssessmentSerializer,
    TrainingAttendanceSerializer,
    TrainingCategorySerializer,
    TrainingCertificateSerializer,
    TrainingCourseSerializer,
    TrainingEnrollmentSerializer,
    TrainingRecommendationSerializer,
    TrainingSessionSerializer,
    TrainingEnrollmentCreateSerializer,
    TrainingAttendanceCreateSerializer,
    TrainingAssessmentCreateSerializer,
    TrainingRecommendationCreateSerializer,
)

from .services import (
    enroll_employee_in_training,
    approve_training_enrollment,
    reject_training_enrollment,
    record_training_attendance,
    record_training_assessment,
    create_training_recommendation,
    accept_training_recommendation,
    decline_training_recommendation,
)


class TrainingCategoryViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "TRAINING"

    queryset = TrainingCategory.objects.all()
    serializer_class = TrainingCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingCourseViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "TRAINING"

    queryset = TrainingCourse.objects.select_related(
        "category",
    )
    serializer_class = TrainingCourseSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingSessionViewSet(
    AuditViewSetMixin,
    viewsets.ModelViewSet,
):
    audit_module = "TRAINING"

    queryset = TrainingSession.objects.select_related(
        "course",
        "trainer",
    )
    serializer_class = TrainingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingEnrollmentViewSet(
    AuditViewSetMixin,
    viewsets.ReadOnlyModelViewSet,
):
    audit_module = "TRAINING"

    queryset = TrainingEnrollment.objects.select_related(
        "employee",
        "session__course",
    )
    serializer_class = TrainingEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        SchemaCompatibleDjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "employee__employee_number",
        "employee__first_name",
        "employee__last_name",
        "session__course__title",
        "status",
    ]
    ordering_fields = "__all__"
    ordering = ["-enrolled_at"]
    filterset_fields = [
        "employee",
        "session",
        "session__course",
        "status",
    ]


class TrainingAttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingAttendance.objects.select_related(
        "enrollment__employee",
        "enrollment__session__course",
    )
    serializer_class = TrainingAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingAssessmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingAssessment.objects.select_related(
        "enrollment__employee",
        "enrollment__session__course",
    )
    serializer_class = TrainingAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingCertificateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingCertificate.objects.select_related(
        "enrollment__employee",
        "enrollment__session__course",
    )
    serializer_class = TrainingCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingRecommendation.objects.select_related(
        "employee",
        "performance_review",
        "recommended_course",
        "recommended_by",
    )
    serializer_class = TrainingRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    request=TrainingEnrollmentCreateSerializer,
    responses={201: TrainingEnrollmentSerializer},
    tags=["Training"],
)
class EnrollEmployeeTrainingView(APIView):
    permission_classes = [
        RequiredPermission("training.enroll")
    ]

    def post(self, request):
        serializer = TrainingEnrollmentCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        enrollment = enroll_employee_in_training(
            employee_id=serializer.validated_data["employee_id"],
            session_id=serializer.validated_data["session_id"],
            enrolled_by=request.user,
        )

        log_activity(
            user=request.user,
            action="CREATE",
            module="Training",
            description=(
                f"Enrolled employee "
                f"{enrollment.employee.employee_number} "
                f"in {enrollment.session.course.title}."
            ),
            object_id=enrollment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            TrainingEnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )


class ApproveTrainingEnrollmentView(APIView):
    permission_classes = [
        RequiredPermission("training.approve")
    ]

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(
            TrainingEnrollment.objects.select_related(
                "employee",
                "session__course",
            ),
            id=enrollment_id,
        )

        enrollment = approve_training_enrollment(
            enrollment=enrollment,
        )

        log_activity(
            user=request.user,
            action="APPROVE",
            module="Training",
            description=f"Approved training enrollment {enrollment.id}.",
            object_id=enrollment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training enrollment approved successfully.",
                "enrollment": TrainingEnrollmentSerializer(enrollment).data,
            },
            status=status.HTTP_200_OK,
        )


class RejectTrainingEnrollmentView(APIView):
    permission_classes = [
        RequiredPermission("training.reject")
    ]

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(
            TrainingEnrollment.objects.select_related(
                "employee",
                "session__course",
            ),
            id=enrollment_id,
        )

        enrollment = reject_training_enrollment(
            enrollment=enrollment,
        )

        log_activity(
            user=request.user,
            action="REJECT",
            module="Training",
            description=f"Rejected training enrollment {enrollment.id}.",
            object_id=enrollment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training enrollment rejected successfully.",
                "enrollment": TrainingEnrollmentSerializer(enrollment).data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    request=TrainingAttendanceCreateSerializer,
    responses={201: TrainingAttendanceSerializer},
    tags=["Training"],
)
class RecordTrainingAttendanceView(APIView):
    permission_classes = [
        RequiredPermission("training.attendance")
    ]

    def post(self, request):
        serializer = TrainingAttendanceCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        attendance = record_training_attendance(
            enrollment_id=serializer.validated_data["enrollment_id"],
            attendance_status=serializer.validated_data["attendance_status"],
            check_in=serializer.validated_data.get("check_in"),
            check_out=serializer.validated_data.get("check_out"),
        )

        log_activity(
            user=request.user,
            action="CREATE",
            module="Training",
            description=f"Recorded training attendance {attendance.id}.",
            object_id=attendance.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            TrainingAttendanceSerializer(attendance).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    request=TrainingAssessmentCreateSerializer,
    responses={201: TrainingAssessmentSerializer},
    tags=["Training"],
)
class RecordTrainingAssessmentView(APIView):
    permission_classes = [
        RequiredPermission("training.assessment")
    ]

    def post(self, request):
        serializer = TrainingAssessmentCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        assessment = record_training_assessment(
            enrollment_id=serializer.validated_data["enrollment_id"],
            score=serializer.validated_data["score"],
            remarks=serializer.validated_data.get("remarks", ""),
        )

        log_activity(
            user=request.user,
            action="CREATE",
            module="Training",
            description=f"Recorded training assessment {assessment.id}.",
            object_id=assessment.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            TrainingAssessmentSerializer(assessment).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    request=TrainingRecommendationCreateSerializer,
    responses={201: TrainingRecommendationSerializer},
    tags=["Training"],
)
class RecommendTrainingView(APIView):
    permission_classes = [
        RequiredPermission("training.recommend")
    ]

    def post(self, request):
        serializer = TrainingRecommendationCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        recommendation = create_training_recommendation(
            employee_id=serializer.validated_data["employee_id"],
            performance_review_id=serializer.validated_data[
                "performance_review_id"
            ],
            recommended_course_id=serializer.validated_data[
                "recommended_course_id"
            ],
            reason=serializer.validated_data["reason"],
            recommended_by=request.user,
        )

        log_activity(
            user=request.user,
            action="CREATE",
            module="Training",
            description=f"Created training recommendation {recommendation.id}.",
            object_id=recommendation.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            TrainingRecommendationSerializer(recommendation).data,
            status=status.HTTP_201_CREATED,
        )


class AcceptTrainingRecommendationView(APIView):
    permission_classes = [
        RequiredPermission("training.recommend")
    ]

    def post(self, request, recommendation_id):
        recommendation = get_object_or_404(
            TrainingRecommendation.objects.select_related(
                "employee",
                "recommended_course",
            ),
            id=recommendation_id,
        )

        recommendation = accept_training_recommendation(
            recommendation=recommendation,
        )

        log_activity(
            user=request.user,
            action="UPDATE",
            module="Training",
            description=f"Accepted training recommendation {recommendation.id}.",
            object_id=recommendation.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training recommendation accepted successfully.",
                "recommendation": TrainingRecommendationSerializer(
                    recommendation,
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class DeclineTrainingRecommendationView(APIView):
    permission_classes = [
        RequiredPermission("training.recommend")
    ]

    def post(self, request, recommendation_id):
        recommendation = get_object_or_404(
            TrainingRecommendation.objects.select_related(
                "employee",
                "recommended_course",
            ),
            id=recommendation_id,
        )

        recommendation = decline_training_recommendation(
            recommendation=recommendation,
        )

        log_activity(
            user=request.user,
            action="UPDATE",
            module="Training",
            description=f"Declined training recommendation {recommendation.id}.",
            object_id=recommendation.id,
            ip_address=get_client_ip(request),
        )

        return Response(
            {
                "message": "Training recommendation declined successfully.",
                "recommendation": TrainingRecommendationSerializer(
                    recommendation,
                ).data,
            },
            status=status.HTTP_200_OK,
        )
