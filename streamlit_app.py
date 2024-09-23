import os
import streamlit as st
from greptile import GreptileAPI
import uuid

# Show app title and description
st.set_page_config(page_title="Batch Ticket Generator", page_icon="🎫")
st.title("🎫 Batch Ticket Generator")
st.write(
    """
    This app allows you to generate multiple JIRA tickets based on a prompt and a selected template.
    You can edit the prompt and the ticket format, then generate multiple tickets at once.
    It also uses Greptile to query a GitHub repository for additional context.
    """
)

# Greptile repository input
st.header("GitHub Repository")
col1, col2, col3 = st.columns(3)
with col1:
    remote = st.text_input("Remote", value="github")
with col2:
    repository = st.text_input("Repository", value="ariel-frischer/bmessages.nvim")
with col3:
    branch = st.text_input("Branch", value="main")

# Initialize Greptile API
greptile = GreptileAPI()


# Function to load templates
def load_templates():
    templates = {}
    template_dir = "ticket_templates"
    for filename in os.listdir(template_dir):
        if filename.endswith(".md"):
            with open(os.path.join(template_dir, filename), "r") as file:
                templates[filename[:-3]] = file.read()
    return templates


# Load templates
templates = load_templates()

# Prompt input and Greptile query
st.header("Prompt")
prompt = st.text_area("Enter your prompt here:", height=150)

if st.button("Query Repository"):
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

# Add a divider after the prompt
st.markdown("---")


# Create an outlined box for the JIRA ticket format section
with st.container(border=True):
    # Template selection and editing
    st.header("JIRA Ticket Format")

    selected_template = st.selectbox("Select a template:", list(templates.keys()))

    # Add a button to switch between edit and preview modes
    if "preview_mode" not in st.session_state:
        st.session_state.preview_mode = False

    def toggle_preview():
        st.session_state.preview_mode = not st.session_state.preview_mode

    # col1, col2, col3 = st.columns([3, 1])
    # with col2:
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

if st.button("Generate Tickets"):
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

# Display the prompt for reference
# st.sidebar.header("Prompt Reference")
# st.sidebar.markdown(prompt)
