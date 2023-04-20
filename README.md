Usage guide for PDF management API
This API is designed to manage PDF files. It allows users to upload, store, and search for PDF files, as well as extract text from uploaded PDF files and search for specific words in the extracted text.

Prerequisites
I use MySQL DB locally with two tables called pdf_files and pdf_sentences.
database='filetest'

The pdf_files table have the following columns:

id - The unique ID of the PDF file.
upload_time - The time the PDF file was uploaded.
num_pages - The number of pages in the PDF file.
file_size - The size of the PDF file in bytes.

The pdf_sentences table should have the following columns:

pdf_files - The ID of the PDF file.
sentence - The extracted sentence from the PDF file.

----------------------------------------------------------
API Endpoints
-POST /uploadfile
-GET /files
-GET /downloadfile?id={id}
-GET /parsedSentence?id={id}
-GET /occurrence?word={word}&id={id}
-DELETE /pdf?id={id}
-GET /pdf/search?keyword={keyword}
-GET /topwords?id={id}
