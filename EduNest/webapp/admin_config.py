# Model to Category Mapping Configuration

ADMIN_GROUPS = {
    'School': [
        'School',
        'SchoolContact',
        'SchoolRegistration',
        'ExamType',
        'Exam',
        'Event',
    ],
    'Class': [
        'SchoolClass',
        'Subjects',
        'ClassSubjects',
        'SubjectGroup',
        'AttendanceSession',
        'ClassTimetable',
        'ClassTimetableEntry',
        'ExamClass',
        'ExamSchedule',
        'EventClass',
        "Period",
    ],
    'Teacher': [
        'SchoolTeacher',
        'TeacherEducationDetails',
        'TeacherExperianceDetails',
        'TeacherEmploymentDetails',
    ],
    'Student': [
        'Students',
        'StudentsAdmissionDetails',
        'StudentParentDetails',
        'StudentAcademicdetails',
        'StudentAttendance',
        'Mark',
        'StudentMark',
        'EventResponse',
        'Fee',
        'Payment',
        'FeeReminder',
        'FeeWarning',
    ],
    'AddressBook': [
        'AddressBook',
    ],
    'Users': [
        'Users',
    ],
}

def get_category_for_model(model_name):
    """
    Returns the category for a given model name.
    If not explicitly defined, attempts auto-detection via keywords.
    """
    for category, models in ADMIN_GROUPS.items():
        if model_name in models:
            return category
    
    # Auto-detection fallback
    model_name_lower = model_name.lower()
    if 'student' in model_name_lower or 'fee' in model_name_lower or 'payment' in model_name_lower:
        return 'Student'
    if 'teacher' in model_name_lower:
        return 'Teacher'
    if 'class' in model_name_lower or 'subject' in model_name_lower or 'timetable' in model_name_lower:
        return 'Class'
    if 'school' in model_name_lower:
        return 'School'
    
    return 'Other'
