"""Docling Parser"""

from typing import List, Union, cast
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.document_converter import DocumentConverter, PdfFormatOption, FormatOption

from docling_core.types.doc.document import DoclingDocument

from app.services.extractor.base import BaseExtractor
from app.core.logger import setuplog

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

    def extract(self, file_paths: Union[str, List[str]]) -> List[DoclingDocument]:
        """Extracting documents using Docling"""

        try:
            if isinstance(file_paths, str):
                file_paths = [file_paths]

            all_docs: List[DoclingDocument] = []

            for file_path in file_paths:
                file_path = Path(file_path)
                ext = file_path.suffix.lower().lstrip(".")

                if ext not in self.supported_extension():
                    raise ValueError(
                        f"Unsupported file extension {file_path.suffix.lower()}. Supported: {', '.join(self.supported_extension())}"
                    )

                converter = (
                    self._build_pdf_converter()
                    if ext == "pdf"
                    else self.default_converter
                )

                logger.info("Converting documents: %s", file_path)

                doc = converter.convert(str(file_path)).document
                all_docs.append(doc)
                logger.info("Extracted DoclingDocument with %d pages", len(doc.pages))

            return all_docs

        except Exception as e:
            logger.error("Error parsing data using DoclingParser: %s", str(e))
            raise
