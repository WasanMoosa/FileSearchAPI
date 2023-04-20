from fastapi import FastAPI, UploadFile
from typing import List
import tempfile
import os
from services.File_service import *

app = FastAPI()

@app.post("/uploadfile")
async def create_upload_files(files: List[UploadFile]):
    for file in files:
        # Save uploaded file to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Upload PDF to Firebase object storage, save record in MySQL, and extract sentences from PDF
        upload_pdf_and_save_record(temp_file_path)

        # Delete temporary file
        os.remove(temp_file_path)
        
    return "done successfully"



@app.get("/files")
async def get_list_file():

 return get_record_files()


@app.get('/downloadfile')
async def download_pdf_file(id: str):
  pdf_data = download_file(id)
  return pdf_data


@app.get("/parsedSentence")
async def get_sentences(id: str):

 return get_parsed_sentences(id)
 
@app.get('/occurrence') 
async def get_word_occurrence(word: str, id: str):
  
  return get_num_word(word, id)

@app.get('/topwords')
async def get_top_words(id: str):
  
  return top_words(id)

# @app.get('/pdf/page')
# async def get_pdf_page(id: str, page_num: int):

#  return pdf_image(id, page_num)

@app.delete('/pdf')
async def delete_pdf(id: str):

  return delete_pdfFile(id)


@app.get('/pdf/search')
async def search_pdf_files(keyword: str):
  return search_keyword(keyword)