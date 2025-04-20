import streamlit as st
import requests
import json
import time
from PIL import Image
from config import BACKEND_URL
import io
import base64

# Page config
st.set_page_config(
    page_title="Chat with Optional Images",
    page_icon="💬",
    layout="centered"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Hide file uploader label */
    .stFileUploader > div > label {
        font-size: 0;
    }
    
    /* Image preview styling */
    .image-preview {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* File uploader area styling */
    .upload-area {
        margin-bottom: 1rem;
        padding: 10px;
        border-radius: 8px;
        background-color: #f7f7f9;
    }
    
    /* Attachment button styling */
    .attachment-btn {
        position: relative;
        top: 5px;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Backend URL

st.title("Chat Assistant 💬")
st.write("Ask questions or share images when needed.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you today?"}]

# Track if image upload is being shown
if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = False

# Function to toggle image uploader visibility
def toggle_uploader():
    st.session_state.show_uploader = not st.session_state.show_uploader

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image_display" in message and message["image_display"]:
            st.image(message["image_display"], width=300)

# Optional image upload area
uploaded_file = None

# Create a layout with columns for the attachment button and spacer
cols = st.columns([1, 20])
with cols[0]:
    st.markdown('<div class="attachment-btn">', unsafe_allow_html=True)
    st.button("📎", on_click=toggle_uploader, key="attachment_button", help="Attach an image")
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.show_uploader:
    st.markdown("<div class='upload-area'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload an image", 
                                    type=["png", "jpg", "jpeg"], 
                                    key="image_upload",
                                    label_visibility="collapsed")
    
    # Show image preview if uploaded
    if uploaded_file:
        st.image(uploaded_file, caption="Image preview", width=300)  # Display the image in a smaller box
    st.markdown("</div>", unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Process the uploaded image if any
    image_data = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_data = image_bytes.getvalue()
    
    # Add user message to chat history - Store display image separately
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt,
        "image_display": image_data  # This is only for display purposes
    })
    
    # Display user message in chat
    with st.chat_message("user"):
        st.markdown(prompt)
        if image_data:
            st.image(image_data,width=300)  # Display in a smaller box
    
    # Format history for backend - exclude image data
    formatted_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages[:-1]  # Exclude the latest message
    ]
    
    # Prepare the payload
    payload = {
        "message": prompt,
        "history": formatted_history
    }
    
    # Add image to payload if present
    if image_data:
        # Convert image data to base64 string
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        payload["image"] = image_base64
    
    # Display assistant message with streaming
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Send request with stream=True to get streaming response
            with requests.post(BACKEND_URL, json=payload, stream=True) as response:
                if response.status_code == 200:
                    # Process the streaming response
                    for line in response.iter_lines():
                        if line:
                            # Decode the line
                            line_text = line.decode('utf-8')
                            
                            # Handle different streaming formats
                            # Some servers might send "data: " prefixed SSE events
                            if line_text.startswith('data: '):
                                line_text = line_text[6:]  # Remove 'data: ' prefix
                                
                            # Try to parse as JSON if it looks like JSON
                            try:
                                if line_text.strip().startswith('{'):
                                    json_data = json.loads(line_text)
                                    # Extract text from common JSON formats
                                    if 'text' in json_data:
                                        chunk = json_data['text']
                                    elif 'content' in json_data:
                                        chunk = json_data['content']
                                    elif 'delta' in json_data and 'content' in json_data['delta']:
                                        chunk = json_data['delta']['content']
                                    else:
                                        chunk = line_text
                                else:
                                    chunk = line_text
                            except json.JSONDecodeError:
                                chunk = line_text
                                
                            # Update the response
                            full_response += chunk
                            # Add a blinking cursor to simulate typing
                            message_placeholder.markdown(full_response + "▌")
                            
                    # Final update without cursor
                    message_placeholder.markdown(full_response)
                else:
                    error_msg = f"Error: Received status code {response.status_code} from backend"
                    message_placeholder.markdown(error_msg)
                    full_response = error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Error connecting to backend: {str(e)}"
            message_placeholder.markdown(error_msg)
            full_response = error_msg
    
    # Add assistant response to chat history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response,
        "image_display": None
    })
    
    # Reset image uploader state
    st.session_state.show_uploader = False
    st.rerun()


