import fitz     # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

##########################################################################
# Extract PDF Text
##########################################################################
def process_pdf(file_path: str) -> list[dict]:
    # -- open PDF and extract text from all pages --
    with fitz.open(file_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"

    # -- chunk text using RecursiveCharacterTextSplitter --
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_text(full_text)

    return [{"text": chunk, "start_time": None, "end_time": None} for chunk in chunks]