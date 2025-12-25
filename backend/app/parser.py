import os
from fastapi import UploadFile

# Список розширень, які ми будемо читати як звичайний текст (код)
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', 
    '.java', '.cpp', '.c', '.h', '.cs', 
    '.go', '.rs', '.php', '.rb', 
    '.json', '.yaml', '.yml', '.xml', 
    '.html', '.css', '.scss', '.sql', 
    '.sh', '.bat', '.md', '.txt', '.env'
}

async def read_text_file(file: UploadFile) -> str:
    """Reads generic text or code files."""
    content = await file.read()
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        # Fallback for Windows-1251 or other encodings if UTF-8 fails
        try:
            return content.decode("windows-1251")
        except:
            return content.decode("utf-8", errors="ignore")

async def read_pdf(file: UploadFile) -> str:
    """Extracts text from PDF using pypdf."""
    try:
        import pypdf
    except ImportError:
        return "[Error] pypdf library not installed. Please run: pip install pypdf"

    content = await file.read()
    
    # Save to temp file because pypdf needs a file stream or path
    import io
    pdf_file = io.BytesIO(content)
    
    text = []
    try:
        reader = pypdf.PdfReader(pdf_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text.append(extracted)
        return "\n".join(text)
    except Exception as e:
        return f"[Error parsing PDF: {str(e)}]"

async def parse_file(file: UploadFile) -> str:
    """
    Main entry point for parsing files.
    Determines functionality based on file extension.
    """
    filename = file.filename.lower()
    _, ext = os.path.splitext(filename)

    # 1. Parsing Code / Text
    if ext in CODE_EXTENSIONS:
        print(f"📄 Detected code/text file: {ext}")
        return await read_text_file(file)

    # 2. Parsing PDF
    elif ext == '.pdf':
        print(f"📕 Detected PDF file.")
        return await read_pdf(file)

    # 3. Unsupported
    else:
        print(f"⚠️ Unsupported file type: {ext}")
        return f"[System: Unsupported file type '{ext}'. Content could not be indexed.]"