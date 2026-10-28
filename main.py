import uuid
import streamlit as st
from supabase import create_client

# NOTE: Streamlit >= 1.37 lagbe (st.fragment run_every er jonno).
# streamlit_autorefresh ar lagbe na, requirements.txt theke soriye dite paro.

# ==========================================
# PAGE SETTINGS
# ==========================================

st.set_page_config(
    page_title="WatchTogether",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 WatchTogether")
st.caption("Watch videos and chat with friends.")

# ==========================================
# SUPABASE CONNECTION
# ==========================================

@st.cache_resource
def get_supabase():
    url = st.secrets["https://qpsiuborxailivktpght.supabase.co"]
    key = st.secrets["sb_secret_gU8NQnHJVzfM2Z32bV52aw_JrKfn6wL"]
    return create_client(url, key)

try:
    supabase = get_supabase()
except Exception as error:
    st.error(
        "Supabase connection failed. "
        f"Check your Streamlit Secrets and API key. ({error})"
    )
    st.stop()

# ==========================================
# SESSION STATE
# ==========================================

if "room_id" not in st.session_state:
    st.session_state.room_id = ""

if "chat_name" not in st.session_state:
    st.session_state.chat_name = ""

# ==========================================
# CREATE / JOIN ROOM (room-e dhukle ar dekhabe na)
# ==========================================

if not st.session_state.room_id:
    st.subheader("🏠 Room")

    if st.button("➕ Create New Room", use_container_width=True):
        new_room_id = uuid.uuid4().hex[:8].upper()

        try:
            supabase.table("rooms").insert({"id": new_room_id}).execute()
            st.session_state.room_id = new_room_id
            st.rerun()
        except Exception as error:
            st.error(f"Could not create room: {error}")

    with st.form("join_room_form"):
        room_input = st.text_input(
            "Enter Room ID",
            placeholder="Example: A1B2C3D4"
        )
        join_clicked = st.form_submit_button("Join Room")

        if join_clicked:
            requested_room = room_input.strip().upper()

            if not requested_room:
                st.warning("Please enter a Room ID.")
            else:
                try:
                    response = (
                        supabase.table("rooms")
                        .select("id")
                        .eq("id", requested_room)
                        .limit(1)
                        .execute()
                    )

                    if response.data:
                        st.session_state.room_id = requested_room
                        st.rerun()
                    else:
                        st.error("Room not found.")
                except Exception as error:
                    st.error(f"Could not join room: {error}")

    st.info("Create a new room or join an existing room.")
    st.stop()

room_id = st.session_state.room_id

# ==========================================
# ROOM HEADER
# ==========================================

st.success(f"Connected to Room: {room_id}")
st.code(f"Room ID: {room_id}", language="text")
st.caption(
    "Share your deployed website link and this Room ID "
    "with your friends."
)

if st.button("Leave Room"):
    st.session_state.room_id = ""
    st.rerun()

st.divider()

# ==========================================
# CHAT FRAGMENT
# Shudhu chat part ta every 3 seconds refresh hobe,
# tai video bar bar reload/restart hobe na.
# ==========================================

@st.fragment(run_every=3)
def chat_box(current_room: str):
    # Latest 100 message ana: desc order e niye pore ulte dei
    # (age asc + limit e shudhu purono 100 ta ashto)
    try:
        chat_response = (
            supabase.table("messages")
            .select("id, name, message, created_at")
            .eq("room_id", current_room)
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )
        messages = list(reversed(chat_response.data or []))
    except Exception as error:
        st.error(f"Could not load messages: {error}")
        messages = []

    box = st.container(height=420)
    with box:
        if not messages:
            st.caption("No messages yet. Say hi 👋")
        for item in messages:
            with st.chat_message(item["name"]):
                # st.text use kora hoyeche jate markdown/link injection na hoy
                st.text(item["message"])

    with st.form(f"chat_form_{current_room}", clear_on_submit=True):
        message_text = st.text_input("Write a message", max_chars=2000)
        send_clicked = st.form_submit_button("Send", use_container_width=True)

        if send_clicked:
            name = st.session_state.chat_name.strip()
            message = message_text.strip()

            if not name or not message:
                st.warning("Enter your name and a message.")
            else:
                try:
                    supabase.table("messages").insert({
                        "room_id": current_room,
                        "name": name,
                        "message": message
                    }).execute()
                    # Shudhu fragment rerun, video disturb hobe na
                    st.rerun(scope="fragment")
                except Exception as error:
                    st.error(f"Could not send message: {error}")

# ==========================================
# VIDEO AND CHAT LAYOUT
# ==========================================

video_column, chat_column = st.columns([2, 1], gap="large")

with video_column:
    st.subheader("🎥 Video Player")

    uploaded_video = st.file_uploader(
        "Choose a video from your PC",
        type=["mp4", "webm", "mov"],
        key=f"video_{room_id}"
    )

    if uploaded_video is not None:
        st.video(uploaded_video)
        st.caption(
            "This video is currently available in your "
            "browser session only. Other room members "
            "cannot see it yet."
        )
    else:
        st.info("Upload a small video to test playback.")

    st.warning(
        "Playback synchronization and shared video storage "
        "are not implemented in this version."
    )

with chat_column:
    st.subheader("💬 Live Chat")

    # key diyei session_state e save hoy, alada value= dorkar nei
    st.text_input("Your name", max_chars=50, key="chat_name")

    chat_box(room_id)

st.divider()
st.caption("WatchTogether Demo | Streamlit + Supabase")
