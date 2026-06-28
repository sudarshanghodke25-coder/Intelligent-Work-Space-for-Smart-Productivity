import asyncio
from file_converter.models.conversion_job import ConversionJob
from file_converter.services.conversion_engine import engine
from file_converter.database.converter_db import init_converter_tables
import os
import fitz

init_converter_tables()

# Create a test PDF file using fitz
doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 50), "Hello World, this is a PDF to Word test!", fontsize=12)
doc.save("test_input2.pdf")
doc.close()

job = ConversionJob(
    source_path=os.path.abspath('test_input2.pdf'),
    source_ext='.pdf',
    source_name='test_input2.pdf',
    target_ext='.docx'
)

try:
    output = engine.execute(job)
    print("Conversion Output:", output)
except Exception as e:
    print("Error:", repr(e))
