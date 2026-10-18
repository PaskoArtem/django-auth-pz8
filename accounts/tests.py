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
            'title': 'SQL',
            'description': '',
            'department': self.department.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Course.objects.filter(title='SQL').exists())

    def test_duplicate_group_in_same_department_is_rejected(self):
        AcademicGroup.objects.create(name='ИВТ-1', department=self.department)
        self.client.force_authenticate(user=self.methodist)
        response = self.client.post('/api/groups/', {
            'name': 'ИВТ-1',
            'department': self.department.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
