from fastapi import FastAPI , APIRouter, Depends
import os
from helpers.config import get_settings, Settings
from fastapi import FastAPI , APIRouter, Depends, UploadFile, status, Request, File
from fastapi.responses import JSONResponse
from controllers import ClientController, ImageController
import aiofiles
import logging
from models.enums.ResponseSignal import ResponseSignal
from models import ClientDataModel
from models.db_schemes.client import Client
logger = logging.getLogger('uvicorn.error')

client_router =  APIRouter(
    prefix="/api/v1/client",
    tags=["api_v1", "client"],
)


@client_router.post("/register_client")
async def register_client(
    request: Request, client_name: str, client_id: str,
    image1: UploadFile, app_settings = Depends(get_settings)):
    
    db_client = request.app.mongo_db
    
    image_controller = ImageController()
    
    is_valid, result_message = image_controller.validate_image(file=image1)
    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"repsonse signal" : result_message})
    
    #all images are vaild
    image_path, unique_fileID = image_controller.generate_unique_file_path(original_file_name=image1.filename,client_id=client_id)
    
    try:
        async with aiofiles.open(image_path, 'wb') as f:
            while chunk := await image1.read(app_settings.IMAGE_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f'Client image upload error: {e}')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"response signal" : ResponseSignal.IMAGE_READ_FAIL.value})
    
    
    client_data_model = await ClientDataModel.initialize_client_model(db_client=db_client)
    
    client_record = await client_data_model.create_client(client= Client(client_name= client_name,
                                                                   client_id= client_id,
                                                                   client_image_path= image_path) )
    
    
    return JSONResponse(content={"repsonse signal" : ResponseSignal.CLIENT_ADD_SUCCESS.value,
                                 "Client ID": str(client_record.id)})