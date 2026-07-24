import uuid
import datetime
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator, 
    MaxValueValidator,
)
from django_countries.fields import CountryField
from accounts.models import Users
from common.choices import (
    EmployementType,
    EmployeStatus,
    ClassMedium,
    ClassBoard,
    AddressType,
    SchoolType,
    CasteCategory,
    StudentStatus,
    AdmissionType,
    SubjectType,
    Attendance,
    ClassTimeTableDays,
    ExamStatus,
    ExamSessions,
    PaymentStatus,
    PaymentMethods,
    FeeWarningType,
    ExamStatus,
    EventCategory,
    EventType,
    ParticipationType,
    EventResponseStatus,
    EventRespondedBy,

)

current_year = datetime.date.today().year

class BaseModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class School(BaseModel):
    name = models.TextField(null=True, blank=True)
    short_name = models.CharField(max_length=255, null=True, blank=True)
    motto = models.TextField(null=True, blank=True)
    school_code = models.CharField(max_length=255, unique=True)
    school_type = models.CharField(max_length=255, null=True, blank=True, choices=SchoolType.choices)
    board = models.CharField(max_length=255, null=True, blank=True, choices=ClassBoard.choices)
    medium_of_instructions = models.CharField(max_length=255, null=True, blank=True, choices=ClassMedium.choices)
    logo = models.ImageField(upload_to="school_logos/", null=True, blank=True)
    total_students = models.IntegerField(default=0)
    total_staffs = models.IntegerField(default=0)
    principal = models.ForeignKey("SchoolTeacher", on_delete=models.CASCADE, null=True, blank=True, related_name="school_principal")
    academic_year = models.PositiveSmallIntegerField(default=current_year)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'School'
        verbose_name_plural = 'Schools'

    def __str__(self):
        return f"[{self.id}] {self.short_name}"
    

class SchoolContact(BaseModel):
    school = models.OneToOneField(School, blank=True, null=True, on_delete=models.CASCADE, related_name="school_contact")
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    alternative_phone_number = models.CharField(max_length=15, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=15, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    instagram = models.URLField(null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    youtube = models.URLField(null=True, blank=True)
    google_map = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'School Contact'
        verbose_name_plural = 'School Contacts'

    def __str__(self):
        return f"[{self.id}] {self.school.short_name}"
    
    
class SchoolRegistration(BaseModel):
    school = models.OneToOneField(School, blank=True, null=True, on_delete=models.CASCADE, related_name="school_registeration")
    registeration_number = models.CharField(max_length=255, null=True, blank=True)
    affiliation_number = models.CharField(max_length=255, null=True, blank=True)
    udise_code = models.CharField(max_length=20, null=True, blank=True)
    school_code = models.CharField(max_length=255, null=True, blank=True)
    recognition_number = models.CharField(max_length=255, null=True, blank=True)
    pan_number = models.CharField(max_length=20, null=True, blank=True)
    gst_number = models.CharField(max_length=20, null=True, blank=True)
    tan_number = models.CharField(max_length=255, null=True, blank=True)
    section_certificate = models.CharField(max_length=255, null=True, blank=True)
    epf_registeration_number = models.CharField(max_length=255, null=True, blank=True)
    esi_registeration_number = models.CharField(max_length=255, null=True, blank=True)
    pen_number = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'School Registeration'
        verbose_name_plural = 'School Registerations'

    def __str__(self):
        return f"[{self.id}] {self.school.short_name}"
    

class SchoolTeacher(BaseModel):
    user = models.ForeignKey(Users, blank=True, null=True, on_delete=models.CASCADE, related_name="school_teacher")
    school = models.ForeignKey(School, blank=True, null=True, on_delete=models.SET_NULL, related_name="techer_school")
    teacher_code = models.CharField(max_length=255, unique=True) # username should be teacher code
    joining_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=30, choices=EmployementType.choices)
    status = models.CharField(max_length=30, null=True, blank=True, choices=EmployeStatus.choices)
    is_class_teacher = models.BooleanField(default=False)
    is_assistant_class_teacher = models.BooleanField(default=False)
    is_principal = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'School Teacher'
        verbose_name_plural = 'School Teacher'

    def __str__(self):
        return f"[{self.id}] {self.user.get_full_name()} school: {self.school.name}"
    

class TeacherEducationDetails(BaseModel):
    teacher = models.ForeignKey(SchoolTeacher, on_delete=models.CASCADE, related_name="teacher_education")
    degree = models.CharField(max_length=255, null=True, blank=True)
    specialization = models.CharField(max_length=255, null=True, blank=True)
    institution_name = models.CharField(max_length=255, null=True, blank=True)
    university = models.CharField(max_length=255, null=True, blank=True)
    year_of_passing = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(current_year)]
    )
    pass_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True, validators=[MaxValueValidator(100)]
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Teacher Education Details'
        verbose_name_plural = 'Teacher Education Details'

    def __str__(self):
        return f"[{self.id}] {self.teacher.user.get_full_name()} Degree: {self.degree}"
    
    
class TeacherExperianceDetails(BaseModel):
    teacher = models.ForeignKey(SchoolTeacher, on_delete=models.CASCADE, related_name="teacher_experiance")
    school_name = models.CharField(max_length=255, null=True, blank=True)
    school_address = models.CharField(max_length=255, null=True, blank=True)
    designation = models.CharField(max_length=255, null=True, blank=True)
    subjects_taught = models.CharField(max_length=255, null=True, blank=True) # need multichoice many to many field here..
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    years_of_experiance = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(100)]
    )   # auto calculate
    reason_for_leaving = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Teacher Experiance Details'
        verbose_name_plural = 'Teacher Experiance Details'

    def __str__(self):
        return f"[{self.id}] {self.teacher.user.get_full_name()} Experaince as {self.designation}"
    
    
class TeacherEmploymentDetails(BaseModel):
    teacher = models.ForeignKey(SchoolTeacher, on_delete=models.CASCADE, related_name="teacher_employment")
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_account_number = models.CharField(max_length=30, null=True, blank=True)
    ifsc_code = models.CharField(max_length=15, null=True, blank=True)
    pf_number = models.CharField(max_length=25, null=True, blank=True)
    esi_number = models.CharField(max_length=15, null=True, blank=True)
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Teacher Employment Details'
        verbose_name_plural = 'Teacher Employment Details'

    def __str__(self):
        return f"[{self.id}] {self.teacher.user.get_full_name()} school: {self.teacher.school.name}"
    

class SchoolClass(BaseModel):
    school = models.ForeignKey(School, blank=True, null=True, on_delete=models.SET_NULL, related_name="school_class")
    class_teacher = models.ForeignKey(SchoolTeacher, null=True, blank=True, on_delete=models.SET_NULL, related_name="classes_as_class_teacher")
    assistant_teacher = models.ManyToManyField(SchoolTeacher, related_name="classes_as_assistant_teacher")
    class_name = models.CharField(max_length=255, null=True, blank=True)
    section = models.CharField(max_length=255, null=True, blank=True)
    academic_year = models.PositiveSmallIntegerField(default=current_year)
    medium = models.CharField(max_length=255, null=True, blank=True, choices=ClassMedium.choices)
    board = models.CharField(max_length=255, null=True, blank=True, choices=ClassBoard.choices)
    max_strength = models.PositiveSmallIntegerField(null=True, blank=True)
    whatsapp_group_link = models.URLField(null=True, blank=True)
    classroom_number = models.CharField(max_length=255, null=True, blank=True)
    smart_class_enabled = models.BooleanField(default=False)
    class_color_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'

    def __str__(self):
        return f"[{self.id}] class: {self.class_name} {self.section} school id: {self.school.id}"
    

class Subjects(BaseModel):
    school = models.ForeignKey(School, blank=True, null=True, on_delete=models.SET_NULL, related_name="school_subjects")
    name = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)
    subject_type = models.CharField(max_length=255, null=True, blank=True, choices=SubjectType.choices)
    
    class Meta:
        unique_together = ['school', 'code']
        ordering = ["-created_at"]
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'

    def __str__(self):
        return f"[{self.id}] {self.code} {self.name}"
    

class ClassSubjects(BaseModel):
    subject = models.ForeignKey(Subjects, null=True, blank=True, on_delete=models.CASCADE, related_name="class_subjects")
    subject_class = models.ForeignKey(SchoolClass, null=True, blank=True, on_delete=models.CASCADE, related_name="class_as_subject_class")
    teacher = models.ManyToManyField(SchoolTeacher, blank=True, related_name="subject_teacher")
    is_optional = models.BooleanField(default=False)
    is_language = models.BooleanField(default=False)
    max_marks = models.FloatField(default=100)
    pass_marks = models.FloatField(default=35)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Class Subject'
        verbose_name_plural = 'Class Subjects'

    def __str__(self):
        return f"[{self.id}] {self.subject_class.class_name} {self.subject.code} {self.subject.name}"
    

class SubjectGroup(BaseModel):
    school = models.ForeignKey(School, blank=True, null=True, on_delete=models.SET_NULL, related_name="school_subject_groups")
    name = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=15, null=True, blank=True)
    classes = models.ManyToManyField(SchoolClass, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Subject Group'
        verbose_name_plural = 'Subject Groups'

    def __str__(self):
        return f"[{self.id}] {self.name}"
    
    
class Students(BaseModel):
    """
    Initital MVP: No need of student login
    But user requires password
    For Password:
        1. Use parents password
        2. Or use common (or) unique to all
    """
    user = models.ForeignKey(Users, blank=True, null=True, on_delete=models.CASCADE, related_name="student_profile")
    school = models.ForeignKey(School, blank=True, null=True, on_delete=models.SET_NULL, related_name="school_student")
    religion = models.CharField(max_length=255, null=True, blank=True)
    caste_category = models.CharField(max_length=255, null=True, blank=True, choices=CasteCategory.choices)
    mother_tongue = models.CharField(max_length=255, null=True, blank=True)
    identification_mark_1 = models.CharField(max_length=255, null=True, blank=True)
    identification_mark_2 = models.CharField(max_length=255, null=True, blank=True)
    previous_academic_years = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"[{self.id}] {self.user.get_full_name()} school: {self.school.name}"
    
    
class StudentsAdmissionDetails(BaseModel):
    student = models.ForeignKey(Students, null=True, blank=True, on_delete=models.CASCADE, related_name="student_admission_details")
    admission_number = models.CharField(max_length=30, null=True, blank=True)
    admission_type = models.CharField(max_length=30, null=True, blank=True, choices=AdmissionType.choices)
    admission_date = models.DateField(null=True, blank=True)
    academic_year = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(current_year)]
    )
    student_status = models.CharField(max_length=255, null=True, blank=True, choices=StudentStatus.choices)
    previous_school = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Student Admission Detail'
        verbose_name_plural = 'Students Admission Details'

    def save(self, *args, **kwargs):
        if self.admission_number == "":
            self.admission_number = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.id}] {self.student.user.get_full_name()} school: {self.student.school.name}"
    
    
class StudentParentDetails(BaseModel):
    user = models.ForeignKey(Users, blank=True, null=True, on_delete=models.CASCADE, related_name="parent_profile")
    student = models.ForeignKey(Students, null=True, blank=True, on_delete=models.CASCADE, related_name="student_parent_details")
    father_name = models.CharField(max_length=255, null=True, blank=True)
    father_occupation = models.CharField(max_length=255, null=True, blank=True)
    father_phone = models.CharField(max_length=15, null=True, blank=True)
    father_email = models.EmailField(null=True, blank=True)
    mother_name = models.CharField(max_length=255, null=True, blank=True)
    mother_occupation = models.CharField(max_length=255, null=True, blank=True)
    mother_phone = models.CharField(max_length=15, null=True, blank=True)
    mother_email = models.EmailField(null=True, blank=True)
    gurdian_name = models.CharField(max_length=255, null=True, blank=True)
    gurdian_releation = models.CharField(max_length=255, null=True, blank=True)
    gurdian_phone = models.CharField(max_length=15, null=True, blank=True)
    gurdian_email = models.EmailField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Student Parent Detail'
        verbose_name_plural = 'Students Parent Details'

    def __str__(self):
        return f"[{self.id}] {self.student.user.get_full_name()} school: {self.student.school.name}"
    
    
class StudentAcademicdetails(BaseModel):
    student = models.ForeignKey(Students, null=True, blank=True, on_delete=models.CASCADE, related_name="student_academic_details")
    student_class = models.ForeignKey(SchoolClass, null=True, blank=True, on_delete=models.SET_NULL, related_name="student_class")
    subject_group = models.ForeignKey(SubjectGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="student_group")
    roll_number = models.CharField(max_length=30, null=True, blank=True)
    register_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    second_language = models.CharField(max_length=255, null=True, blank=True)
    third_language = models.CharField(max_length=255, null=True, blank=True)
    transport_requird = models.BooleanField(default=False)
    pickup_point = models.CharField(max_length=255, null=True, blank=True)
    vehicle_number = models.CharField(max_length=30, null=True, blank=True)
    vehicle_rc_number = models.CharField(max_length=30, null=True, blank=True)
    driver_name = models.CharField(max_length=255, null=True, blank=True)
    driver_phone = models.CharField(max_length=15, null=True, blank=True)
    hostel_requird = models.BooleanField(default=False)
    hostel_name = models.CharField(max_length=255, null=True, blank=True)
    room_number = models.CharField(max_length=30, null=True, blank=True)    
    warden_name = models.CharField(max_length=255, null=True, blank=True)
    warden_phone = models.CharField(max_length=15, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.register_number == "":
            self.register_number = None
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Student Academic Detail'
        verbose_name_plural = 'Students Academic Details'

    def __str__(self):
        return f"[{self.id}] {self.student.user.get_full_name()} school: {self.student.school.name}"
    

class AttendanceSession(BaseModel):
    """ to consolidate through date """
    class_obj = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, blank=True, related_name="attendance_session_class")
    date = models.DateField()
    total_students = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    leave_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_session_user")

    class Meta:
        unique_together = ['class_obj', 'date']
        ordering = ["-created_at"]
        verbose_name = 'Class Attendance Session'
        verbose_name_plural = 'Class Attendance Sessions'

    def __str__(self):
        return f"[{self.id}] {self.class_obj.school.school_code} {self.class_obj.school.short_name} {self.class_obj.class_name}"
    

class StudentAttendance(BaseModel):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(Students, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=1, choices=Attendance.choices, null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['session', 'student']
        ordering = ["-created_at"]
        verbose_name = 'Student Attendance'
        verbose_name_plural = 'Student Attendance'

    def __str__(self):
        return f"[{self.id}] {self.student.user.username} {self.status}"
    

class Period(BaseModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="school_periods")
    class_obj = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="class_periods")
    name = models.CharField(max_length=50, null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_break = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Period'
        verbose_name_plural = 'Periods'

    def __str__(self):
        return f"[{self.id}] {self.school.short_name} {self.start_time}-{self.end_time}"
    

class ClassTimetable(BaseModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="class_time_table")
    class_obj = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    is_published = models.BooleanField(default=False)
    is_save_as_draft = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Class Time table'
        verbose_name_plural = 'Class Time tables'

    def __str__(self):
        status = "Published" if self.is_published else "Drafted"
        return f"[{self.id}] {self.school.short_name} {self.class_obj.class_name} {status}"
    

class ClassTimetableEntry(BaseModel):
    timetable = models.ForeignKey(ClassTimetable, on_delete=models.CASCADE, related_name="time_table")
    day = models.CharField(max_length=30, choices=ClassTimeTableDays.choices, null=True, blank=True)
    period = models.ForeignKey(Period, on_delete=models.CASCADE, null=True, blank=True, related_name="class_period")
    subject = models.ForeignKey(ClassSubjects, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_class")
    teacher = models.ForeignKey(SchoolTeacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_teacher")

    class Meta:
        unique_together = ('timetable', 'day', 'period')
        ordering = ["-created_at"]
        verbose_name = 'Time table Entry'
        verbose_name_plural = 'Time table Entries'
            
    def __str__(self):
        return f"[{self.id}] {self.timetable.school.short_name} {self.timetable.class_obj.class_name} {self.day}"
            

class ExamType(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="exam_types")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Exam Type'
        verbose_name_plural = 'Exam Types'

    def __str__(self):
        return f"[{self.id}] {self.school.short_name} {self.name}"
    

class Exam(BaseModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="school_exam")
    academic_year = models.PositiveSmallIntegerField(default=current_year)
    name = models.CharField(max_length=100)
    exam_type = models.ForeignKey(ExamType, on_delete=models.SET_NULL, null=True, blank=True, related_name="exam_type")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=ExamStatus.choices, default='draft')
    is_locked = models.BooleanField(default=False)
    created_by = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True, related_name="exam_created_by")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'

    def __str__(self):
        return f"[{self.id}] {self.name} ({self.start_date})"
    

class ExamClass(BaseModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="exam_classes")
    class_obj = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="exam_class")

    class Meta:
        unique_together = ['exam', 'class_obj']
        ordering = ["-created_at"]
        verbose_name = 'Exam Class'
        verbose_name_plural = 'Exam Classes'

    def __str__(self):
        return f"[{self.id}] {self.exam.name} {self.class_obj.class_name}"
    

class ExamSchedule(BaseModel):
    exam_class = models.ForeignKey(
        ExamClass,
        on_delete=models.CASCADE,
        related_name="schedules"
    )
    subject = models.ForeignKey(ClassSubjects, on_delete=models.CASCADE, related_name="exam_subjects") # need validation here
    max_marks = models.FloatField(default=100)
    pass_marks = models.FloatField()
    exam_date = models.DateField()
    session = models.CharField(max_length=10, choices=ExamSessions.choices, null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_rescheduled = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Exam Schedule'
        verbose_name_plural = 'Exam Schedules'
    
    def clean(self):
        if not (self.exam_class.exam.start_date <= self.exam_date <= self.exam_class.exam.end_date):
            raise ValidationError("Exam date must be within exam duration")
        
        if self.session and self.session != ExamSessions.FULL and not (self.start_time and self.end_time):
            raise ValidationError("Start and End time required")

        if (self.start_time and not self.end_time) or (self.end_time and not self.start_time):
            raise ValidationError("Start and End time must be provided together")

        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")
        
    def __str__(self):
        return f"[{self.id}] {self.exam_class.exam.name} {self.exam_class.class_obj.class_name} {self.subject.subject.name}"
    

class Mark(BaseModel):
    exam_class = models.ForeignKey(
        ExamClass,
        on_delete=models.CASCADE,
        related_name="student_exams"
    )
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name="student_mark")
    total_marks = models.FloatField(default=0)
    out_of_marks = models.FloatField(default=0)
    result = models.CharField(
        max_length=10,
        choices=[('PASS', 'Pass'), ('FAIL', 'Fail')],
        null=True,
        blank=True
    )
    rank = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ExamStatus.choices,
        default=ExamStatus.DRAFT
    )
    is_parent_viewed = models.BooleanField(default=False)
    recorded_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="recorded_exams"
    )
    recorded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['exam_class', 'student']
        ordering = ["-created_at"]
        verbose_name = 'Exam Schedule'
        verbose_name_plural = 'Exam Schedules'

    def __str__(self):
        return f"""
            [{self.id}] {self.student.user.get_full_name()} 
            {self.exam_class.class_obj.class_name} {self.total_marks}/{self.out_of_marks}
        """
    

class StudentMark(BaseModel):
    exam_schedule = models.ForeignKey(
        ExamSchedule,
        on_delete=models.CASCADE,
        related_name="marks"
    )
    consolidated_mark = models.ForeignKey(
        Mark,
        on_delete=models.CASCADE,
        related_name="consolidated_marks"
    )
    marks_obtained = models.FloatField(null=True, blank=True)
    is_absent = models.BooleanField(default=False)
    remarks = models.CharField(max_length=255, null=True, blank=True)
    entered_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ['exam_schedule', 'consolidated_mark']
        ordering = ["-created_at"]
        verbose_name = 'Exam Schedule'
        verbose_name_plural = 'Exam Schedules'

    def clean(self):
        if not self.is_absent and self.marks_obtained is None:
            raise ValidationError("Enter marks or mark as absent")

        if self.marks_obtained:
            if self.marks_obtained > self.exam_schedule.max_marks:
                raise ValidationError("Marks cannot exceed max marks")

    def __str__(self):
        return f"""
        [{self.id}] {self.consolidated_mark.student.user.get_full_name()}
        {self.exam_schedule.subject.subject.name} {self.marks_obtained}
    """

class Event(BaseModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="school_event") 
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=20, null=True, blank=True, choices=EventCategory.choices)
    type = models.CharField(max_length=50, null=True, blank=True, choices=EventType.choices)
    participation_type = models.CharField(max_length=20, null=True, blank=True, choices=ParticipationType.choices)
    response_deadline = models.DateTimeField(null=True, blank=True)
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=255, null=True, blank=True)
    organizer = models.CharField(max_length=255, null=True, blank=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    is_all_classes = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='event_attachments/', null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return f"[{self.id}] {self.school.short_name} {self.title}"
    

class EventClass(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_classes')
    class_obj = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="event_class")

    class Meta:
        unique_together = ('event', 'class_obj')
        ordering = ["-created_at"]
        verbose_name = 'Event Class'
        verbose_name_plural = 'Event Classes'

    def __str__(self):
        return f"[{self.id}] {self.event.school.short_name} {self.event.title} {self.class_obj.class_name}"
    

class EventResponse(BaseModel):
    event_obj = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_responses')
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=EventResponseStatus.choices, default=EventResponseStatus.NOT_RESPONDED)
    responed_by = models.CharField(max_length=10, choices=EventRespondedBy.choices, null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    edited_by_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ('event_obj', 'student')
        ordering = ["-created_at"]
        verbose_name = 'Event Response'
        verbose_name_plural = 'Event Responses'

    def confirmed_count(self):
        return self.event_responses.filter(status='confirmed').count()
    
    def participation_rate(self):
        total = self.event_responses.count()
        confirmed = self.event_responses.filter(status='confirmed').count()
        return (confirmed / total) * 100 if total > 0 else 0

    def __str__(self):
        return f"[{self.id}] {self.event_obj.title} {self.student.user.get_full_name()} {self.status}"


class Fee(BaseModel):
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name="fees")
    fee_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    last_due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    additional_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Fee'
        verbose_name_plural = 'Fees'

    @property
    def final_amount(self):
        return self.total_amount - (self.discount_amount + self.additional_discount_amount)

    @property
    def paid_amount(self):
        return sum(p.amount for p in self.payments.filter(status="SUCCESS"))

    @property
    def balance_amount(self):
        return self.final_amount - self.paid_amount

    @property
    def status(self):
        if self.paid_amount == 0:
            return "NOT_PAID"
        elif self.paid_amount < self.final_amount:
            return "PARTIALLY_PAID"
        return "PAID"
    
    def __str__(self):
        return f"[{self.id}] {self.student.user.get_full_name()} {self.fee_name} Rs.{self.final_amount}"
    

class Payment(BaseModel):
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    is_additional_discount = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=PaymentMethods.choices)
    status = models.CharField(max_length=10, choices=PaymentStatus.choices)
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def clean(self):
        if self.amount > self.fee.balance_amount:
            raise ValidationError("Payment exceeds remaining balance")
        
    def __str__(self):
        return f"[{self.id}] {self.fee.student.user.get_full_name()} {self.fee.fee_name} Paid: Rs.{self.amount}"
    

class FeeReminder(BaseModel):
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name="reminders")
    reminder_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Fee Reminder'
        verbose_name_plural = 'Fee Reminders'

    def __str__(self):
        return f"""[{self.id}] 
            {self.fee.student.user.get_full_name()} {self.fee.fee_name} 
            {self.reminder_date}: Rs.{self.amount}
        """
    

class FeeWarning(BaseModel):
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name="warnings")
    type = models.CharField(max_length=10, choices=FeeWarningType.choices)
    message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Fee Warning'
        verbose_name_plural = 'Fee Warnings'

    def __str__(self):
        return f"[{self.id}] {self.type} for {self.fee.student.user.get_full_name()} {self.fee.fee_name}"
    

class AddressBook(BaseModel):
    address_type = models.CharField(max_length=255, null=True, blank=True, choices=AddressType.choices)
    user = models.ForeignKey(Users, blank=True, null=True, on_delete=models.CASCADE, related_name="user_address")
    school = models.ForeignKey(School, blank=True, null=True, on_delete=models.CASCADE, related_name="school_address")
    address_line_1 = models.CharField(max_length=50, blank=True, null=True)
    address_line_2 = models.CharField(max_length=50, blank=True, null=True)
    address_line_3 = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    Country = CountryField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'AddressBook'
        verbose_name_plural = 'AddressBook'

    def __str__(self):
        return f"[{self.id}] {
            self.user.get_full_name() if self.user else self.school.short_name
        }"
