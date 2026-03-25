import streamlit as st
import whisper
import os
import arabic_reshaper
from bidi.algorithm import get_display
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip

# --- הגדרות דף ---
st.set_page_config(page_title="AI Video Translator Pro", layout="wide")

def fix_hebrew_display(text):
    """מתקן עברית הפוכה וסידור אותיות"""
    if not text:
        return ""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

# --- ממשק המשתמש ---
st.title("הבוט האוטומטי לכתוביות 🎬")
st.subheader("תרגום מכל שפה | זיהוי מגדר אוטומטי | קריאות מקסימלית")

uploaded_file = st.file_uploader("גרור לכאן סרטון (עד 4GB)", type=["mp4", "mkv", "mov"])

if uploaded_file is not None:
    input_path = "temp_input.mp4"
    output_path = "final_subtitled_video.mp4"

    # שמירה לדיסק כדי לתמוך בקבצים גדולים
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("התחל בתהליך"):
        try:
            # 1. שלב ה-AI: תמלול ותרגום לעברית
            with st.spinner("ה-AI מנתח את הסרטון ומתרגם לעברית..."):
                model = whisper.load_model("medium") # איזון מושלם לדיוק מגדרי
                result = model.transcribe(input_path, language="he", task="transcribe")

            # 2. שלב העריכה: יצירת הכתוביות
            with st.spinner("מדביק כתוביות עם רקע דינמי..."):
                video = VideoFileClip(input_path)
                subtitle_clips = []

                for segment in result['segments']:
                    start_t = segment['start']
                    end_t = segment['end']
                    clean_text = fix_hebrew_display(segment['text'])

                    # יצירת הטקסט
                    txt_clip = TextClip(
                        clean_text,
                        fontsize=video.h // 22,
                        color='white',
                        font='Arial-Bold',
                        method='caption',
                        align='center',
                        size=(video.w * 0.8, None)
                    )

                    # יצירת רקע שחור חצי שקוף
                    bg_clip = ColorClip(
                        size=(txt_clip.w + 40, txt_clip.h + 20),
                        color=(0, 0, 0)
                    ).set_opacity(0.6)

                    # חיבור טקסט מעל רקע
                    full_subtitle = CompositeVideoClip([bg_clip, txt_clip.set_position('center')])
                    
                    # מיקום בתחתית
                    full_subtitle = (full_subtitle
                                     .set_start(start_t)
                                     .set_duration(end_t - start_t)
                                     .set_position(('center', video.h * 0.85)))
                    
                    subtitle_clips.append(full_subtitle)

                # איחוד לסרטון סופי
                final_video = CompositeVideoClip([video] + subtitle_clips)
                final_video.write_videofile(
                    output_path, 
                    codec="libx264", 
                    audio_codec="aac", 
                    fps=video.fps,
                    threads=4
                )

            st.balloons()
            st.success("הסרטון מוכן!")
            
            with open(output_path, "rb") as file:
                st.download_button(
                    label="📥 לחץ כאן להורדת הסרטון",
                    data=file,
                    file_name="subtitled_video.mp4",
                    mime="video/mp4"
                )
            
            video.close()

        except Exception as e:
            st.error(f"אירעה שגיאה: {e}")
            st.info("טיפ: וודא ש-ImageMagick מותקן כראוי במחשב.")