from fastapi import UploadFile, HTTPException, Depends
from helpers.config import Settings, get_settings
from models.response_models import MessageResponse, FileUploadResponse
from models.enums import ResponseSignal
from controllers.base_controller import BaseController, base_controller
from controllers.project_controller import project_controller
from pathlib import Path
import shutil
import re
import random
import string
import os

class DataController(BaseController):
    """Controller for data tasks with custom validation."""
    
    def __init__(self, app_settings: Settings = None): 
        super().__init__()
        self.app_settings = app_settings
        self.size_scale = 1048576 # convert MB to bytes
        
    def get_clean_file_name(self, orig_file_name: str) -> str:
        # allow alphanumeric, dots, and spaces in the first pass
        cleaned_file_name = re.sub(r'[^\w\s.]', '', orig_file_name.strip())

        # now explicitly replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")

        return cleaned_file_name

    def generate_unique_filepath(self, orig_file_name: str, project_id: str) -> tuple[str, str]:
        random_key = self.generate_random_string()
        project_path = project_controller.get_project_path(project_id=project_id)

        cleaned_file_name = self.get_clean_file_name(
            orig_file_name=orig_file_name
        )

        new_file_path = os.path.join(
            project_path,
            random_key + "_" + cleaned_file_name
        )

        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(
                project_path,
                random_key + "_" + cleaned_file_name
            )

        return os.path.basename(new_file_path), new_file_path
    

    def validate_uploaded_file(self, file: UploadFile, settings: Settings = None):
        """Validation logic with result signals."""
        actual_settings = settings or self.app_settings or get_settings()
        
        if file.content_type not in actual_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > actual_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value

    def validate_file_properties(self, file: UploadFile, settings: Settings = Depends(get_settings)):
        """Explicit validation that returns result."""
        # 1. Update instance settings
        self.app_settings = settings
        
        # 2. Run screenshot validation logic
        is_valid, _ = self.validate_uploaded_file(file)
        if not is_valid:
            return "bad_request"
            
        # 3. Run base validation (Centralized)
        try:
            base_controller.validate_file(file, settings)
        except HTTPException:
            return "bad_request"
        
        return "ok"

    @staticmethod
    async def get_data_info(settings: Settings) -> MessageResponse:
        """Logic for data info page."""
        return MessageResponse(
            message=f"Data services for {settings.APP_NAME} are ready.",
            version=settings.APP_VERSION
        )

    async def upload_file(self, project_id: str, file: UploadFile, settings: Settings) -> FileUploadResponse:
        """Upload file. Validation is already done in the route via Depends."""
            
        # 3. Ensure deep assets directory exists via ProjectController
        project_path = project_controller.ensure_project_path(project_id)
        
        # 4. Define file path
        file_path = project_path / file.filename
        
        # 5. Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Get file size for response
        file_size = file_path.stat().st_size
            
        return FileUploadResponse(
            message="File uploaded successfully!",
            project_id=project_id,
            file_name=file.filename,
            file_size=file_size
        )


# Create controller object
data_controller = DataController()
