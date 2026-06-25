import sys
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print("youtube-transcript-api version installed.")
    
    # Let's try getting transcript for a known public video (e.g. jNQXAC9IVRw - Me at the zoo)
    video_id = "jNQXAC9IVRw"
    print(f"Testing video ID: {video_id}")
    
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    text = " ".join([t['text'] for t in transcript_list])
    
    print(f"Transcript Length: {len(text)}")
    print(f"Transcript Language: en") # get_transcript defaults to english if available
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
