import streamlit as st
import base64
import os
import whisper
import tempfile
import google.generativeai as genai
import time
from dotenv import load_dotenv, find_dotenv

# ⚠️ Sempre primeiro
st.set_page_config(page_title="Transcrição de Áudio - Uzui Style", layout="centered")

# ffmpeg config (ajuste conforme necessário)
ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg-7.1.1-essentials_build", "bin")
os.environ["PATH"] += os.pathsep + ffmpeg_path

# Load .env
_ = load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("Configure a variável de ambiente GOOGLE_API_KEY.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# Função de background
def set_custom_background(image_file_path):
    with open(image_file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(f"""
        <style>
            body {{
                background-image: url("data:image/jpg;base64,{encoded_string}");
                background-size: cover;
                background-attachment: fixed;
                background-position: center;
            }}
            .stApp {{
                background-color: rgba(0, 0, 0, 0.6);
            }}
            .stProgress > div > div > div > div {{
                background-image: linear-gradient(to right, #ff66c4, #ffff66, #66ffcc);
            }}
        </style>
    """, unsafe_allow_html=True)

# ✅ Transcrição principal com fallback Gemini
def transcribe_to_english(uploaded_file):
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0)

    try:
        # Cria um arquivo temporário com extensão .mp3
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        for percent in range(0, 30, 5):
            time.sleep(0.05)
            progress_bar.progress(percent)

        model = whisper.load_model("base")
        result = model.transcribe(tmp_path, task="translate")

        for percent in range(30, 101, 10):
            time.sleep(0.05)
            progress_bar.progress(percent)

        os.remove(tmp_path)
        progress_placeholder.empty()
        return result["text"]

    except Exception as e:
        st.warning("Whisper falhou. Tentando transcrição com Gemini...")
        try:
            uploaded_file.seek(0)  # volta ao início do arquivo
            audio_bytes = uploaded_file.read()

            # Envia áudio para Gemini
            model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
            response = model.generate_content([
                genai.upload_file(audio_bytes, mime_type="audio/mpeg"),
                "Transcreva esse áudio para inglês."
            ])
            progress_bar.progress(100)
            progress_placeholder.empty()
            return response.text
        except Exception as e2:
            st.error(f"Falha total na transcrição: {e2}")
            return None

# Tradução com Gemini
def translate_text_gemini(text, target_language):
    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0)
        for percent in range(0, 40, 5):
            time.sleep(0.05)
            progress_bar.progress(percent)

        prompt = f"Translate the following English text to {target_language}:\n\n{text}"
        response = model.generate_content(prompt)

        for percent in range(40, 101, 10):
            time.sleep(0.05)
            progress_bar.progress(percent)

        progress_placeholder.empty()
        return response.text
    except Exception as e:
        st.error(f"Erro durante a tradução para {target_language}: {e}")
        return None

# App
def main():
    set_custom_background("img/tengen-bg.jpg")

    st.markdown("<h1 style='text-align: center; color: #ffffff;'>🎧 Transcrição de Áudio - Estilo Tengen Uzui</h1>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("💽 Carregue um arquivo de áudio MP3 ou WAV", type=["mp3", "wav"])

    # Sidebar personalizada com ícone local
    st.sidebar.image("img/tengen-icon.jpg", width=120)  # Caminho local do ícone
    st.sidebar.markdown("## 💎 Escolha suas traduções")
    selected_languages = st.sidebar.multiselect(
        "Idiomas disponíveis:",
        ["Português (Brasil)", "Francês", "Espanhol", "Italiano"]
)


    if uploaded_file is not None:
        st.audio(uploaded_file, format="audio/mp3")

        st.subheader("📤 Transcrevendo para inglês...")
        transcription = transcribe_to_english(uploaded_file)

        if transcription:
            st.success("✅ Transcrição concluída!")
            st.subheader("📝 Transcrição (Inglês):")
            st.write(transcription)

            if selected_languages:
                st.markdown("### 🌍 Traduções Selecionadas")
                lang_map = {
                    "Português (Brasil)": "Portuguese (Brazilian)",
                    "Francês": "French",
                    "Espanhol": "Spanish",
                    "Italiano": "Italian"
                }

                for lang in selected_languages:
                    st.subheader(f"🗨️ {lang}:")
                    translated = translate_text_gemini(transcription, lang_map[lang])
                    st.success(f"✅ Tradução para {lang} concluída!")
                    st.write(translated)

if __name__ == "__main__":
    main()
