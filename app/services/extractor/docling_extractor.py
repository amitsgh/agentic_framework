"""Docling Extractor"""

from typing import List, Union, cast
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.document_converter import DocumentConverter, PdfFormatOption, FormatOption
from docling_core.types.doc.document import DoclingDocument

from app.services.extractor.base import BaseExtractor
from app.exceptions import DocumentProcessingError, ValidationError
from app.utils.logger import setuplog

logger = setuplog(__name__)


class DoclingExtractor(BaseExtractor):
    """Docling Extractor Class"""

    def __init__(self):
        self.default_converter = DocumentConverter()

    def supported_extension(self) -> List[str]:
        """Return supported document extensions"""

        supported_formats = self.default_converter.allowed_formats
        return [fmt.value for fmt in supported_formats]

    def _build_pdf_converter(self) -> DocumentConverter:
        """Build a DocumentConverter Configuration"""

        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_page_images = True
        pipeline_options.ocr_options = EasyOcrOptions()

        format_options = {
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options, backend=PyPdfiumDocumentBackend
            )
        }

        # cast to the expected dict[InputFormat, FormatOption] to satisfy static type checkers
        format_options_typed = cast(dict[InputFormat, FormatOption], format_options)

        return DocumentConverter(format_options=format_options_typed)

    def extract_data(self, file_paths: Union[str, List[str]]) -> List[DoclingDocument]:
        """Extracting documents using Docling"""

        try:
            if isinstance(file_paths, str):
                file_paths = [file_paths]

            if not file_paths:
                raise ValidationError("No file paths provided for extraction")

            all_docs: List[DoclingDocument] = []

            for file_path in file_paths:
                file_path = Path(file_path)
                
                if not file_path.exists():
                    raise ValidationError(f"File not found: {file_path}")
                
                ext = file_path.suffix.lower().lstrip(".")

                if ext not in self.supported_extension():
                    raise ValidationError(
                        f"Unsupported file extension {file_path.suffix.lower()}. "
                        f"Supported: {', '.join(self.supported_extension())}"
                    )

                converter = (
                    self._build_pdf_converter()
                    if ext == "pdf"
                    else self.default_converter
                )

                logger.info("Converting document: %s", file_path)

                try:
                    doc = converter.convert(str(file_path)).document
                    all_docs.append(doc)
                    logger.info("Extracted DoclingDocument with %d pages", len(doc.pages))

                except Exception as e:
                    logger.error("Error converting file %s: %s", file_path, str(e))
                    raise DocumentProcessingError(f"Failed to convert file {file_path}: {str(e)}") from e

            if not all_docs:
                raise DocumentProcessingError("No documents were extracted from the provided files")

            return all_docs

        except Exception as e:
            logger.error("Error parsing data using DoclingExtractor: %s", str(e), exc_info=True)
            raise DocumentProcessingError(f"Extraction failed: {str(e)}") from e