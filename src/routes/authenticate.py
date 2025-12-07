from fastapi import FastAPI , APIRouter, Depends
import os
from helpers.config import get_settings, Settings
from fastapi import FastAPI , APIRouter, Depends, UploadFile, status, Request, File
from fastapi.responses import JSONResponse
from controllers import ImageController, EmbeddingController
import aiofiles
import logging
from models.enums.ResponseSignal import ResponseSignal
from models import ClientDataModel
from models.db_schemes import Client
logger = logging.getLogger('uvicorn.error')

authenticate_router =  APIRouter(
    prefix="/api/v1/authenticate",
    tags=["api_v1", "authenticate"],
)


@authenticate_router.post("/authenticate")
async def authenticate_client(request: Request, image1: UploadFile):
    image_controller = ImageController()
    
    numpy_image = image_controller.read_frame(file=image1)
    
    if numpy_image is None:
        logger.error("reading camera frame failed")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"response signal" : ResponseSignal.CAMERA_FRAME_READ_FAIL.value})
    
    #now we have image
    face_model_client = request.app.face_model_client
    vector_db_client = request.app.vector_db_client
    
    embedding_controller = EmbeddingController(vector_db_client=vector_db_client,
                                               embedding_client=face_model_client)
    
    vector = embedding_controller.get_frame_query_embeddeing(image=numpy_image)
    
    if vector == None:
        logger.error("error in embedding camera frame")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"response signal" : ResponseSignal.IMAGE_EMBEDDING_FAIL.value})
        
    # now we have a vector---> search database
    records = embedding_controller.search_data_base(vector=vector)
    if records != None:
        print(100*"#")
        record = records[0]
        
    score = record.score
    meta_data =  record.meta_data
    
    if score >= 0.40:
        return JSONResponse(content={"repsonse signal" : ResponseSignal.CLEINT_AUTHENTICATION_SUCCEED.value,
                                 "Client ID": meta_data['client_id'],
                                 "Client_name": meta_data["client_name"]})
    
    return JSONResponse(content={"repsonse signal" : ResponseSignal.CLEINT_AUTHENTICATION_FAIL.value})
    
    
    
    
        
    
    
    