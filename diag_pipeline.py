import sys
import os
import time
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
load_dotenv()

# Setup Event Bus Mocking to trace UI events
from services.event_bus import bus
events_logged = []
def log_event(payload):
    events_logged.append(payload)
bus.subscribe("ANALYSIS_PROGRESS", log_event)
bus.subscribe("ANALYSIS_COMPLETED", log_event)

print("========================================================")
print("PHASE 4 - PROVIDER CHAIN TEST")
print("=============================")

from services.youtube.providers.transcript_api import YouTubeTranscriptProvider
from services.youtube.providers.yt_dlp import YtDlpSubtitleProvider
from services.youtube.providers.whisper import WhisperProvider

test_video_id = "jNQXAC9IVRw" # Me at the zoo (Shortest video, great for testing)
test_url = f"https://www.youtube.com/watch?v={test_video_id}"

providers = [
    YouTubeTranscriptProvider(),
    YtDlpSubtitleProvider(),
    WhisperProvider()
]

for p in providers:
    print(f"Testing Provider: {p.name}")
    start = time.time()
    try:
        res = p.extract_transcript(test_video_id, test_url, source_id=None)
        status = "SUCCESS"
        error = "None"
        length = len(res)
    except Exception as e:
        status = "FAIL"
        error = str(e)
        length = 0
    duration = time.time() - start
    print(f"Status: {status} | Execution Time: {duration:.2f}s | Length: {length} | Error: {error}")
    print("-")

print("========================================================")
print("PHASE 6 - CACHE DIAGNOSTICS & AUTO-FIX")
print("======================================")

from database.database import get_connection

conn = get_connection()
c = conn.cursor()

c.execute("SELECT id, title, video_id, transcript_length, raw_response FROM knowledge_sources WHERE source_type='youtube'")
records = c.fetchall()
invalidated = 0

for r in records:
    is_bad = False
    if not r["transcript_length"] or r["transcript_length"] < 100:
        is_bad = True
    elif r["raw_response"] and "YouTube's general information" in r["raw_response"]:
        is_bad = True
        
    if is_bad:
        print(f"Invalidating bad cache for ID: {r['id']} (Title: {r['title']})")
        c.execute("DELETE FROM knowledge_sources WHERE id=?", (r["id"],))
        invalidated += 1

conn.commit()
print(f"Total invalid cache entries cleared: {invalidated}")

print("========================================================")
print("PHASE 5 - TEST VIDEO PIPELINE")
print("=============================")

from services.knowledge_pipeline import knowledge_pipeline
try:
    print(f"Running pipeline on {test_url}...")
    knowledge_pipeline.process_url_background(test_url, "Test Video", "youtube")
    
    # process_url_background runs in a thread. Let's wait for completion event.
    timeout = 60
    while timeout > 0:
        if any(e.get("success") is not None for e in events_logged if isinstance(e, dict)):
            break
        time.sleep(1)
        timeout -= 1
        
    for ev in events_logged:
        print(f"UI EVENT: {ev}")
        
except Exception as e:
    print(f"Pipeline crashed: {e}")

print("========================================================")
print("PHASE 7 - DATABASE DIAGNOSTICS")
print("==============================")
c.execute("SELECT id, title, video_id, channel, transcript_length, extraction_method, processing_time FROM knowledge_sources WHERE url=? ORDER BY id DESC LIMIT 1", (test_url,))
last_record = c.fetchone()
if last_record:
    print("Record saved successfully:")
    for k in last_record.keys():
        print(f"{k}: {last_record[k]}")
else:
    print("No record found in DB after pipeline execution.")

conn.close()

print("========================================================")
print("PHASE 8 - UI DIAGNOSTICS")
print("========================")
print("Event Bus received the following terminal events:")
completed_events = [e for e in events_logged if e.get('success') is not None]
for ce in completed_events:
    print(ce)

