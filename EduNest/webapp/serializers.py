import datetime
import re
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from accounts.models import Users
from webapp.models import (
    SchoolTeacher, 
    TeacherEducationDetails, 
    TeacherExperianceDetails, 
    TeacherEmploymentDetails,
    AddressBook,
    School
)
from common.choices import UserRoles, UserGender, MaritalStatus, EmployementType, EmployeStatus, AddressType
from common.helper import generate_user_code

class TeacherEducationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', read_only=False, required=False)

    class Meta:
        model = TeacherEducationDetails
        fields = [
            'id', 'degree', 'specialization', 'institution_name', 
            'university', 'year_of_passing', 'pass_percentage'
        ]

class TeacherExperienceSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', read_only=False, required=False)
    years_of_experience = serializers.IntegerField(source='years_of_experiance', read_only=True)

    class Meta:
        model = TeacherExperianceDetails
        fields = [
            'id', 'school_name', 'school_address', 'designation', 
            'subjects_taught', 'start_date', 'end_date', 
            'years_of_experience', 'reason_for_leaving'
        ]

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be earlier than start date.")
        return data

class TeacherEmploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherEmploymentDetails
        fields = [
            'basic_salary', 'allowance', 'bank_name', 'bank_account_number',
            'ifsc_code', 'pf_number', 'esi_number', 'contract_start_date', 'contract_end_date'
        ]

    def validate(self, data):
        start_date = data.get('contract_start_date')
        end_date = data.get('contract_end_date')
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("Contract end date cannot be earlier than contract start date.")
        return data

class TeacherAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressBook
        fields = [
            'address_line_1', 'address_line_2', 'address_line_3',
            'city', 'district', 'state', 'pincode', 'Country', 'landmark'
        ]

    def validate_pincode(self, value):
        if value and not re.match(r'^\d{6}$', value):
            raise serializers.ValidationError("Pincode must be 6 digits.")
        return value

class TeacherSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', required=False, allow_null=True, allow_blank=True)
    phone_number = serializers.CharField(source='user.phone_number', required=False, allow_null=True, allow_blank=True)
    alternative_phone_number = serializers.CharField(source='user.alternative_phone_number', required=False, allow_blank=True)
    profile_picture = serializers.ImageField(source='user.profile_picture', required=False, allow_null=True)
    aadhaar_number = serializers.CharField(source='user.aadhaar_number', required=False, allow_blank=True)
    nationality = serializers.CharField(source='user.nationality', required=False, allow_blank=True)
    passport = serializers.CharField(source='user.passport', required=False, allow_blank=True)
    date_of_birth = serializers.DateField(source='user.date_of_birth', required=False, allow_null=True)
    gender = serializers.ChoiceField(source='user.gender', choices=UserGender.choices, required=False, allow_blank=True)
    blood_group = serializers.CharField(source='user.blood_group', required=False, allow_blank=True)
    marital_status = serializers.ChoiceField(source='user.marital_status', choices=MaritalStatus.choices, required=False, allow_blank=True)
    
    # Nested objects
    address = TeacherAddressSerializer(required=False)
    education_details = TeacherEducationSerializer(many=True, required=False, source='teacher_education')
    experience_details = TeacherExperienceSerializer(many=True, required=False, source='teacher_experiance')
    employment_details = TeacherEmploymentSerializer(many=True, required=False, source='teacher_employment') 
    
    # Account Credentials
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    # Read only fields
    uuid = serializers.UUIDField(read_only=True)
    teacher_code = serializers.CharField(read_only=True)

    class Meta:
        model = SchoolTeacher
        fields = [
            'uuid', 'teacher_code', 'first_name', 'last_name', 'email', 'phone_number',
            'alternative_phone_number', 'profile_picture', 'aadhaar_number',
            'nationality', 'passport', 'date_of_birth', 'gender', 'blood_group',
            'marital_status', 'joining_date', 'employment_type', 'status',
            'address', 'education_details', 'experience_details', 'employment_details',
            'password', 'confirm_password'
        ]

    def validate_aadhaar_number(self, value):
        if value and not re.match(r'^\d{12}$', value):
            raise serializers.ValidationError("Aadhaar number must be 12 digits.")
        return value

    def validate_email(self, value):
        if value == "":
            return None
        return value

    def validate_phone_number(self, value):
        if value == "":
            return None
        if value and not re.match(r'^\d{10,15}$', value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value

    def validate(self, data):
        user_data = data.get('user', {})
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Password validation
        if not self.instance:
            if not password or not confirm_password:
                raise serializers.ValidationError({"password": "Password and confirm password are required for new teacher."})
        
        if password or confirm_password:
            # Update or Creation mode with password provided
            if password != confirm_password:
                raise serializers.ValidationError({"password": "Passwords do not match."})
            try:
                validate_password(password)
            except Exception as e:
                raise serializers.ValidationError({"password": list(e.messages)})

        # Nationality and Passport validation
        nationality = user_data.get('nationality')
        passport = user_data.get('passport')
        if nationality and str(nationality).upper() != 'IN' and not passport:
            raise serializers.ValidationError({"passport": "Passport is mandatory for non-Indian citizens."})

        # Date of birth validation
        dob = user_data.get('date_of_birth')
        if dob and dob > datetime.date.today():
            raise serializers.ValidationError({"date_of_birth": "Date of birth cannot be in the future."})

        # Email and Phone uniqueness (manual check if needed, but model handles it mostly)
        # Email uniqueness check for new users
        email = user_data.get('email')
        if email:
            query = Users.objects.filter(email=email, is_deleted=False)
            if self.instance:
                query = query.exclude(id=self.instance.user.id)
            if query.exists():
                raise serializers.ValidationError({"email": "User with this email already exists."})

        return data

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        address_data = validated_data.pop('address', None)
        education_data = validated_data.pop('teacher_education', [])
        experience_data = validated_data.pop('teacher_experiance', [])
        employment_data = validated_data.pop('teacher_employment', [])
        password = validated_data.pop('password')
        validated_data.pop('confirm_password', None)
        
        school = self.context.get('school')
        
        # Generate user code
        username = generate_user_code(school, UserRoles.TEACHER)
        
        # Create User
        user = Users.objects.create(
            username=username,
            role=UserRoles.TEACHER,
            school=school,
            **user_data
        )
        user.set_password(password)
        user.save()
        
        # Create SchoolTeacher
        teacher = SchoolTeacher.objects.create(
            user=user,
            school=school,
            teacher_code=username,
            is_class_teacher=False,
            is_principal=False,
            **validated_data
        )
        
        # Create Address
        if address_data:
            AddressBook.objects.create(
                user=user,
                address_type=AddressType.USER,
                **address_data
            )
            
        # Create Education
        for edu in education_data:
            TeacherEducationDetails.objects.create(teacher=teacher, **edu)
            
        # Create Experience
        for exp in experience_data:
            # Calculate years of experience
            start_date = exp.get('start_date')
            end_date = exp.get('end_date')
            if start_date and end_date:
                delta = end_date - start_date
                exp['years_of_experiance'] = round(delta.days / 365.25)
            TeacherExperianceDetails.objects.create(teacher=teacher, **exp)
            
        # Create Employment
        for emp in employment_data:
            TeacherEmploymentDetails.objects.create(teacher=teacher, **emp)
            
        return teacher

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        address_data = validated_data.pop('address', None)
        education_data = validated_data.pop('teacher_education', None)
        experience_data = validated_data.pop('teacher_experiance', None)
        employment_data = validated_data.pop('teacher_employment', None)
        
        # Handle Account Credentials
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        # Update User
        user = instance.user
        if password:
            user.set_password(password)
        
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        # Update SchoolTeacher
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.is_class_teacher=False
        instance.is_principal=False
        instance.save()
        
        # Update Address
        if address_data:
            address_obj, created = AddressBook.objects.get_or_create(
                user=user,
                address_type=AddressType.USER,
                defaults=address_data
            )
            if not created:
                for attr, value in address_data.items():
                    setattr(address_obj, attr, value)
                address_obj.save()
                
        # Update Education
        if education_data is not None:
            existing_ids = [edu.uuid for edu in instance.teacher_education.all()]
            incoming_ids = [edu.get('uuid') for edu in education_data if edu.get('uuid')]
            
            # Delete records not in incoming data
            for edu_uuid in existing_ids:
                if edu_uuid not in incoming_ids:
                    TeacherEducationDetails.objects.filter(uuid=edu_uuid).delete()
            
            # Update or create
            for edu in education_data:
                edu_uuid = edu.pop('uuid', None)
                if edu_uuid:
                    TeacherEducationDetails.objects.filter(uuid=edu_uuid).update(**edu)
                else:
                    TeacherEducationDetails.objects.create(teacher=instance, **edu)

        # Update Experience
        if experience_data is not None:
            existing_ids = [exp.uuid for exp in instance.teacher_experiance.all()]
            incoming_ids = [exp.get('uuid') for exp in experience_data if exp.get('uuid')]
            
            for exp_uuid in existing_ids:
                if exp_uuid not in incoming_ids:
                    TeacherExperianceDetails.objects.filter(uuid=exp_uuid).delete()
                    
            for exp in experience_data:
                exp_uuid = exp.pop('uuid', None)
                start_date = exp.get('start_date')
                end_date = exp.get('end_date')
                if start_date and end_date:
                    delta = end_date - start_date
                    exp['years_of_experiance'] = round(delta.days / 365.25)
                
                if exp_uuid:
                    TeacherExperianceDetails.objects.filter(uuid=exp_uuid).update(**exp)
                else:
                    TeacherExperianceDetails.objects.create(teacher=instance, **exp)

        # Update Employment
        if employment_data is not None:
            # Assuming employment details is also multi-row because of ForeignKey, 
            # but usually it's treated as one set. I'll follow the same logic as above.
            existing_ids = [emp.uuid for emp in instance.teacher_employment.all()]
            incoming_ids = [emp.get('uuid') for emp in employment_data if emp.get('uuid')]
            
            for emp_uuid in existing_ids:
                if emp_uuid not in incoming_ids:
                    TeacherEmploymentDetails.objects.filter(uuid=emp_uuid).delete()
                    
            for emp in employment_data:
                emp_uuid = emp.pop('uuid', None)
                if emp_uuid:
                    TeacherEmploymentDetails.objects.filter(uuid=emp_uuid).update(**emp)
                else:
                    TeacherEmploymentDetails.objects.create(teacher=instance, **emp)

        return instance
