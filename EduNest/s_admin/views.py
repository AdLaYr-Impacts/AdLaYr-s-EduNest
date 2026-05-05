from rest_framework import viewsets, status
from rest_framework.response import Response
from webapp.models import School
from .serializers import SchoolSerializer
from permissions.permissions import IsSuperAdmin
from common.helper import generate_school_code, get_next_school_sequence

class SchoolViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Schools, including their Contacts and Registrations, 
    to be view, create, edit & delete in a single request.
    """
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsSuperAdmin]

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
