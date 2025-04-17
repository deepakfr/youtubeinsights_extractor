import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs

# Get API key from Streamlit secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# --- Streamlit setup ---
st.set_page_config(page_title="🧠 Smart YouTube Insight Extractor", layout="centered")
st.title("🧠 Smart YouTube Insight Extractor")
st.markdown("Paste any YouTube URL – transcript or not – and get key insights powered by Groq AI.")

# --- Helpers ---

# Extract video ID
def get_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]
    elif parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    return None

# Try to get transcript
@st.cache_data(show_spinner=False)
def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception as e:
        return f"Transcript fetch error: {e}"

# Fallback: Get metadata using YouTube oEmbed API
def get_video_metadata(video_url):
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={video_url}&format=json"
        response = requests.get(oembed_url)
        data = response.json()
        return {
            "title": data.get("title", ""),
            "author": data.get("author_name", ""),
        }
    except Exception:
        return {}

# Create a prompt from available data
def build_prompt(transcript, metadata):
    if transcript:
        return f"Analyze this YouTube transcript and extract key insights:\n\n{transcript}\n\nInsights:"
    elif metadata:
        return (
            f"Here's a YouTube video titled '{metadata.get('title', '')}' by {metadata.get('author', '')}.\n"
            f"Although there's no transcript, try to infer the key themes and possible insights based on this context."
        )
    else:
        return "Analyze this video and extract key insights. (No transcript or metadata available.)"

# Call Groq API
def query_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error from Groq: {e}"

# --- UI ---

youtube_url = st.text_input("📺 Enter a YouTube video URL:")

if youtube_url:
    video_id = get_video_id(youtube_url)
    
    if not video_id:
        st.error("❌ Invalid YouTube URL.")
        st.stop()

    with st.spinner("🔍 Checking for transcript..."):
        transcript = get_transcript(video_id)

    metadata = {}
    if not transcript:
        with st.spinner("📄 No transcript found. Fetching video metadata..."):
            metadata = get_video_metadata(youtube_url)

    prompt = build_prompt(transcript, metadata)

    with st.spinner("⚡ Extracting insights using Groq..."):
        insights = query_groq(prompt)

    st.subheader("🧠 Key Insights:")
    st.markdown(insights)
