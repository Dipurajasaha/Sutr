import fitz     # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

#####################################################################################
# -- extracts text from PDF and chunks it --
#####################################################################################
def process_pdf(file_path: str) -> list[dict]:

    # Using 'with' ensures the document is safely closed from memory after reading
    with fitz.open(file_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"

    # -- chunking logic --
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_text(full_text)

    return [{"text": chunk, "start_time": None, "end_time": None} for chunk in chunks]