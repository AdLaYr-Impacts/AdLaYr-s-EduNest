from rest_framework import serializers
from django.db import transaction
from webapp.models import School, SchoolContact, SchoolRegistration, AddressBook
from common.choices import AddressType

class SchoolContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolContact
        exclude = ['school']

class SchoolRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolRegistration
        exclude = ['school']

class AddressBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressBook
        exclude = ['school', 'user']

class SchoolSerializer(serializers.ModelSerializer):
    school_contact = SchoolContactSerializer(required=False, allow_null=True)
    school_registeration = SchoolRegistrationSerializer(required=False, allow_null=True)
    school_address = AddressBookSerializer(many=True, required=False)

    class Meta:
        model = School
        fields = '__all__'
        extra_kwargs = {
            'school_code': {'read_only': True},
            'total_students': {'read_only': True},
            'total_staffs': {'read_only': True},
        }

    @transaction.atomic
    def create(self, validated_data):
        contact_data = validated_data.pop('school_contact', None)
        registration_data = validated_data.pop('school_registeration', None)
        address_data = validated_data.pop('school_address', [])
        
        school = School.objects.create(**validated_data)
        
        if contact_data:
            SchoolContact.objects.create(school=school, **contact_data)
            
        if registration_data:
            SchoolRegistration.objects.create(school=school, **registration_data)

        if address_data:
            for addr in address_data:
                AddressBook.objects.create(school=school, address_type=AddressType.SCHOOL, **addr)
            
        return school

    @transaction.atomic
    def update(self, instance, validated_data):
        contact_data = validated_data.pop('school_contact', None)
        registration_data = validated_data.pop('school_registeration', None)
        address_data = validated_data.pop('school_address', None)
        
        # Update School instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or Create SchoolContact
        if contact_data is not None:
            SchoolContact.objects.update_or_create(school=instance, defaults=contact_data)

        # Update or Create SchoolRegistration
        if registration_data is not None:
            SchoolRegistration.objects.update_or_create(school=instance, defaults=registration_data)

        # Update or Create AddressBook
        if address_data is not None:
            # For simplicity, we'll clear existing addresses and recreate them if provided
            instance.school_address.all().delete()
            for addr in address_data:
                AddressBook.objects.create(school=instance, address_type=AddressType.SCHOOL, **addr)
            
        return instance
