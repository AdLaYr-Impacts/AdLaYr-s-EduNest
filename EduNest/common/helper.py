import datetime
import re
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
