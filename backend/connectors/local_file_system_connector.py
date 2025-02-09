import os
import requests
import itertools
from langchain.schema import Document
from bs4 import BeautifulSoup
from typing import List, Optional, Generator, Tuple, Iterator
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
import sys
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from openai import OpenAI
from langchain.prompts import PromptTemplate
import concurrent.futures
import tabula
import pandas as pd
from io import StringIO
import numpy as np
from tqdm import tqdm
import pdfplumber
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from util.envutils import EnvUtils
from connectors.data_connector_base import DataSourceConnector
class LocalFileSystemConnector(DataSourceConnector):
    def __init__(self):
        # Load environment variables
        self.env_utils = EnvUtils()
        # Initialize Pinecone
        self.pinecone_api_key = self.env_utils.get_required_env("PINECONE_API_KEY")
        self.openai_api_key = self.env_utils.get_required_env("OPENAI_API_KEY")
        self.index_name = self.env_utils.get_required_env("PINECONE_INDEX")
        if not all([self.pinecone_api_key, self.index_name]):
            raise ValueError("Missing required environment variables")
        # Initialize embedding model
        self.embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
        self.langchain_embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        # Get or create index
        self.index = self.pc.Index(self.index_name)
        
        # Initialize text splitter with streaming optimized settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            length_function=len
        )
        self.vectorstore = PineconeVectorStore(
            index=self.index,
            embedding=self.langchain_embeddings,
            text_key="text"
        )
    
    def process_chunk_batch(self, chunks: List[Document], file_path: str, start_idx: int = 0) -> None:
        """
        Process a batch of chunks and upload to Pinecone.
        """
        vectors = []
        for i, chunk in enumerate(chunks):
            # Skip empty chunks
            if not chunk.page_content.strip():
                continue
                
            try:
                embedding = self.embedding_model.encode(chunk.page_content)
                
                metadata = {
                    'text': chunk.page_content,
                    'source': file_path,
                    'chunk_id': start_idx + i
                }
                
                if hasattr(chunk, 'metadata'):
                    metadata.update(chunk.metadata)
                
                vectors.append((
                    f"{os.path.basename(file_path)}_{start_idx + i}",
                    embedding.tolist(),
                    metadata
                ))
            except Exception as e:
                print(f"Warning: Error processing chunk {i}: {str(e)}")
                continue
        
        if vectors:
            try:
                self.index.upsert(vectors=vectors)
            except Exception as e:
                print(f"Warning: Error upserting vectors to Pinecone: {str(e)}")

    def stream_pdf_pages(self, file_path: str) -> Iterator[Document]:
        """
        Stream pages from a PDF file one at a time using pdfplumber.
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    try:
                        # Extract text with better encoding handling
                        text = page.extract_text(x_tolerance=2, y_tolerance=2)
                        if text and text.strip():  # Only yield if there's actual content
                            yield Document(
                                page_content=text,
                                metadata={
                                    'source': file_path,
                                    'page': page_num + 1
                                }
                            )
                    except Exception as e:
                        print(f"Warning: Error extracting text from page {page_num + 1}: {str(e)}")
                        continue
                        
        except Exception as e:
            print(f"Error opening PDF {file_path}: {str(e)}")
            return

    def stream_text_file(self, file_path: str, chunk_size: int = 4096) -> Iterator[Document]:
        """
        Stream content from a text file in chunks.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                chunk_num = 0
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                        
                    if chunk.strip():  # Only yield if there's actual content
                        yield Document(
                            page_content=chunk,
                            metadata={
                                'source': file_path,
                                'chunk_num': chunk_num
                            }
                        )
                    chunk_num += 1
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    chunk_num = 0
                    while True:
                        chunk = file.read(chunk_size)
                        if not chunk:
                            break
                            
                        if chunk.strip():
                            yield Document(
                                page_content=chunk,
                                metadata={
                                    'source': file_path,
                                    'chunk_num': chunk_num
                                }
                            )
                        chunk_num += 1
            except Exception as e:
                print(f"Error reading text file {file_path}: {str(e)}")
                return

    def extract_tables_from_pdf(self, file_path: str) -> Iterator[Document]:
        """
        Extract and stream tables from PDF using pdfplumber.
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        tables = page.extract_tables()
                        
                        for table_idx, table in enumerate(tables):
                            if not table:  # Skip empty tables
                                continue
                                
                            # Convert table to DataFrame and then to string
                            df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
                            table_str = df.to_string(index=False)
                            
                            if table_str.strip():  # Only yield if there's actual content
                                yield Document(
                                    page_content=f"Table {table_idx+1} on Page {page_num+1}:\n{table_str}",
                                    metadata={
                                        'source': file_path,
                                        'type': 'table',
                                        'page': page_num + 1,
                                        'table_index': table_idx
                                    }
                                )
                                
                    except Exception as e:
                        print(f"Warning: Error extracting tables from page {page_num + 1}: {str(e)}")
                        continue
                        
        except Exception as e:
            print(f"Warning: Error extracting tables from PDF: {str(e)}")

    def stream_process_documents(self, document_iterator: Iterator[Document], file_path: str,
                               batch_size: int = 10) -> None:
        """
        Stream process documents in small batches.
        """
        current_batch = []
        chunk_idx = 0
        
        with tqdm(desc="Processing documents") as pbar:
            for doc in document_iterator:
                try:
                    # Split document into chunks
                    chunks = self.text_splitter.split_documents([doc])
                    
                    for chunk in chunks:
                        if chunk.page_content.strip():  # Only process non-empty chunks
                            current_batch.append(chunk)
                            
                            # Process batch if it reaches the desired size
                            if len(current_batch) >= batch_size:
                                self.process_chunk_batch(current_batch, file_path, chunk_idx)
                                chunk_idx += len(current_batch)
                                current_batch = []
                                pbar.update(1)
                                
                except Exception as e:
                    print(f"Warning: Error processing document: {str(e)}")
                    continue
        
        # Process any remaining chunks
        if current_batch:
            self.process_chunk_batch(current_batch, file_path, chunk_idx)
            pbar.update(1)

    def load_from_local(self, file_path: str) -> None:
        """
        Load and chunk a document from local storage, then store in Pinecone.
        """
        print(f"Loading document from {file_path}")
        
        if file_path.endswith('.pdf'):
            # Create iterators for both content and tables
            content_iterator = self.stream_pdf_pages(file_path)
            table_iterator = self.extract_tables_from_pdf(file_path)
            
            # Combine iterators
            document_iterator = itertools.chain(content_iterator, table_iterator)
            
        elif file_path.endswith('.txt'):
            document_iterator = self.stream_text_file(file_path)
        else:
            raise ValueError("Unsupported file type. Only PDF and TXT files are supported.")
        
        # Process documents in streaming fashion
        self.stream_process_documents(document_iterator, file_path)
        
        print(f"Document {file_path} loaded and stored in Pinecone.")

    def load_data(self, json_data: dict):
        data_id = json_data['data_id']
        self.load_from_local(data_id)