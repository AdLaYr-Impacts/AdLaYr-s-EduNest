from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from permissions.permissions import (
    IsSchoolAdmin,
    IsClassTeacher,
)


class SchoolAdminView(APIView):

    permission_classes = [IsSchoolAdmin]
    
    @extend_schema(
        summary="EduNest APIs",
        description="To Test School Admin Permissions"
    )
    def get(self, request, *args, **kwargs):
        return Response(
            {"messsage": "School Admin View"}, status=status.HTTP_202_ACCEPTED
        )
    

class ClassTeacherView(APIView):

    permission_classes = [IsClassTeacher]

    @extend_schema(
        summary="EduNest APIs",
        description="To Test School Admin Permissions"
    )
    def get(self, request, *args, **kwargs):
        return Response(
            {"message": "Class teacher view"}, status=status.HTTP_202_ACCEPTED
        )