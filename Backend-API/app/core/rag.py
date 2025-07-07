"""
@Author: Borja Otero Ferreira
RAG - Retrieval Augmented Generation implementation
Migración completa desde Rag.py legacy manteniendo el flujo original
"""
import os
import glob
import re
import logging
import time
import pickle
import hashlib
import shutil
from typing import List, Dict, Tuple, Set, Any

from PyPDF2 import PdfReader
from llama_cpp import Llama
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    CSVLoader, EverNoteLoader, TextLoader, UnstructuredWordDocumentLoader,
    UnstructuredEPubLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader,
    UnstructuredODTLoader, UnstructuredPowerPointLoader,
)

from app.utils.logger import logger




class DocumentHasher:
    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute a hash of the document content for deduplication."""
        return hashlib.md5(content.encode()).hexdigest()


class DocumentStore:
    def __init__(self, index_path: str):
        self.index_path = index_path
        
        # Verificar y migrar el índice de documento_index.pkl en raíz si existe
        legacy_index_path = "document_index.pkl"
        if os.path.exists(legacy_index_path) and not os.path.exists(self.index_path):
            print(f"⚠️ Encontrado índice legacy en raíz, migrando a {self.index_path}")
            logger.info(f"Encontrado índice legacy en raíz, migrando a {self.index_path}")
            # Crear directorio si no existe
            parent_dir = os.path.dirname(self.index_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            # Copiar el archivo
            try:
                shutil.copy2(legacy_index_path, self.index_path)
                print("✅ Migración del índice completada con éxito")
                logger.info("Migración del índice completada con éxito")
            except Exception as e:
                print(f"❌ Error al migrar el índice: {e}")
                logger.error(f"Error al migrar el índice: {e}")
        
        self.document_index = self.load_index()
        self.document_hashes: Set[str] = {
            DocumentHasher.compute_hash(page["content"])
            for pages in self.document_index.values()
            for page in pages.values()
        }
        print(f"🔍 Document store inicializado con {len(self.document_hashes)} fragmentos de documentos")
        logger.info(f"Document store inicializado con {len(self.document_hashes)} fragmentos de documentos")
        self.document_summaries = {}

    def load_index(self) -> Dict:
        if os.path.exists(self.index_path):
            try:
                print(f"📂 Cargando índice de documentos desde: {self.index_path}")
                logger.info(f"Cargando índice de documentos desde: {self.index_path}")
                with open(self.index_path, 'rb') as f:
                    index_data = pickle.load(f)
                print(f"✅ Índice cargado con éxito: {len(index_data)} documentos")
                logger.info(f"Índice cargado con éxito: {len(index_data)} documentos")
                return index_data
            except (pickle.PickleError, EOFError) as e:
                print(f"❌ Error al cargar el índice de documentos: {e}")
                print(f"❌ Creando un nuevo índice vacío")
                logger.error(f"Error al cargar el índice de documentos: {e}")
                return {}
        else:
            parent_dir = os.path.dirname(self.index_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                print(f"📁 Directorio creado para el índice de documentos: {parent_dir}")
                logger.info(f"Directorio creado para el índice de documentos: {parent_dir}")
            print(f"⚠️ No se encontró el archivo de índice en: {self.index_path}")
            print(f"⚠️ Creando un nuevo índice vacío")
            logger.warning(f"No se encontró el archivo de índice en: {self.index_path}")
            return {}

    def save_index(self):
        """Guardar índice de documentos con manejo mejorado de errores"""
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(self.index_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                logger.info(f"Directorio creado para guardar índice: {parent_dir}")
            
            # Guardar primero a un archivo temporal
            temp_path = f"{self.index_path}.tmp"
            with open(temp_path, 'wb') as f:
                pickle.dump(self.document_index, f)
            
            # Renombrar para una escritura atómica
            if os.path.exists(self.index_path):
                os.replace(temp_path, self.index_path)
            else:
                os.rename(temp_path, self.index_path)
            
            num_docs = len(self.document_index)
            print(f"💾 Índice guardado con éxito en {self.index_path} ({num_docs} documentos)")
            logger.info(f"Índice guardado con éxito en {self.index_path} ({num_docs} documentos)")
            
            # Verificar tamaño del archivo para debugging
            file_size = os.path.getsize(self.index_path)
            logger.info(f"Tamaño del archivo de índice: {file_size} bytes")
            
            return True
        except Exception as e:
            print(f"❌ Error al guardar el índice: {e}")
            logger.error(f"❌ Error al guardar el índice: {e}")
            return False

    def is_duplicate(self, content: str) -> bool:
        """Check if document content already exists in the store."""
        return DocumentHasher.compute_hash(content) in self.document_hashes

    def add_document(self, file_name: str, page_num: int, content: str, metadata: Dict):
        """Add a document to the store if it's not a duplicate."""
        content_hash = DocumentHasher.compute_hash(content)
        if content_hash not in self.document_hashes:
            if file_name not in self.document_index:
                self.document_index[file_name] = {}
            self.document_index[file_name][page_num] = {"content": content, "metadata": metadata}
            self.document_hashes.add(content_hash)
            return True
        return False


class PaginatedPDFLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        reader = PdfReader(self.file_path)
        documents = []
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            documents.append(Document(
                page_content=text,
                metadata={
                    "page_num": page_num + 1,
                    "file_name": os.path.basename(self.file_path),
                    "file_path": self.file_path
                }
            ))
        return documents


class Retriever:
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
        """
        Initialize the Retriever for RAG.
        
        Args:
            model: The LLM model to use
            prompt: List of chat messages
            socket: Socket connection for sending responses
        """
        self.model = model
        self.prompt = prompt
        self.socket = socket
        self.source_dir = 'documents'
        self.llm_context = 8192
        self.max_tokens = int(0.5 * self.llm_context)
        self.vectorstore_path = "chroma_db"
        
        # Importar aquí para evitar dependencia circular
        from app.core.socket_handler import SocketResponseHandler
        # Usar la clase directamente para métodos estáticos
        self.socket_handler = SocketResponseHandler
        
        logger.info("🔍 RAG Retriever initialized - Usando RAG exclusivamente para la respuesta")
        print("🔍 RAG Retriever initialized - Usando RAG exclusivamente para la respuesta")
        print(f"🔍 DEBUG: Socket recibido: {type(self.socket)}")
        logger.info(f"🔍 DEBUG: Socket recibido: {type(self.socket)}")
        
        # Test inicial del socket
        try:
            logger.info("🔍 Probando conectividad del socket...")
            print("🔍 Probando conectividad del socket...")
            self.socket_handler.emit_console_output(self.socket, "RAG inicializado correctamente", "info")
        except Exception as socket_test_error:
            logger.error(f"❌ Error en test inicial del socket: {socket_test_error}")
            print(f"❌ Error en test inicial del socket: {socket_test_error}")
        
        # Initialize document store in chroma_db directory
        # Ensure the directory exists
        os.makedirs(self.vectorstore_path, exist_ok=True)
        document_index_path = os.path.join(self.vectorstore_path, "document_index.pkl")
        self.doc_store = DocumentStore(document_index_path)
        logger.info(f"🔍 Document store inicializado desde {self.doc_store.index_path}")
        print(f"🔍 Document store inicializado desde {self.doc_store.index_path}")
        
        try:
            # Load and process documents
            logger.info("🔍 Cargando documentos...")
            print("🔍 Cargando documentos...")
            self.docs = self.load_documents(self.source_dir)
            logger.info(f"🔍 {len(self.docs)} documentos cargados")
            print(f"🔍 {len(self.docs)} documentos cargados")
            
            logger.info("🔍 Configurando vectorstore...")
            print("🔍 Configurando vectorstore...")
            self.setup_vectorstore()
            
            if self.is_new_documents():
                logger.info("🔍 Indexando documentos nuevos...")
                print("🔍 Indexando documentos nuevos...")
                self.index_documents()
                self.doc_store.save_index()
                logger.info("🔍 Indexación completada")
                print("🔍 Indexación completada")

            logger.info("🔍 Preparando historial de chat para RAG...")
            print("🔍 Preparando historial de chat para RAG...")
            self.prepare_chat_history()
            logger.info("🔍 Generando respuesta RAG...")
            print("🔍 Generando respuesta RAG...")
            self.emitir_respuesta()
        except Exception as e:
            logger.error(f"Error in RAG processing: {e}")
            # Usar SocketResponseHandler para enviar error
            self.socket_handler.emit_rag_error(
                self.socket, 
                f"Error procesando documentos en RAG: {str(e)}"
            )

    def load_documents(self, source_dir: str) -> List[Document]:
        """Load documents with deduplication."""
        logger.info(f"Loading documents from {source_dir}")
        
        if not os.path.exists(source_dir):
            logger.warning(f"Directory {source_dir} does not exist. Creating it.")
            os.makedirs(source_dir)
            return []
        
        # Check if directory is empty
        files_in_dir = os.listdir(source_dir)
        logger.info(f"🔍 DEBUG: Files in {source_dir}: {files_in_dir}")
            
        all_files = (
            f for ext in self.LOADER_MAPPING 
            for f in glob.glob(os.path.join(source_dir, f"**/*{ext}"), recursive=True)
        )
        
        all_files_list = list(all_files)
        logger.info(f"🔍 DEBUG: Found {len(all_files_list)} document files: {all_files_list}")
        
        documents = []
        for file_path in all_files_list:
            try:
                logger.info(f"🔍 DEBUG: Loading file: {file_path}")
                loaded_docs = self.load_single_document(file_path)
                logger.info(f"🔍 DEBUG: Loaded {len(loaded_docs)} documents from {file_path}")
                # Only add non-duplicate documents
                for doc in loaded_docs:
                    if not self.doc_store.is_duplicate(doc.page_content):
                        documents.append(doc)
                        self.doc_store.add_document(
                            doc.metadata["file_name"],
                            doc.metadata["page_num"],
                            doc.page_content,
                            doc.metadata
                        )
                # Free memory after processing each file
                del loaded_docs
            except Exception as e:
                logger.error(f"Error loading document {file_path}: {e}")
                
        logger.info(f"Loaded {len(documents)} documents")
        return documents

    def load_single_document(self, file_path: str) -> List[Document]:
        """Load a single document using the appropriate loader."""
        ext = os.path.splitext(file_path)[-1].lower()
        if ext in self.LOADER_MAPPING:
            loader_class, loader_args = self.LOADER_MAPPING[ext]
            loader = loader_class(file_path, **loader_args)
            return loader.load()
        else:
            raise ValueError(f"Unsupported file extension '{ext}'")

    def setup_vectorstore(self):
        """Initialize the vector store with embeddings."""
        logger.info("Initializing vector store")
        
        if not self.docs:
            logger.warning("No documents to index. Creating empty vector store.")
            # Initialize empty vectorstore
            embeddings = GPT4AllEmbeddings(
                model_name="all-MiniLM-L6-v2.gguf2.f16.gguf",
                gpt4all_kwargs={'allow_download': 'True'},
                device="cuda"
            )
            self.vectorstore = Chroma(
                collection_name="rag-chroma",
                embedding_function=embeddings,
                persist_directory=self.vectorstore_path,
            )
            self.retriever = self.vectorstore.as_retriever()
            return
            
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=1024
        )
        all_splits = text_splitter.split_documents(self.docs)
        
        # Free memory after splitting documents
        del self.docs
        
        # Initialize embeddings
        model_name = "all-MiniLM-L6-v2.gguf2.f16.gguf"
        embeddings = GPT4AllEmbeddings(
            model_name=model_name,
            gpt4all_kwargs={'allow_download': 'True'},
            device="cuda"
        )
        
        # Create vectorstore with error handling
        try:
            self.vectorstore = Chroma.from_documents(
                documents=all_splits,
                collection_name="rag-chroma",
                embedding=embeddings,
                persist_directory=self.vectorstore_path,
            )
            self.retriever = self.vectorstore.as_retriever()
            logger.info("Vector store initialized successfully")
        except RuntimeError as e:
            if "Cannot open header file" in str(e):
                logger.warning(f"ChromaDB corrupted, recreating database at {self.vectorstore_path}")
                # Remove corrupted database
                if os.path.exists(self.vectorstore_path):
                    shutil.rmtree(self.vectorstore_path)
                # Recreate vectorstore
                self.vectorstore = Chroma.from_documents(
                    documents=all_splits,
                    collection_name="rag-chroma",
                    embedding=embeddings,
                    persist_directory=self.vectorstore_path,
                )
                self.retriever = self.vectorstore.as_retriever()
                logger.info("Vector store recreated successfully")
            else:
                raise

    def is_new_documents(self) -> bool:
        """Check if new documents need to be indexed."""
        return True  # Simplified for now, always reindex

    def index_documents(self):
        """Index documents (placeholder)."""
        logger.info("Indexing documents")
        # Nothing to do here, indexing is done in setup_vectorstore

    def prepare_chat_history(self):
        """Prepare chat history for RAG (identical to legacy)."""
        logger.info("🔍 Preparando historial de chat para RAG")
        print("🔍 Preparando historial de chat para RAG")
        
        question = self.prompt[-1]['content']
        
        logger.info(f"🔍 Pregunta RAG: {question}")
        print(f"🔍 Pregunta RAG: {question}")
        
        # Mejorar la detección de referencias a páginas y documentos (like legacy)
        page_match = re.search(r'página (\d+)', question, re.IGNORECASE)
        file_match = re.search(r'(?:en|del|de|documento|pdf) ([^\.]+\.pdf)', question, re.IGNORECASE)
        
        if page_match and file_match:
            page_num = int(page_match.group(1))
            file_name = file_match.group(1).strip()
            
            logger.info(f"🔍 Referencia explícita detectada: documento '{file_name}', página {page_num}")
            print(f"🔍 Referencia explícita detectada: documento '{file_name}', página {page_num}")
            
            # Buscar específicamente en la página solicitada
            content = self.get_page_content(file_name, page_num)
            if content != "Página no encontrada":
                # Si hay una consulta específica, buscar en la página
                query_terms = re.sub(r'página \d+|(?:en|del|de|documento|pdf) [^\.]+\.pdf', '', question).strip()
                if query_terms:
                    logger.info(f"🔍 Buscando términos específicos: '{query_terms}' en {file_name}, página {page_num}")
                    print(f"🔍 Buscando términos específicos: '{query_terms}' en {file_name}, página {page_num}")
                    content = self.search_in_page(file_name, page_num, query_terms)
                
                from langchain.docstore.document import Document
                doc = Document(
                    page_content=content,
                    metadata={"file_name": file_name, "page_num": page_num}
                )
                docs = [doc]
                
                logger.info(f"🔍 Usando contenido específico de página: {len(content)} caracteres")
                print(f"🔍 Usando contenido específico de página: {len(content)} caracteres")
            else:
                logger.warning(f"🔍 No se encontró la página {page_num} en el documento {file_name}, realizando búsqueda de similitud")
                print(f"🔍 No se encontró la página {page_num} en el documento {file_name}, realizando búsqueda de similitud")
                docs = self.vectorstore.similarity_search(question.lower(), k=10)
        elif file_match:
            file_name = file_match.group(1).strip()
            
            logger.info(f"🔍 Referencia a documento detectada: '{file_name}'")
            print(f"🔍 Referencia a documento detectada: '{file_name}'")
            
            query_terms = re.sub(r'(?:en|del|de|documento|pdf) [^\.]+\.pdf', '', question).strip()
            if query_terms:
                logger.info(f"🔍 Buscando términos específicos: '{query_terms}' en todo el documento {file_name}")
                print(f"🔍 Buscando términos específicos: '{query_terms}' en todo el documento {file_name}")
                
                search_results = self.search_in_document(file_name, query_terms)
                from langchain.docstore.document import Document
                docs = [
                    Document(page_content=content, metadata={"file_name": file_name, "page_num": page_num})
                    for page_num, content in search_results.items()
                ]
                
                logger.info(f"🔍 Encontradas {len(search_results)} páginas con coincidencias")
                print(f"🔍 Encontradas {len(search_results)} páginas con coincidencias")
            else:
                logger.info(f"🔍 No hay términos específicos, realizando búsqueda de similitud en {file_name}")
                print(f"🔍 No hay términos específicos, realizando búsqueda de similitud en {file_name}")
                docs = self.vectorstore.similarity_search(question.lower(), k=10)
        else:
            logger.info("🔍 No se detectaron referencias a documentos específicos, realizando búsqueda de similitud general")
            print("🔍 No se detectaron referencias a documentos específicos, realizando búsqueda de similitud general")
            docs = self.vectorstore.similarity_search(question.lower(), k=10)
        
        logger.info(f"🔍 Se encontraron {len(docs)} documentos relevantes")
        print(f"🔍 Se encontraron {len(docs)} documentos relevantes")
        
        # Check if the documents fit into the context
        if self.fits_in_context(docs):
            logger.info("🔍 Los documentos caben en el contexto sin truncar")
            print("🔍 Los documentos caben en el contexto sin truncar")
            doc_txt = self.format_docs(docs)
        else:
            # Perform similarity search if documents don't fit in context
            logger.info("🔍 Los documentos exceden el tamaño del contexto, truncando")
            print("🔍 Los documentos exceden el tamaño del contexto, truncando")
            docs = self.truncate_docs(docs, self.max_tokens)
            doc_txt = self.format_docs(docs)
            logger.info(f"🔍 Documentos truncados a {len(docs)}")
            print(f"🔍 Documentos truncados a {len(docs)}")
        
        logger.info(f"🔍 Longitud del texto de documentos: {len(doc_txt)} caracteres")
        print(f"🔍 Longitud del texto de documentos: {len(doc_txt)} caracteres")
        
        # Mostrar una vista previa del contexto que se enviará al modelo
        preview = doc_txt[:200] + "..." if len(doc_txt) > 200 else doc_txt
        logger.info(f"🔍 Vista previa del contexto: {preview}")
        print(f"🔍 Vista previa del contexto: {preview}")
        
        # Construir el mensaje del sistema para el modelo
        system_message = f"""Eres un asistente de IA especializado en búsqueda de información en documentos. 
        
        IMPORTANTE: Debes SOLO utilizar la información que se encuentra en los siguientes fragmentos de documentos para responder a la pregunta. 
        NO utilices conocimientos generales ni información externa.
        
        Si la información NO está en los fragmentos proporcionados, responde claramente: 
        "Lo siento, no encuentro información sobre esto en los documentos disponibles."
        
        No menciones que estás utilizando fragmentos ni hables sobre el formato de tu respuesta.
        No pidas información adicional.
        No inventes información.
        
        Documentos: \n\n {doc_txt} \n\n
        
        Pregunta: {question}\n"""

        self.chat_history = [{"role": "system", "content": system_message}]
        
        # Añadir un mensaje del usuario con la pregunta para asegurar que el modelo responde a ella
        prompt_with_instruction = f"Por favor, responde a mi pregunta basándote ÚNICAMENTE en los documentos proporcionados: {question}"
        self.chat_history.append({"role": "user", "content": prompt_with_instruction})
        
        logger.info(f"🔍 Historial de chat creado con mensaje del sistema de {len(system_message)} caracteres")
        print(f"🔍 Historial de chat creado con mensaje del sistema de {len(system_message)} caracteres")
        
        logger.info(f"🔍 DEBUG: Chat history created with system message length: {len(system_message)}")
        
        # Free memory after preparing chat history
        del docs

    def get_page_content(self, file_name: str, page_num: int) -> str:
        """Obtiene el contenido de una página específica de un documento """
        if file_name in self.doc_store.document_index:
            if page_num in self.doc_store.document_index[file_name]:
                return self.doc_store.document_index[file_name][page_num]["content"]
        return "Página no encontrada"

    def search_in_page(self, file_name: str, page_num: int, query: str) -> str:
        """Busca un término específico en una página particular """
        content = self.get_page_content(file_name, page_num)
        if content != "Página no encontrada":
            # Realizar búsqueda de similitud en el contenido de la página
            return self.perform_similarity_search(content, query)
        return "Página no encontrada"

    def perform_similarity_search(self, content: str, query: str) -> str:
        """Realiza una búsqueda de similitud en un contenido específico"""
        # Crear un documento temporal para la búsqueda
        from langchain.docstore.document import Document
        temp_doc = Document(page_content=content)
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=1024
        )
        splits = text_splitter.split_documents([temp_doc])
        
        # Crear una colección temporal en el vectorstore
        temp_vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.vectorstore._embedding_function,
            collection_name="temp_search"
        )
        
        # Realizar búsqueda
        results = temp_vectorstore.similarity_search(query, k=1)
        
        # Limpiar la colección temporal
        temp_vectorstore = None
        
        return results[0].page_content if results else "No se encontraron resultados relevantes"

    def search_in_document(self, file_name: str, query: str) -> Dict[int, str]:
        """Busca un término específico en todas las páginas de un documento """
        if file_name in self.doc_store.document_index:
            results = {}
            for page_num, page_data in self.doc_store.document_index[file_name].items():
                content = page_data["content"]
                if query.lower() in content.lower():
                    results[page_num] = content
            return results
        return {"error": "Documento no encontrado"}

    def fits_in_context(self, docs: List[Document]) -> bool:
        """Check if the documents fit into the context size"""
        total_tokens = sum(len(doc.page_content.split()) for doc in docs)
        return total_tokens <= self.max_tokens

    def truncate_docs(self, docs: List[Document], max_tokens: int) -> List[Document]:
        """Truncate documents to fit in context """
        truncated_docs = []
        total_tokens = 0
        for doc in docs:
            doc_tokens = len(doc.page_content.split())
            if total_tokens + doc_tokens > max_tokens:
                remaining_tokens = max_tokens - total_tokens
                truncated_content = ' '.join(
                    doc.page_content.split()[:remaining_tokens]
                )
                truncated_docs.append(
                    Document(
                        page_content=truncated_content, 
                        metadata=doc.metadata
                    )
                )
                break
            truncated_docs.append(doc)
            total_tokens += doc_tokens
        return truncated_docs

    def format_docs(self, docs: List[Document]) -> str:
        """Format documents for display """
        return "\n\n".join(
            f"{doc.metadata['file_name']} - página {doc.metadata.get('page_num', 'N/A')}\n{doc.page_content.lower()}" 
            for doc in docs
        )

    def emitir_respuesta(self):
        """Generate and emit RAG response."""
        response_completa = ''
        total_tokens = 0
        
        try:
            logger.info("🔍 Generando respuesta RAG exclusivamente (sin modelo base)")
            print("🔍 Generando respuesta RAG exclusivamente (sin modelo base)")
            
            # Use chat_history instead of rag_messages (like legacy)
            if not hasattr(self, 'chat_history') or not self.chat_history:
                logger.error("No chat history to process")
                print("❌ Error: No hay historial de chat para procesar en RAG")
                # Socket directo como en legacy
                self.socket.emit('assistant_response', {
                    'content': "Error: No se pudo procesar la consulta RAG.",
                    'finished': True,
                    'error': True
                }, namespace='/test')
                return
            
            logger.info(f"🔍 Enviando prompt al modelo con {len(self.chat_history[0]['content'])} caracteres")
            print(f"🔍 Enviando prompt al modelo con {len(self.chat_history[0]['content'])} caracteres")
            
            # Stream exactly like legacy - chunk by chunk manually con socket directo
            for chunk in self.model.create_chat_completion(
                messages=self.chat_history,
                max_tokens=10000,
                stream=True
            ):
                if 'content' in chunk['choices'][0]['delta']:
                    fragmento_response = chunk['choices'][0]['delta']['content']
                    response_completa += fragmento_response
                    total_tokens += 1
                    
                    # Emit EXACTO como legacy - socket directo
                    self.socket.emit(
                        'assistant_response',
                        {'content': fragmento_response},
                        namespace='/test'
                    )
                    
                    import time
                    time.sleep(0.01)
            
            logger.info(f"🔍 Respuesta RAG completada con éxito - {total_tokens} tokens generados")
            print(f"🔍 Respuesta RAG completada con éxito - {total_tokens} tokens generados")
            
            # Send finalization signal EXACTO como legacy - socket directo
            # Calcular tokens del usuario con manejo de excepciones
            try:
                user_tokens = len(' '.join([msg['content'] for msg in self.prompt if 'content' in msg]).split())
            except Exception:
                user_tokens = 0
                logger.warning("⚠️ Error al calcular tokens del usuario, usando 0")
            
            self.socket.emit('assistant_response', {
                'content': '',
                'total_user_tokens': user_tokens,
                'total_assistant_tokens': total_tokens,
                'finished': True
            }, namespace='/test')
            
            logger.info("🔍 Señal de finalización enviada")
            print("🔍 Señal de finalización enviada")
            
        except Exception as e:
            logger.error(f"❌ Error en RAG response: {e}")
            print(f"❌ Error en RAG response: {e}")
            # Enviar error EXACTO como legacy - socket directo
            self.socket.emit('assistant_response', {
                'content': f"Error en RAG: {str(e)}",
                'finished': True,
                'error': True
            }, namespace='/test')

    def search_in_document(self, file_name: str, query: str) -> Dict[int, str]:
        """Busca en todo un documento """
        if file_name in self.doc_store.document_index:
            results = {}
            for page_num, page_data in self.doc_store.document_index[file_name].items():
                content = page_data["content"]
                if query.lower() in content.lower():
                    results[page_num] = content
            return results
        return {}

    def fits_in_context(self, docs: List[Document]) -> bool:
        """Check if documents fit in context """
        total_length = sum(len(doc.page_content) for doc in docs)
        return total_length <= self.max_tokens * 4  # Rough estimate

    def format_docs(self, docs: List[Document]) -> str:
        """Format documents for context with improved structure."""
        formatted_docs = []
        
        for i, doc in enumerate(docs, 1):
            filename = doc.metadata.get('file_name', 'Documento sin nombre')
            page_num = doc.metadata.get('page_num', 'N/A')
            
            # Formato claro con separadores y numeración
            doc_header = f"--- DOCUMENTO {i}: {filename} (página {page_num}) ---"
            formatted_docs.append(f"{doc_header}\n{doc.page_content}")
        
        return "\n\n".join(formatted_docs)

    def truncate_docs(self, docs: List[Document], max_tokens: int) -> List[Document]:
        """Truncate documents to fit in context"""
        truncated = []
        total_length = 0
        for doc in docs:
            if total_length + len(doc.page_content) <= max_tokens * 4:
                truncated.append(doc)
                total_length += len(doc.page_content)
            else:
                break
        return truncated
