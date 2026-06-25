import sys
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    
    video_id = "jNQXAC9IVRw"
    print(f"Testing video ID: {video_id}")
    
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)
    transcript = transcript_list.find_transcript(['en'])
    fetched = transcript.fetch()
    
    text = " ".join([t['text'] for t in fetched])
    
    print(f"Transcript Length: {len(text)}")
    print(f"Transcript Language: {transcript.language_code}")
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
