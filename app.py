import streamlit as st
import base64
import os
import time
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv

# Deve ser o primeiro comando
st.set_page_config(page_title="Transcrição de Áudio - Uzui Style", layout="centered")

# Carrega variáveis de ambiente
_ = load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("A chave da API do Gemini não foi encontrada. Configure a variável de ambiente GOOGLE_API_KEY.")
    st.stop()

# Configura o Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# 🔥 Função para aplicar imagem de fundo local via base64
def set_custom_background(image_file_path):
    with open(image_file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True
    )

# 🎤 Transcrição com Gemini
def transcribe_with_gemini(uploaded_audio):
    try:
        st.info("📥 Processando transcrição com Gemini...")
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

        progress = st.progress(0)

        # Salva temporariamente o áudio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(uploaded_audio.read())
            temp_audio_path = temp_audio.name

        progress.progress(30)

        # Faz upload do arquivo salvo
        uploaded = genai.upload_file(temp_audio_path)
        progress.progress(60)

        # Gera a transcrição
        response = model.generate_content([
            uploaded,
            "Transcreva esse áudio para inglês."
        ])

        progress.progress(100)
        time.sleep(0.3)
        progress.empty()

        # Remove o arquivo temporário
        os.remove(temp_audio_path)

        return response.text

    except Exception as e:
        st.error(f"Erro ao transcrever com Gemini: {e}")
        return None

# 🌍 Tradução com Gemini
def translate_text_gemini(text, target_language):
    try:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        progress_bar = st.progress(0)

        prompt = f"Translate the following English text to {target_language}:\n{text}"
        for i in range(0, 40, 10):
            time.sleep(0.1)
            progress_bar.progress(i)

        response = model.generate_content(prompt)

        for i in range(40, 101, 20):
            time.sleep(0.1)
            progress_bar.progress(i)

        progress_bar.empty()
        return response.text
    except Exception as e:
        st.error(f"Erro durante a tradução para {target_language}: {e}")
        return None

# 🚀 Main App
def main():
    set_custom_background("img/tengen-bg.jpg")

    st.markdown("<h1 style='text-align: center; color: #ffffff;'>🎧 Transcrição de Áudio - Estilo Tengen Uzui</h1>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📎 Carregue um arquivo de áudio MP3 ou WAV", type=["mp3", "wav"])

    st.sidebar.image("img/tengen-icon.jpg", width=120)
    st.sidebar.markdown("## 💎 Escolha suas traduções")
    selected_languages = st.sidebar.multiselect(
        "Idiomas disponíveis:",
        ["Português (Brasil)", "Francês", "Espanhol", "Italiano"]
    )

    if uploaded_file is not None:
        st.audio(uploaded_file, format=uploaded_file.type)

        transcription = transcribe_with_gemini(uploaded_file)

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
