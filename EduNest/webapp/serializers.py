import datetime
import re
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
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
    ExamType,
    Exam,
    ExamClass,
    ExamSchedule,
    ClassSubjects,
    SubjectGroup,
    Students,
    StudentsAdmissionDetails,
    StudentParentDetails,
    StudentAcademicdetails,
    AttendanceSession,
    StudentAttendance,
    Period,
    ClassTimetable,
    ClassTimetableEntry,
)
from common.choices import (
    UserRoles, 
    UserGender, 
    MaritalStatus, 
    AddressType,
    SubjectType,
    CasteCategory,
    Attendance,
    ClassTimeTableDays,
    ExamSessions,
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
        read_only_fields = ['uuid', 'academic_year']

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
        academic_year = school.academic_year if school else None
        
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
            academic_year=school.academic_year,
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
        school = self.context.get('school')
        validated_data['academic_year'] = school.academic_year if school else instance.academic_year

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
    already_assigned_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = SchoolTeacher
        fields = ['uuid', 'full_name', 'already_assigned_count']


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

class TeacherUUIDField(serializers.Field):
    def __init__(self, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if data in (None, ''):
            return []

        if not isinstance(data, (list, tuple)):
            data = [data]

        teachers = []
        seen = set()

        for teacher_uuid in data:
            try:
                teacher = self.queryset.get(uuid=teacher_uuid)
            except self.queryset.model.DoesNotExist:
                raise serializers.ValidationError({
                    'teacher_uuid': f'Teacher with UUID {teacher_uuid} does not exist.'
                })

            if str(teacher.uuid) not in seen:
                seen.add(str(teacher.uuid))
                teachers.append(teacher)

        return teachers

    def to_representation(self, value):
        if value is None:
            return []

        if hasattr(value, 'all'):
            return [str(item.uuid) for item in value.all() if item]

        if isinstance(value, (list, tuple, set)):
            return [str(item.uuid) for item in value if item]

        return [str(getattr(value, 'uuid', value))]

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
    teacher_uuid = TeacherUUIDField(
        queryset=SchoolTeacher.objects.all(),
        source='teacher',
        required=False
    )
    
    subject_details = SubjectListSerializer(source='subject', read_only=True)
    class_details = ClassListSerializer(source='subject_class', read_only=True)
    teacher_details = TeacherMiniSerializer(source='teacher', many=True, read_only=True)
    
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
        teachers = data.get('teacher') or []

        # School validations
        if subject and subject.school != school:
            raise serializers.ValidationError({"subject_uuid": "Subject does not belong to this school."})
        
        if subject_class and subject_class.school != school:
            raise serializers.ValidationError({"class_uuid": "Class does not belong to this school."})
            
        for teacher in teachers:
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
        teachers = validated_data.pop('teacher', [])
        instance = super().create(validated_data)
        if teachers:
            instance.teacher.add(*teachers)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        teachers = validated_data.pop('teacher', None)
        instance = super().update(instance, validated_data)
        if teachers is not None:
            instance.teacher.set(teachers)
        return instance


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


# Supportive Serializers for Student CRUD APIs
class SchoolClassSupportSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = SchoolClass
        fields = ['uuid', 'name']

    @extend_schema_field(serializers.CharField)
    def get_name(self, obj):
        return f"{obj.class_name} - {obj.section}" if obj.section else obj.class_name


class StudentSupportSerializer(serializers.ModelSerializer):
    user_code = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)
    roll_number = serializers.CharField(source='academic_details.roll_number', read_only=True)
    register_number = serializers.CharField(source='academic_details.register_number', read_only=True)
    parent_user_code = serializers.CharField(source='parent_details.user.username', read_only=True)
    father_name = serializers.CharField(source='parent_details.father_name', read_only=True)
    father_phone = serializers.CharField(source='parent_details.father_phone', read_only=True)
    mother_name = serializers.CharField(source='parent_details.mother_name', read_only=True)
    mother_phone = serializers.CharField(source='parent_details.mother_phone', read_only=True)
    guardian_name = serializers.CharField(source='parent_details.gurdian_name', read_only=True)
    guardian_phone = serializers.CharField(source='parent_details.gurdian_phone', read_only=True)
    status = serializers.CharField(source='admission_details.student_status', read_only=True)

    class Meta:
        model = Students
        fields = [
            'uuid', 'user_code', 'full_name', 'profile_picture', 'roll_number', 
            'register_number', 'parent_user_code', 'father_name', 'father_phone', 
            'mother_name', 'mother_phone', 'guardian_name', 'guardian_phone', 'status'
        ]

    def to_representation(self, instance):
        instance.academic_details = instance.student_academic_details.first()
        instance.parent_details = instance.student_parent_details.first()
        instance.admission_details = instance.student_admission_details.first()
        
        return super().to_representation(instance)


class SubjectSupportSerializer(serializers.ModelSerializer):
    subject_uuid = serializers.UUIDField(source='uuid', read_only=True)
    subject_name = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Subjects
        fields = ['subject_uuid', 'subject_name']


class ClassSubjectSupportSerializer(serializers.ModelSerializer):
    class_subject_uuid = serializers.UUIDField(source='uuid', read_only=True)
    subject_uuid = serializers.UUIDField(source='subject.uuid', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = ClassSubjects
        fields = ['class_subject_uuid', 'subject_uuid', 'subject_name', 'is_optional']


class StudentAttendanceListSerializer(serializers.ListSerializer):
    @transaction.atomic
    def create(self, validated_data):
        school = self.context.get('school')
        class_obj = self.context.get('class_obj')
        user = self.context.get('request').user
        
        # Validate that all records have the same date
        dates = {item['date'] for item in validated_data}
        if len(dates) > 1:
            raise serializers.ValidationError("All bulk attendance records must be for the same date.")
        date = list(dates)[0]
        
        # Validate no duplicate student_uuid in the request itself
        student_ids = [item['student'].id for item in validated_data]
        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError("Duplicate student entries found in the request.")

        # Get or create the AttendanceSession
        session, created = AttendanceSession.objects.get_or_create(
            class_obj=class_obj,
            date=date,
            defaults={
                'created_by': user,
                'total_students': 0,
                'present_count': 0,
                'absent_count': 0,
                'leave_count': 0
            }
        )
        
        if created:
            total_students = Students.objects.filter(
                school=school,
                student_academic_details__student_class=class_obj,
                user__is_deleted=False
            ).count()
            session.total_students = total_students
            session.save()

        # Check database duplicates for all requested students
        existing_students = StudentAttendance.objects.filter(
            session=session,
            student__id__in=student_ids
        ).values_list('student__uuid', flat=True)
        if existing_students:
            raise serializers.ValidationError("Attendace already marked")

        # Prepare StudentAttendance objects
        attendance_objects = []
        for item in validated_data:
            attendance_objects.append(
                StudentAttendance(
                    session=session,
                    student=item['student'],
                    status=item['status'],
                    note=item.get('note', '')
                )
            )
            
        created_records = StudentAttendance.objects.bulk_create(attendance_objects)
        
        present_count = StudentAttendance.objects.filter(session=session, status=Attendance.P).count()
        absent_count = StudentAttendance.objects.filter(session=session, status=Attendance.A).count()
        leave_count = StudentAttendance.objects.filter(session=session, status=Attendance.L).count()
        
        session.present_count = present_count
        session.absent_count = absent_count
        session.leave_count = leave_count
        session.save()
        
        return created_records


class StudentAttendanceSerializer(serializers.ModelSerializer):
    student_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Students.objects.all(),
        source='student',
        error_messages={
            'does_not_exist': 'Student with this UUID does not exist.',
            'invalid': 'Invalid UUID format.'
        }
    )
    date = serializers.DateField(required=True, write_only=True)
    
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_code = serializers.CharField(source='student.user.username', read_only=True)
    roll_number = serializers.SerializerMethodField(read_only=True)
    attendance_date = serializers.DateField(source='session.date', read_only=True)

    class Meta:
        model = StudentAttendance
        list_serializer_class = StudentAttendanceListSerializer
        fields = [
            'id', 'uuid', 'student_uuid', 'date', 'status', 'note',
            'student_name', 'student_code', 'roll_number', 'attendance_date'
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_roll_number(self, obj):
        if obj.student:
            academic = obj.student.student_academic_details.first()
            return academic.roll_number if academic else None
        return None

    def validate_status(self, value):
        if not value:
            raise serializers.ValidationError("Status is required.")
        if value not in Attendance.values:
            raise serializers.ValidationError("Invalid status value.")
        return value

    def validate_note(self, value):
        if value is not None:
            if value.strip() == "" and value != "":
                raise serializers.ValidationError("Note cannot contain only whitespace.")
        return value

    def validate_date(self, value):
        if not value:
            raise serializers.ValidationError("Date is required.")
        if value > datetime.date.today():
            raise serializers.ValidationError("Attendance cannot be marked for future dates.")
        return value

    def validate(self, data):
        school = self.context.get('school')
        class_obj = self.context.get('class_obj')
        user = self.context.get('request').user
        
        student = data.get('student')
        date = data.get('date')
        
        if self.instance:
            created_at = self.instance.created_at
            now = timezone.now()
            time_difference = now - created_at
            
            if user.role == UserRoles.CLASS_TEACHER:
                if time_difference > datetime.timedelta(hours=10):
                    raise serializers.ValidationError("Edit is not allowed after 10 hours of creation.")
            elif user.role == UserRoles.SCHOOL_ADMIN:
                if time_difference > datetime.timedelta(days=2):
                    raise serializers.ValidationError("Edit is not allowed after 2 days of creation.")
            
            student = self.instance.student
            date = self.instance.session.date

        if student:
            if student.school != school:
                raise serializers.ValidationError({"student_uuid": "Student does not belong to this school."})
            
            academic = student.student_academic_details.filter(student_class=class_obj).first()
            if not academic:
                raise serializers.ValidationError({"student_uuid": "Student is not assigned to this class."})

        if date and student:
            query = StudentAttendance.objects.filter(
                session__class_obj__school=school,
                session__date=date,
                student=student
            )
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError("Attendace already marked")

        return data

    @transaction.atomic
    def create(self, validated_data):
        school = self.context.get('school')
        class_obj = self.context.get('class_obj')
        user = self.context.get('request').user
        
        date = validated_data['date']
        student = validated_data['student']
        status = validated_data['status']
        note = validated_data.get('note', '')

        session, created = AttendanceSession.objects.get_or_create(
            class_obj=class_obj,
            date=date,
            defaults={
                'created_by': user,
                'total_students': 0,
                'present_count': 0,
                'absent_count': 0,
                'leave_count': 0
            }
        )
        
        if created:
            total_students = Students.objects.filter(
                school=school,
                student_academic_details__student_class=class_obj,
                user__is_deleted=False
            ).count()
            session.total_students = total_students
            session.save()
            
        if StudentAttendance.objects.filter(session=session, student=student).exists():
            raise serializers.ValidationError("Attendace already marked")
            
        attendance_record = StudentAttendance.objects.create(
            session=session,
            student=student,
            status=status,
            note=note
        )
        
        present_count = StudentAttendance.objects.filter(session=session, status=Attendance.P).count()
        absent_count = StudentAttendance.objects.filter(session=session, status=Attendance.A).count()
        leave_count = StudentAttendance.objects.filter(session=session, status=Attendance.L).count()
        
        session.present_count = present_count
        session.absent_count = absent_count
        session.leave_count = leave_count
        session.save()
        
        return attendance_record

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.note = validated_data.get('note', instance.note)
        instance.save()
        
        session = instance.session
        present_count = StudentAttendance.objects.filter(session=session, status=Attendance.P).count()
        absent_count = StudentAttendance.objects.filter(session=session, status=Attendance.A).count()
        leave_count = StudentAttendance.objects.filter(session=session, status=Attendance.L).count()
        
        session.present_count = present_count
        session.absent_count = absent_count
        session.leave_count = leave_count
        session.save()
        
        return instance


class PeriodSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Period
        fields = [
            'id', 'uuid', 'name', 'start_time', 'end_time',
            'is_break', 'order'
        ]
        read_only_fields = ['id']

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Period name is required.")
        if not value.strip():
            raise serializers.ValidationError("Period name cannot be whitespace only.")
        return value

    def validate_order(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Order cannot be negative.")
        return value

    def validate(self, data):
        school = self.context.get('school')
        class_obj = self.context.get('class_obj')

        name = data.get('name', self.instance.name if self.instance else None)
        start_time = data.get('start_time', self.instance.start_time if self.instance else None)
        end_time = data.get('end_time', self.instance.end_time if self.instance else None)
        
        # Basic validation for existence of name, start_time, end_time
        if not name:
            raise serializers.ValidationError({"name": "Period name is required."})
        if not start_time:
            raise serializers.ValidationError({"start_time": "Start time is required."})
        if not end_time:
            raise serializers.ValidationError({"end_time": "End time is required."})

        # Validate start_time and end_time logic
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        
        # Duplicate validation within the same school and class
        query = Period.objects.filter(
            school=school,
            class_obj=class_obj,
            name__iexact=name
        )
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
            
        if query.exists():
            raise serializers.ValidationError(
                f"Period {name} already assigned to this Class {class_obj.class_name} {class_obj.section}."
            )
        
        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data['school'] = self.context.get('school')
        validated_data['class_obj'] = self.context.get('class_obj')
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        # The school and class_obj cannot be changed after creation, so they are not in validated_data
        return super().update(instance, validated_data)


# DEPENDENCIES - CLASS TIMETABLE ENTRIES
def _times_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a


def _entry_value(entry, key):
    if isinstance(entry, dict):
        return entry.get(key)
    return getattr(entry, key, None)


def _entry_conflicts(entry_a, entry_b):
    teacher_a = _entry_value(entry_a, 'teacher')
    teacher_b = _entry_value(entry_b, 'teacher')
    day_a = _entry_value(entry_a, 'day')
    day_b = _entry_value(entry_b, 'day')
    period_a = _entry_value(entry_a, 'period')
    period_b = _entry_value(entry_b, 'period')

    if not teacher_a or not teacher_b or not day_a or not day_b or not period_a or not period_b:
        return False

    if teacher_a.id != teacher_b.id or day_a != day_b:
        return False

    if not period_a.start_time or not period_a.end_time or not period_b.start_time or not period_b.end_time:
        return False

    return _times_overlap(period_a.start_time, period_a.end_time, period_b.start_time, period_b.end_time)


class ClassTimetableEntryListSerializer(serializers.ListSerializer):
    def _get_timetable_instance(self):
        timetable = self.context.get('timetable')
        if isinstance(timetable, ClassTimetable):
            return timetable

        parent = getattr(self, 'parent', None)
        while parent is not None:
            parent_instance = getattr(parent, 'instance', None)
            if isinstance(parent_instance, ClassTimetable):
                return parent_instance
            parent = getattr(parent, 'parent', None)

        return None

    def _get_existing_instances(self):
        if isinstance(self.instance, (list, tuple)):
            return list(self.instance)

        if self.instance is None:
            timetable = self._get_timetable_instance()
            if timetable is not None:
                return list(timetable.time_table.filter(is_active=True))
            return []

        if hasattr(self.instance, "all"):
            return list(self.instance.all())

        return [self.instance]

    def validate(self, attrs):
        school = self.context.get('school')
        class_obj = self.context.get('class_obj')

        if not school or not class_obj:
            raise serializers.ValidationError('School and class are required for class timetable entries.')

        existing_instances = {
            str(entry.uuid): entry for entry in self._get_existing_instances()
        }

        request_uuids = {str(item.get('uuid')) for item in attrs if item.get('uuid')}

        existing_entries = list(
            ClassTimetableEntry.objects.filter(
                timetable__school=school,
                timetable__class_obj__academic_year=class_obj.academic_year,
                timetable__is_active=True,
            ).exclude(uuid__in=request_uuids).select_related('timetable', 'timetable__class_obj', 'teacher', 'teacher__user', 'period')
        )
        class_entries = list(
            ClassTimetableEntry.objects.filter(
                timetable__school=school,
                timetable__class_obj=class_obj,
                timetable__is_active=True,
                is_active=True,
            ).exclude(uuid__in=request_uuids).select_related('timetable', 'timetable__class_obj', 'teacher', 'teacher__user', 'period')
        )

        request_slots = set()
        merged_entries = []

        for item in attrs:
            entry_uuid = item.get('uuid')
            existing_instance = existing_instances.get(str(entry_uuid)) if entry_uuid else None

            if entry_uuid and not existing_instance:
                if self._get_timetable_instance() is None:
                    raise serializers.ValidationError({'id': 'UUID cannot be provided while creating class timetable entries.'})
                raise serializers.ValidationError({'id': f'Entry {entry_uuid} does not belong to this class timetable.'})

            merged_entry = {
                'uuid': str(existing_instance.uuid) if existing_instance else (str(entry_uuid) if entry_uuid else None),
                'day': item.get('day', _entry_value(existing_instance, 'day')),
                'period': item.get('period', _entry_value(existing_instance, 'period')),
                'subject': item.get('subject', _entry_value(existing_instance, 'subject')),
                'teacher': item.get('teacher', _entry_value(existing_instance, 'teacher')),
            }

            period = merged_entry['period']
            if merged_entry['day'] and period:
                slot_key = (merged_entry['day'], period.id)
                if slot_key in request_slots:
                    raise serializers.ValidationError({
                        'entries': f'Duplicate timetable entry for {merged_entry["day"]} and {period.name} in the request.'
                    })
                request_slots.add(slot_key)

                for existing in class_entries:
                    if merged_entry['uuid'] and str(existing.uuid) == merged_entry['uuid']:
                        continue
                    if existing.day == merged_entry['day'] and existing.period_id == period.id:
                        raise serializers.ValidationError({
                            'entries': f'Class timetable entry for {merged_entry["day"]} and {period.name} already exists in this class.'
                        })

            if merged_entry['teacher'] and period and not period.is_break:
                conflict = None
                for existing in existing_entries:
                    if merged_entry['uuid'] and str(existing.uuid) == merged_entry['uuid']:
                        continue
                    if _entry_conflicts(merged_entry, existing):
                        conflict = existing
                        break

                if conflict is None:
                    for previous in merged_entries:
                        if merged_entry['uuid'] and previous['uuid'] == merged_entry['uuid']:
                            continue
                        if _entry_conflicts(merged_entry, previous):
                            conflict = previous
                            break

                if conflict:
                    conflict_class_name = f"{conflict.timetable.class_obj.class_name}{conflict.timetable.class_obj.section}" if hasattr(conflict, 'timetable') else f"{class_obj.class_name}{class_obj.section}"
                    raise serializers.ValidationError({
                        'entries': (
                            f"Teacher {merged_entry['teacher'].user.get_full_name()} already assigned to the Class "
                            f"{conflict_class_name} at the same duration"
                        )
                    })

            merged_entries.append(merged_entry)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        timetable = self.context.get('timetable')
        if not timetable:
            raise serializers.ValidationError('Class timetable context is required.')

        created_entries = []
        for item in validated_data:
            created_entries.append(ClassTimetableEntry.objects.create(timetable=timetable, **item))
        return created_entries

    @transaction.atomic
    def update(self, instance, validated_data):
        timetable = self.context.get('timetable')
        if not timetable:
            raise serializers.ValidationError('Class timetable context is required.')

        existing_entries = {str(entry.uuid): entry for entry in instance}
        updated_entries = []

        for item in validated_data:
            entry_uuid = item.pop('uuid', None)
            if entry_uuid:
                entry = existing_entries.get(str(entry_uuid))
                if not entry:
                    raise serializers.ValidationError({
                        'id': f'Entry {entry_uuid} does not belong to this class timetable.'
                    })

                for attr, value in item.items():
                    setattr(entry, attr, value)
                entry.save()
                updated_entries.append(entry)
            else:
                updated_entries.append(ClassTimetableEntry.objects.create(timetable=timetable, **item))

        return updated_entries


class ClassTimetableEntrySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', required=False)
    day = serializers.ChoiceField(choices=ClassTimeTableDays.choices)
    period_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Period.objects.all(),
        source='period'
    )
    subject_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=ClassSubjects.objects.all(),
        source='subject',
        required=False,
        allow_null=True
    )
    teacher_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=SchoolTeacher.objects.all(),
        source='teacher',
        required=False,
        allow_null=True
    )

    period_details = PeriodSerializer(source='period', read_only=True)
    subject_details = ClassSubjectSerializer(source='subject', read_only=True)
    teacher_details = TeacherMiniSerializer(source='teacher', read_only=True)

    class Meta:
        model = ClassTimetableEntry
        list_serializer_class = ClassTimetableEntryListSerializer
        fields = [
            'id', 'day', 'period_uuid', 'subject_uuid', 'teacher_uuid',
            'period_details', 'subject_details', 'teacher_details',
        ]

    def _get_timetable_instance(self):
        timetable = self.context.get('timetable')
        if isinstance(timetable, ClassTimetable):
            return timetable

        parent = getattr(self, 'parent', None)
        while parent is not None:
            parent_instance = getattr(parent, 'instance', None)
            if isinstance(parent_instance, ClassTimetable):
                return parent_instance
            parent = getattr(parent, 'parent', None)

        return None

    def _get_current_instance(self, data):
        if isinstance(self.instance, ClassTimetableEntry):
            return self.instance

        timetable = self._get_timetable_instance()
        entry_uuid = data.get('uuid')

        if timetable and entry_uuid:
            return timetable.time_table.filter(uuid=entry_uuid, is_active=True).first()

        return None

    def validate(self, data):
        school = self.context.get('school')
        class_obj = self.context.get('class_obj')

        current_instance = self._get_current_instance(data)
        entry_uuid = data.get('uuid')
        timetable = self._get_timetable_instance()

        if entry_uuid and timetable and current_instance is None:
            raise serializers.ValidationError({
                'id': f'Entry {entry_uuid} does not belong to this class timetable.'
            })

        period = data.get('period', _entry_value(current_instance, 'period'))
        subject = data.get('subject', _entry_value(current_instance, 'subject'))
        teacher = data.get('teacher', _entry_value(current_instance, 'teacher'))
        day = data.get('day', _entry_value(current_instance, 'day'))

        errors = {}

        if not school or not class_obj:
            raise serializers.ValidationError("School and class are required for timetable entries.")

        if period:
            if period.school != school:
                errors['period_uuid'] = 'Period does not belong to this school.'
            if period.class_obj != class_obj:
                errors['period_uuid'] = 'Period does not belong to this class.'
            if period.start_time is None or period.end_time is None:
                errors['period_uuid'] = 'Period start time and end time are required.'
            elif period.end_time <= period.start_time:
                errors['period_uuid'] = 'Period end time must be after start time.'

        if subject:
            if subject.subject_class is None or subject.subject_class.school != school:
                errors['subject_uuid'] = 'Subject does not belong to this school.'
            elif subject.subject_class != class_obj:
                errors['subject_uuid'] = 'Subject does not belong to this class.'

        if teacher:
            if teacher.school != school:
                errors['teacher_uuid'] = 'Teacher does not belong to this school.'
            elif teacher.user and teacher.user.is_deleted:
                errors['teacher_uuid'] = (
                    f"The teacher '{teacher.user.get_full_name()}' cannot be assigned because their account has been deactivated or deleted."
                )

        if period and not period.is_break:
            if not subject:
                errors['subject_uuid'] = 'Subject is required for non-break periods.'
            if not teacher:
                errors['teacher_uuid'] = 'Teacher is required for non-break periods.'

        if period and day:
            class_slot_query = ClassTimetableEntry.objects.filter(
                timetable__school=school,
                timetable__class_obj=class_obj,
                timetable__is_active=True,
                is_active=True,
                day=day,
                period=period,
            )
            if current_instance:
                class_slot_query = class_slot_query.exclude(uuid=current_instance.uuid)
            if class_slot_query.exists():
                errors['entries'] = f'Class timetable entry for {day} and {period.name} already exists in this class.'

        if teacher and period and day and not period.is_break:
            conflict_entries = ClassTimetableEntry.objects.filter(
                timetable__school=school,
                timetable__class_obj__academic_year=class_obj.academic_year,
                timetable__is_active=True,
            ).select_related('timetable', 'timetable__class_obj', 'teacher', 'teacher__user', 'period')

            if current_instance:
                conflict_entries = conflict_entries.exclude(uuid=current_instance.uuid)

            conflict = None
            for existing in conflict_entries:
                if _entry_conflicts(
                    {'teacher': teacher, 'day': day, 'period': period},
                    existing,
                ):
                    conflict = existing
                    break

            if conflict:
                errors['teacher_uuid'] = (
                    f"Teacher {teacher.user.get_full_name()} already assigned to the Class "
                    f"{conflict.timetable.class_obj.class_name}{conflict.timetable.class_obj.section} at the same duration"
                )

        if errors:
            raise serializers.ValidationError(errors)

        return data


class ClassTimetableSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', read_only=True)
    class_details = ClassListSerializer(source='class_obj', read_only=True)
    entries = ClassTimetableEntrySerializer(many=True, source='time_table', required=False)
    is_published = serializers.BooleanField(required=False)
    is_save_as_draft = serializers.BooleanField(required=False)

    class Meta:
        model = ClassTimetable
        fields = [
            'id', 'class_details', 'is_published', 'is_save_as_draft',
            'is_active', 'entries',
        ]
        read_only_fields = ['id', 'is_active']

    def _sync_class_subject_teacher(self, subject, teacher):
        if not subject or not teacher:
            return

        subject.teacher.add(teacher)

    def _sync_timetable_class_subject_teachers(self, timetable):
        subjects = {}
        entries = timetable.time_table.select_related('subject', 'teacher').filter(is_active=True)

        for entry in entries:
            if not entry.subject or not entry.teacher:
                continue
            subjects.setdefault(entry.subject_id, {"subject": entry.subject, "teachers": set()})
            subjects[entry.subject_id]["teachers"].add(entry.teacher)

        for item in subjects.values():
            item["subject"].teacher.set(list(item["teachers"]))

    def validate(self, data):
        school = self.context.get('school')
        class_obj = self.context.get('class_obj')
        entries = data.get('time_table')

        if not school or not class_obj:
            raise serializers.ValidationError('School and class are required for class timetables.')

        published_provided = 'is_published' in data
        draft_provided = 'is_save_as_draft' in data
        is_published = data.get('is_published', self.instance.is_published if self.instance else None)
        is_save_as_draft = data.get('is_save_as_draft', self.instance.is_save_as_draft if self.instance else None)

        if self.instance is None and is_published is None and is_save_as_draft is None:
            raise serializers.ValidationError({
                'is_published': 'Either is_published or is_save_as_draft is required.'
            })

        if published_provided and draft_provided:
            if is_published == is_save_as_draft:
                raise serializers.ValidationError({
                    'is_published': 'is_published and is_save_as_draft cannot be the same value.'
                })
        elif published_provided:
            is_save_as_draft = not is_published
        elif draft_provided:
            is_published = not is_save_as_draft

        data['is_published'] = is_published
        data['is_save_as_draft'] = is_save_as_draft

        if self.instance is None:
            exists = ClassTimetable.objects.filter(
                school=school,
                class_obj=class_obj,
                is_active=True,
            ).exists()
            if exists:
                raise serializers.ValidationError({
                    'class_uuid': 'Class timetable already exists for this class.'
                })

        if entries is not None:
            seen_slots = set()
            timetable_id = self.instance.id if self.instance else None
            academic_year = class_obj.academic_year

            for entry in entries:
                day = entry.get('day')
                period = entry.get('period')
                teacher = entry.get('teacher')
                subject = entry.get('subject')
                entry_uuid = entry.get('uuid')

                slot_key = (day, period.id)
                if slot_key in seen_slots:
                    raise serializers.ValidationError({
                        'entries': f'Duplicate timetable entry for {day} and {period.name} in the request.'
                    })
                seen_slots.add(slot_key)

                if teacher and period and not period.is_break:
                    conflict_query = ClassTimetableEntry.objects.filter(
                        teacher=teacher,
                        day=day,
                        timetable__school=school,
                        timetable__class_obj__academic_year=academic_year,
                        timetable__is_active=True,
                        period__start_time__lt=period.end_time,
                        period__end_time__gt=period.start_time,
                    ).select_related('timetable__class_obj', 'teacher__user', 'period')

                    if timetable_id:
                        conflict_query = conflict_query.exclude(timetable_id=timetable_id)
                    if entry_uuid:
                        conflict_query = conflict_query.exclude(uuid=entry_uuid)

                    conflict = conflict_query.first()
                    if conflict:
                        raise serializers.ValidationError({
                            'entries': (
                                f"Teacher {teacher.user.get_full_name()} already assigned to the Class "
                                f"{conflict.timetable.class_obj.class_name}{conflict.timetable.class_obj.section} at the same duration"
                            )
                        })

        return data

    @transaction.atomic
    def create(self, validated_data):
        entries = validated_data.pop('time_table', [])
        school = self.context.get('school')
        class_obj = self.context.get('class_obj')

        timetable = ClassTimetable.objects.create(
            school=school,
            class_obj=class_obj,
            **validated_data
        )

        for entry in entries:
            ClassTimetableEntry.objects.create(timetable=timetable, **entry)

        self._sync_timetable_class_subject_teachers(timetable)

        return timetable

    @transaction.atomic
    def update(self, instance, validated_data):
        entries = validated_data.pop('time_table', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if entries is not None:
            existing_entries = {str(entry.uuid): entry for entry in instance.time_table.all()}
            incoming_uuids = set()

            for entry_data in entries:
                entry_uuid = str(entry_data.pop('uuid', '')) if entry_data.get('uuid') else None

                if entry_uuid:
                    if entry_uuid not in existing_entries:
                        raise serializers.ValidationError({
                            'entries': f'Entry {entry_uuid} does not belong to this timetable.'
                        })

                    incoming_uuids.add(entry_uuid)
                    entry_obj = existing_entries[entry_uuid]
                    for attr, value in entry_data.items():
                        setattr(entry_obj, attr, value)
                    entry_obj.save()
                else:
                    created_entry = ClassTimetableEntry.objects.create(timetable=instance, **entry_data)
                    incoming_uuids.add(str(created_entry.uuid))

            ClassTimetableEntry.objects.filter(timetable=instance).exclude(uuid__in=incoming_uuids).delete()

            self._sync_timetable_class_subject_teachers(instance)

        return instance


class ExamTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExamType
        fields = ['uuid', 'name', 'is_active']
        read_only_fields = ['id']

    def validate_name(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Exam type name cannot be whitespace only.")
        return value

    def validate(self, data):
        name = data.get('name', self.instance.name if self.instance else None)

        if not name:
            raise serializers.ValidationError({"name": "Exam type name is required."})

        query = ExamType.objects.filter(name__iexact=name)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError({"name": f"Exam type {name} already exists."})

        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data['school'] = self.context.get('school')
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class ExamClassSerializer(serializers.ModelSerializer):
    class_obj = SchoolClassSupportSerializer(read_only=True)

    class Meta:
        model = ExamClass
        fields = ['uuid', 'class_obj']


class ExamSerializer(serializers.ModelSerializer):
    exam_type = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=ExamType.objects.filter(is_active=True),
        write_only=True
    )
    exam_type_detail = ExamTypeSerializer(source='exam_type', read_only=True)
    start_date = serializers.DateField(input_formats=['%d/%m/%Y', '%Y-%m-%d'])
    end_date = serializers.DateField(input_formats=['%d/%m/%Y', '%Y-%m-%d'])
    classes = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    exam_classes = ExamClassSerializer(many=True, read_only=True)
    exam_class_uuid = serializers.SerializerMethodField(read_only=True)
    save_as_draft = serializers.BooleanField(write_only=True, required=False, default=False)
    publish = serializers.BooleanField(write_only=True, required=False, default=False)
    academic_year = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Exam
        fields = [
            'uuid', 'name', 'academic_year', 'exam_type', 'exam_type_detail',
            'classes', 'exam_classes', 'exam_class_uuid', 'start_date', 'end_date', 'save_as_draft',
            'publish', 'status', 'status_display', 'is_locked', 'created_by',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'academic_year', 'status', 'status_display', 'is_locked', 'created_by', 'created_at', 'updated_at', 'is_active']

    def validate_name(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("Exam name cannot be whitespace only.")
        return value.strip() if value else value

    def validate(self, data):
        school = self.context.get('school')
        if not school:
            return data

        instance = self.instance
        today = timezone.localdate()
        name = data.get('name', instance.name if instance else None)
        exam_type = data.get('exam_type', instance.exam_type if instance else None)
        start_date = data.get('start_date', instance.start_date if instance else None)
        end_date = data.get('end_date', instance.end_date if instance else None)
        classes = data.get('classes', None)
        save_as_draft = data.get('save_as_draft', False)
        publish = data.get('publish', False)

        if instance and instance.is_locked:
            raise serializers.ValidationError({"is_locked": "This exam is locked and cannot be edited."})

        if instance and today >= instance.start_date:
            allowed_fields = {'end_date'}
            incoming_fields = {
                key for key in self.initial_data.keys()
                if key in {'name', 'exam_type', 'classes', 'start_date', 'end_date', 'save_as_draft', 'publish'}
            }
            disallowed_fields = sorted(incoming_fields - allowed_fields)
            if disallowed_fields:
                raise serializers.ValidationError({
                    field: "Only end_date can be modified after the exam has started."
                    for field in disallowed_fields
                })

        if not name:
            raise serializers.ValidationError({"name": "Exam name is required."})

        if not exam_type:
            raise serializers.ValidationError({"exam_type": "Exam type is required."})

        if exam_type.school_id != school.id:
            raise serializers.ValidationError({"exam_type": "Exam type does not belong to this school."})

        if not start_date:
            raise serializers.ValidationError({"start_date": "Start date is required."})

        if not end_date:
            raise serializers.ValidationError({"end_date": "End date is required."})

        if end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date."})

        if classes is not None and not isinstance(classes, list):
            raise serializers.ValidationError({"classes": "Classes must be provided as a list."})

        if save_as_draft and publish:
            raise serializers.ValidationError({"publish": "Choose either save_as_draft or publish, not both."})

        if not instance and not (save_as_draft or publish):
            raise serializers.ValidationError({"publish": "Choose either save_as_draft or publish."})

        query = Exam.objects.filter(
            school=school,
            academic_year=school.academic_year,
            name__iexact=name,
            is_active=True,
        )
        if instance:
            query = query.exclude(pk=instance.pk)

        if query.exists():
            raise serializers.ValidationError({"name": f"Same Exam {name} exists in school."})

        if classes is not None:
            if len(classes) != len(set(classes)):
                raise serializers.ValidationError({"classes": "Duplicate class entries are not allowed."})

            class_map = {
                str(obj.uuid): obj
                for obj in SchoolClass.objects.filter(
                    uuid__in=classes,
                    school=school,
                    academic_year=school.academic_year,
                    is_active=True,
                ).select_related('school')
            }

            class_errors = {}
            for index, class_uuid in enumerate(classes):
                school_class = class_map.get(str(class_uuid))
                if not school_class:
                    class_errors[f'classes[{index}]'] = "Class does not belong to this school or academic year."

            if class_errors:
                raise serializers.ValidationError(class_errors)

        return data

    @transaction.atomic
    def create(self, validated_data):
        school = self.context.get('school')
        user = self.context.get('request').user
        classes = validated_data.pop('classes', [])
        save_as_draft = validated_data.pop('save_as_draft', False)
        publish = validated_data.pop('publish', False)

        validated_data['school'] = school
        validated_data['academic_year'] = school.academic_year
        validated_data['created_by'] = user
        validated_data['status'] = 'DRAFT' if save_as_draft else 'PUBLISHED'
        validated_data['is_locked'] = False

        exam = Exam.objects.create(**validated_data)

        exam_class_objects = [
            ExamClass(exam=exam, class_obj=school_class)
            for school_class in SchoolClass.objects.filter(
                uuid__in=classes,
                school=school,
                academic_year=school.academic_year,
                is_active=True,
            )
        ]
        if exam_class_objects:
            ExamClass.objects.bulk_create(exam_class_objects)

        return exam

    @transaction.atomic
    def update(self, instance, validated_data):
        school = self.context.get('school')
        classes = validated_data.pop('classes', None)
        save_as_draft = validated_data.pop('save_as_draft', False)
        publish = validated_data.pop('publish', False)

        if save_as_draft:
            instance.status = 'DRAFT'
        elif publish:
            instance.status = 'PUBLISHED'

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if 'academic_year' not in validated_data:
            instance.academic_year = school.academic_year

        instance.save()

        if classes is not None:
            current_classes = {
                str(item.class_obj.uuid): item
                for item in instance.exam_classes.select_related('class_obj')
            }
            incoming_uuids = {str(class_uuid) for class_uuid in classes}

            ExamClass.objects.filter(exam=instance).exclude(class_obj__uuid__in=incoming_uuids).delete()

            existing_uuids = set(current_classes.keys())
            new_class_uuids = incoming_uuids - existing_uuids
            if new_class_uuids:
                school_classes = SchoolClass.objects.filter(
                    uuid__in=new_class_uuids,
                    school=school,
                    academic_year=school.academic_year,
                    is_active=True,
                )
                ExamClass.objects.bulk_create([
                    ExamClass(exam=instance, class_obj=school_class)
                    for school_class in school_classes
                ])

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get('exclude_exam_classes'):
            representation.pop('exam_classes', None)
        return representation

    def get_exam_class_uuid(self, instance):
        class_uuid = self.context.get('class_uuid')
        if not class_uuid:
            return None

        exam_class = next(
            (
                exam_class
                for exam_class in instance.exam_classes.all()
                if str(getattr(exam_class.class_obj, 'uuid', '')) == str(class_uuid)
            ),
            None,
        )
        return str(exam_class.uuid) if exam_class else None


class ExamScheduleExamClassSerializer(serializers.ModelSerializer):
    exam_uuid = serializers.UUIDField(source='exam.uuid', read_only=True)
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    exam_academic_year = serializers.IntegerField(source='exam.academic_year', read_only=True)
    exam_start_date = serializers.DateField(source='exam.start_date', read_only=True)
    exam_end_date = serializers.DateField(source='exam.end_date', read_only=True)
    class_details = SchoolClassSupportSerializer(source='class_obj', read_only=True)

    class Meta:
        model = ExamClass
        fields = [
            'uuid', 'exam_uuid', 'exam_name', 'exam_academic_year',
            'exam_start_date', 'exam_end_date', 'class_details'
        ]


class ExamScheduleSerializer(serializers.ModelSerializer):
    exam_class_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=ExamClass.objects.filter(is_active=True).select_related('exam', 'class_obj', 'class_obj__school'),
        source='exam_class'
    )
    subject_uuid = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=ClassSubjects.objects.filter(is_active=True).select_related('subject', 'subject_class', 'subject__school', 'subject_class__school'),
        source='subject'
    )
    exam_class_details = ExamScheduleExamClassSerializer(source='exam_class', read_only=True)
    subject_details = ClassSubjectSupportSerializer(source='subject', read_only=True)
    session_display = serializers.CharField(source='get_session_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    max_marks = serializers.FloatField(required=False, min_value=0)
    pass_marks = serializers.FloatField(required=False, min_value=0)
    exam_date = serializers.DateField()
    session = serializers.ChoiceField(choices=ExamSessions.choices, required=False, allow_null=True)
    start_time = serializers.TimeField(required=False, allow_null=True)
    end_time = serializers.TimeField(required=False, allow_null=True)

    class Meta:
        model = ExamSchedule
        fields = [
            'uuid', 'exam_class_uuid', 'subject_uuid', 'exam_class_details', 'subject_details',
            'max_marks', 'pass_marks', 'exam_date', 'session', 'session_display',
            'start_time', 'end_time', 'is_rescheduled', 'is_cancelled', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'exam_class_details', 'subject_details', 'session_display', 'is_active', 'created_at', 'updated_at']

    def validate_exam_date(self, value):
        if not value:
            raise serializers.ValidationError("Exam date is required.")
        return value

    def validate_max_marks(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Max marks cannot be negative.")
        return value

    def validate_pass_marks(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Pass marks cannot be negative.")
        return value

    def validate(self, data):
        school = self.context.get('school')
        if not school:
            return data

        instance = self.instance
        exam_class = data.get('exam_class', instance.exam_class if instance else None)
        subject = data.get('subject', instance.subject if instance else None)
        exam_date = data.get('exam_date', instance.exam_date if instance else None)
        session = data.get('session', instance.session if instance else None)
        start_time = data.get('start_time', instance.start_time if instance else None)
        end_time = data.get('end_time', instance.end_time if instance else None)

        if not exam_class:
            raise serializers.ValidationError({"exam_class_uuid": "Exam class is required."})

        if not subject:
            raise serializers.ValidationError({"subject_uuid": "Subject is required."})

        if not exam_class.exam:
            raise serializers.ValidationError({"exam_class_uuid": "Exam class is not linked to an exam."})

        if not exam_class.class_obj:
            raise serializers.ValidationError({"exam_class_uuid": "Exam class does not have a class assigned."})

        if not subject.subject or not subject.subject_class:
            raise serializers.ValidationError({"subject_uuid": "Subject is not assigned to a class."})

        if exam_class.exam.school_id != school.id:
            raise serializers.ValidationError({"exam_class_uuid": "Exam class does not belong to this school."})

        if exam_class.class_obj.school_id != school.id:
            raise serializers.ValidationError({"exam_class_uuid": "Class does not belong to this school."})

        if exam_class.exam.academic_year != school.academic_year:
            raise serializers.ValidationError({"exam_class_uuid": "Exam class does not belong to this academic year."})

        if exam_class.class_obj.academic_year != school.academic_year:
            raise serializers.ValidationError({"exam_class_uuid": "Class does not belong to this academic year."})

        if subject.subject.school_id != school.id:
            raise serializers.ValidationError({"subject_uuid": "Subject does not belong to this school."})

        if subject.subject_class.school_id != school.id:
            raise serializers.ValidationError({"subject_uuid": "Subject class does not belong to this school."})

        if subject.subject_class.academic_year != school.academic_year:
            raise serializers.ValidationError({"subject_uuid": "Subject class does not belong to this academic year."})

        if exam_class.class_obj_id != subject.subject_class_id:
            raise serializers.ValidationError({"subject_uuid": "Subject must be assigned to the same class as the exam class."})

        if exam_date and exam_class.exam:
            if not (exam_class.exam.start_date <= exam_date <= exam_class.exam.end_date):
                raise serializers.ValidationError({"exam_date": "Exam date must be within the exam duration."})

        if session and session != ExamSessions.FULL:
            if not start_time:
                raise serializers.ValidationError({"start_time": "Start time is required for this session."})
            if not end_time:
                raise serializers.ValidationError({"end_time": "End time is required for this session."})

        if (start_time and not end_time) or (end_time and not start_time):
            raise serializers.ValidationError({"end_time": "Start time and end time must be provided together."})

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        if not instance:
            max_marks = data.get('max_marks')
            pass_marks = data.get('pass_marks')
        else:
            max_marks = data.get('max_marks', instance.max_marks)
            pass_marks = data.get('pass_marks', instance.pass_marks)

        if max_marks is None:
            max_marks = subject.max_marks
        if pass_marks is None:
            pass_marks = subject.pass_marks

        if pass_marks > max_marks:
            raise serializers.ValidationError({"pass_marks": "Pass marks cannot be greater than max marks."})

        data['max_marks'] = max_marks
        data['pass_marks'] = pass_marks

        duplicate_query = ExamSchedule.objects.filter(
            exam_class=exam_class,
            subject=subject,
            is_active=True,
        )
        if instance:
            duplicate_query = duplicate_query.exclude(pk=instance.pk)

        effective_is_rescheduled = data.get('is_rescheduled', instance.is_rescheduled if instance else False)

        if duplicate_query.exists():
            if effective_is_rescheduled and not duplicate_query.exclude(is_cancelled=True).exists():
                return data

            exam_name = exam_class.exam.name
            class_name = exam_class.class_obj.class_name
            class_section = exam_class.class_obj.section
            subject_name = subject.subject.name
            raise serializers.ValidationError({
                "non_field_errors": [
                    f"Exam {exam_name} already scheduled for {class_name}-{class_section} for Subject: {subject_name}."
                ]
            })

        return data

    @transaction.atomic
    def create(self, validated_data):
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
