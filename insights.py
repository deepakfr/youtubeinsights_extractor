import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# Load API key from secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# Streamlit UI setup
st.set_page_config(page_title="🔍 YouTube Key Insights", layout="centered")
st.title("🔍 YouTube Key Insights Extractor")
st.markdown("Paste a YouTube video URL and extract key ideas, insights, and takeaways.")

# Extract video ID from URL
def get_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]
    elif parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    return None

# Cached transcript fetching
@st.cache_data(show_spinner=False)
def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])
    except Exception as e:
        return f"Transcript error: {e}"

# Prompt for insight extraction
def create_prompt(transcript_text):
    return (
        "Analyze the following YouTube video transcript and extract the key insights, main points, or important takeaways. "
        "Present them in a clear bullet point list:\n\n"
        f"{transcript_text}\n\n"
        "Key Insights:"
    )

# Call Groq API
def groq_extract_insights(prompt):
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
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"Groq API error: {result}"
    except Exception as e:
        return f"Error parsing Groq response: {e}"

# --- UI ---

youtube_url = st.text_input("📺 Enter YouTube video URL:")

if youtube_url:
    video_id = get_video_id(youtube_url)
    
    if not video_id:
        st.error("❌ Invalid YouTube URL.")
        st.stop()

    with st.spinner("🧠 Extracting transcript..."):
        transcript = fetch_transcript(video_id)

    if transcript.startswith("Transcript error"):
        st.error(transcript)
    else:
        st.success("📃 Transcript fetched successfully.")
        prompt = create_prompt(transcript)

        with st.spinner("🤖 Analyzing with Groq..."):
            insights = groq_extract_insights(prompt)

        if insights:
            st.subheader("🧩 Key Insights:")
            st.markdown(insights)
        else:
            st.warning("⚠️ Could not extract insights.")
