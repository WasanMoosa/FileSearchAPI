from fastapi import HTTPException, Response
import firebase_admin
from firebase_admin import credentials, storage
import mysql.connector
import PyPDF2
import os
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords


# Initialize Firebase
cred = credentials.Certificate("ServiceAccount.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'dbforfiles.appspot.com'
})
bucket = storage.bucket()


# Initialize MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user= "root",
    password='Wsn93989814',
    database='filetest'
)
cursor = db.cursor()


def upload_pdf_and_save_record(file_path):
    
    
    try:
        cursor = db.cursor()
        db.commit()
        # name for file
        file_name = file_path.split('\\')[-1]

        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)
            file_size = os.path.getsize(file_path)

        # Extract sentences from PDF
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in range(len(pdf_reader.pages)):

                # Extract text and put it in lower case
                page_text = pdf_reader.pages[page].extract_text().lower()
                sentences = re.split(r'(?<=[.!?])\s+', page_text)

        # Start transaction
        db.start_transaction()
        
        # Upload PDF to Firebase object storage
        blob = bucket.blob(file_name)
        blob.upload_from_filename(file_path)

        # ID, time of upload, number of pages, and size of file
        upload_time = blob.time_created
        file_id = file_name

        # Save records in MySQL
        sql = "INSERT INTO pdf_files (id, upload_time, num_pages, file_size) VALUES (%s, %s, %s, %s)"
        val = (file_id, upload_time, num_pages, file_size)
        cursor.execute(sql, val)

        # Save sentences in db
        for sentence in sentences:
            sql = "INSERT INTO pdf_sentences (file_id, sentence) VALUES (%s, %s)"
            val = (file_id, sentence.strip())
            cursor.execute(sql, val)
        
        # commit transaction
        db.commit()

        # Close the database connection
        cursor.close()
        db.close()

       
    except Exception as e:
        print(f"Error occurred while uploading PDF and saving record: {str(e)}")
   

# Get list of files, their id, time of upload, number of pages, and size of file
def get_record_files():
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM pdf_files")
        results = cursor.fetchall()
        print(results)
        hash_map = {}
        for row in results:
            print(row)
            name, upload_time, num_pages, file_size = row
            hash_map[name] = {'time': upload_time, 'pages': num_pages, 'size KB': file_size/100 }

        # Close the database connection
        cursor.close()
        db.close()
        return hash_map
    
    except Exception as e:
        print(f"Error occurred: {e}")



# Retrieve a stored PDF given the ID
def download_file(id):

    try:
        # Retrieve PDF file from Firebase Storage
        blob = bucket.blob(id)

        # Check if the file exists
        if not blob.exists():
            raise HTTPException(status_code=404, detail='File not found')

        # Download the file to a BytesIO object
        data = blob.download_as_bytes()

        # Return the file data as a binary response
        return Response(content=data, media_type='application/pdf')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


   
# Retrieve all parsed sentences for a given file name
def get_parsed_sentences(fileID):
    try:
        cursor = db.cursor()

        # Select all rows where the filename matches the provided id
        cursor.execute(f"SELECT * FROM pdf_sentences WHERE file_id ='%{fileID}%'")
        hash_map = {}

        # Retrieve the results and extract the sentences from each row
        for num, row in enumerate(cursor.fetchall()):
            sentence = row[1].replace("\n", " ")  # the sentence is stored in the second column of the row
            hash_map[num] = sentence

        # Close the database connection
        cursor.close()
        db.close()

        return hash_map
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# Check the occurrence of a word in PDF
def get_num_word(word: str, id: str):
    try:
        cursor=db.cursor()
        # Define MySQL query to get sentences from PDF file
        query = 'SELECT sentence FROM pdf_sentences WHERE file_id = %s'

        # Execute MySQL query to get sentences from PDF file
        cursor.execute(query, (id,))
        sentences = [row[0].replace("\n"," ") for row in cursor.fetchall()]

        # Check occurrence of word in sentences
        num_occurrences = 0
        matching_sentences = []
        for sentence in sentences:
            occurrences_in_sentence = sentence.count(word)
            if occurrences_in_sentence > 0:
                num_occurrences += occurrences_in_sentence
                matching_sentences.append(sentence)

        # Close the database connection
        cursor.close()
        db.close()

        # Return results
        return {
         'total_occurrences': num_occurrences,
         'matching_sentences': matching_sentences
        }
    except Exception as e:
        print(f"An error occurred: {str(e)}")


# Give the top 5 occurring words in a PDF 
def top_words(file_name: str):
    try:
        cursor = db.cursor()

        # Define MySQL query to get sentences from PDF file
        query = 'SELECT sentence FROM pdf_sentences WHERE file_id = %s'

        # Download the stop word list
        nltk.download('stopwords')

        # Define the stop words to exclude
        STOP_WORDS = set(stopwords.words('english'))

        # Execute MySQL query to get sentences from PDF file
        cursor.execute(query, (file_name,))
        sentences = [row[0].replace("\n", " ") for row in cursor.fetchall()]

        # Combine sentences into a single string
        text = ' '.join(sentences)
        print(text)

        # Split text into words, filter out stop words, and count occurrences of each word
        words = text.split()
        words=[word for word in words if word not in STOP_WORDS]
        word_counts = Counter(words)

        # Get top 5 occurring words and their counts
        top_words = word_counts.most_common(5)

        # Close the database connection
        cursor.close()
        db.close()

        # Return results
        return {
            'file_name': file_name,
            'top_words': top_words
        }
    except Exception as e:
        print(f"An error occurred while trying to retrieve the top words: {e}")
        return None

    

# Delete a PDF file and all its related data by PDF ID
def delete_pdfFile(id: str):
    try:
        cursor = db.cursor()

        # Begin transaction
        db.start_transaction()

        # Delete PDF file from Firebase Storage
        blob = storage.bucket().blob(id)
        if not blob.exists():
            raise HTTPException(status_code=404, detail='File not found')
        blob.delete()

        # Delete record from pdf_files table
        delete_pdf_file_query = "DELETE FROM pdf_files WHERE name = %s"
        cursor.execute(delete_pdf_file_query, (id,))

        # Delete records from file_sentences table
        delete_file_sentences_query = "DELETE FROM pdf_sentences WHERE file_name = %s"
        cursor.execute(delete_file_sentences_query, (id,))
        db.commit()

         # Close the database connection
        cursor.close()
        db.close()

        # Return success message
        return {'message': f'PDF file with ID {id} was deleted successfully'}

    except Exception as e:
        # Rollback transaction in case of error
        db.rollback()
        # Close the database connection
        cursor.close()
        db.close()
        # Raise HTTP exception with error message
        raise HTTPException(status_code=500, detail=str(e))




def search_keyword(keyword: str):
    # Select all files containing the keyword in their parsed sentences
    query = f"SELECT file_id, sentence FROM pdf_sentences WHERE sentence LIKE '%{keyword}%'"
    cursor.execute(query)
    results = cursor.fetchall()

    # Get unique IDs of files containing the keyword
    file_ids = list(set([result[0] for result in results]))

    # Get the sentences containing the keyword for each file ID
    file_sentences = {}
    for file_id in file_ids:
        sentences = [result[1] for result in results if result[0] == file_id]
        file_sentences[file_id] = sentences

    return {'file_ids': file_ids, 'file_sentences': file_sentences}
