from langchain_openai.chat_models.base import ChatOpenAI
from langchain_core.messages.utils import  messages_from_dict
from langchain_core.messages.base import messages_to_dict
from langchain_core.messages.human import HumanMessage
import streamlit as st
import os
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


API_KEY = os.getenv("OVH_API_KEY")
if "history" not in st.session_state:
    st.session_state.history = []
if "conv_title" not in st.session_state:
    st.session_state.conv_title = None
if "conv" not in st.session_state:
    st.session_state.conv = None
if "conversation_list" not in st.session_state:
    st.session_state.conversation_list = os.listdir("conversations")

# Create LLM list
llama3 = ChatOpenAI(
    base_url='https://llama-3-70b-instruct.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1',
    api_key= API_KEY,
    model="Meta-Llama-3-70B-Instruct"
    )
codellama = ChatOpenAI(base_url='https://codellama-13b-instruct-hf.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1',
                       api_key= API_KEY,
                       model="CodeLlama-13b-Instruct-hf"
                       )
llms = ["llama3", "codellama"]
models = {"llama3": llama3, "codellama": codellama}
def set_conv(conv):
    with open(f"conversations/{conv}") as f:
        conversation = f.read()
        info = json.loads(conversation)
    st.session_state.history = messages_from_dict(info["history"])
    st.session_state.conv_title = info["title"]
    st.session_state.conv = conv

def new_conv(title):
    conv = title + ".json"
    json_conv = {"title": title, "history": []}
    if conv in os.listdir("conversations"):
        st.error("Conversation with that title already exists")
        return
    #create a new conversation file in the directory ./conversations
    with open(f"conversations/{conv}", "w") as f:
        f.write(json.dumps(json_conv))
    set_conv(conv)
    st.session_state.conversation_list = os.listdir("conversations")

# Sidebar
sidebar = st.sidebar.header("OVH Chatbot")
model = st.sidebar.selectbox("Model", llms)
st.sidebar.subheader("Conversations")
#display it as a streamlit scrollable buttons list in the sidebar
if st.session_state.conversation_list:
    for conv in st.session_state.conversation_list:
        if st.sidebar.button(conv, use_container_width=True):
            set_conv(conv)

with st.sidebar.popover("New conversation"):
    st.markdown("Start a new conversation")
    if title := st.text_input("Title"):
        new_conv(title)
        st.session_state.conversation_list = os.listdir("conversations")
st.sidebar.write(f"Current conversation: {st.session_state.conv_title}")



# Main -> Conversation display and chat
if not st.session_state.conv_title:
    st.title( "Waiting for conversation selection")
else:
    st.title(st.session_state.conv_title)
    if not st.session_state.history:
        st.write("No messages yet")
        st.session_state.history = []
    prompt = st.chat_input("Type a message")
    if prompt :
        st.session_state.history.append(HumanMessage(prompt))
        response = models[model].invoke(st.session_state.history)
        st.session_state.history.append(response)
        json_conv = {"title": st.session_state.conv_title, "history": messages_to_dict(st.session_state.history)}
        with open(f"conversations/{st.session_state.conv}", "w") as f:
            f.write(json.dumps(json_conv))
    if st.session_state.history:
        for message in st.session_state.history:
            st.chat_message(message.type).markdown(message.content)
