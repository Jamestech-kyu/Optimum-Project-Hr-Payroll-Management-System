from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Branch, Department, Designation
from .serializers import BranchSerializer, DepartmentSerializer, DesignationSerializer


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all().order_by("name")
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class DesignationViewSet(viewsets.ModelViewSet):
    queryset = Designation.objects.all().order_by("title")
    serializer_class = DesignationSerializer
    permission_classes = [IsAuthenticated]
