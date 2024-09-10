import os
import glob
import re
import logging
import time
import pickle
from typing import List, Dict, Tuple
from PyPDF2 import PdfReader
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    CSVLoader, EverNoteLoader, TextLoader, UnstructuredWordDocumentLoader,
    UnstructuredEPubLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader,
    UnstructuredODTLoader, UnstructuredPowerPointLoader,
)
from llama_cpp import Llama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaginatedPDFLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        reader = PdfReader(self.file_path)
        documents = []
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            documents.append(Document(page_content=text, metadata={"page_num": page_num + 1, "file_name": os.path.basename(self.file_path)}))
        return documents

class Rag:
    LOADER_MAPPING: Dict[str, Tuple[type, Dict]] = {
        ".csv": (CSVLoader, {}),
        ".doc": (UnstructuredWordDocumentLoader, {}),
        ".docx": (UnstructuredWordDocumentLoader, {}),
        ".enex": (EverNoteLoader, {}),
        ".epub": (UnstructuredEPubLoader, {}),
        ".html": (UnstructuredHTMLLoader, {}),
        ".md": (UnstructuredMarkdownLoader, {}),
        ".odt": (UnstructuredODTLoader, {}),
        ".pdf": (PaginatedPDFLoader, {}),
        ".ppt": (UnstructuredPowerPointLoader, {}),
        ".pptx": (UnstructuredPowerPointLoader, {}),
        ".txt": (TextLoader, {"encoding": "utf8"}),
    }

    def __init__(self, model: Llama, prompt: List[Dict], socket):
        self.model = model
        self.prompt = prompt
        self.socket = socket
        self.source_dir = 'rag'
        self.llm_context = 8192
        self.max_tokens = int(0.5 * self.llm_context)
        self.vectorstore_path = "chroma_db"
        self.index_path = "document_index.pkl"
        
        # Load existing index or initialize new
        self.document_index = self.load_index()
        
        # Load and process documents
        self.docs = self.load_documents(self.source_dir)
        self.setup_vectorstore()
        if self.is_new_documents():
            self.index_documents()
            self.save_index()

        self.prepare_chat_history()
        self.emitir_respuesta()

    def load_documents(self, source_dir: str) -> List[Document]:
        all_files = [f for ext in self.LOADER_MAPPING for f in glob.glob(os.path.join(source_dir, f"**/*{ext}"), recursive=True)]
        documents = []
        for file_path in all_files:
            try:
                documents.extend(self.load_single_document(file_path))
            except Exception as e:
                logger.error(f"Error loading document {file_path}: {e}")
        return documents

    def load_single_document(self, file_path: str) -> List[Document]:
        ext = os.path.splitext(file_path)[-1].lower()
        if ext in self.LOADER_MAPPING:
            loader_class, loader_args = self.LOADER_MAPPING[ext]
            loader = loader_class(file_path, **loader_args)
            return loader.load()
        else:
            raise ValueError(f"Unsupported file extension '{ext}'")

    def setup_vectorstore(self):
        logger.debug("Inicializando el vectorstore...")
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=1024
        )
        all_splits = text_splitter.split_documents(self.docs)
        model_name = "all-MiniLM-L6-v2.gguf2.f16.gguf"
        gpt4all_kwargs = {'allow_download': 'True'}
        embeddings = GPT4AllEmbeddings(
            model_name=model_name,
            gpt4all_kwargs=gpt4all_kwargs,
            device="cuda"
        )
        self.vectorstore = Chroma.from_documents(
            documents=all_splits,
            collection_name="rag-chroma",
            embedding=embeddings,
            persist_directory=self.vectorstore_path,
        )
        self.retriever = self.vectorstore.as_retriever()
        logger.debug("Vectorstore inicializado correctamente.")

    def index_documents(self):
        self.document_index = {}
        for doc in self.docs:
            file_name = doc.metadata["file_name"]
            page_num = doc.metadata["page_num"]
            if file_name not in self.document_index:
                self.document_index[file_name] = {}
            self.document_index[file_name][page_num] = doc.page_content

        # Generate summary for each document
        self.document_summaries = {}
        for file_name, pages in self.document_index.items():
            content = " ".join(pages.values())
            summary = self.summarize_content(content)
            self.document_summaries[file_name] = summary

    def summarize_content(self, content: str) -> str:
        chunks = [content[i:i + self.max_tokens] for i in range(0, len(content), self.max_tokens)]
        summaries = []
        for chunk in chunks:
            summary = self.model.create_chat_completion(
                messages=[{"role": "user", "content": f"Resume el siguiente contenido: {chunk}"}],
                max_tokens=200
            )
            summaries.append(summary["choices"][0]["message"]["content"])
        return " ".join(summaries)

    def prepare_chat_history(self):

        question = self.prompt[-1]['content']
        match = re.search(r'página (\d+)', question, re.IGNORECASE)
        if match:
            page_num = int(match.group(1))
            file_name_match = re.search(r'(?:en|del|de|documento|pdf) ([^\.]+\.pdf)', question, re.IGNORECASE)
            if file_name_match:
                file_name = file_name_match.group(1).strip()
                docs = [doc for doc in self.docs if doc.metadata.get("page_num") == page_num and doc.metadata.get("file_name") == file_name]
            else:
                docs = [doc for doc in self.docs if doc.metadata.get("page_num") == page_num]
        else:
            docs = self.vectorstore.similarity_search(question.lower(), k=10)
        
        docs = self.truncate_docs(docs, self.max_tokens)
        doc_txt = self.format_docs(docs)
        
        system_message = f"""Tu trabajo es encontrar los textos relevantes en los documentos para generar una respuesta.
        Aquí están los documentos recuperados: \n\n {doc_txt} \n\n
        Aquí está la pregunta del usuario: {question}\n"""

        self.chat_history = [{"role": "system", "content": system_message}]

    def truncate_docs(self, docs: List[Document], max_tokens: int) -> List[Document]:
        truncated_docs = []
        total_tokens = 0
        for doc in docs:
            doc_tokens = len(doc.page_content.split())
            if total_tokens + doc_tokens > max_tokens:
                remaining_tokens = max_tokens - total_tokens
                truncated_content = ' '.join(doc.page_content.split()[:remaining_tokens])
                truncated_docs.append(Document(page_content=truncated_content, metadata=doc.metadata))
                break
            truncated_docs.append(doc)
            total_tokens += doc_tokens
        return truncated_docs

    def format_docs(self, docs: List[Document]) -> str:
        return "\n\n".join(f"{doc.metadata['file_name']} - página {doc.metadata.get('page_num', 'N/A')}\n{doc.page_content.lower()}" for doc in docs)
   
    def emitir_respuesta(self):
        response_completa = ''
        for chunk in self.model.create_chat_completion(messages=self.chat_history, max_tokens=10000, stream=True):
            if 'content' in chunk['choices'][0]['delta']:
                fragmento_response = chunk['choices'][0]['delta']['content']
                response_completa += fragmento_response
                self.socket.emit('assistant_response', {'content': chunk}, namespace='/test')
                time.sleep(0.01)

    def load_index(self) -> Dict:
        if os.path.exists(self.index_path):
            with open(self.index_path, 'rb') as f:
                return pickle.load(f)
        return {}

    def save_index(self):
        with open(self.index_path, 'wb') as f:
            pickle.dump(self.document_index, f)

    def is_new_documents(self) -> bool:
        current_files = [os.path.basename(f) for ext in self.LOADER_MAPPING for f in glob.glob(os.path.join(self.source_dir, f"**/*{ext}"), recursive=True)]
        indexed_files = set(self.document_index.keys())
        return not indexed_files.issubset(set(current_files))
