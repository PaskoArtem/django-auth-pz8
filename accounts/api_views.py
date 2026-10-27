from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    AcademicGroup, Course, Department, Equipment, EquipmentRequest,
    EquipmentRequestEvent,
)
from .permissions import IsMethodistOrReadOnly
from .serializers import (
    AcademicGroupSerializer, CourseSerializer, DepartmentSerializer,
    EquipmentSerializer, EquipmentRequestSerializer,
)


def is_methodist(user):
    return user.groups.filter(name='Методист').exists() or user.is_superuser


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


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all().order_by('name')
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Список доступен всем вошедшим; менять складские остатки может методист.
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            from rest_framework.permissions import BasePermission
            class MethodistOnly(BasePermission):
                def has_permission(inner_self, request, view):
                    return request.user.is_authenticated and is_methodist(request.user)
            return [MethodistOnly()]
        return super().get_permissions()


class EquipmentRequestViewSet(viewsets.ModelViewSet):
    serializer_class = EquipmentRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = EquipmentRequest.objects.select_related('equipment', 'requester').prefetch_related('events__actor')
        if not is_methodist(self.request.user):
            qs = qs.filter(requester=self.request.user)
        status_filter = self.request.query_params.get('status')
        category_filter = self.request.query_params.get('category')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if category_filter:
            qs = qs.filter(equipment__category=category_filter)
        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            request_obj = serializer.save(requester=self.request.user)
            EquipmentRequestEvent.objects.create(
                request=request_obj, actor=self.request.user,
                event_type='created', details='Заявка создана'
            )

    def perform_update(self, serializer):
        # Сохраняем изменение заявки и запись аудита атомарно.
        instance = serializer.instance
        changed_fields = []
        for field in ('equipment', 'quantity', 'purpose'):
            if field in serializer.validated_data:
                old_value = getattr(instance, f'{field}_id' if field == 'equipment' else field)
                new_value = serializer.validated_data[field]
                new_value = getattr(new_value, 'pk', new_value)
                if old_value != new_value:
                    changed_fields.append(field)
        with transaction.atomic():
            request_obj = serializer.save()
            if changed_fields:
                labels = {'equipment': 'оборудование', 'quantity': 'количество', 'purpose': 'цель использования'}
                details = 'Изменены поля: ' + ', '.join(labels[field] for field in changed_fields)
                EquipmentRequestEvent.objects.create(
                    request=request_obj,
                    actor=self.request.user,
                    event_type='updated',
                    details=details,
                )

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status != 'pending':
            raise ValidationError('Удалить можно только заявку в статусе «Ожидает согласования».')
        with transaction.atomic():
            EquipmentRequestEvent.objects.create(
                request=obj, actor=request.user, event_type='deleted',
                details='Заявка удалена пользователем'
            )
            obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        target = request.data.get('status')
        allowed = {
            'pending': {'approved', 'cancelled'},
            'approved': {'issued', 'cancelled'},
            'issued': {'returned'},
            'returned': set(),
            'cancelled': set(),
        }
        with transaction.atomic():
            obj = get_object_or_404(
                EquipmentRequest.objects.select_for_update().select_related('equipment', 'requester'),
                pk=pk
            )
            if not is_methodist(request.user) and obj.requester_id != request.user.id:
                raise PermissionDenied('У вас нет доступа к этой заявке.')
            if target not in allowed.get(obj.status, set()):
                raise ValidationError(f'Переход из состояния «{obj.get_status_display()}» в указанное состояние запрещён.')
            if target in {'approved', 'issued', 'returned'} and not is_methodist(request.user):
                raise PermissionDenied('Изменять этап выдачи оборудования может только методист.')

            equipment = Equipment.objects.select_for_update().get(pk=obj.equipment_id)
            old_status = obj.status
            if target == 'approved':
                if equipment.available_quantity < obj.quantity:
                    raise ValidationError('Недостаточно свободного оборудования для согласования заявки.')
                Equipment.objects.filter(pk=equipment.pk).update(
                    available_quantity=F('available_quantity') - obj.quantity
                )
            elif target == 'cancelled' and old_status == 'approved':
                Equipment.objects.filter(pk=equipment.pk).update(
                    available_quantity=F('available_quantity') + obj.quantity
                )
            elif target == 'returned':
                Equipment.objects.filter(pk=equipment.pk).update(
                    available_quantity=F('available_quantity') + obj.quantity
                )

            # Учебный флаг для демонстрации отката: передайте simulate_failure=true.
            # Он разрешён только методисту и не изменяет данные при ошибке.
            if request.data.get('simulate_failure') and is_methodist(request.user):
                raise ValidationError('Учебная имитация сбоя: транзакция отменена, изменения не сохранены.')

            obj.status = target
            obj.save(update_fields=['status', 'updated_at'])
            EquipmentRequestEvent.objects.create(
                request=obj, actor=request.user, event_type=target,
                details=f'Статус изменён: {old_status} → {target}'
            )
        obj.refresh_from_db()
        return Response(self.get_serializer(obj).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        obj = self.get_object()
        from .serializers import EquipmentRequestEventSerializer
        return Response(EquipmentRequestEventSerializer(obj.events.select_related('actor').all(), many=True).data)
