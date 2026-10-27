from django.contrib.auth.models import Group, User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import AcademicGroup, Course, Department


class AcademicDataAPITests(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(name='Информатика')
        self.user = User.objects.create_user(username='student_test', password='StrongPass123!')
        self.methodist_group, _ = Group.objects.get_or_create(name='Методист')
        self.methodist = User.objects.create_user(username='methodist_test', password='StrongPass123!')
        self.methodist.groups.add(self.methodist_group)

    def test_anonymous_user_cannot_read_api(self):
        response = self.client.get('/api/courses/')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_authenticated_user_can_read_but_cannot_create(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/departments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post('/api/courses/', {
            'title': 'Python basics',
            'description': '',
            'department': self.department.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_methodist_can_create_course(self):
        self.client.force_authenticate(user=self.methodist)
        response = self.client.post('/api/courses/', {
            'title': 'Python basics',
            'description': 'Учебный курс',
            'department': self.department.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Course.objects.filter(title='Python basics').exists())

    def test_course_title_validation(self):
        self.client.force_authenticate(user=self.methodist)
        response = self.client.post('/api/courses/', {
            'title': '',
            'description': '',
            'department': self.department.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Course.objects.filter(title='').exists())

    def test_duplicate_group_in_same_department_is_rejected(self):
        AcademicGroup.objects.create(name='ИВТ-1', department=self.department)
        self.client.force_authenticate(user=self.methodist)
        response = self.client.post('/api/groups/', {
            'name': 'ИВТ-1',
            'department': self.department.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EquipmentWorkflowAPITests(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import Group
        from .models import Equipment
        self.user = User.objects.create_user(username='requester', password='StrongPass123!')
        self.methodist = User.objects.create_user(username='workflow_methodist', password='StrongPass123!')
        group, _ = Group.objects.get_or_create(name='Методист')
        self.methodist.groups.add(group)
        self.equipment = Equipment.objects.create(
            name='Ноутбук для лаборатории', category='computer',
            total_quantity=3, available_quantity=3
        )

    def create_request(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/equipment-requests/', {
            'equipment': self.equipment.id, 'quantity': 2,
            'purpose': 'Лабораторная работа'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data['id']

    def test_create_request_writes_history(self):
        from .models import EquipmentRequestEvent
        request_id = self.create_request()
        self.assertTrue(EquipmentRequestEvent.objects.filter(request_identifier=str(request_id), event_type='created').exists())

    def test_user_only_sees_own_requests(self):
        self.create_request()
        other = User.objects.create_user(username='other_user', password='StrongPass123!')
        self.client.force_authenticate(user=other)
        self.assertEqual(len(self.client.get('/api/equipment-requests/').data), 0)

    def test_approval_reserves_stock_and_changes_status(self):
        request_id = self.create_request()
        self.client.force_authenticate(user=self.methodist)
        response = self.client.post(f'/api/equipment-requests/{request_id}/transition/', {'status': 'approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.available_quantity, 1)
        self.assertEqual(response.data['status'], 'approved')

    def test_invalid_transition_is_rejected(self):
        request_id = self.create_request()
        self.client.force_authenticate(user=self.methodist)
        response = self.client.post(f'/api/equipment-requests/{request_id}/transition/', {'status': 'returned'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transaction_rolls_back_stock_when_simulated_failure_occurs(self):
        from .models import EquipmentRequestEvent
        request_id = self.create_request()
        initial_events = EquipmentRequestEvent.objects.filter(request_identifier=str(request_id)).count()
        self.client.force_authenticate(user=self.methodist)
        response = self.client.post(f'/api/equipment-requests/{request_id}/transition/', {
            'status': 'approved', 'simulate_failure': True
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.available_quantity, 3)
        from .models import EquipmentRequest
        self.assertEqual(EquipmentRequest.objects.get(pk=request_id).status, 'pending')
        self.assertEqual(EquipmentRequestEvent.objects.filter(request_identifier=str(request_id)).count(), initial_events)


class EquipmentWorkflowAdditionalTests(APITestCase):
    """Дополнительные проверки сверх минимального набора СРС №7."""

    def setUp(self):
        from .models import Equipment
        self.owner = User.objects.create_user(username='owner_extra', password='StrongPass123!')
        self.other = User.objects.create_user(username='other_extra', password='StrongPass123!')
        self.methodist = User.objects.create_user(username='methodist_extra', password='StrongPass123!')
        group, _ = Group.objects.get_or_create(name='Методист')
        self.methodist.groups.add(group)
        self.equipment = Equipment.objects.create(
            name='Камера для практики', category='lab',
            total_quantity=2, available_quantity=2,
        )

    def create_request(self, quantity=1):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post('/api/equipment-requests/', {
            'equipment': self.equipment.id,
            'quantity': quantity,
            'purpose': 'Практическое занятие',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data['id']

    def test_insufficient_stock_does_not_approve(self):
        first = self.create_request(quantity=2)
        second = self.create_request(quantity=1)
        self.client.force_authenticate(user=self.methodist)
        self.assertEqual(self.client.post(f'/api/equipment-requests/{first}/transition/', {'status': 'approved'}, format='json').status_code, status.HTTP_200_OK)
        response = self.client.post(f'/api/equipment-requests/{second}/transition/', {'status': 'approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.available_quantity, 0)

    def test_other_user_cannot_retrieve_or_update_foreign_request(self):
        request_id = self.create_request()
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(f'/api/equipment-requests/{request_id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(f'/api/equipment-requests/{request_id}/', {'purpose': 'Чужая заявка'}, format='json').status_code, status.HTTP_404_NOT_FOUND)

    def test_editing_request_creates_history_event(self):
        from .models import EquipmentRequestEvent
        request_id = self.create_request()
        self.client.patch(f'/api/equipment-requests/{request_id}/', {'purpose': 'Обновлённая цель'}, format='json')
        self.assertTrue(EquipmentRequestEvent.objects.filter(request_identifier=str(request_id), event_type='updated').exists())

    def test_filters_by_status_and_category(self):
        self.create_request()
        response = self.client.get('/api/equipment-requests/?status=pending&category=lab')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        response = self.client.get('/api/equipment-requests/?status=returned&category=lab')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
