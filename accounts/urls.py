from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .api_views import (AcademicGroupViewSet, CourseViewSet, DepartmentViewSet, EquipmentViewSet, EquipmentRequestViewSet)
from . import views


router = DefaultRouter()
router.register('departments', DepartmentViewSet, basename='api-departments')
router.register('groups', AcademicGroupViewSet, basename='api-groups')
router.register('courses', CourseViewSet, basename='api-courses')
router.register('equipment', EquipmentViewSet, basename='api-equipment')
router.register('equipment-requests', EquipmentRequestViewSet, basename='api-equipment-requests')


urlpatterns = [
    path('api/', include(router.urls)),
    path('api-dashboard/', views.api_dashboard, name='api_dashboard'),
    path('equipment-workflow/', views.equipment_workflow, name='equipment_workflow'),
    path(
        'profile/',
        views.profile,
        name='profile'
    ),

    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    path(
        'dashboard/groups/',
        views.groups_dashboard,
        name='groups_dashboard'
    ),

    path(
        'dashboard/courses/',
        views.courses_dashboard,
        name='courses_dashboard'
    ),

    path(
        'courses/',
        views.course_list,
        name='course_list'
    ),

    path(
        'departments/',
        views.department_list,
        name='department_list'
    ),

    path(
        'departments/add/',
        views.department_create,
        name='department_create'
    ),

    path(
        'departments/<int:pk>/edit/',
        views.department_update,
        name='department_update'
    ),

    path(
        'departments/<int:pk>/delete/',
        views.department_delete,
        name='department_delete'
    ),

    path(
        'groups/',
        views.academic_group_list,
        name='academic_group_list'
    ),

    path(
        'groups/add/',
        views.academic_group_create,
        name='academic_group_create'
    ),

    path(
        'groups/<int:pk>/edit/',
        views.academic_group_update,
        name='academic_group_update'
    ),

    path(
        'groups/<int:pk>/delete/',
        views.academic_group_delete,
        name='academic_group_delete'
    ),

    path(
        'courses/add/',
        views.course_create,
        name='course_create'
    ),

    path(
        'courses/<int:pk>/edit/',
        views.course_update,
        name='course_update'
    ),

    path(
        'courses/<int:pk>/delete/',
        views.course_delete,
        name='course_delete'
    ),
]