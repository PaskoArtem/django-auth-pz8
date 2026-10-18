from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import AcademicGroup, Course, Department
from .permissions import IsMethodistOrReadOnly
from .serializers import (
    AcademicGroupSerializer,
    CourseSerializer,
    DepartmentSerializer,
)


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all().order_by('name')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class AcademicGroupViewSet(viewsets.ModelViewSet):
    queryset = AcademicGroup.objects.select_related('department').all().order_by('name')
    serializer_class = AcademicGroupSerializer
    permission_classes = [IsMethodistOrReadOnly]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related('department').all().order_by('title')
    serializer_class = CourseSerializer
    permission_classes = [IsMethodistOrReadOnly]
