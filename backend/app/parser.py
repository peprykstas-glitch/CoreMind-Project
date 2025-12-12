import io
from fastapi import UploadFile
import pypdf

async def parse_file(file: UploadFile) -> str:
    """
    Визначає тип файлу та витягує з нього текст.
    """
    content = ""
    filename = file.filename.lower()

    # Читаємо файл у пам'ять
    file_bytes = await file.read()
    
    try:
        if filename.endswith(".pdf"):
            # Обробка PDF
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_list = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_list.append(text)
            content = "\n".join(text_list)
            
        elif filename.endswith((".txt", ".md")):
            # Обробка тексту
            content = file_bytes.decode("utf-8")
            
        else:
            raise ValueError("Unsupported file type. Please upload .pdf, .txt, or .md")
            
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return ""

    return content