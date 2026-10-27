from django.contrib import admin
from .models import AcademicGroup, Course, Department, StudentProfile, Equipment, EquipmentRequest, EquipmentRequestEvent


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'department')
    list_filter = ('department',)
    search_fields = ('title',)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'department')
    list_filter = ('department',)
    search_fields = ('user__username',)
    filter_horizontal = ('courses',)


@admin.register(AcademicGroup)
class AcademicGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'department')
    list_filter = ('department',)
    search_fields = ('name',)

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'total_quantity', 'available_quantity')
    list_filter = ('category',)
    search_fields = ('name',)


class EquipmentRequestEventInline(admin.TabularInline):
    model = EquipmentRequestEvent
    extra = 0
    readonly_fields = ('actor', 'event_type', 'details', 'created_at')


@admin.register(EquipmentRequest)
class EquipmentRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipment', 'requester', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'equipment__category')
    search_fields = ('equipment__name', 'requester__username', 'purpose')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [EquipmentRequestEventInline]


@admin.register(EquipmentRequestEvent)
class EquipmentRequestEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'event_type', 'actor', 'created_at')
    readonly_fields = ('request', 'event_type', 'actor', 'details', 'created_at')
