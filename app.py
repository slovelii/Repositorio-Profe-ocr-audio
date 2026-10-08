import streamlit as st
import httpx
import os
import time
import glob
import cv2
import numpy as np
import pytesseract
from PIL import Image
from gtts import gTTS
from googletrans import Translator
import re

# Configuración de página optimizada para accesibilidad
st.set_page_config(
    page_title="Asistente de Lectura Accesible",
    page_icon="🔊",
    layout="centered"
)

text = ""

def clean_filename(filename):
    """Limpia el texto para generar un nombre de archivo seguro."""
    return re.sub(r'[^\w\-_\. ]', '_', filename).strip()

def text_to_speech(input_language, output_language, text, tld):
    translation = translator.translate(text, src=input_language, dest=output_language)
    trans_text = translation.text
    
    tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
    
    # Manejo seguro del nombre del archivo
    clean_text = clean_filename(text[0:20]) if text and text.strip() else "audio_lectura"
    if not clean_text:
        clean_text = "audio_lectura"
        
    my_file_name = clean_text
    file_path = f"temp/{my_file_name}.mp3"
    tts.save(file_path)
    return my_file_name, trans_text


def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400
        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_days:
                os.remove(f)

# Limpieza periódica de archivos temporales
remove_files(7)

# --- Encabezado Principal Accesible ---
st.title("🔊 Lector Audible e Intérprete Visual para personas con mutismo selectivo")
st.subheader("Herramienta de asistencia para la lectura de textos e imágenes mediante voz que no es la propia")

image = Image.open('OCR.jpg')
st.image(image)

st.markdown("""
Esta aplicación convierte texto impreso o digital en audio. 
Puedes capturar una foto con la cámara o subir una imagen desde tu dispositivo para que el sistema lea el contenido en voz alta.
Así, cuando te sientas pérdido, o sin saber de qué manera decir las cosas, encontrarás ayuda.
""")

# --- Selección de Fuente de Imagen ---
cam_ = st.checkbox("Activar uso de cámara en vivo")

if cam_:
    img_file_buffer = st.camera_input("Capturar foto del texto a leer")
else:
    img_file_buffer = None

# --- Panel Lateral de Configuración ---
with st.sidebar:
    st.header("⚙️ Ajustes de Lectura y Voz")
    
    st.subheader("Mejora de Imagen")
    filtro = st.radio(
        "¿Aplicar filtro de alto contraste para cámara?",
        ('No', 'Sí'),
        help="Invierte los colores para mejorar la detección en textos oscuros o con sombra."
    )

bg_image = st.file_uploader("Cargar archivo de imagen con texto (PNG o JPG):", type=["png", "jpg"])

# --- Procesamiento de Archivo Subido ---
if bg_image is not None:
    uploaded_file = bg_image
    st.image(uploaded_file, caption='Imagen seleccionada cargada correctamente.', use_container_width=True)
    
    with open(uploaded_file.name, 'wb') as f:
        f.write(uploaded_file.read())
    
    st.success(f"Imagen procesada: {uploaded_file.name}")
    img_cv = cv2.imread(f'{uploaded_file.name}')
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    text = pytesseract.image_to_string(img_rgb)

if text.strip():
    st.markdown("### 📝 Texto detectado:")
    st.write(text)

# --- Procesamiento de Imagen de Cámara ---
if img_file_buffer is not None:
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    if filtro == 'Sí':
        cv2_img = cv2.bitwise_not(cv2_img)
        
    img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    text = pytesseract.image_to_string(img_rgb)
    
    st.markdown("### 📝 Texto detectado desde la cámara:")
    st.write(text)

# --- Configuración de Idioma y Generación de Voz ---
with st.sidebar:
    st.subheader("Idioma y Reproducción")
    
    try:
        os.makedirs("temp", exist_ok=True)
    except Exception:
        pass

    translator = Translator()

    in_lang = st.selectbox(
        "Idioma del texto original (Origen)",
        ("Español", "Ingles", "Bengali", "koreano", "Mandarin", "Japones"),
    )
    
    lang_map_in = {
        "Ingles": "en",
        "Español": "es",
        "Bengali": "bn",
        "koreano": "ko",
        "Mandarin": "zh-cn",
        "Japones": "ja"
    }
    input_language = lang_map_in.get(in_lang, "es")

    out_lang = st.selectbox(
        "Idioma en el que deseas escuchar la lectura",
        ("Español", "Ingles", "Bengali", "koreano", "Mandarin", "Japones"),
    )
    
    lang_map_out = {
        "Ingles": "en",
        "Español": "es",
        "Bengali": "bn",
        "koreano": "ko",
        "Mandarin": "zh-cn",
        "Japones": "ja"
    }
    output_language = lang_map_out.get(out_lang, "es")

    english_accent = st.selectbox(
        "Variante regional de voz (Acento)",
        (
            "Default",
            "India",
            "United Kingdom",
            "United States",
            "Canada",
            "Australia",
            "Ireland",
            "South Africa",
        ),
    )
    
    tld_map = {
        "Default": "com",
        "India": "co.in",
        "United Kingdom": "co.uk",
        "United States": "com",
        "Canada": "ca",
        "Australia": "com.au",
        "Ireland": "ie",
        "South Africa": "co.za"
    }
    tld = tld_map.get(english_accent, "com")

    display_output_text = st.checkbox("Mostrar transcripción en pantalla", value=True)

    btn_convert = st.button("🔊 Leer texto en voz alta")

# --- Generación de Audio Principal ---
if btn_convert:
    if text and text.strip():
        with st.spinner("Generando audio de lectura..."):
            result, output_text = text_to_speech(input_language, output_language, text, tld)
            
            audio_path = f"temp/{result}.mp3"
            if os.path.exists(audio_path):
                with open(audio_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                
                st.markdown("## 🎧 Audio de Lectura:")
                st.audio(audio_bytes, format="audio/mp3", start_time=0)

                if display_output_text:
                    st.markdown("## 📖 Texto traducido / interpretado:")
                    st.write(output_text)
    else:
        st.warning("No se ha encontrado texto para leer. Por favor carga una imagen o toma una foto primero.")
