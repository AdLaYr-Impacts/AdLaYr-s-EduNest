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
    School,
    SchoolClass,
    Subjects,
    ClassSubjects
)
from common.choices import (
    UserRoles, 
    UserGender, 
    MaritalStatus, 
    AddressType,
    SubjectType
)
from drf_spectacular.utils import extend_schema_field
from common.helper import generate_user_code


# School Teacher
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


# School Class
class TeacherMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = SchoolTeacher
        fields = ['uuid', 'full_name', 'teacher_code']

class SchoolClassSerializer(serializers.ModelSerializer):
    class_teacher_uuid = serializers.SlugRelatedField(
        slug_field='uuid', 
        queryset=SchoolTeacher.objects.all(),
        source='class_teacher',
        required=False,
        allow_null=True
    )
    assistant_teachers_uuids = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=SchoolTeacher.objects.all(),
        source='assistant_teacher',
        many=True,
        required=False
    )
    
    # For response
    class_teacher = TeacherMiniSerializer(read_only=True)
    assistant_teacher = TeacherMiniSerializer(many=True, read_only=True)
    
    class Meta:
        model = SchoolClass
        fields = [
            'uuid', 'class_name', 'section', 'academic_year', 'medium', 
            'board', 'max_strength', 'whatsapp_group_link', 'classroom_number', 
            'smart_class_enabled', 'class_color_code', 'class_teacher_uuid',
            'assistant_teachers_uuids', 'class_teacher', 'assistant_teacher'
        ]
        read_only_fields = ['uuid']

    def validate_class_name(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Class name cannot be whitespace only.")
        return value

    def validate_section(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Section cannot be whitespace only.")
        return value

    def validate_max_strength(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Max strength cannot be negative.")
        return value

    def validate(self, data):
        school = self.context.get('school')
        class_name = data.get('class_name', self.instance.class_name if self.instance else None)
        section = data.get('section', self.instance.section if self.instance else None)
        academic_year = data.get('academic_year', self.instance.academic_year if self.instance else None)
        
        if not class_name:
            raise serializers.ValidationError({"class_name": "This field is required."})
        if not section:
            raise serializers.ValidationError({"section": "This field is required."})
        if not academic_year:
            raise serializers.ValidationError({"academic_year": "This field is required."})

        # Duplicate validation within same school
        query = SchoolClass.objects.filter(
            school=school,
            class_name__iexact=class_name,
            section__iexact=section,
            academic_year=academic_year
        )
        
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
            
        if query.exists():
            raise serializers.ValidationError(
                f"Class {class_name} - Section {section} for Academic Year {academic_year} already exists in this school"
            )
            
        # Validate that the teachers belong to the same school and are not deleted
        class_teacher = data.get('class_teacher')
        if class_teacher:
            if class_teacher.school != school:
                raise serializers.ValidationError({"class_teacher_uuid": "Teacher does not belong to this school."})
            if class_teacher.user.is_deleted:
                raise serializers.ValidationError({"class_teacher_uuid": f"The teacher '{class_teacher.user.get_full_name()}' cannot be assigned because their account has been deactivated or deleted."})
            
        assistant_teachers = data.get('assistant_teacher', [])
        for teacher in assistant_teachers:
            if teacher.school != school:
                raise serializers.ValidationError({"assistant_teachers_uuids": f"Teacher {teacher.teacher_code} does not belong to this school."})
            if teacher.user.is_deleted:
                raise serializers.ValidationError({"assistant_teachers_uuids": f"The teacher '{teacher.user.get_full_name()}' cannot be assigned as an assistant because their account has been deactivated or deleted."})

        return data

    @transaction.atomic
    def create(self, validated_data):
        school = self.context.get('school')
        assistant_teachers = validated_data.pop('assistant_teacher', [])

        school_class = SchoolClass.objects.create(
            school=school,
            **validated_data
        )

        if assistant_teachers:
            school_class.assistant_teacher.set(assistant_teachers)

        # Update teacher statuses
        if school_class.class_teacher:
            school_class.class_teacher.is_class_teacher = True
            school_class.class_teacher.save()

        for teacher in assistant_teachers:
            teacher.is_assistant_class_teacher = True
            teacher.save()

        return school_class

    @transaction.atomic
    def update(self, instance, validated_data):
        old_class_teacher = instance.class_teacher
        old_assistant_teachers = set(instance.assistant_teacher.all())

        assistant_teachers = validated_data.pop('assistant_teacher', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if assistant_teachers is not None:
            instance.assistant_teacher.set(assistant_teachers)
            new_assistant_teachers = set(assistant_teachers)
        else:
            new_assistant_teachers = old_assistant_teachers

        # Update Class Teacher Status
        new_class_teacher = instance.class_teacher
        if old_class_teacher != new_class_teacher:
            if old_class_teacher:
                still_class_teacher = SchoolClass.objects.filter(class_teacher=old_class_teacher).exclude(pk=instance.pk).exists()
                if not still_class_teacher:
                    old_class_teacher.is_class_teacher = False
                    old_class_teacher.save()

            if new_class_teacher:
                new_class_teacher.is_class_teacher = True
                new_class_teacher.save()

        # Update Assistant Teacher Status
        # Teachers removed
        removed_assistants = old_assistant_teachers - new_assistant_teachers
        for teacher in removed_assistants:
            still_assistant = SchoolClass.objects.filter(assistant_teacher=teacher).exclude(pk=instance.pk).exists()
            if not still_assistant:
                teacher.is_assistant_class_teacher = False
                teacher.save()

        # Teachers added
        added_assistants = new_assistant_teachers - old_assistant_teachers
        for teacher in added_assistants:
            teacher.is_assistant_class_teacher = True
            teacher.save()

        return instance


class TeacherSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    class_teacher_count = serializers.IntegerField(read_only=True)
    assistant_class_teacher_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = SchoolTeacher
        fields = ['uuid', 'full_name', 'class_teacher_count', 'assistant_class_teacher_count']


class SubjectSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', read_only=True)
    
    class Meta:
        model = Subjects
        fields = ['id', 'name', 'code', 'description', 'subject_type', 'is_active']
        read_only_fields = ['id']

    def validate_name(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Subject name cannot be whitespace only.")
        return value

    def validate_code(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Subject code cannot be whitespace only.")
        
        school = self.context.get('school')
        query = Subjects.objects.filter(school=school, code__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError(f"Subject code {value} already exists in this school")
            
        return value

    def validate_subject_type(self, value):
        if value and value not in SubjectType.values:
            raise serializers.ValidationError(f"Invalid subject type. Must be one of: {', '.join(SubjectType.values)}")
        return value

    def validate(self, data):
        school = self.context.get('school')
        name = data.get('name', self.instance.name if self.instance else None)
        
        if not name:
            raise serializers.ValidationError({"name": "Subject name is required."})

        query = Subjects.objects.filter(
            school=school,
            name__iexact=name
        )
        
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
            
        if query.exists():
            raise serializers.ValidationError(
                {"name": f"Subject {name} already exists in this school"}
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data['school'] = self.context.get('school')
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class ClassListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = SchoolClass
        fields = ['uuid', 'name']

    @extend_schema_field(serializers.CharField)
    def get_name(self, obj):
        return f"{obj.class_name} - {obj.section}" if obj.section else obj.class_name


class SubjectListSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = Subjects
        fields = ['uuid', 'code', 'name']
class ClassSubjectSerializer(serializers.ModelSerializer):
    subject_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Subjects.objects.all(),
        source='subject'
    )
    class_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=SchoolClass.objects.all(),
        source='subject_class'
    )
    teacher_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=SchoolTeacher.objects.all(),
        source='teacher',
        required=False,
        allow_null=True
    )
    
    subject_details = SubjectListSerializer(source='subject', read_only=True)
    class_details = ClassListSerializer(source='subject_class', read_only=True)
    teacher_details = TeacherMiniSerializer(source='teacher', read_only=True)
    
    class Meta:
        model = ClassSubjects
        fields = [
            'uuid', 'subject_uuid', 'class_uuid', 'teacher_uuid',
            'is_optional', 'is_language', 'max_marks', 'pass_marks',
            'sort_order', 'subject_details', 'class_details', 'teacher_details'
        ]
        read_only_fields = ['uuid']

    def validate(self, data):
        school = self.context.get('school')
        subject = data.get('subject')
        subject_class = data.get('subject_class')
        teacher = data.get('teacher')

        # School validations
        if subject and subject.school != school:
            raise serializers.ValidationError({"subject_uuid": "Subject does not belong to this school."})
        
        if subject_class and subject_class.school != school:
            raise serializers.ValidationError({"class_uuid": "Class does not belong to this school."})
            
        if teacher:
            if teacher.school != school:
                raise serializers.ValidationError({"teacher_uuid": "Teacher does not belong to this school."})
            if teacher.user.is_deleted:
                raise serializers.ValidationError({"teacher_uuid": f"The teacher '{teacher.user.get_full_name()}' cannot be assigned because their account has been deactivated or deleted."})

        # Duplicate validation
        if subject and subject_class:
            query = ClassSubjects.objects.filter(
                subject=subject,
                subject_class=subject_class
            )
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise serializers.ValidationError(
                    f"Subject {subject.name} already assigned to the class {subject_class.class_name}"
                )

        # Marks validation
        max_marks = data.get('max_marks', self.instance.max_marks if self.instance else 100)
        pass_marks = data.get('pass_marks', self.instance.pass_marks if self.instance else 35)
        
        if pass_marks is not None and max_marks is not None:
            if pass_marks > max_marks:
                raise serializers.ValidationError({"pass_marks": "Pass marks cannot be greater than max marks."})
            if pass_marks < 0:
                raise serializers.ValidationError({"pass_marks": "Pass marks cannot be negative."})
            if max_marks < 0:
                raise serializers.ValidationError({"max_marks": "Max marks cannot be negative."})

        return data

    @transaction.atomic
    def create(self, validated_data):
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
