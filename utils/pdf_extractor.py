import io

def extract_text_from_pdf(pdf_source):
    """
    Extract readable text content from a PDF file using PyPDF2 / pypdf.
    
    :param pdf_source: File path (str) or file-like object (bytes/stream).
    :return: Tuple (extracted_text: str, error: str or None)
    """
    try:
        try:
            import pypdf as pdf_lib
        except ImportError:
            import PyPDF2 as pdf_lib

        reader = pdf_lib.PdfReader(pdf_source)
        extracted_pages = []

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text.strip())

        full_text = "\n\n".join(extracted_pages).strip()

        if not full_text:
            return "", "The uploaded PDF file contains no extractable text. It may be a scanned image or empty."

        return full_text, None

    except Exception as e:
        return "", f"Failed to extract text from PDF: {str(e)}"
