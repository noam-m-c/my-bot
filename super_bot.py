import streamlit as st
import whisper
import os
import arabic_reshaper
from bidi.algorithm import get_display
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip

# הסרנו את change_settings כי אנחנו ננסה לעבוד בלי ImageMagick במידת האפשר
# או להשתמש בשיטה שלא חסומה על ידי ה-Security Policy

st.set_page_config(page_title="Safe Subtitle Bot", layout="wide")

def fix_hebrew_display(text):
    if not text: return ""
    return get_display(arabic_reshaper.reshape(text))

st.title("בוט כתוביות - גרסה יציבה 🛡️")

uploaded_file = st.file_uploader("העלה סרטון", type=["mp4", "mov"])

if uploaded_file is not None:
    input_path = "temp_input.mp4"
    output_path = "final_video.mp4"

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("התחל עיבוד"):
        try:
            # 1. AI Transcription
            with st.spinner("מנתח סאונד (AI)..."):
                model = whisper.load_model("tiny")
                result = model.transcribe(input_path, language="he")

            # 2. Subtitle Rendering
            with st.spinner("מכין כתוביות..."):
                video = VideoFileClip(input_path)
                if video.w > 720: video = video.resize(width=720)

                subtitle_clips = []
                for segment in result['segments']:
                    txt = fix_hebrew_display(segment['text'])
                    
                    # שימוש ב-method='label' במקום 'caption' - לפעמים זה עוקף את חסימת האבטחה
                    txt_clip = TextClip(txt, fontsize=video.h//20, color='white', 
                                       font='DejaVu-Sans', method='label')
                    
                    bg_clip = ColorClip(size=(txt_clip.w + 20, txt_clip.h + 10), color=(0,0,0)).set_opacity(0.6)
                    
                    final_sub = CompositeVideoClip([bg_clip, txt_clip.set_position('center')])
                    final_sub = (final_sub.set_start(segment['start'])
                                 .set_duration(segment['end'] - segment['start'])
                                 .set_position(('center', video.h * 0.85)))
                    subtitle_clips.append(final_sub)

                result_video = CompositeVideoClip([video] + subtitle_clips)
                
                # ייצוא מהיר
                result_video.write_videofile(output_path, codec="libx264", audio_codec="aac", 
                                          fps=24, preset="ultrafast", threads=4)

            st.balloons()
            st.success("הסרטון מוכן!")
            with open(output_path, "rb") as f:
                st.download_button("📥 הורד סרטון", f, "video_ready.mp4")

        except Exception as e:
            st.error(f"שגיאה טכנית: {e}")
            st.info("אם השגיאה נמשכת, ייתכן ששרת Streamlit חוסם עריכת וידאו ישירה. נסה סרטון קצר מאוד של 5 שניות לבדיקה.")
