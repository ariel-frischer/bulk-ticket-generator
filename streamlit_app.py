import streamlit as st
from greptile import GreptileAPI
import uuid
import os
import time
import json
from pathlib import Path

# Set session state variables from environment variables at startup
st.session_state.greptile_api_key = os.environ.get("GREPTILE_API_KEY", "")
st.session_state.github_token = os.environ.get("GITHUB_TOKEN", "")

st.set_page_config(
    page_title="Batch Issue Generator", page_icon="🎫", layout="centered"
)
st.title("🎫 Batch Ticket Generator")
st.markdown(
    """
    * Generate multiple Github issues based on a prompt and an issue template.
    * Instead of painstakingly creating issues one by one, this app allows bulk generation of issues through leveraging LLMs. 
    * Utilizes Greptile to give codebase-related context to the issue generator.
    """
)

if st.session_state.greptile_api_key and os.environ.get("GREPTILE_API_KEY"):
    st.info("Greptile API Key has been prefilled from the environment variable.")
if st.session_state.github_token and os.environ.get("GITHUB_TOKEN"):
    st.info("GitHub Token has been prefilled from the environment variable.")

st.text_input(
    "Greptile API Key (required)",
    type="password",
    key="greptile_api_key_input",
    value=st.session_state.greptile_api_key,
    on_change=lambda: setattr(
        st.session_state, "greptile_api_key", st.session_state.greptile_api_key_input
    ),
)
st.text_input(
    "GitHub Token (required)",
    type="password",
    key="github_token_input",
    value=st.session_state.github_token,
    on_change=lambda: setattr(
        st.session_state, "github_token", st.session_state.github_token_input
    ),
)


def are_api_keys_provided():
    return bool(st.session_state.greptile_api_key) and bool(
        st.session_state.github_token
    )


st.header("GitHub Repository")
col1, col2, col3 = st.columns(3)
with col1:
    remote = st.text_input("Remote", value="github")
with col2:
    repository = st.text_input("Repository", value="ariel-frischer/alias-gen")
with col3:
    branch = st.text_input("Branch", value="main")

greptile = GreptileAPI(st.session_state.greptile_api_key, st.session_state.github_token)


def load_templates(template_dir):
    templates = {}
    for filename in os.listdir(template_dir):
        if filename.endswith(".md"):
            with open(os.path.join(template_dir, filename), "r") as file:
                templates[filename[:-3]] = file.read()
    return templates


ticket_templates = load_templates("ticket_templates")
prompt_templates = load_templates("prompt_templates")

st.header("Phase 1 - Generate Ticket List Overview")
st.markdown(
    "Instruct the LLM generate a list of generalized tickets before creating each in detail."
)

selected_prompt_template = st.selectbox(
    "Select a prompt template:", list(prompt_templates.keys())
)

prompt = st.text_area(
    "Enter some generalized high-level (epic) prompt here:",
    height=300,
    value=prompt_templates[selected_prompt_template],
)

num_tickets = st.number_input(
    "Number of tickets to generate:", min_value=1, max_value=10, value=1
)
prompt_mod = f"Create up to {num_tickets} tickets based on the following prompt:"
st.info(
    "Will automatically index your repository with Greptile if it hasn't already been indexed."
)
response_format_prompt = """
    Each ticket title and description should be distinct from one another.
    You must respond in JSON format with the following structure: "tickets": List[Object], 
    Where each Object has the following keys:
    title: str, body: str, labels: List[str]
    Do not response with any code brackets like ```json ONLY respond in pure JSON.
"""

greptile_content = prompt_mod + "\n" + prompt + "\n" + response_format_prompt

if st.button("Create Ticket List", disabled=not are_api_keys_provided()):
    if repository:
        message_id = str(uuid.uuid4())
        try:
            mock_file = os.environ.get("MOCK_FILE")
            if mock_file and Path(mock_file).is_file():
                st.info(f"Using mock data from {mock_file}")
                with open(mock_file, "r") as f:
                    response_json = json.load(f)
            else:
                with st.spinner("Ensuring repository is indexed..."):
                    greptile.ensure_repository_indexed(remote, repository, branch)

                indexing_status = False
                with st.spinner("Checking if repository is indexed..."):
                    for _ in range(90):  # 15 minutes timeout (90 * 10 seconds)
                        if greptile.is_repository_indexed(remote, repository, branch):
                            indexing_status = True
                            break
                        time.sleep(10)

                if not indexing_status:
                    st.error(
                        "Repository indexing timed out after 15 minutes. Check your email to see if the repository has been indexed then try again."
                    )

                st.toast("Repository is indexed.")

                with st.spinner("Querying Greptile..."):
                    response = greptile.query(
                        messages=[
                            {
                                "id": message_id,
                                "content": greptile_content,
                                "role": "user",
                            },
                        ],
                        repositories=[
                            {
                                "remote": remote,
                                "repository": repository,
                                "branch": branch,
                            }
                        ],
                        genius=False,
                    )

                st.success("Query completed successfully!")
                response_json = response.json()

            with st.expander("See Full Response JSON"):
                st.json(response_json)

            sources = response_json.get("sources", [])
            message = response_json.get("message", "")

            # Function to extract tickets from the message
            def extract_tickets(msg):
                if isinstance(msg, dict) and "tickets" in msg:
                    return msg["tickets"]
                elif isinstance(msg, str):
                    try:
                        parsed = json.loads(msg)
                        if isinstance(parsed, dict) and "tickets" in parsed:
                            return parsed["tickets"]
                    except json.JSONDecodeError:
                        pass
                return None

            tickets = extract_tickets(message)

            if tickets is not None:
                if len(tickets) != num_tickets and not mock_file:
                    st.warning(
                        f"Warning: The number of tickets generated ({len(tickets)}) does not match the requested number ({num_tickets})."
                    )

                st.subheader("Generated Tickets")
                st.info("Double-click on a row to edit the ticket.")
                edited_tickets = st.data_editor(
                    tickets,
                    column_config={
                        "title": st.column_config.TextColumn("Title", width="medium"),
                        "body": st.column_config.TextColumn("Body", width="large"),
                        "labels": st.column_config.ListColumn("Labels", width="medium"),
                    },
                    num_rows="dynamic",
                    width=None,
                )
            else:
                st.error(
                    "Unable to extract tickets from the response. Please check the Greptile API response format."
                )
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.error("Please enter a repository name.")

st.markdown("---")

with st.container(border=True):
    st.header("Github Issue Format")

    selected_template = st.selectbox(
        "Select a template:", list(ticket_templates.keys())
    )

    if "preview_mode" not in st.session_state:
        st.session_state.preview_mode = False

    def toggle_preview():
        st.session_state.preview_mode = not st.session_state.preview_mode

    st.button(
        "Preview Markdown" if not st.session_state.preview_mode else "Edit",
        on_click=toggle_preview,
    )

    if st.session_state.preview_mode:
        st.markdown(ticket_templates[selected_template])
    else:
        ticket_format = st.text_area(
            "Edit the ticket format:",
            value=ticket_templates[selected_template],
            height=300,
        )


if st.button("Generate Tickets", disabled=not are_api_keys_provided()):
    st.header("Generated Tickets")
    for i in range(num_tickets):
        st.subheader(f"Ticket {i+1}")
        st.markdown(
            ticket_format
            if not st.session_state.preview_mode
            else ticket_templates[selected_template]
        )
        st.markdown("---")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Created by Ariel Frischer | "
    "<a href='mailto:arielfrischer@gmail.com'>arielfrischer@gmail.com</a>"
    "</div>",
    unsafe_allow_html=True,
)
