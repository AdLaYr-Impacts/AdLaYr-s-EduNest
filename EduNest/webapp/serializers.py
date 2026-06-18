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
    ClassSubjects,
    SubjectGroup,
    Students,
    StudentsAdmissionDetails,
    StudentParentDetails,
    StudentAcademicdetails
)
from common.choices import (
    UserRoles, 
    UserGender, 
    MaritalStatus, 
    AddressType,
    SubjectType,
    CasteCategory
)
from drf_spectacular.utils import extend_schema_field
from django_countries.serializer_fields import CountryField
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
    Country = CountryField(required=False, allow_blank=True)

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
    nationality = CountryField(source='user.nationality', required=False, allow_blank=True)
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
            query = Users.objects.filter(email=email)
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


class ClassSubjectGroupSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    uuid = serializers.UUIDField(read_only=True)
    subjects = serializers.SerializerMethodField()

    class Meta:
        model = SchoolClass
        fields = ['uuid', 'name', 'subjects']

    @extend_schema_field(serializers.CharField)
    def get_name(self, obj):
        return f"{obj.class_name} - {obj.section}" if obj.section else obj.class_name

    @extend_schema_field(SubjectListSerializer(many=True))
    def get_subjects(self, obj):
        if hasattr(obj, 'active_subjects'):
            subjects = [cs.subject for cs in obj.active_subjects if cs.subject]
        else:
            class_subjects = obj.class_as_subject_class.filter(
                is_active=True, 
                subject__is_active=True
            ).select_related('subject')
            subjects = [cs.subject for cs in class_subjects]
        return SubjectListSerializer(subjects, many=True).data


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


class SubjectGroupSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', read_only=True)
    class_uuids = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=SchoolClass.objects.all(),
        source='classes',
        many=True,
        required=False
    )
    
    classes_details = ClassListSerializer(source='classes', many=True, read_only=True)

    class Meta:
        model = SubjectGroup
        fields = ['id', 'name', 'code', 'class_uuids', 'description', 'is_active', 'classes_details']
        read_only_fields = ['id']

    def validate_name(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("SubjectGroup name cannot be whitespace only.")
        return value

    def validate_code(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("SubjectGroup code cannot be whitespace only.")
        return value

    def validate(self, data):
        school = self.context.get('school')
        name = data.get('name', self.instance.name if self.instance else None)
        code = data.get('code', self.instance.code if self.instance else None)
        classes = data.get('classes', [])

        if not name:
            raise serializers.ValidationError({"name": "Subject Group name is required."})

        # One school should contain one unique name
        name_query = SubjectGroup.objects.filter(school=school, name__iexact=name)
        if self.instance:
            name_query = name_query.exclude(pk=self.instance.pk)
        if name_query.exists():
            raise serializers.ValidationError({"name": f"SubjectGroup {name} already assigned to this School"})

        # One school should contain one unique code
        if code:
            code_query = SubjectGroup.objects.filter(school=school, code__iexact=code)
            if self.instance:
                code_query = code_query.exclude(pk=self.instance.pk)
            if code_query.exists():
                raise serializers.ValidationError({"code": f"SubjectGroup {code} already assigned to this School"})

        # Classes belongs to same school
        for cls in classes:
            if cls.school != school:
                raise serializers.ValidationError({"class_uuids": f"Class {cls.uuid} does not belong to this school."})

        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data['school'] = self.context.get('school')
        classes = validated_data.pop('classes', [])
        subject_group = SubjectGroup.objects.create(**validated_data)
        if classes:
            subject_group.classes.set(classes)
        return subject_group

    @transaction.atomic
    def update(self, instance, validated_data):
        classes = validated_data.pop('classes', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if classes is not None:
            instance.classes.set(classes)
        return instance


# Student Management
class StudentAdmissionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', read_only=True)

    class Meta:
        model = StudentsAdmissionDetails
        fields = [
            'id', 'admission_number', 'admission_type', 'admission_date', 
            'academic_year', 'student_status', 'previous_school'
        ]

    def validate(self, data):
        admission_number = data.get('admission_number')
        if admission_number:
            school = self.context.get('school')
            query = StudentsAdmissionDetails.objects.filter(
                student__school=school,
                admission_number=admission_number
            )
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise serializers.ValidationError({
                    "admission_number": f"Admission number '{admission_number}' already exists within this school."
                })
        return data


class StudentAcademicSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', read_only=True)
    class_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=SchoolClass.objects.all(),
        source='student_class',
        required=False,
        allow_null=True
    )
    subject_group_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=SubjectGroup.objects.all(),
        source='subject_group',
        required=False,
        allow_null=True
    )
    
    class_details = ClassListSerializer(source='student_class', read_only=True)
    subject_group_details = SubjectGroupSerializer(source='subject_group', read_only=True)

    class Meta:
        model = StudentAcademicdetails
        fields = [
            'id', 'class_uuid', 'subject_group_uuid', 'roll_number', 
            'register_number', 'second_language', 'third_language', 
            'transport_requird', 'pickup_point', 'vehicle_number', 
            'vehicle_rc_number', 'driver_name', 'driver_phone', 
            'hostel_requird', 'hostel_name', 'room_number', 
            'warden_name', 'warden_phone', 'class_details', 
            'subject_group_details'
        ]

    def validate(self, data):
        school = self.context.get('school')
        student_class = data.get('student_class')
        subject_group = data.get('subject_group')
        roll_number = data.get('roll_number')

        # Fallback to existing values if not provided in partial updates (PUT/PATCH)
        if self.instance:
            if student_class is None and 'student_class' not in data:
                student_class = self.instance.student_class
            if subject_group is None and 'subject_group' not in data:
                subject_group = self.instance.subject_group

        if student_class and student_class.school != school:
            raise serializers.ValidationError({"class_uuid": "Class does not belong to this school."})
        
        if subject_group and subject_group.school != school:
            raise serializers.ValidationError({"subject_group_uuid": "Subject group does not belong to this school."})

        # Check if student_class belongs to subject_group (when subject_group is set)
        if subject_group and student_class:
            if not subject_group.classes.filter(pk=student_class.pk).exists():
                raise serializers.ValidationError({
                    "subject_group_uuid": f"The class '{student_class.class_name} {student_class.section}' does not belong to the subject group '{subject_group.name}'."
                })

        if student_class and roll_number:
            query = StudentAcademicdetails.objects.filter(
                student_class=student_class,
                roll_number=roll_number
            )
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise serializers.ValidationError({
                    "roll_number": f"Roll number {roll_number} already assigned in this class."
                })

        return data


class StudentParentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', read_only=True)
    parent_user_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Users.objects.filter(role=UserRoles.PARENT),
        source='user',
        required=False,
        allow_null=True
    )
    username = serializers.CharField(source='user.username', read_only=True)
    # Fields for parent user creation
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = StudentParentDetails
        fields = [
            'id', 'parent_user_uuid', 'username', 'father_name', 'father_occupation', 
            'father_phone', 'father_email', 'mother_name', 'mother_occupation', 
            'mother_phone', 'mother_email', 'gurdian_name', 'gurdian_releation', 
            'gurdian_phone', 'gurdian_email', 'password', 'confirm_password'
        ]

    def validate(self, data):
        parent_user = data.get('user')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not parent_user:
            # Updating current or creating new parent (no parent_user_uuid provided)
            # If creating (no instance or no instance.user), require password
            if not self.instance or not self.instance.user:
                 if not password or not confirm_password:
                     raise serializers.ValidationError({"password": "Password and confirm password are required for new parent."})
            
            # If password provided, validate it
            if password or confirm_password:
                if password != confirm_password:
                    raise serializers.ValidationError({"password": "Passwords do not match."})
                try:
                    validate_password(password)
                except Exception as e:
                    raise serializers.ValidationError({"password": list(e.messages)})
        else:
            # parent_user_uuid provided
            is_same_user = self.instance and self.instance.user == parent_user

            # If instance is None (e.g., nested serializer update), check if already linked
            if not is_same_user and not self.instance:
                view = self.context.get('view')
                student_uuid = view.kwargs.get('uuid') if view else None
                if student_uuid:
                    is_same_user = StudentParentDetails.objects.filter(
                        student__uuid=student_uuid,
                        user=parent_user
                    ).exists()

            if not is_same_user:
                # Linking a NEW existing user
                if not password:
                    raise serializers.ValidationError({"password": "Parent password is required to link an existing parent account."})
                if not parent_user.check_password(password):
                    raise serializers.ValidationError({"password": "Invalid parent password. Verification failed."})
            
            # Allow password reset if password is provided
            if password or confirm_password:
                if password != confirm_password:
                    raise serializers.ValidationError({"password": "Passwords do not match."})
                try:
                    validate_password(password)
                except Exception as e:
                    raise serializers.ValidationError({"password": list(e.messages)})

            school = self.context.get('school')
            if parent_user.school != school:
                raise serializers.ValidationError({"parent_user_uuid": "This parent belongs to another school."})

        return data

class StudentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', required=False, allow_null=True, allow_blank=True)
    phone_number = serializers.CharField(source='user.phone_number', required=False, allow_null=True, allow_blank=True)
    profile_picture = serializers.ImageField(source='user.profile_picture', required=False, allow_null=True)
    aadhaar_number = serializers.CharField(source='user.aadhaar_number', required=False, allow_blank=True)
    nationality = CountryField(source='user.nationality', required=False, allow_blank=True)
    date_of_birth = serializers.DateField(source='user.date_of_birth', required=False, allow_null=True)
    gender = serializers.ChoiceField(source='user.gender', choices=UserGender.choices, required=False, allow_blank=True)
    blood_group = serializers.CharField(source='user.blood_group', required=False, allow_blank=True)

    # Student specific fields
    religion = serializers.CharField(required=False, allow_blank=True)
    caste_category = serializers.ChoiceField(choices=CasteCategory.choices, required=False, allow_blank=True)
    mother_tongue = serializers.CharField(required=False, allow_blank=True)
    identification_mark_1 = serializers.CharField(required=False, allow_blank=True)
    identification_mark_2 = serializers.CharField(required=False, allow_blank=True)

    # Nested objects
    address = TeacherAddressSerializer(required=False)
    admission_details = StudentAdmissionSerializer(required=False)
    academic_details = StudentAcademicSerializer(required=False)
    parent_details = StudentParentSerializer(required=False)
    
    # Credentials for Student
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    # Read only
    uuid = serializers.UUIDField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Students
        fields = [
            'uuid', 'username', 'first_name', 'last_name', 'email', 'phone_number',
            'profile_picture', 'aadhaar_number', 'nationality', 'date_of_birth',
            'gender', 'blood_group', 'religion', 'caste_category', 'mother_tongue',
            'identification_mark_1', 'identification_mark_2', 'address',
            'admission_details', 'academic_details', 'parent_details',
            'password', 'confirm_password'
        ]

    def get_fields(self):
        fields = super().get_fields()
        if self.instance and isinstance(self.instance, Students):
            if 'address' in fields:
                fields['address'].instance = self.instance.user.user_address.first() if self.instance.user else None
            if 'admission_details' in fields:
                fields['admission_details'].instance = self.instance.student_admission_details.first()
            if 'academic_details' in fields:
                fields['academic_details'].instance = self.instance.student_academic_details.first()
            if 'parent_details' in fields:
                fields['parent_details'].instance = self.instance.student_parent_details.first()
        return fields

    def validate_aadhaar_number(self, value):
        if value and not re.match(r'^\d{12}$', value):
            raise serializers.ValidationError("Aadhaar number must be 12 digits.")
        return value

    def validate(self, data):
        user_data = data.get('user', {})
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if not self.instance:
            if not password or not confirm_password:
                raise serializers.ValidationError({"password": "Password and confirm password are required for new student."})
        
        if password or confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError({"password": "Passwords do not match."})
            try:
                validate_password(password)
            except Exception as e:
                raise serializers.ValidationError({"password": list(e.messages)})

        dob = user_data.get('date_of_birth')
        if dob and dob > datetime.date.today():
            raise serializers.ValidationError({"date_of_birth": "Date of birth cannot be in the future."})

        email = user_data.get('email')
        if email:
            query = Users.objects.filter(email=email)
            if self.instance:
                query = query.exclude(id=self.instance.user.id)
            if query.exists():
                raise serializers.ValidationError({"email": "User with this email already exists."})

        return data

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        address_data = validated_data.pop('address', None)
        admission_data = validated_data.pop('admission_details', None)
        academic_data = validated_data.pop('academic_details', None)
        parent_data = validated_data.pop('parent_details', None)
        password = validated_data.pop('password')
        validated_data.pop('confirm_password', None)
        
        school = self.context.get('school')
        
        # Student User
        username = generate_user_code(school, UserRoles.STUDENT)
        user = Users.objects.create(
            username=username,
            role=UserRoles.STUDENT,
            school=school,
            **user_data
        )
        user.set_password(password)
        user.save()
        
        # Student Profile
        student = Students.objects.create(
            user=user,
            school=school,
            **validated_data
        )
        
        # Address
        if address_data:
            AddressBook.objects.create(
                user=user,
                address_type=AddressType.USER,
                **address_data
            )
            
        # Admission Details
        if admission_data:
            StudentsAdmissionDetails.objects.create(student=student, **admission_data)
            
        # Academic Details
        if academic_data:
            StudentAcademicdetails.objects.create(student=student, **academic_data)
            
        # Parent Details
        if parent_data:
            parent_user = parent_data.pop('user', None)
            par_password = parent_data.pop('password', None)
            parent_data.pop('confirm_password', None)
            
            if not parent_user:
                # Create new parent user
                p_username = generate_user_code(school, UserRoles.PARENT)
                parent_user = Users.objects.create(
                    username=p_username,
                    role=UserRoles.PARENT,
                    school=school,
                )
                parent_user.set_password(par_password)
                parent_user.save()
            
            # Create StudentParentDetails link
            StudentParentDetails.objects.create(
                student=student,
                user=parent_user,
                **parent_data
            )
            
        return student

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        address_data = validated_data.pop('address', None)
        admission_data = validated_data.pop('admission_details', None)
        academic_data = validated_data.pop('academic_details', None)
        parent_data = validated_data.pop('parent_details', None)
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        school = self.context.get('school')
        
        # Update User
        user = instance.user
        if password:
            user.set_password(password)
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        # Update Student Profile
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
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
                
        # Update Admission Details
        if admission_data is not None:
            admission_obj = instance.student_admission_details.first()
            if admission_obj:
                for attr, value in admission_data.items():
                    setattr(admission_obj, attr, value)
                admission_obj.save()
            else:
                StudentsAdmissionDetails.objects.create(student=instance, **admission_data)

        # Update Academic Details
        if academic_data is not None:
            academic_obj = instance.student_academic_details.first()
            if academic_obj:
                for attr, value in academic_data.items():
                    setattr(academic_obj, attr, value)
                academic_obj.save()
            else:
                StudentAcademicdetails.objects.create(student=instance, **academic_data)

        # Update Parent Details
        if parent_data is not None:
            parent_user = parent_data.pop('user', None)
            par_password = parent_data.pop('password', None)
            parent_data.pop('confirm_password', None)
            
            parent_obj = instance.student_parent_details.first()
            
            if not parent_user:
                if parent_obj and parent_obj.user:
                    parent_user = parent_obj.user
                else:
                    # Create new parent user
                    p_username = generate_user_code(school, UserRoles.PARENT)
                    parent_user = Users.objects.create(
                        username=p_username,
                        role=UserRoles.PARENT,
                        school=school,
                        first_name=parent_data.get('father_name', 'Parent'),
                        email=parent_data.get('father_email'),
                        phone_number=parent_data.get('father_phone')
                    )
            
            if parent_user and par_password:
                parent_user.set_password(par_password)
                parent_user.save()
            
            if parent_obj:
                for attr, value in parent_data.items():
                    setattr(parent_obj, attr, value)
                parent_obj.user = parent_user
                parent_obj.save()
            else:
                StudentParentDetails.objects.create(
                    student=instance,
                    user=parent_user,
                    **parent_data
                )

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Manually handle single object serialization for FK relationships
        address = instance.user.user_address.first() if instance.user else None
        representation['address'] = TeacherAddressSerializer(address).data if address else None
        
        admission = instance.student_admission_details.first()
        representation['admission_details'] = StudentAdmissionSerializer(admission).data if admission else None
            
        academic = instance.student_academic_details.first()
        representation['academic_details'] = StudentAcademicSerializer(academic).data if academic else None
            
        parent = instance.student_parent_details.first()
        representation['parent_details'] = StudentParentSerializer(parent).data if parent else None
            
        return representation
