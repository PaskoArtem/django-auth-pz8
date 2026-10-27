from django.contrib.auth.models import User
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)

    description = models.TextField(
        blank=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses'
    )

    def __str__(self):
        return self.title

class AcademicGroup(models.Model):
    name = models.CharField(max_length=50)

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='groups'
    )

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    academic_group = models.ForeignKey(
        AcademicGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    courses = models.ManyToManyField(
        Course,
        blank=True,
        related_name='students'
    )

    def __str__(self):
        return self.user.username
description = models.TextField(blank=True)

class Equipment(models.Model):
    """Учётный ресурс, который можно выдавать для учебных занятий."""

    CATEGORY_CHOICES = [
        ('computer', 'Компьютерная техника'),
        ('lab', 'Лабораторное оборудование'),
        ('presentation', 'Презентационное оборудование'),
        ('other', 'Другое'),
    ]

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    total_quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} ({self.available_quantity}/{self.total_quantity})'


class EquipmentRequest(models.Model):
    """Заявка пользователя на получение оборудования."""

    STATUS_CHOICES = [
        ('pending', 'Ожидает согласования'),
        ('approved', 'Согласована'),
        ('issued', 'Выдано'),
        ('returned', 'Возвращено'),
        ('cancelled', 'Отменена'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipment_requests')
    quantity = models.PositiveIntegerField(default=1)
    purpose = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Заявка #{self.pk}: {self.equipment.name}'


class EquipmentRequestEvent(models.Model):
    """Неизменяемая история действий по заявке."""

    request = models.ForeignKey(EquipmentRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    request_identifier = models.CharField(max_length=30, blank=True, default='')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment_request_events')
    event_type = models.CharField(max_length=40)
    details = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'id')

    def save(self, *args, **kwargs):
        if self.request_id and not self.request_identifier:
            self.request_identifier = str(self.request_id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Заявка {self.request_identifier or self.request_id}: {self.event_type}'
