import streamlit as st
import requests
import time
import os
from dotenv import load_dotenv

# --- 0. НАЛАШТУВАННЯ СТОРІНКИ ТА ФІНАЛЬНИХ СТИЛІВ ---
st.set_page_config(
    page_title="CoreMind v0.4 Dark",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ФІНАЛЬНИЙ БЛОК CSS (ТЕМНА ТЕМА v2.1 з виправленим полем вводу) ---
st.markdown("""
<style>
    /* --- Глобальні --- */
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif; line-height: 1.6; }
    .stApp { background-color: #1E1E2E; color: #EAEAEA; }

    /* --- Заголовки --- */
    h1 { color: #FFFFFF; font-weight: 600; border-bottom: 2px solid #7F5AF0; padding-bottom: 2px; display: inline-block; margin-bottom: 0.5rem;}
    h2, h3 { color: #A0AEC0; font-weight: 500;}
    .stCaption { color: #A0AEC0; font-weight: 400;}
    .stCaption a { color: #7F5AF0; }

    /* --- Бічна Панель --- */
    [data-testid="stSidebar"] { background-color: #2A2A3A; border-right: 1px solid #3A3A4A; padding: 1.5rem 1.2rem; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #FFFFFF; font-weight: 600; margin-bottom: 1.5rem; }

    [data-testid="stSidebar"] .stButton>button {
        background-color: #7F5AF0; color: #FFFFFF; border: none; border-radius: 5px; width: 100%;
        margin-bottom: 0.8rem; padding: 0.7rem 1rem; font-weight: 500; text-align: left;
        transition: background-color 0.2s ease, transform 0.1s ease;
    }
    [data-testid="stSidebar"] .stButton>button:hover { background-color: #6A48D7; transform: translateY(-1px); color: #FFFFFF; }

    /* Іконки та особливі кнопки */
    [data-testid="stSidebar"] button:contains("Save Note")::before { content: "💾 "; }
    [data-testid="stSidebar"] button:contains("Rebuild Memory") { background-color: #6A48D7; } /* Темніший фіолетовий */
    [data-testid="stSidebar"] button:contains("Rebuild Memory")::before { content: "🔄 ";}
    [data-testid="stSidebar"] button:contains("Rebuild Memory"):hover { background-color: #5838B0; } /* Ще темніший */
    [data-testid="stSidebar"] button:contains("Clear Chat History") { background-color: #F93B5B; }
    [data-testid="stSidebar"] button:contains("Clear Chat History")::before { content: "🗑️ ";}
    [data-testid="stSidebar"] button:contains("Clear Chat History"):hover { background-color: #D61F4B; }

    [data-testid="stSidebar"] textarea {
        border: 1px solid #4A4A5A; border-radius: 8px; /* Заокруглення */
        background-color: #1E1E2E; color: #EAEAEA; min-height: 150px;
        resize: vertical; overflow-y: auto;
    }
    [data-testid="stSidebar"] label { color: #A0AEC0; font-weight: 500; margin-bottom: 0.5rem; }

    /* Стрілка згортання панелі */
    button[kind="minimal"] { opacity: 0.7 !important; }
    button[kind="minimal"] svg { fill: #A0AEC0 !important; }
    button[kind="minimal"]:hover { opacity: 1 !important; background-color: rgba(160, 174, 192, 0.1) !important; }

    /* --- Область Чату --- */
    .main .block-container { padding: 2rem 3rem; max-width: 950px; margin: auto; }

    /* --- Повідомлення Чату --- */
    [data-testid="stChatMessage"] {
        border-radius: 18px; padding: 1rem 1.4rem; margin-bottom: 1.2rem; border: none;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2); width: fit-content; max-width: 80%; word-wrap: break-word;
    }
    [data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) {
       margin-left: auto; background: linear-gradient(to right, #7F5AF0, #6A48D7); color: #FFFFFF;
    }
    [data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-assistant"]) {
       margin-right: auto; background-color: #2A2A3A; color: #EAEAEA; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] svg,
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] svg { width: 30px; height: 30px; }
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] svg { fill: #FFFFFF; }
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] svg { fill: #A0AEC0; }

    /* --- Спойлер (expander) для Джерел --- */
    .stExpander { background-color: rgba(42, 42, 58, 0.7); border: 1px dashed #4A4A5A; border-radius: 5px; margin-top: 0.8rem; }
    .stExpander header { color: #A0AEC0; font-size: 0.9em; font-weight: 500; }
    .stExpander header svg { fill: #A0AEC0; }
    .stExpander div[role="button"] { padding: 0.5rem 0.8rem; }
    .stExpander [data-testid="stCaptionContainer"] { font-size: 0.85em; color: #BDC3CF; padding-left: 0.5rem; }

    /* --- Поле Вводу Чату (ВИПРАВЛЕННЯ №2 - Заокруглене поле) --- */
    [data-testid="stChatInput"] {
        background-color: transparent !important; /* Фон контейнера прозорий */
        border-top: 1px solid #3A3A4A;
        padding: 0.8rem 1rem;
    }
    /* Прибираємо фон дочірнього div */
    [data-testid="stChatInput"] > div:first-child {
        background: none !important; border: none !important; box-shadow: none !important;
    }
    /* Форма всередині */
    [data-testid="stChatInput"] form {
        display: flex;
        align-items: center;
        gap: 8px; /* Невеликий відступ між полем та кнопкою */
    }

    .stTextInput { flex-grow: 1; } /* Контейнер текстового поля займає простір */
    .stTextInput>div>div>input { /* Саме текстове поле */
        background-color: #2A2A3A !important; /* Фон як у бічної панелі */
        color: #EAEAEA !important; /* Світлий текст */
        border: 1px solid #4A4A5A !important; /* Рамка */
        border-radius: 25px !important; /* ОСНОВНА ЗМІНА: Заокруглюємо саме поле */
        padding: 0.8rem 1.3rem !important; /* Внутрішні відступи */
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
        height: 48px; /* Фіксована висота для кращого вигляду */
        line-height: 1.5;
        box-shadow: none !important; /* Забираємо тінь */
    }
    .stTextInput>div>div>input:focus {
         border-color: #7F5AF0 !important;
         box-shadow: 0 0 0 3px rgba(127, 90, 240, 0.3) !important;
     }

    .stChatInput button { /* Кнопка відправки */
         background-color: #7F5AF0 !important; color: white !important;
         border: none; border-radius: 50%;
         width: 48px; height: 48px;
         flex-shrink: 0; /* Не стискати */
         display: flex; justify-content: center; align-items: center;
         transition: background-color 0.2s ease;
     }
    .stChatInput button:hover { background-color: #6A48D7 !important; }
    .stChatInput button svg { margin: 0; width: 20px; height: 20px; }

    /* --- Інші елементи --- */
    .stSpinner > div > div { border-top-color: #7F5AF0; }
    .stAlert { border-radius: 5px; padding: 1rem; color: #FFFFFF; border-left: 4px solid; }
    .stAlert[data-baseweb="alert"] > div:nth-child(2) { padding-top: 0.2rem; padding-bottom: 0.2rem;}
    /* Кольори ліній та фону для повідомлень */
    .stAlert.st-emotion-cache-1wivap2 { border-left-color: #00BFA5; background-color: rgba(0, 191, 165, 0.1); color: #00BFA5;} /* Success */
    .stAlert.st-emotion-cache-12ro0eu { border-left-color: #7F5AF0; background-color: rgba(127, 90, 240, 0.1); color: #7F5AF0;} /* Info */
    .stAlert.st-emotion-cache-1k1i9wy { border-left-color: #FFAB00; background-color: rgba(255, 171, 0, 0.1); color: #FFAB00;} /* Warning */
    .stAlert.st-emotion-cache-1gjd575 { border-left-color: #F93B5B; background-color: rgba(249, 59, 91, 0.1); color: #F93B5B;} /* Error */

</style>
""", unsafe_allow_html=True)
# --- КІНЕЦЬ ФІНАЛЬНОГО БЛОКУ CSS ---


# --- ОСНОВНИЙ КОД ДОДАТКУ ---
load_dotenv()
API_BASE_URL = "http://127.0.0.1:5000"

# --- 0. Інтерфейс Бічної Панелі (для керування пам'яттю) ---
st.sidebar.header("🧠 Living Memory") # Використаємо header
# st.sidebar.caption("Add new knowledge to the AI's brain.")
new_note_content = st.sidebar.text_area("Add a New Note:", height=150, key="new_note_area", label_visibility="collapsed", placeholder="Type your new knowledge here...")

if st.sidebar.button("Save Note", key="save_note"):
    if new_note_content.strip():
        try:
            response = requests.post(f"{API_BASE_URL}/add_note", json={"content": new_note_content})
            response.raise_for_status()
            data = response.json()
            st.sidebar.success(data.get("message", "Note saved!"))
            st.sidebar.info("Now, press 'Rebuild Memory' below.")
        except requests.exceptions.ConnectionError:
            st.sidebar.error(f"API Connection Error. Is api.py running?")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("Note cannot be empty.")

# Прибираємо (Re-index) з тексту кнопки
if st.sidebar.button("Rebuild Memory", key="rebuild_index"):
    with st.spinner("Sending command to rebuild memory..."):
        try:
            response = requests.post(f"{API_BASE_URL}/rebuild_index")
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                st.sidebar.success(data.get("message", "Memory rebuilt!"))
                st.info("Reloading app...")
                time.sleep(1)
                st.rerun()
            else:
                st.sidebar.error(f"Failed to rebuild: {data.get('message', 'Unknown error')}")
        except requests.exceptions.ConnectionError:
            st.sidebar.error(f"API Connection Error. Is api.py running?")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

st.sidebar.divider()
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []


# --- 1. Ініціалізація Історії Чату ---
st.title("CoreMind")
st.caption("Your personalized AI assistant powered by local knowledge.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. Відображення Історії Чату ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("context"):
            with st.expander("Show Sources Used"):
                for note in message["context"]:
                    st.caption(f"**(From: {note['source']})** {note['content'][:150]}...")

# --- 3. Інтерфейс Чату (Поле Вводу) ---
if prompt := st.chat_input("Ask Ana..."):
    try:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        messages_to_send = [msg.copy() for msg in st.session_state.messages]
        for msg in messages_to_send:
            msg.pop('context', None)

        with st.chat_message("assistant"):
            with st.spinner("Ana is thinking..."):
                response = requests.post(f"{API_BASE_URL}/query", json={"messages": messages_to_send})
                response.raise_for_status()
                data = response.json()

                response_text = data.get("response_text")
                found_context = data.get("found_context")

                st.markdown(response_text)

                if found_context:
                    with st.expander("Show Sources Used"):
                        for note in found_context:
                            st.caption(f"**(From: {note['source']})** {note['content'][:150]}...")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "context": found_context
                })

    except requests.exceptions.ConnectionError:
        st.error(f"Failed to connect to CoreMind API at {API_BASE_URL}. Is api.py running?")
    except Exception as e:
        st.error(f"An error occurred: {e}")