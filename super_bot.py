import streamlit as st
import whisper
import os
import arabic_reshaper
from bidi.algorithm import get_display
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.config import change_settings

# הגדרת נתיב ל-ImageMagick בשרתי לינוקס
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

st.set_page_config(page_title="Turbo Subtitle Bot", layout="wide")

def fix_hebrew_display(text):
    if not text: return ""
    return get_display(arabic_reshaper.reshape(text))

st.title("הבוט האוטומטי לכתוביות - גרסת טורבו ⚡")

uploaded_file = st.file_uploader("העלה סרטון", type=["mp4", "mkv", "mov"])

if uploaded_file is not None:
    input_path = "temp_input.mp4"
    output_path = "fast_output.mp4"

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("התחל לעבוד"):
        try:
            with st.spinner("1/2 - ה-AI מקשיב לסרטון..."):
                model = whisper.load_model("tiny") 
                result = model.transcribe(input_path, language="he")

            with st.spinner("2/2 - מדביק כתוביות..."):
                video = VideoFileClip(input_path)
                
                if video.w > 720:
                    video = video.resize(width=720)

                subtitle_clips = []
                for segment in result['segments']:
                    txt = fix_hebrew_display(segment['text'])
                    
                    # שימוש בגופן ברירת מחדל של המערכת כדי למנוע שגיאות
                    txt_clip = TextClip(txt, fontsize=video.h//18, color='white', 
                                       font='DejaVu-Sans', method='caption', size=(video.w*0.8, None))
                    
                    bg_clip = ColorClip(size=(txt_clip.w+30, txt_clip.h+10), color=(0,0,0)).set_opacity(0.6)
                    
                    final_sub = CompositeVideoClip([bg_clip, txt_clip.set_position('center')])
                    final_sub = (final_sub.set_start(segment['start'])
                                 .set_duration(segment['end'] - segment['start'])
                                 .set_position(('center', video.h*0.8)))
                    subtitle_clips.append(final_sub)

                result_video = CompositeVideoClip([video] + subtitle_clips)
                result_video.write_videofile(output_path, codec="libx264", audio_codec="aac", 
                                          fps=min(video.fps, 24), preset="ultrafast", threads=4)

            st.balloons()
            with open(output_path, "rb") as f:
                st.download_button("📥 הורד סרטון מוכן", f, "bot_video.mp4")
            
            video.close()
            result_video.close()

        except Exception as e:
            st.error(f"שגיאה: {e}")
