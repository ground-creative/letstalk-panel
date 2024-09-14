from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from flask import current_app as app
import os, shutil, docx, pdfplumber, docxtpl


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text


def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def extract_text_from_doc(doc_path):
    doc = docxtpl.DocxTemplate(doc_path)
    text = doc.render(context={})
    return text


def get_file_extension(filename):
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower()


def build_vector_store(workspace_id, assistant_id, docs, embeddings):

    documents_folder = f"{app.config.get('KNOWLEDGE_BASE_PATH')}/{workspace_id}"
    combined_text = ""
    for doc_name in docs:
        app.logger.debug(f"Combining knowledge base file {doc_name}")
        file_extension = get_file_extension(doc_name)

        if file_extension == ".pdf":
            combined_text += (
                extract_text_from_pdf(f"{documents_folder}/{doc_name}") + "\n"
            )
        elif file_extension == ".doc":
            combined_text += (
                extract_text_from_doc(f"{documents_folder}/{doc_name}") + "\n"
            )
        elif file_extension == ".docx":
            combined_text += (
                extract_text_from_docx(f"{documents_folder}/{doc_name}") + "\n"
            )
        elif file_extension == ".txt":
            with open(f"{documents_folder}/{doc_name}", "r") as file:
                combined_text += file.read() + "\n"
        else:
            error = f"Unsupported file type: {file_extension}"
            app.logger.error(error)
            raise Exception(error)

    text_splitter = RecursiveCharacterTextSplitter()
    text_chunks = text_splitter.split_text(combined_text)
    vector = FAISS.from_texts(text_chunks, embeddings)
    vector_store_folder = f"{app.config.get('VECTOR_STORE_PATH')}/{workspace_id}"
    vector_store_subfolder_path = f"{vector_store_folder}/{assistant_id}"
    store_path = f"{vector_store_subfolder_path}/knowledge_base"
    app.logger.debug(f"Building vector store: {store_path}")
    os.makedirs(f"{vector_store_folder}", exist_ok=True)
    os.makedirs(f"{vector_store_subfolder_path}", exist_ok=True)
    os.makedirs(store_path, exist_ok=True)
    vector.save_local(store_path)
    return store_path


def get_vector_store_path(workspace_id, assistant_id):

    return f"{app.config.get('VECTOR_STORE_PATH')}/{workspace_id}/{assistant_id}"


def delete_vector_store(workspace_id, assistant_id):

    vector_store_folder = get_vector_store_path(workspace_id, assistant_id)

    if os.path.exists(vector_store_folder):
        shutil.rmtree(vector_store_folder)
        app.logger.debug(f"Deleted vector store: {vector_store_folder}")
        return True

    return False


def get_vector_store(workspace_id, assistant_id, embeddings):

    vector_store_folder = (
        f"{get_vector_store_path(workspace_id, assistant_id)}/knowledge_base"
    )
    vector_store = FAISS.load_local(
        vector_store_folder,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    retrieve_tool = create_retriever_tool(
        vector_store.as_retriever(),
        name="knowledge_base",
        description="This is the knowledge_base tool, use it to find relevant information.",
    )
    return retrieve_tool
