import streamlit as st
from greptile import GreptileAPI
import uuid
import os

st.set_page_config(page_title="Batch Issue Generator", page_icon="🎫")
st.title("🎫 Batch Ticket Generator")
st.markdown(
    """
    * Generate multiple Github issues based on a prompt and an issue template.
    * Instead of painstakingly creating issues one by one, this app allows bulk generation of issues through leveraging LLMs. 
    * Utilizes Greptile to give codebase-related context to the issue generator.
    """
)

for key in ["greptile_api_key", "github_token"]:
    if key not in st.session_state:
        st.session_state[key] = ""

greptile_api_key = os.environ.get("GREPTILE_API_KEY", "")
github_token = os.environ.get("GITHUB_TOKEN", "")

if greptile_api_key:
    st.info("Greptile API Key has been prefilled from the environment variable.")
if github_token:
    st.info("GitHub Token has been prefilled from the environment variable.")

st.text_input(
    "Greptile API Key (required)",
    type="password",
    key="greptile_api_key_input",
    value=greptile_api_key,
    on_change=lambda: setattr(
        st.session_state, "greptile_api_key", st.session_state.greptile_api_key_input
    ),
)
st.text_input(
    "GitHub Token (required)",
    type="password",
    key="github_token_input",
    value=github_token,
    on_change=lambda: setattr(
        st.session_state, "github_token", st.session_state.github_token_input
    ),
)


def are_api_keys_provided():
    return bool(
        os.environ.get("GREPTILE_API_KEY") or st.session_state.greptile_api_key
    ) and bool(os.environ.get("GITHUB_TOKEN") or st.session_state.github_token)


st.header("GitHub Repository")
col1, col2, col3 = st.columns(3)
with col1:
    remote = st.text_input("Remote", value="github")
with col2:
    repository = st.text_input("Repository", value="ariel-frischer/alias-gen")
with col3:
    branch = st.text_input("Branch", value="main")

greptile = GreptileAPI()


def load_templates():
    templates = {}
    template_dir = "ticket_templates"
    for filename in os.listdir(template_dir):
        if filename.endswith(".md"):
            with open(os.path.join(template_dir, filename), "r") as file:
                templates[filename[:-3]] = file.read()
    return templates


templates = load_templates()

st.header("Phase 1 - Generate Ticket List Overview")
prompt = st.text_area(
    "Enter some generalized high-level (epic) prompt here:",
    height=150,
    placeholder="Generate a list of common python software development tasks to setup a comprehensive developer workflow including linting, formatting, etc...",
)

if st.button("Query Repository", disabled=not are_api_keys_provided()):
    if repository:
        message_id = str(uuid.uuid4())
        response = greptile.query(
            messages=[{"id": message_id, "content": prompt, "role": "user"}],
            repositories=[
                {"remote": remote, "repository": repository, "branch": branch}
            ],
            genius=False,
        )
        with st.container(border=True):
            st.write("Greptile Response:")
            st.json(response.json())
    else:
        st.error("Please enter a repository name.")

st.markdown("---")

with st.container(border=True):
    st.header("JIRA Ticket Format")

    selected_template = st.selectbox("Select a template:", list(templates.keys()))

    if "preview_mode" not in st.session_state:
        st.session_state.preview_mode = False

    def toggle_preview():
        st.session_state.preview_mode = not st.session_state.preview_mode

    st.button(
        "Preview Markdown" if not st.session_state.preview_mode else "Edit",
        on_click=toggle_preview,
    )

    if st.session_state.preview_mode:
        st.markdown(templates[selected_template])
    else:
        ticket_format = st.text_area(
            "Edit the ticket format:", value=templates[selected_template], height=300
        )

num_tickets = st.number_input(
    "Number of tickets to generate:", min_value=1, max_value=10, value=1
)

if st.button("Generate Tickets", disabled=not are_api_keys_provided()):
    st.header("Generated Tickets")
    for i in range(num_tickets):
        st.subheader(f"Ticket {i+1}")
        st.markdown(
            ticket_format
            if not st.session_state.preview_mode
            else templates[selected_template]
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
