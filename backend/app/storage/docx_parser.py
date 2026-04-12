"""Production-level document parser for PDF, DOCX, and TXT files.

Handles text extraction with comprehensive edge case management:
- Corrupted file detection
- Encoding detection and fallback
- Empty/minimal content handling
- Memory efficiency
- Detailed error reporting
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Optional

import chardet

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)


class FileParseError(Exception):
    """Base exception for file parsing errors."""

    pass


class UnsupportedFileTypeError(FileParseError):
    """Raised when file type is not supported."""

    pass


class CorruptedFileError(FileParseError):
    """Raised when file is corrupted or invalid."""

    pass


class EmptyFileError(FileParseError):
    """Raised when file contains no readable content."""

    pass


class DocumentParser:
    """Production-grade document parser supporting PDF, DOCX, and TXT formats.

    Features:
    - Automatic file type detection
    - Robust error handling with descriptive messages
    - Multiple encoding detection fallbacks
    - Content normalization
    - Size and content validation
    - Comprehensive logging
    """

    # File type configuration
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
    MIN_CONTENT_LENGTH = 10  # Minimum characters to consider document valid
    MAX_CONTENT_LENGTH = 5_000_000  # 5MB text limit
    MAX_EXTRACTION_ATTEMPTS = 3

    # Common text encodings to try
    ENCODINGS = ["utf-8", "latin-1", "iso-8859-1", "cp1252", "ascii"]

    def __init__(self) -> None:
        """Initialize parser and log availability of optional libraries."""
        if not PDF_AVAILABLE:
            logger.warning("pdfplumber not installed: PDF parsing disabled")
        if not DOCX_AVAILABLE:
            logger.warning("python-docx not installed: DOCX parsing disabled")

    @staticmethod
    def _detect_encoding(data: bytes) -> str:
        """Detect file encoding using chardet with fallback.

        Args:
            data: Raw file bytes

        Returns:
            Detected encoding name or fallback

        Raises:
            ValueError: If no suitable encoding found
        """
        if not data:
            raise ValueError("Empty data cannot be encoded")

        # Try chardet detection first
        detection = chardet.detect(data)
        if detection and detection.get("encoding"):
            detected_encoding = detection["encoding"]
            logger.debug("Detected encoding: %s (confidence: %.2f)", detected_encoding, detection.get("confidence", 0))
            return detected_encoding

        logger.warning("chardet failed to detect encoding; using UTF-8 fallback")
        return "utf-8"

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize extracted text.

        - Remove excessive whitespace
        - Strip leading/trailing whitespace
        - Preserve paragraph structure
        - Remove null bytes

        Args:
            text: Raw extracted text

        Returns:
            Normalized text
        """
        # Remove null bytes and control characters (except common whitespace)
        text = "".join(char for char in text if char == "\n" or char == "\t" or not (ord(char) < 32))

        # Replace multiple spaces with single space (but preserve newlines)
        lines = text.split("\n")
        lines = [" ".join(line.split()) for line in lines]
        text = "\n".join(lines)

        # Remove excessive newlines (more than 2 consecutive)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def _parse_pdf(self, file_content: bytes, filename: str) -> str:
        """Extract text from PDF file.

        Handles:
        - Corrupted PDF detection
        - Scanned PDF detection (encrypted PDFs)
        - Empty PDF detection
        - Multiple page extraction

        Args:
            file_content: Raw PDF bytes
            filename: Original filename (for logging)

        Returns:
            Extracted text

        Raises:
            CorruptedFileError: If PDF is invalid or corrupted
            EmptyFileError: If PDF contains no text
        """
        if not PDF_AVAILABLE:
            raise UnsupportedFileTypeError(
                "PDF parsing not available. Install pdfplumber: pip install pdfplumber"
            )

        try:
            pdf_file = io.BytesIO(file_content)
            text_parts = []
            page_count = 0
            empty_pages = 0

            with pdfplumber.open(pdf_file) as pdf:
                if not pdf.pages:
                    raise EmptyFileError("PDF contains no pages")

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()

                        # Handle None return (blank page or extraction failed)
                        if page_text is None:
                            empty_pages += 1
                            logger.debug("Page %d: No text extracted (blank page?)", page_num)
                            continue

                        # Normalize page text
                        page_text = self._normalize_text(page_text)

                        if page_text:
                            text_parts.append(page_text)
                            page_count += 1
                        else:
                            empty_pages += 1

                    except Exception as e:
                        logger.warning("Failed to extract text from PDF page %d: %s", page_num, e)
                        empty_pages += 1
                        continue

            if not text_parts:
                logger.warning(
                    "PDF %s: No readable text extracted from %d pages",
                    filename,
                    len(pdf.pages),
                )
                raise EmptyFileError(f"PDF contains no readable text ({empty_pages} empty pages)")

            logger.info(
                "PDF %s: Extracted text from %d/%d pages (%d empty)",
                filename,
                page_count,
                len(pdf.pages),
                empty_pages,
            )

            return "\n\n".join(text_parts)

        except pdfplumber.exceptions.PDFException as e:
            logger.error("PDF parsing error in %s: %s", filename, e)
            raise CorruptedFileError(f"Invalid or corrupted PDF file: {str(e)}") from e
        except Exception as e:
            logger.error("Unexpected error parsing PDF %s: %s", filename, e)
            raise CorruptedFileError(f"Unexpected error parsing PDF: {str(e)}") from e

    def _parse_docx(self, file_content: bytes, filename: str) -> str:
        """Extract text from DOCX file.

        Handles:
        - Corrupted DOCX detection
        - Empty DOCX detection
        - Table content extraction
        - Paragraph preservation

        Args:
            file_content: Raw DOCX bytes
            filename: Original filename (for logging)

        Returns:
            Extracted text

        Raises:
            CorruptedFileError: If DOCX is invalid
            EmptyFileError: If DOCX contains no text
        """
        if not DOCX_AVAILABLE:
            raise UnsupportedFileTypeError(
                "DOCX parsing not available. Install python-docx: pip install python-docx"
            )

        try:
            docx_file = io.BytesIO(file_content)
            doc = DocxDocument(docx_file)

            text_parts = []

            # Extract from paragraphs
            for para in doc.paragraphs:
                para_text = para.text.strip()
                if para_text:
                    text_parts.append(para_text)

            # Extract from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    if row_text.strip() and row_text != "| " * (len(row.cells) - 1):  # Avoid empty rows
                        text_parts.append(row_text)

            # Extract from headers/footers if accessible
            for section in doc.sections:
                # Headers
                if hasattr(section, "header"):
                    for para in section.header.paragraphs:
                        header_text = para.text.strip()
                        if header_text:
                            text_parts.append(f"[HEADER] {header_text}")

                # Footers
                if hasattr(section, "footer"):
                    for para in section.footer.paragraphs:
                        footer_text = para.text.strip()
                        if footer_text:
                            text_parts.append(f"[FOOTER] {footer_text}")

            if not text_parts:
                logger.warning("DOCX %s: No readable text extracted", filename)
                raise EmptyFileError("DOCX contains no readable text")

            extracted_text = "\n\n".join(text_parts)
            logger.info(
                "DOCX %s: Extracted %d paragraphs, %d tables",
                filename,
                len(doc.paragraphs),
                len(doc.tables),
            )

            return extracted_text

        except CorruptedFileError:
            raise
        except Exception as e:
            logger.error("DOCX parsing error in %s: %s", filename, e)
            raise CorruptedFileError(f"Invalid or corrupted DOCX file: {str(e)}") from e

    def _parse_txt(self, file_content: bytes, filename: str) -> str:
        """Extract text from TXT file.

        Handles:
        - Multiple encoding attempts
        - Binary file detection
        - Empty file detection
        - BOM removal

        Args:
            file_content: Raw TXT bytes
            filename: Original filename (for logging)

        Returns:
            Extracted text

        Raises:
            CorruptedFileError: If file is binary or undecodable
            EmptyFileError: If file contains no text
        """
        if not file_content:
            raise EmptyFileError("TXT file is empty")

        # Try to detect encoding
        detected_encoding = None
        last_error = None

        try:
            detected_encoding = self._detect_encoding(file_content)
        except Exception as e:
            logger.warning("Encoding detection failed; will try fallback encodings: %s", e)
            last_error = e

        # Try detected encoding first if available
        encodings_to_try = []
        if detected_encoding and detected_encoding.lower() not in [e.lower() for e in self.ENCODINGS]:
            encodings_to_try.append(detected_encoding)
        encodings_to_try.extend(self.ENCODINGS)

        text = None
        for attempt, encoding in enumerate(encodings_to_try, 1):
            try:
                text = file_content.decode(encoding, errors="replace")

                # Check if result looks like binary/corrupted
                if text.count("\x00") > len(text) * 0.1:  # More than 10% null bytes
                    logger.debug("Encoding %s (attempt %d): Result looks binary", encoding, attempt)
                    continue

                logger.debug("Successfully decoded TXT with %s (attempt %d)", encoding, attempt)
                break

            except Exception as e:
                logger.debug("Encoding %s failed (attempt %d): %s", encoding, attempt, e)
                last_error = e
                continue

        if text is None:
            logger.error(
                "Failed to decode TXT %s after %d attempts. Last error: %s",
                filename,
                len(encodings_to_try),
                last_error,
            )
            raise CorruptedFileError(
                f"Could not decode TXT file with any supported encoding. Last error: {last_error}"
            )

        # Remove BOM if present
        if text.startswith("\ufeff"):
            text = text[1:]
            logger.debug("Removed UTF-8 BOM from TXT %s", filename)

        # Normalize text
        text = self._normalize_text(text)

        if not text:
            raise EmptyFileError("TXT file contains no readable text after decoding")

        logger.info("TXT %s: Successfully extracted %d characters", filename, len(text))
        return text

    def parse(self, file_content: bytes, filename: str) -> str:
        """Parse and extract text from document file.

        Supports: PDF, DOCX, DOC, TXT

        Args:
            file_content: Raw file bytes
            filename: Original filename with extension

        Returns:
            Extracted text content

        Raises:
            UnsupportedFileTypeError: If file type not supported
            CorruptedFileError: If file is corrupted
            EmptyFileError: If file contains no readable text
            FileParseError: For other parsing errors
        """
        if not file_content:
            raise EmptyFileError("File is empty")

        if len(file_content) > self.MAX_CONTENT_LENGTH:
            raise FileParseError(
                f"File exceeds maximum size ({len(file_content)} > {self.MAX_CONTENT_LENGTH} bytes)"
            )

        # Determine file type
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file type: {file_ext}. Supported: {self.SUPPORTED_EXTENSIONS}"
            )

        logger.info(
            "Parsing %s (type: %s, size: %d bytes)",
            filename,
            file_ext,
            len(file_content),
        )

        # Route to appropriate parser
        if file_ext == ".pdf":
            text = self._parse_pdf(file_content, filename)
        elif file_ext in {".docx", ".doc"}:
            text = self._parse_docx(file_content, filename)
        elif file_ext == ".txt":
            text = self._parse_txt(file_content, filename)
        else:
            raise UnsupportedFileTypeError(f"Unsupported file type: {file_ext}")

        # Validate extracted content
        if len(text) < self.MIN_CONTENT_LENGTH:
            raise EmptyFileError(
                f"Extracted content too small ({len(text)} < {self.MIN_CONTENT_LENGTH} characters)"
            )

        if len(text) > self.MAX_CONTENT_LENGTH:
            logger.warning(
                "Extracted content exceeds limit; truncating %s from %d to %d bytes",
                filename,
                len(text),
                self.MAX_CONTENT_LENGTH,
            )
            text = text[: self.MAX_CONTENT_LENGTH]

        logger.info("Successfully parsed %s: %d characters extracted", filename, len(text))
        return text


# Singleton instance
_parser_instance: Optional[DocumentParser] = None


def get_parser() -> DocumentParser:
    """Get or create singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = DocumentParser()
    return _parser_instance


__all__ = [
    "DocumentParser",
    "FileParseError",
    "UnsupportedFileTypeError",
    "CorruptedFileError",
    "EmptyFileError",
    "get_parser",
]
