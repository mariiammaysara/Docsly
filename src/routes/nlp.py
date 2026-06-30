from fastapi import APIRouter, status, Request, Depends
from fastapi.responses import JSONResponse
from src.routes.schemas.nlp import PushRequest, SearchRequest
from src.models import ProjectRepository, ChunkRepository
from src.controllers.nlp_controller import NLPController
from src.models.enums.response import ResponseSignal
from src.tasks.data_indexing import index_data_content
from src.helpers.dependencies import get_vector_db, get_generation_client, get_embedding_client, get_template_parser
import logging

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(
    request: Request,
    project_id: str,
    push_request: PushRequest,
    vectordb_client=Depends(get_vector_db),
    generation_client=Depends(get_generation_client),
    embedding_client=Depends(get_embedding_client),
    template_parser=Depends(get_template_parser),
):
    """
    Triggers the indexing process. 
    Synchronous version for testing to ensure collection is created.
    """
    from src.controllers.process_controller import ProcessController
    
    project_repo = await ProjectRepository.create(db_client=request.app.db)
    project = await project_repo.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=vectordb_client,
        generation_client=generation_client,
        embedding_client=embedding_client,
        template_parser=template_parser,
    )

    # For testing: run indexing immediately
    # 1. Get all chunks for the project from DB
    chunk_repo = await ChunkRepository.create(db_client=request.app.db)
    chunks = await chunk_repo.get_project_chunks(project_id=project.id)
    
    if chunks:
        await nlp_controller.index_into_vector_db(
            project=project,
            chunks=chunks,
            chunks_ids=[str(c.id) for c in chunks],
            do_reset=bool(push_request.do_reset)
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.DATA_PUSH_TASK_READY.value,
            "msg": "Indexing completed synchronously for testing."
        }
    )

@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(
    request: Request,
    project_id: str,
    vectordb_client=Depends(get_vector_db),
    generation_client=Depends(get_generation_client),
    embedding_client=Depends(get_embedding_client),
    template_parser=Depends(get_template_parser),
):
    """
    Retrieves information about the project's vector collection.
    """
    project_repo = await ProjectRepository.create(
        db_client=request.app.db
    )

    project = await project_repo.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(
        vectordb_client=vectordb_client,
        generation_client=generation_client,
        embedding_client=embedding_client,
        template_parser=template_parser,
    )

    collection_info = await nlp_controller.get_vector_db_collection_info(project=project)

    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info
        }
    )

@nlp_router.post("/index/search/{project_id}")
async def search_index(
    request: Request,
    project_id: str,
    search_request: SearchRequest,
    vectordb_client=Depends(get_vector_db),
    generation_client=Depends(get_generation_client),
    embedding_client=Depends(get_embedding_client),
    template_parser=Depends(get_template_parser),
):
    """
    Performs semantic search within the project's vectors.
    """
    project_repo = await ProjectRepository.create(
        db_client=request.app.db
    )

    project = await project_repo.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(
        vectordb_client=vectordb_client,
        generation_client=generation_client,
        embedding_client=embedding_client,
        template_parser=template_parser,
    )

    results = await nlp_controller.search_vector_db_collection(
        project=project, text=search_request.text, limit=search_request.limit
    )

    if not results:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value
                }
            )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "results": [ result.model_dump() for result in results ]
        }
    )

@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(
    request: Request,
    project_id: str,
    search_request: SearchRequest,
    vectordb_client=Depends(get_vector_db),
    generation_client=Depends(get_generation_client),
    embedding_client=Depends(get_embedding_client),
    template_parser=Depends(get_template_parser),
):
    """
    Full RAG implementation: Retrieves context and generates an answer using LLM.
    """
    project_repo = await ProjectRepository.create(
        db_client=request.app.db
    )

    project = await project_repo.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(
        vectordb_client=vectordb_client,
        generation_client=generation_client,
        embedding_client=embedding_client,
        template_parser=template_parser,
    )

    answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
        project=project,
        query=search_request.text,
        limit=search_request.limit,
    )

    if not answer:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.RAG_ANSWER_ERROR.value
                }
        )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        }
    )
