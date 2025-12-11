from fastapi import FastAPI , APIRouter, Depends
import os
from helpers.config import get_settings, Settings
from fastapi import FastAPI , APIRouter, Depends, UploadFile, status, Request, File, Form
from fastapi.responses import JSONResponse
from controllers import ClientController, ImageController, EmbeddingController
import aiofiles
import logging
from models.enums.ResponseSignal import ResponseSignal
from models import ClientDataModel
from models.db_schemes import Client
logger = logging.getLogger('uvicorn.error')

client_router =  APIRouter(
    prefix="/api/v1/client",
    tags=["api_v1", "client"],
)


@client_router.post("/register_client")
async def register_client(
    request: Request, image1: UploadFile = File(...), client_name: str = Form(...), client_id: str = Form(...), app_settings = Depends(get_settings)):
    
    db_client = request.app.mongo_db
    
    image_controller = ImageController()
    
    is_valid, result_message = image_controller.validate_image(file=image1)
    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"repsonse signal" : result_message})
    
    #all images are vaild
    image_path, unique_fileID = image_controller.generate_unique_file_path(original_file_name=image1.filename,client_id=client_id)
    
    
    client_data_model = await ClientDataModel.initialize_client_model(db_client=db_client)
    
    try:
        client_record = await client_data_model.create_client(client= Client(client_name= client_name,
                                                                   client_id= client_id,
                                                                   client_image_path= image_path) )
    except Exception as e:
        logger.error(f'Client database insersion error: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"response signal" : ResponseSignal.CLIENT_ADD_FAIL.value})
        
    
    try:
        async with aiofiles.open(image_path, 'wb') as f:
            while chunk := await image1.read(app_settings.IMAGE_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f'Client image upload error: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"response signal" : ResponseSignal.IMAGE_READ_FAIL.value})
    
    
    
    return JSONResponse(content={"repsonse signal" : ResponseSignal.CLIENT_ADD_SUCCESS.value,
                                 "Client ID": str(client_record.id)})
    

@client_router.post("/proccess_client_image/{client_id}")
async def proccess_client_image(
    request: Request, client_id: str, app_settings = Depends(get_settings)):
    
    db_client = request.app.mongo_db
    face_model_client = request.app.face_model_client
    vector_db_client = request.app.vector_db_client
    
    client_data_model = await ClientDataModel.initialize_client_model(db_client=db_client)
    
    client =  await client_data_model.get_client_by_client_id(client_id=client_id)
    
    if client == None:
        #logger.error(f'no client with such and id')
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={"response signal" : ResponseSignal.NO_CLIENT_WITH_SUCH_ID.value})
    
    image_path = client.client_image_path
    embedding_controller = EmbeddingController(vector_db_client=vector_db_client,
                                               embedding_client=face_model_client)
    
    
    #meta_data = client.model_dump()
    meta_data = {"client_id" : client.client_id,
                 "client_image_path": client.client_image_path,
                 "client_name":client.client_name}
    return_val = embedding_controller.push_image_to_vector_db(image_path=image_path,
                                                              meta_data=meta_data)
    
    if return_val == None:
        logger.error(f'Client image embedding error')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"response signal" : ResponseSignal.IMAGE_EMBEDDING_FAIL.value})
        
    return JSONResponse(content={"repsonse signal" : ResponseSignal.IMAGE_ADDED_TO_VECTOR_DB_SUCCESS.value})