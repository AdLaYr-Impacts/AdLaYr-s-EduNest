from rest_framework import viewsets
from webapp.models import School
from .serializers import SchoolSerializer
from permissions.permissions import IsSuperAdmin

class SchoolViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Schools, including their Contacts and Registrations, 
    to be viewed or edited in a single request.
    """
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsSuperAdmin]
