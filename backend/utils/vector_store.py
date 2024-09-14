from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from flask import current_app as app
import os, shutil


def build_vector_store(workspace_id, assistant_id, docs, embeddings):

    documents_folder = f"{app.config.get('KNOWLEDGE_BASE_PATH')}/{workspace_id}"

    # Combine text content from all documents
    combined_text = ""
    for doc_name in docs:
        app.logger.debug(f"Combining knowledge base file {doc_name}")
        with open(f"{documents_folder}/{doc_name}", "r") as file:
            combined_text += file.read() + "\n"

    # Split text and create vector store
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

    # Save vector store
    vector.save_local(store_path)

    return store_path


def get_vector_store_path(workspace_id, assistant_id):

    return f"{app.config.get('VECTOR_STORE_PATH')}/{workspace_id}/{assistant_id}"


def delete_vector_store(workspace_id, assistant_id):

    vector_store_folder = get_vector_store_path(workspace_id, assistant_id)
    app.logger.debug(f"Deleting vector store: {vector_store_folder}")

    if os.path.exists(vector_store_folder):
        shutil.rmtree(vector_store_folder)
        # app.logger.debug(f"Deleted vector store folder: {vector_store_folder}")
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
