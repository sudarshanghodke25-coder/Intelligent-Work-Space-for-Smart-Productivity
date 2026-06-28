import asyncio
from file_converter.models.conversion_job import ConversionJob
from file_converter.services.conversion_engine import engine
from file_converter.database.converter_db import init_converter_tables
import os

init_converter_tables()

# Create a test text file
with open('test_input.txt', 'w') as f:
    f.write('Hello World! This is a test for the Aurex File Converter.')

job = ConversionJob(
    source_path=os.path.abspath('test_input.txt'),
    source_ext='.txt',
    source_name='test_input.txt',
    target_ext='.pdf'
)

try:
    output = engine.execute(job)
    print("Conversion Output:", output)
except Exception as e:
    print("Error:", repr(e))
