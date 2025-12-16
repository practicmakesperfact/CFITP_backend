from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible
import os
from datetime import datetime

@deconstructible
class CustomAttachmentStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        # Add timestamp to avoid filename collisions
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        
        # Create timestamp string
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # New filename with timestamp
        new_name = f"{file_root}_{timestamp}{file_ext}"
        
        # Reconstruct full path
        if dir_name:
            new_name = os.path.join(dir_name, new_name)
        
        return super().get_available_name(new_name, max_length)