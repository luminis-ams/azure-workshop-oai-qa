from typing import List

import streamlit as st
from dotenv import load_dotenv
from langchain.callbacks import StreamlitCallbackHandler
from langchain.schema import ChatMessage, Document

from workshop_oai_qa.chain import AssistantMessage
from workshop_oai_qa.resources import conversation_chain
from workshop_oai_qa.utils import role_from_message

st.set_page_config(
    page_title='Luminis Azure OpenAI QA Workshop',
    layout='centered',
    initial_sidebar_state=st.session_state.get('sidebar_state', 'expanded')
)

st.session_state.sidebar_state = 'expanded'


def main():
    st.title('Luminis Azure OpenAI QA Workshop')

    # Store LLM generated responses
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [ChatMessage(role='assistant', content='How may I help you?')]

    with st.sidebar:
        sidebar_content = st.empty()

    with sidebar_content.container():
        st.markdown('Click on a citation to view it\'s content.')

    chat_window_container = st.container()

    st.session_state.sidebar_content = sidebar_content
    st.session_state.chat_window_container = chat_window_container

    chat_window()


def chat_window():
    with st.session_state.chat_window_container:
        # Display chat messages
        for i, message in enumerate(st.session_state.messages):
            role = role_from_message(message)

            with st.chat_message(role):
                if isinstance(message, AssistantMessage):
                    st.write(message.formatted_content)
                    followup_block(message.follow_ups, id=i)
                    citations_block(message.citations, id=i)
                else:
                    st.write(message.content)

    # User-provided prompt
    if prompt := st.chat_input(disabled=False):
        on_chat_input(prompt)


def followup_block(follow_ups: List[str], id=None):
    for j, follow_up in enumerate(follow_ups):
        if st.button(
            follow_up,
            type='secondary',
            key=f'followup-{id}-{j}',
        ):
            on_followup_click(follow_up)


def citations_block(citations: List[Document], id=None):
    if not citations:
        return

    with st.expander(f"{len(citations)} references"):
        for j, citation in enumerate(citations):
            if st.button(
                f'🔗  {j}. {citation.metadata["source"]}',
                key=f'citation-{id}-{j}',
            ):
                on_citation_click(citation)


def on_followup_click(follow_up):
    with st.session_state.chat_window_container:
        on_chat_input(follow_up)


def on_citation_click(citation):
    with st.session_state.sidebar_content.container():
        st.markdown(citation.page_content, unsafe_allow_html=True)


def on_chat_input(prompt):
    st.session_state.messages.append(ChatMessage(role='user', content=prompt))
    with st.chat_message("user"):
        st.write(prompt)

    # Generate a new response if last message is not from assistant
    with st.chat_message("assistant"):
        message = on_generate_response(st.session_state.messages)
        st.session_state.messages.append(message)

    # Rerender the chat now messages have been updated
    st.rerun()


def on_generate_response(messages) -> AssistantMessage:
    message_placeholder = st.empty()

    st_cb = StreamlitCallbackHandler(message_placeholder.container(), expand_new_thoughts=False)

    chain = conversation_chain()
    output = chain({
        'input': messages[-1].content,
        'callbacks': [st_cb],
        'history': messages[:-1],
    })

    return output['reply']


if __name__ == '__main__':
    load_dotenv()

    main()
