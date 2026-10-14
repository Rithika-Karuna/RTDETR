"""
RAG Document Processor — parses PDF, DOCX, CSV, JSON documents
into text chunks for the vector store.
"""
import os
import json
import csv
import re
from typing import Optional

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base")
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)


class DocumentProcessor:
    """Processes uploaded documents into text chunks for embedding."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_file(self, filepath: str) -> list:
        """
        Process a single file and return list of text chunks.
        Each chunk is a dict: {text, source, filepath, chunk_index, metadata}
        """
        ext = os.path.splitext(filepath)[1].lower()
        filename = os.path.basename(filepath)
        
        if ext == ".csv":
            return self._process_csv(filepath, filename)
        elif ext == ".json":
            return self._process_json(filepath, filename)
        elif ext == ".pdf":
            text = self._read_pdf(filepath)
        elif ext in (".docx", ".doc"):
            text = self._read_docx(filepath)
        elif ext in (".txt", ".md"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            print(f"[DocProcessor] Unsupported format: {ext}")
            return []
        
        if not text or not text.strip():
            return []
        
        chunks = self._chunk_text(text)
        return [
            {
                "text": chunk,
                "source": filename,
                "filepath": filepath,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "metadata": {
                    "source": filename,
                    "format": ext
                }
            }
            for i, chunk in enumerate(chunks)
        ]

    def _process_csv(self, filepath: str, filename: str) -> list:
        """Process CSV file into individual record chunks with preserved metadata."""
        chunks = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    row_clean = {k.strip(): v.strip() for k, v in row.items() if k and v}
                    if not row_clean:
                        continue
                    entry = " | ".join(f"{k}: {v}" for k, v in row_clean.items())
                    chunks.append({
                        "text": entry,
                        "source": filename,
                        "filepath": filepath,
                        "chunk_index": i,
                        "metadata": row_clean
                    })
        except Exception as e:
            print(f"[DocProcessor] Error reading CSV {filename}: {e}")
        return chunks

    def _process_json(self, filepath: str, filename: str) -> list:
        """Process JSON file into structured authority chunks."""
        chunks = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list):
                        items.extend(val)
                if not items:
                    items = [data]

            for i, item in enumerate(items):
                if isinstance(item, dict):
                    entry = " | ".join(f"{k}: {v}" for k, v in item.items() if v is not None)
                    chunks.append({
                        "text": entry,
                        "source": filename,
                        "filepath": filepath,
                        "chunk_index": i,
                        "metadata": item
                    })
                else:
                    chunks.append({
                        "text": str(item),
                        "source": filename,
                        "filepath": filepath,
                        "chunk_index": i,
                        "metadata": {"raw": str(item)}
                    })
        except Exception as e:
            print(f"[DocProcessor] Error reading JSON {filename}: {e}")
        return chunks
    
    def _read_pdf(self, filepath: str) -> str:
        """Read PDF file to text."""
        try:
            import PyPDF2
            text_parts = []
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            try:
                import pdfplumber
                text_parts = []
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                return "\n".join(text_parts)
            except ImportError:
                print("[DocProcessor] Install PyPDF2 or pdfplumber for PDF support: pip install PyPDF2")
                return ""
    
    def _read_docx(self, filepath: str) -> str:
        """Read DOCX file to text."""
        try:
            import docx
            doc = docx.Document(filepath)
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except ImportError:
            print("[DocProcessor] Install python-docx for DOCX support: pip install python-docx")
            return ""
    
    def _read_csv(self, filepath: str) -> str:
        """Read CSV file to text (each row as a formatted entry)."""
        text_parts = []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Format each row as key: value pairs
                entry = " | ".join(f"{k}: {v}" for k, v in row.items() if v and v.strip())
                if entry:
                    text_parts.append(entry)
        return "\n".join(text_parts)
    
    def _read_json(self, filepath: str) -> str:
        """Read JSON file to text."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # Array of objects — format each as text
            parts = []
            for item in data:
                if isinstance(item, dict):
                    entry = " | ".join(f"{k}: {v}" for k, v in item.items() if v)
                    parts.append(entry)
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        elif isinstance(data, dict):
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return str(data)
    
    def _chunk_text(self, text: str) -> list:
        """Split text into overlapping chunks."""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                for sep in ['. ', '.\n', '\n\n', '\n', '; ', ', ']:
                    last_sep = text.rfind(sep, start + self.chunk_size // 2, end)
                    if last_sep > start:
                        end = last_sep + len(sep)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def process_directory(self, directory: str = None) -> list:
        """Process all supported files in a directory."""
        dir_path = directory or KNOWLEDGE_DIR
        all_chunks = []
        
        supported = {".pdf", ".docx", ".doc", ".csv", ".json", ".txt", ".md"}
        
        for filename in os.listdir(dir_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported:
                filepath = os.path.join(dir_path, filename)
                chunks = self.process_file(filepath)
                all_chunks.extend(chunks)
                print(f"[DocProcessor] Processed {filename}: {len(chunks)} chunks")
        
        return all_chunks


# Singleton
document_processor = DocumentProcessor()
