from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, HTTPException, Request
from fastapi.responses import JSONResponse
import os
import aiofiles
import logging
from src.helpers.config import get_settings, Settings
from src.controllers import DataController, ProjectController, ProcessController
from src.models.response_models import MessageResponse, FileUploadResponse
from src.models import ProjectRepository, AssetModel, ChunkRepository
from src.models.db_schemas import Asset, Chunk
from src.models.enums import ResponseSignal
from src.routes.schemas import ProcessRequest
import shutil

logger = logging.getLogger(__name__)

# Instantiate controllers
data_ctrl = DataController()
project_ctrl = ProjectController()

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.get("/info", response_model=MessageResponse)
async def data_info(settings: Settings = Depends(get_settings)):
    """Data info route from the controller."""
    return await data_ctrl.get_data_info(settings)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    """Upload data file with manual validation and chunked storage."""
    
    # Get project repository and ensure project exists in DB
    project_repo = await ProjectRepository.create(request.app.db)
    project = await project_repo.get_project_or_create_one(project_id)
    
    # validate the file properties using shared instance
    is_valid, result_signal = data_ctrl.validate_uploaded_file(file=file)
    
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )
    
    # Get project path and ensure it exists using shared instance
    project_dir_path = project_ctrl.get_project_path(project_id=project_id)
    project_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique file path exactly as required
    file_id, file_path = data_ctrl.generate_unique_filepath(
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
        
    # --- Integration: Save to Assets Collection ---
    try:
        asset_model = await AssetModel.create_instance(request.app.db)
        asset_size = os.path.getsize(file_path)
        
        logger.info(f"Accepted upload request: {file.filename} ({asset_size} bytes) for Project: {project_id}")
        
        new_asset = Asset(
            asset_project_id=project.id,
            asset_name=file.filename,
            asset_type=file.content_type,
            asset_size=asset_size,
            asset_path=str(file_path),
            asset_config={}
        )
        
        created_asset = await asset_model.create_asset(new_asset)
        logger.info(f"Asset registered in DB: {created_asset.asset_uuid} | Project: {project_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                "message": "File uploaded and registered successfully",
                "asset_id": str(created_asset.id),
                "asset_uuid": created_asset.asset_uuid,
                "project_id": project_id,
                "file_path": str(file_path),
                "original_name": file.filename,
                "file_size": asset_size
            }
        )
    except Exception as e:
        logger.error(f"Failed to register asset in database: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.DATABASE_ERROR.value,
                "message": "File uploaded but database registration failed"
            }
        )

@data_router.post("/process/{project_id}")
async def process_data(request: Request, project_id: str, request_data: ProcessRequest):
    """Process uploaded data using file_id or all project assets."""
    
    # 0. Handle Reset Logic (Project-wide)
    if request_data.do_reset == 1:
        chunk_repo = await ChunkRepository.create(request.app.db)
        deleted_count = await chunk_repo.delete_project_chunks(project_id)
        logger.info(f"Reset triggered for project {project_id}: Deleted {deleted_count} old chunks.")
    
    # Instantiate the process controller for the specific project
    process_controller = ProcessController(
        project_id, 
        request.app.embedding_client, 
        request.app.vectordb_client
    )
    all_chunks = []
    processed_files = []
    
    # 1. Determine which assets to process
    asset_model = await AssetModel.create_instance(request.app.db)
    project_assets = await asset_model.get_project_assets(project_id)

    if request_data.file_id:
        # Process specific file
        target_asset = None
        for asset in project_assets:
            unique_name = os.path.basename(asset.asset_path)
            if request_data.file_id in (str(asset.id), asset.asset_uuid, asset.asset_name, unique_name):
                target_asset = asset
                break
        assets_to_process = [target_asset] if target_asset else []
    else:
        # Batch process: Get all assets for this project from DB
        assets_to_process = project_assets
        
    if not assets_to_process:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_EMPTY.value,
                "message": "No files found to process for this project. Please upload files first."
            }
        )
        
    # 2. Process each asset in the list
    logger.info(f"Starting batch processing loop for {len(assets_to_process)} assets...")
    project_repo = await ProjectRepository.create(request.app.db)
    project = await project_repo.get_project_or_create_one(project_id)
    chunk_repo = await ChunkRepository.create(request.app.db)

    for asset in assets_to_process:
        unique_filename = os.path.basename(asset.asset_path)
        is_success, process_message, chunks = await process_controller.process_file(
            file_id=unique_filename,
            chunk_size=request_data.chunk_size,
            overlap_size=request_data.overlap_size,
            do_reset=request_data.do_reset
        )
        
        if is_success:
            # Map langchain Document chunks to database Chunk objects
            chunk_objects = [
                Chunk(
                    chunk_project_id=project.id,
                    chunk_asset_id=asset.id,
                    file_id=asset.asset_name,
                    chunk_order=idx + 1,
                    chunk_text=doc.page_content,
                    chunk_metadata=doc.metadata
                )
                for idx, doc in enumerate(chunks)
            ]
            
            # Save chunks to DB
            if chunk_objects:
                inserted = await chunk_repo.insert_many_chunks(chunk_objects)
                if inserted:
                    logger.info(f"Saved {len(chunk_objects)} chunks to database for asset: {asset.asset_name}")
                else:
                    logger.error(f"Failed to save chunks to database for asset: {asset.asset_name}")
            
            all_chunks.extend(chunks)
            processed_files.append(asset.asset_name)
        else:
            logger.warning(f"Skipping file {asset.asset_name}: {process_message}")


    if not all_chunks:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_EMPTY_RESULT.value,
                "message": "Failed to extract any chunks from the found files."
            }
        )
    
    # 3. Format chunks as requested (page_content, metadata, type: "Document")
    formatted_chunks = [
        {
            "page_content": chunk.page_content,
            "metadata": chunk.metadata,
            "type": "Document"
        }
        for chunk in all_chunks
    ]
    
    logger.info(f"Batch processing complete: {len(processed_files)} files converted into {len(all_chunks)} total chunks.")
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=formatted_chunks
    )
