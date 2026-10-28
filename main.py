
import uuid
import streamlit as st
from supabase import create_client
from streamlit_autorefresh import st_autorefresh

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
except Exception:
    st.error(
        "Supabase connection failed. "
        "Check your Streamlit Secrets and API key."
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
# CREATE ROOM
# ==========================================

st.subheader("🏠 Room")

if st.button("➕ Create New Room", use_container_width=True):
    new_room_id = uuid.uuid4().hex[:8].upper()

    try:
        supabase.table("rooms").insert({
            "id": new_room_id
        }).execute()

        st.session_state.room_id = new_room_id
        st.rerun()

    except Exception as error:
        st.error(f"Could not create room: {error}")

# ==========================================
# JOIN ROOM
# ==========================================

with st.form("join_room_form"):
    room_input = st.text_input(
        "Enter Room ID",
        value=st.session_state.room_id,
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

room_id = st.session_state.room_id

# ==========================================
# ROOM CONTENT
# ==========================================

if not room_id:
    st.info("Create a new room or join an existing room.")
    st.stop()

st.success(f"Connected to Room: {room_id}")

st.code(
    f"Room ID: {room_id}",
    language="text"
)

st.caption(
    "Share your deployed website link and this Room ID "
    "with your friends."
)

if st.button("Leave Room"):
    st.session_state.room_id = ""
    st.rerun()

st.divider()

# Refresh page every 3 seconds to retrieve new chat messages.
# This is polling, not true Supabase Realtime.
st_autorefresh(
    interval=3000,
    key=f"refresh_{room_id}"
)

# ==========================================
# VIDEO AND CHAT LAYOUT
# ==========================================

video_column, chat_column = st.columns(
    [2, 1],
    gap="large"
)

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

# ==========================================
# CHAT
# ==========================================

with chat_column:
    st.subheader("💬 Live Chat")

    st.session_state.chat_name = st.text_input(
        "Your name",
        value=st.session_state.chat_name,
        max_chars=50,
        key="name_input"
    )

    try:
        chat_response = (
            supabase.table("messages")
            .select("id, name, message, created_at")
            .eq("room_id", room_id)
            .order("created_at", desc=False)
            .limit(100)
            .execute()
        )

        for chat_item in chat_response.data:
            st.markdown(
                f"**{chat_item['name']}**: "
                f"{chat_item['message']}"
            )

    except Exception as error:
        st.error(f"Could not load messages: {error}")

    with st.form(
        f"chat_form_{room_id}",
        clear_on_submit=True
    ):
        message_text = st.text_input(
            "Write a message",
            max_chars=2000
        )

        send_clicked = st.form_submit_button(
            "Send",
            use_container_width=True
        )

        if send_clicked:
            name = st.session_state.chat_name.strip()
            message = message_text.strip()

            if not name or not message:
                st.warning("Enter your name and a message.")

            else:
                try:
                    supabase.table("messages").insert({
                        "room_id": room_id,
                        "name": name,
                        "message": message
                    }).execute()

                    st.rerun()

                except Exception as error:
                    st.error(f"Could not send message: {error}")

st.divider()

st.caption(
    "WatchTogether Demo | Streamlit + Supabase"
)
