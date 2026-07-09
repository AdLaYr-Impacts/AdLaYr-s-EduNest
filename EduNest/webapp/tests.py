from datetime import date
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Users
from common.choices import UserRoles
from webapp.models import Exam, ExamType, School, SchoolClass


class ExamApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.school = School.objects.create(
            name='Alpha School',
            short_name='Alpha',
            school_code='ALP-2026-0001',
            academic_year=2026,
        )
        self.other_school = School.objects.create(
            name='Beta School',
            short_name='Beta',
            school_code='BET-2026-0002',
            academic_year=2026,
        )

        self.user = Users.objects.create_user(
            username='admin-alpha',
            password='password123',
            role=UserRoles.SCHOOL_ADMIN,
            school=self.school,
        )
        self.other_user = Users.objects.create_user(
            username='admin-beta',
            password='password123',
            role=UserRoles.SCHOOL_ADMIN,
            school=self.other_school,
        )

        self.exam_type = ExamType.objects.create(name='Mid Term', school=self.school)
        self.other_exam_type = ExamType.objects.create(name='Final Term', school=self.other_school)

        self.class_1 = SchoolClass.objects.create(
            school=self.school,
            class_name='1',
            section='A',
            academic_year=2026,
        )
        self.class_2 = SchoolClass.objects.create(
            school=self.school,
            class_name='2',
            section='A',
            academic_year=2026,
        )
        self.other_class = SchoolClass.objects.create(
            school=self.other_school,
            class_name='3',
            section='A',
            academic_year=2026,
        )

        self.url = f'/edunest/api/schools/{self.school.uuid}/exams/'
        self.other_school_url = f'/edunest/api/schools/{self.other_school.uuid}/exams/'

    def _payload(self, **overrides):
        payload = {
            'name': 'Half Yearly',
            'exam_type': str(self.exam_type.uuid),
            'classes': [str(self.class_1.uuid), str(self.class_2.uuid)],
            'start_date': '12/07/2026',
            'end_date': '22/07/2026',
            'save_as_draft': True,
            'publish': False,
        }
        payload.update(overrides)
        return payload

    def test_create_exam_with_classes(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.url, self._payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Exam.objects.count(), 1)
        exam = Exam.objects.first()
        self.assertEqual(exam.school, self.school)
        self.assertEqual(exam.status, 'DRAFT')
        self.assertFalse(exam.is_locked)
        self.assertEqual(exam.exam_classes.count(), 2)
        self.assertEqual(response.data['academic_year'], 2026)

    def test_duplicate_exam_name_in_same_school_is_rejected(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url, self._payload(), format='json')

        response = self.client.post(self.url, self._payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_cross_school_class_assignment_is_blocked(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            self._payload(classes=[str(self.class_1.uuid), str(self.other_class.uuid)]),
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('classes[1]', response.data)

    def test_published_exam_allows_only_dates_and_classes(self):
        self.client.force_authenticate(user=self.user)
        create_response = self.client.post(
            self.url,
            self._payload(name='Annual Exam', publish=True, save_as_draft=False),
            format='json'
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        exam = Exam.objects.get(uuid=create_response.data['uuid'])
        detail_url = f'{self.url}{exam.uuid}/'

        rejected = self.client.patch(detail_url, {'name': 'Changed'}, format='json')
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', rejected.data)

        allowed = self.client.patch(detail_url, {'start_date': '13/07/2026'}, format='json')
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        exam.refresh_from_db()
        self.assertEqual(str(exam.start_date), '2026-07-13')

    def test_list_defaults_to_school_academic_year(self):
        Exam.objects.create(
            school=self.school,
            academic_year=2025,
            name='Archived Exam',
            exam_type=self.exam_type,
            start_date=date(2025, 7, 12),
            end_date=date(2025, 7, 22),
            status='DRAFT',
            is_locked=False,
            created_by=self.user,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)

        response = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

        response = self.client.get(self.url, {'academic_year': 2025})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_cross_school_access_is_blocked(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.other_school_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
