import streamlit as st
import whisper
import os
import arabic_reshaper
from bidi.algorithm import get_display
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.config import change_settings

# --- תיקון קריטי עבור שרתי Streamlit Cloud ---
# פקודה זו אומרת ל-MoviePy איפה למצוא את התוכנה ליצירת טקסט בלינוקס
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

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

uploaded_file = st.file_uploader("גרור לכאן סרטון (MP4, MOV)", type=["mp4", "mkv", "mov"])

if uploaded_file is not None:
    input_path = "temp_input.mp4"
    output_path = "final_subtitled_video.mp4"

    # שמירה לדיסק
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("התחל בתהליך"):
        try:
            # 1. שלב ה-AI: תמלול (שימוש במודל base כדי למנוע קריסה בענן)
            with st.spinner("ה-AI מנתח את הסרטון (זה עשוי לקחת דקה)..."):
                model = whisper.load_model("base") 
                result = model.transcribe(input_path, language="he")

            # 2. שלב העריכה: יצירת הכתוביות
            with st.spinner("מדביק כתוביות לסרטון..."):
                video = VideoFileClip(input_path)
                subtitle_clips = []

                for segment in result['segments']:
                    start_t = segment['start']
                    end_t = segment['end']
                    # תיקון טקסט לעברית
                    clean_text = fix_hebrew_display(segment['text'])

                    # יצירת הטקסט
                    txt_clip = TextClip(
                        clean_text,
                        fontsize=video.h // 20,
                        color='white',
                        font='Arial', # פונט סטנדרטי שקיים בלינוקס
                        method='caption',
                        align='center',
                        size=(video.w * 0.8, None)
                    )

                    # יצירת רקע שחור חצי שקוף
                    bg_clip = ColorClip(
                        size=(txt_clip.w + 40, txt_clip.h + 20),
                        color=(0, 0, 0)
                    ).set_opacity(0.6)

                    # חיבור טקסט מעל רקע ומיקום
                    full_subtitle = CompositeVideoClip([bg_clip, txt_clip.set_position('center')])
                    full_subtitle = (full_subtitle
                                     .set_start(start_t)
                                     .set_duration(end_t - start_t)
                                     .set_position(('center', video.h * 0.8)))
                    
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
            
            # סגירת קבצים לשחרור זיכרון
            video.close()
            final_video.close()

        except Exception as e:
            st.error(f"אירעה שגיאה: {e}")
