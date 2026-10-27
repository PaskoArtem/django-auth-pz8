from rest_framework import serializers
from .models import (
    AcademicGroup, Course, Department, Equipment, EquipmentRequest, EquipmentRequestEvent,
)


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


class EquipmentSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Equipment
        fields = ('id', 'name', 'category', 'category_display', 'total_quantity', 'available_quantity', 'created_at')
        read_only_fields = ('available_quantity', 'created_at')

    def validate(self, attrs):
        total = attrs.get('total_quantity', getattr(self.instance, 'total_quantity', 1))
        if self.instance and total < (self.instance.total_quantity - self.instance.available_quantity):
            raise serializers.ValidationError({'total_quantity': 'Нельзя уменьшить общее количество ниже числа уже зарезервированных единиц.'})
        if total < 1:
            raise serializers.ValidationError({'total_quantity': 'Количество должно быть не меньше 1.'})
        return attrs

    def create(self, validated_data):
        validated_data['available_quantity'] = validated_data['total_quantity']
        return super().create(validated_data)

    def update(self, instance, validated_data):
        old_total = instance.total_quantity
        new_total = validated_data.get('total_quantity', old_total)
        validated_data['available_quantity'] = instance.available_quantity + (new_total - old_total)
        return super().update(instance, validated_data)


class EquipmentRequestEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)
    class Meta:
        model = EquipmentRequestEvent
        fields = ('id', 'event_type', 'details', 'actor_name', 'created_at')


class EquipmentRequestSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    requester_name = serializers.CharField(source='requester.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    events = EquipmentRequestEventSerializer(many=True, read_only=True)

    class Meta:
        model = EquipmentRequest
        fields = ('id', 'equipment', 'equipment_name', 'requester', 'requester_name',
                  'quantity', 'purpose', 'status', 'status_display', 'created_at',
                  'updated_at', 'events')
        read_only_fields = ('requester', 'status', 'created_at', 'updated_at', 'events')

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество должно быть не меньше 1.')
        return value

    def validate(self, attrs):
        equipment = attrs.get('equipment', getattr(self.instance, 'equipment', None))
        quantity = attrs.get('quantity', getattr(self.instance, 'quantity', 1))
        if equipment is None:
            return attrs
        if self.instance and self.instance.status != 'pending':
            changed_fields = set(attrs) - {'purpose'}
            if changed_fields:
                raise serializers.ValidationError('После согласования можно изменить только цель заявки.')
        if self.instance is None and quantity > equipment.total_quantity:
            raise serializers.ValidationError({'quantity': 'Количество превышает общее количество оборудования.'})
        return attrs
