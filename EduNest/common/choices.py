from django.db import models

# User roles 
class UserRoles(models.TextChoices):

    SUPER_ADMIN = "SUPER_ADMIN", "Super_admin"
    SCHOOL_ADMIN = "SCHOOL_ADMIN", "School_admin"
    CLASS_TEACHER = "CLASS_TEACHER", "Class_teacher"
    SUBJECT_TEACHER = "SUBJECT_TEACHER", "Subject_teacher"
    TEACHER = "TEACHER", "Teacher"
    PARENT = "PARENT", "Parent"
    STUDENT = "STUDENT", "Student"

# User Gender
class UserGender(models.TextChoices):

    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    TRANSGENDER = "TRANSGENDER", "Transgender"
    OTHERS = "OTHERS", "Others"

# Marital Status
class MaritalStatus(models.TextChoices):

    SINGLE = "SINGLE", "Single"
    MARRIED = "MARRIED", "Married"
    DIVOURCED = "DIVOURCED", "Divourced"

# Employment Type
class EmployementType(models.TextChoices):

    FULLTIME = "FULLTIME", "Full-time"
    PARTTIME = "PARTTIME", "Part-time"
    GUEST = "GUEST", "Guest"

# Employee Status
class EmployeStatus(models.TextChoices):

    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    ON_LEAVE = "ON_LEAVE", "On_leave"
    RESIGNED = "RESIGNED", "Resigned"

# Class Medium
class ClassMedium(models.TextChoices):

    ENGLISH = "ENGLISH", "English"
    TAMIL = "TAMIL", "Tamil"
    MALAYALAM = "MALAYALAM", "Malayalam"
    HINDI = "HINDI", "Hindi"

# Class Board
class ClassBoard(models.TextChoices):

    STATE_BOARD = "STATE_BOARD", "State_board"
    CBSE = "CBSE", "CBSE"
    ICSE = "ICSE", "ICSE"
    IB = "IB", "International_baccalaureate"
    IGCSE = "IGCSE", "IGCSE"

# Address Type
class AddressType(models.TextChoices):

    SCHOOL = "SCHOOL", "School"
    USER = "USER", "User"

# School Type
class SchoolType(models.TextChoices):

    PRIVATE = "PRIVATE", "Private"
    GOVT = "GOVT", "Govt"
    AIDED = "AIDED", "Aided"

# Caste Category
class CasteCategory(models.TextChoices):
    
    GENERAL = "GENERAL", "General"
    OBC = "OBC", "obc"
    SC = "SC", "sc"
    ST = "ST", "st"

# Student Status
class StudentStatus(models.TextChoices):

    ACTIVE = "ACTIVE", "Active"
    TC = "TC", "tc"
    DROPOUT = "DROPOUT", "Dropout"
    ALUMNI = "ALUMNI", "Alumni"
    SUSPENDED = "SUSPENDED", "Suspended"

# Admission Type
class AdmissionType(models.TextChoices):

    NEW = "NEW", "New"
    TRANSFER = "TRANSFER", "Transfer"

# Subject Type
class SubjectType(models.TextChoices):
    THEORY = "THEORY", "Theory"
    PRACTICAL = "PRACTICAL", "Practical"
    BOTH = "BOTH", "Both"

# Attendance
class Attendance(models.TextChoices):
    P = 'P', 'Present'
    A = 'A', 'Absent'
    L = 'L', 'Leave'

# Class time table - days
class ClassTimeTableDays(models.TextChoices):
    MONDAY = 'MONDAY', 'Monday'
    TUESDAY = 'TUESDAY', 'Tuesday'
    WEDNESDAY = 'WEDNESDAY', 'Wednesday'
    THURSDAY = 'THURSDAY', 'Thursday'
    FRIDAY = 'FRIDAY', 'Friday'
    SATURDAY = 'SATURDAY', 'Saturday'
    SUNDAY = 'SUNDAY', 'Sunday'

# Exam Status
class ExamStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PUBLISHED = 'PUBLISHED', 'Published'

# Exam Sessions
class ExamSessions(models.TextChoices):
    FN = 'FN', 'Forenoon'
    AN = 'AN', 'Afternoon'
    FULL = 'FULL', 'Full Day'

# Exam Status
class ExamStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    RECORDED = 'RECORDED', 'Recorded'
    PUBLISHED = 'PUBLISHED', 'Published'

# Event Category
class EventCategory(models.TextChoices):
    EVENT = 'EVENT', 'Event'
    ACTIVITY = 'ACTIVITY', 'Activity'

# Event Type
class EventType(models.TextChoices):
    PROGRAM = 'PROGRAM', 'Program'
    SPORTS = 'SPORTS', 'Sports'
    EXPO = 'EXPO', 'Expo'
    WORKSHOP = 'WORKSHOP', 'Workshop'
    SEMINAR = 'SEMINAR', 'Seminar'
    MEETING = 'MEETING', 'Meeting'
    TRIP = 'TRIP', 'Trip'
    CLUB = 'CLUB', 'Club'

# Participation Type
class ParticipationType(models.TextChoices):
    MANDATORY = 'MANDATORY', 'Mandatory'
    OPTIONAL = 'OPTIONAL', 'Optional'

# Event Response Status
class EventResponseStatus(models.TextChoices):
    NOT_RESPONDED = 'NOT_RESPONDED', 'Not Responded'
    INTRESTED = 'INTRESTED', 'Interested'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    NOT_PARTICIPATING = 'NOT_PARTICIPATING', 'Not Participating'

# Event Responded By
class EventRespondedBy(models.TextChoices):
    PARENT = 'PARENT', 'Parent'
    ADMIN = 'ADMIN', 'Admin'

# Payment Status
class PaymentStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "Success"
    PENDING = "PENDING", "Pending"
    FAILED = "FAILED", "Failed"

# Payment Methods
class PaymentMethods(models.TextChoices):
    CASH = "CASH", "Cash"
    UPI = "UPI", "UPI"
    BANK = "BANK", "Bank Transfer"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"

# Fee Warning Types
class FeeWarningType(models.TextChoices):
    GENTLE = "GENTLE", "Gentle Reminder"
    URGENT = "URGENT", "Urgent"
    FINAL = "FINAL", "Final Notice"
