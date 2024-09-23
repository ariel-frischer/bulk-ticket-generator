import streamlit as st
from greptile import GreptileAPI
import os
import asyncio
from ticket_list import create_ticket_list, display_and_edit_tickets
from detailed_tickets import display_detailed_tickets

st.session_state.greptile_api_key = os.environ.get("GREPTILE_API_KEY", "")
st.session_state.github_token = os.environ.get("GITHUB_TOKEN", "")

is_prod = os.environ.get("STREAMLIT_ENV", "development") == "production"

st.set_page_config(
    page_title="Bulk Ticket Generator", page_icon="🎫", layout="centered"
)
st.title("🎫 Bulk Ticket Generator")
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
)
st.text_input(
    "GitHub Token (required)",
    type="password",
    key="github_token_input",
    value=st.session_state.github_token,
)


def api_keys_provided():
    return bool(st.session_state.greptile_api_key_input) and bool(
        st.session_state.github_token_input
    )


st.header("GitHub Repository")
col1, col2, col3 = st.columns(3)
with col1:
    remote = st.text_input(
        "Remote",
        value="github",
        disabled=True,
        help="Only support github repositories for now.",
    )
with col2:
    val = "ariel-frischer/alias-gen" if not is_prod else ""
    repository = st.text_input(
        "Repository",
        value=val,
        placeholder="ariel-frischer/alias-gen",
    )
with col3:
    branch = st.text_input("Branch", value="main")

greptile = GreptileAPI(
    st.session_state.greptile_api_key_input, st.session_state.github_token_input
)


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
    "Instruct the LLM generate a list of generalized tickets before creating each in detail. Uses one Greptile query request."
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
st.markdown(
    "Will automatically index your repository with Greptile if it hasn't already been indexed."
)
response_format_prompt = f"""
    Create precise and atomic tickets. Each ticket should focus on implementing one specific feature, fixing one particular bug, or addressing one distinct aspect of the project.
    If you cannot create all specified tasks given the limited number of tickets, that is ok just choose the first {num_tickets} to create in a reasonable order.
    
    Guidelines for ticket creation:
    1. Title: Make it specific and descriptive. It should clearly indicate the single task or feature being addressed.
    2. Description: Provide a brief but clear explanation of what needs to be done. Focus on the 'what' and 'why', not the 'how'.
    3. Scope: Ensure each ticket represents a single, self-contained unit of work that can be completed independently.
    4. Clarity: Avoid vague or general descriptions. Be as specific as possible about what needs to be accomplished.
    5. Atomicity: If a proposed task seems too large or complex, break it down into smaller, more manageable tickets.
    6. Decisions: If there ever is a decision to be made, make it in the ticket body. Choose frameworks that are popular and stable.

    You must respond in JSON format with the following structure: "tickets": List[Object], 
    Where each Object has the following keys:
    title: str, body: str, labels: List[str]
    
    Ensure each ticket title and description is distinct from the others.
    Do not include any code brackets like ```json. ONLY respond in pure JSON.
"""

greptile_content = prompt_mod + "\n" + prompt + "\n" + response_format_prompt

if "create_ticket_list_state" not in st.session_state:
    st.session_state.create_ticket_list_state = False
if "tickets" not in st.session_state:
    st.session_state.tickets = None

button_disabled = not api_keys_provided() or not repository or not branch
help_text = (
    "Must Provide Greptile API Key and GitHub Token and repository info."
    if button_disabled
    else None
)
if st.button("Create Ticket List", disabled=button_disabled, help=help_text):
    st.session_state.create_ticket_list_state = True
    if repository:

        async def run_create_ticket_list():
            st.session_state.tickets = await create_ticket_list(
                repository,
                remote,
                branch,
                greptile,
                greptile_content,
                num_tickets,
            )

        asyncio.run(run_create_ticket_list())
    else:
        st.error("Please enter a repository name.")

if st.session_state.create_ticket_list_state and st.session_state.tickets is not None:
    display_and_edit_tickets(st.session_state.tickets)

display_detailed_tickets(
    num_tickets,
    api_keys_provided,
    greptile,
    repository,
    remote,
    branch,
    st.session_state.github_token_input,
)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Created by Ariel Frischer | "
    "<a href='mailto:arielfrischer@gmail.com'>arielfrischer@gmail.com</a>"
    "</div>",
    unsafe_allow_html=True,
)
