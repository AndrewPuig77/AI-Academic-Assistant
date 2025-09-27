"""
PDF Processing Module
Handles PDF text extraction, cleaning, and chunking for analysis
"""

import fitz  # PyMuPDF
import re
from typing import Dict, List, Tuple
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Handles PDF processing operations including text extraction,
    cleaning, and intelligent chunking for AI analysis.
    """
    
    def __init__(self, max_chunk_size: int = 4000):
        """
        Initialize PDF processor with configuration.
        
        Args:
            max_chunk_size: Maximum size for text chunks (in characters)
        """
        self.max_chunk_size = max_chunk_size
        
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract raw text from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as string
            
        Raises:
            Exception: If PDF cannot be processed
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
                
            doc.close()
            
            logger.info(f"Successfully extracted {len(text)} characters from {pdf_path}")
            return self.clean_text(text)
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace and newlines
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers patterns
        text = re.sub(r'Page \d+', '', text)
        text = re.sub(r'\d+\s*\n', '', text)
        
        # Fix common OCR issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        
        # Clean up references formatting
        text = re.sub(r'\[\d+\]', ' [REF] ', text)
        
        return text.strip()
    
    def extract_structured_content(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract structured content from research paper PDF.
        Attempts to identify sections like abstract, introduction, methods, etc.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with extracted sections
        """
        text = self.extract_text(pdf_path)
        
        # Common section patterns in academic papers
        section_patterns = {
            'abstract': r'abstract\s*[:.]?\s*\n(.*?)(?=\n\s*(?:introduction|keywords|1\.|i\.|background))',
            'introduction': r'introduction\s*[:.]?\s*\n(.*?)(?=\n\s*(?:methods|methodology|materials|2\.|ii\.|related work))',
            'methods': r'(?:methods|methodology|materials and methods)\s*[:.]?\s*\n(.*?)(?=\n\s*(?:results|findings|3\.|iii\.|experiments))',
            'results': r'(?:results|findings)\s*[:.]?\s*\n(.*?)(?=\n\s*(?:discussion|conclusion|4\.|iv\.|analysis))',
            'conclusion': r'(?:conclusion|conclusions|summary)\s*[:.]?\s*\n(.*?)(?=\n\s*(?:references|bibliography|acknowledgments))',
            'references': r'(?:references|bibliography)\s*[:.]?\s*\n(.*?)$'
        }
        
        extracted_sections = {'full_text': text}
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text.lower(), re.DOTALL | re.IGNORECASE)
            if match:
                section_text = match.group(1).strip()
                extracted_sections[section_name] = section_text[:2000]  # Limit section size
                logger.info(f"Extracted {section_name} section: {len(section_text)} characters")
            else:
                logger.warning(f"Could not find {section_name} section")
                
        return extracted_sections
    
    def chunk_text(self, text: str, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for processing long documents.
        
        Args:
            text: Text to chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find end of chunk
            end = start + self.max_chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to break at sentence boundary
            sentence_break = text.rfind('.', start, end)
            if sentence_break > start + self.max_chunk_size // 2:
                end = sentence_break + 1
            
            chunks.append(text[start:end])
            start = end - overlap
        
        logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract metadata from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with metadata
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            doc.close()
            
            # Clean and format metadata
            cleaned_metadata = {
                'title': metadata.get('title', 'Unknown Title'),
                'author': metadata.get('author', 'Unknown Author'),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', '')
            }
            
            return cleaned_metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {pdf_path}: {str(e)}")
            return {}
    
    def get_paper_statistics(self, pdf_path: str) -> Dict[str, int]:
        """
        Get basic statistics about the research paper.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with paper statistics
        """
        try:
            text = self.extract_text(pdf_path)
            doc = fitz.open(pdf_path)
            
            stats = {
                'page_count': len(doc),
                'character_count': len(text),
                'word_count': len(text.split()),
                'paragraph_count': len([p for p in text.split('\n\n') if p.strip()]),
                'reference_count': len(re.findall(r'\[REF\]', text)),
                'figure_mention_count': len(re.findall(r'(?:figure|fig\.)\s*\d+', text.lower())),
                'table_mention_count': len(re.findall(r'table\s*\d+', text.lower()))
            }
            
            doc.close()
            
            logger.info(f"Paper statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating statistics for {pdf_path}: {str(e)}")
            return {}

# Example usage and testing
if __name__ == "__main__":
    # Test the PDF processor
    processor = PDFProcessor()
    
    # This would be used for testing with actual PDF files
    # pdf_path = "sample_paper.pdf"
    # text = processor.extract_text(pdf_path)
    # sections = processor.extract_structured_content(pdf_path)
    # chunks = processor.chunk_text(text)
    # metadata = processor.extract_metadata(pdf_path)
    # stats = processor.get_paper_statistics(pdf_path)
    
    print("PDF Processor module loaded successfully!")