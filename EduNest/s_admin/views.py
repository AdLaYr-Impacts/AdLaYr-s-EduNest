from rest_framework import viewsets, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from webapp.models import School
from .serializers import SchoolSerializer
from permissions.permissions import IsSuperAdmin
from common.helper import generate_school_code, get_next_school_sequence
from common.pagination import StandardPagination, StandardPageNumberPagination

class SchoolViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Schools, including their Contacts and Registrations, 
    to be viewed, created, edited & deleted.
    """
    
    queryset = School.objects.select_related('school_contact', 'school_registeration').all()
    serializer_class = SchoolSerializer
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardPagination

    # Adding support for Filtering, Searching, and Ordering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['school_type', 'board', 'medium_of_instructions', 'is_active']
    search_fields = ['name', 'short_name', 'school_code']
    ordering_fields = ['created_at', 'name', 'total_students']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        short_name = self.request.data.get('short_name')
        name = self.request.data.get('name')
        
        sequence = get_next_school_sequence()
        school_code = generate_school_code(short_name or name, sequence)
        
        serializer.save(
            school_code=school_code,
            total_students=0,
            total_staffs=0
        )

    def perform_update(self, serializer):
        # To ensure school_code is not updated if passed in request data
        serializer.save(school_code=serializer.instance.school_code)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(
            {"message": "School deactivated successfully."},
            status=status.HTTP_200_OK
        )
