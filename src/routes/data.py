from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, HTTPException
from fastapi.responses import JSONResponse
import os
import aiofiles
import logging
from helpers.config import get_settings, Settings
from controllers import data_controller, project_controller, ProcessController
from models.response_models import MessageResponse, FileUploadResponse
from models.enums import ResponseSignal
from routes.schemas import ProcessRequest
import shutil

logger = logging.getLogger(__name__)

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.get("/info", response_model=MessageResponse)
async def data_info(settings: Settings = Depends(get_settings)):
    """Data info route from the controller."""
    return await data_controller.get_data_info(settings)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    """Upload data file with manual validation and chunked storage."""
    
    # validate the file properties using shared instance
    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)
    
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )
    
    # Get project path and ensure it exists using shared instance
    project_dir_path = project_controller.get_project_path(project_id=project_id)
    project_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique file path exactly as required
    file_id, file_path = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )
    
    # Save file in chunks for memory efficiency using aiofiles
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error while uploading file {file.filename} to project {project_id}: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )
        
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.FILE_VALIDATED_SUCCESS.value,
            "message": "File uploaded successfully in chunks",
            "file_id": file_id,
            "file_path": str(file_path),
            "original_name": file.filename,
            "file_size": os.path.getsize(file_path)
        }
    )

@data_router.post("/process/{project_id}")
async def process_data(project_id: str, request: ProcessRequest):
    """Process uploaded data using file_id."""
    
    # Instantiate the process controller for the specific project
    process_controller = ProcessController(project_id)
    
    # Process the file
    is_success, process_message, chunks = process_controller.process_file(
        file_id=request.file_id,
        chunk_size=request.chunk_size,
        overlap_size=request.overlap_size,
        do_reset=request.do_reset
    )
    
    if not is_success:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_FAILED.value,
                "message": process_message
            }
        )
    
    # Format chunks as requested (page_content, metadata, type: "Document")
    formatted_chunks = [
        {
            "page_content": chunk.page_content,
            "metadata": chunk.metadata,
            "type": "Document"
        }
        for chunk in chunks
    ]
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=formatted_chunks
    )
