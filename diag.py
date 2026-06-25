import sys
import os
import shutil

print("========================================================")
print("PHASE 1 - ENVIRONMENT AUDIT")
print("===========================")
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Virtual Environment Path: {os.environ.get('VIRTUAL_ENV', 'Not inside a virtual environment')}")
print(f"Current Working Directory: {os.getcwd()}")

try:
    import yt_dlp
    print("yt_dlp imported successfully")
except ImportError as e:
    print(f"yt_dlp import failed: {e}")

try:
    import faster_whisper
    print("faster_whisper imported successfully")
except ImportError as e:
    print(f"faster_whisper import failed: {e}")

try:
    import youtube_transcript_api
    print("youtube_transcript_api imported successfully")
except ImportError as e:
    print(f"youtube_transcript_api import failed: {e}")

print("========================================================")
print("PHASE 2 - DEPENDENCY DIAGNOSTICS")
print("================================")
import pkg_resources

for pkg in ['yt-dlp', 'faster-whisper', 'youtube-transcript-api']:
    try:
        dist = pkg_resources.get_distribution(pkg)
        print(f"✓ {pkg}")
        print(f"Version: {dist.version}")
        print(f"Path: {dist.location}\n")
    except pkg_resources.DistributionNotFound:
        print(f"✗ {pkg}")
        print("Not Found\n")

print("========================================================")
print("PHASE 3 - FFMPEG VALIDATION")
print("===========================")
ffmpeg_path = shutil.which("ffmpeg")
if ffmpeg_path:
    print(f"ffmpeg found at: {ffmpeg_path}")
    os.system("ffmpeg -version | head -n 1")
else:
    print("ffmpeg not found in PATH")
