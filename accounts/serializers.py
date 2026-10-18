from rest_framework import serializers
from .models import AcademicGroup, Course, Department


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name')


class AcademicGroupSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = AcademicGroup
        fields = ('id', 'name', 'department', 'department_name')

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError('Название группы должно содержать не менее 2 символов.')
        return value

    def validate(self, attrs):
        name = attrs.get('name', getattr(self.instance, 'name', '')).strip()
        department = attrs.get('department', getattr(self.instance, 'department', None))
        qs = AcademicGroup.objects.filter(name__iexact=name, department=department)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({
                'name': 'В этой кафедре уже существует группа с таким названием.'
            })
        return attrs


class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'title', 'description', 'department', 'department_name')


    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                'Название курса не может быть пустым.'
            )
        return value


    def validate(self, attrs):
        title = attrs.get('title', getattr(self.instance, 'title', '')).strip()
        department = attrs.get('department', getattr(self.instance, 'department', None))
        qs = Course.objects.filter(title__iexact=title, department=department)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({
                'title': 'В этой кафедре уже существует курс с таким названием.'
            })
        return attrs
