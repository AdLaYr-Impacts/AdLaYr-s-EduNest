import datetime
import re
from django.db import transaction
from django.core.exceptions import ValidationError
from django.apps import apps
from django.db.models.functions import Length
from common.choices import UserRoles
from webapp.models import School

def generate_school_code(short_name, sequence_number):
    """
    Generates a unique school code in the format: <SHORT_NAME>-<YEAR>-<SEQUENCE>
    
    Args:
        short_name (str): The school's short name from the payload.
        sequence_number (int): The sequence number for the current year.
        
    Returns:
        str: The generated school code.
    """
    if not short_name:
        short_name = "SCH"
    
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', short_name).upper()
    
    if ' ' in short_name:
        prefix = clean_name[:3]
    else:
        prefix = clean_name[:5]
        
    if not prefix:
        prefix = "SCH"
        
    year = datetime.date.today().year
    formatted_sequence = f"{sequence_number:04d}"
    
    return f"{prefix}-{year}-{formatted_sequence}"

def get_next_school_sequence():
    """
    Calculates the next sequence number for a school based on the current year's count.
    """
    current_year = datetime.date.today().year
    
    # Count schools created in the current year
    count = School.objects.filter(created_at__year=current_year).count()
    return count + 1

def generate_user_code(school, role):
    """
    Generates a unique user code (username) for all users.
    
    Format: <SCHOOL_IDENTIFIER><ROLE><SEQUENCE>
    Examples: S1T0001, J21P0001, B105A0001
    
    Args:
        school (webapp.models.School): The school instance.
        role (str): The role value from common.choices.UserRoles.
        
    Returns:
        str: The generated unique user code.
        
    Raises:
        ValidationError: If school_code format is invalid, school is missing, 
                         or role mapping is not found.
    """
    ROLE_MAP = {
        UserRoles.SCHOOL_ADMIN: 'A',
        UserRoles.TEACHER: 'T',
        UserRoles.CLASS_TEACHER: 'T',
        UserRoles.SUBJECT_TEACHER: 'T',
        UserRoles.PARENT: 'P',
        UserRoles.STUDENT: 'S',
    }
    
    role_code = ROLE_MAP.get(role)
    if not role_code:
        raise ValidationError(f"Invalid role or role mapping not found for: {role}")

    # School Identifier Extraction
    # Logic: Extract the last numeric part from school_code and prefix with the first letter of school_code.
    # Example: JOYS-2026-0021 -> J21
    if not school:
        raise ValidationError("School instance is required to generate user code.")
        
    if not school.school_code:
        raise ValidationError(f"School '{school}' does not have a school_code.")
        
    # Find the last numeric group in the school_code
    match = re.search(r'(\d+)$', school.school_code)
    if not match:
        raise ValidationError(
            f"Invalid school_code format: '{school.school_code}'. "
            "Expected format ending with numeric sequence (e.g., SRE-2026-0001)"
        )
    
    # Extract numeric part and omit leading zeros
    sequence_part = match.group(1)
    school_numeric_id = sequence_part.lstrip('0')
    
    # If numeric part is all zeros (e.g., "0000"), lstrip returns empty string
    if not school_numeric_id:
        school_numeric_id = '0'
        
    school_prefix = school.school_code[0].upper()
    school_identifier = f"{school_prefix}{school_numeric_id}"
    
    # Prefix format: <SCHOOL_PREFIX><SCHOOL_ID><ROLE_CODE> (e.g., J21T)
    prefix = f"{school_identifier}{role_code}"
    
    Users = apps.get_model('accounts', 'Users')
    # School = apps.get_model('webapp', 'School') # Redundant import above
    
    with transaction.atomic():
        # Lock the school record to ensure serial generation of user codes for this school.
        # This prevents race conditions during concurrent requests even if no users exist yet.
        School.objects.select_for_update().get(pk=school.pk)
        
        # Find the last username with the given prefix.
        # We order by length descending first, then by username descending.
        # This handles cases where the sequence grows from 4 digits (e.g., 9999) to 5 digits (10000)
        # because lexicographical sort alone would put '9999' > '10000'.
        last_user = Users.objects.filter(
            username__startswith=prefix,
            school=school
        ).order_by(Length('username').desc(), '-username').first()
        
        if last_user:
            try:
                # Extract the numeric sequence part after the prefix
                last_username = last_user.username
                sequence_str = last_username[len(prefix):]
                if sequence_str.isdigit():
                    next_sequence = int(sequence_str) + 1
                else:
                    # Fallback if the format was somehow tampered with
                    next_sequence = 1
            except (ValueError, IndexError):
                next_sequence = 1
        else:
            # Start sequence at 1 if no user exists for this school and role
            next_sequence = 1
            
        # Padding and Final Construction
        # Minimum 4 digit padding, but supports values above 9999 (e.g., 10000)
        formatted_sequence = f"{next_sequence:04d}"
        user_code = f"{prefix}{formatted_sequence}"
        
        # Final safety check for uniqueness (handles manual entries or gaps from deletions)
        while Users.objects.filter(username=user_code).exists():
            next_sequence += 1
            formatted_sequence = f"{next_sequence:04d}"
            user_code = f"{prefix}{formatted_sequence}"
            
        return user_code
