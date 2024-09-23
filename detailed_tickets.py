import streamlit as st
import os
import json
from github import Auth, Github
from greptile import GreptileAPI
import asyncio
import aiohttp

# New prompt string for detailed ticket generation
DETAILED_TICKET_PROMPT = """
Create a detailed ticket based on the following information. Make concrete decisions, do not list multiple implementations or frameworks. Give full, comprehensive, atomic task details to accomplish this task:

Title: {task_title}
Description: {task_body}
Labels: {task_labels}

Please provide a comprehensive and detailed ticket that includes:
1. A clear and specific description of the task
2. Step-by-step implementation details
3. Any potential challenges or considerations
4. Acceptance criteria
5. Any relevant technical specifications or requirements

Ensure the response is thorough and actionable, providing all necessary information for a developer to complete the task without ambiguity.

You must respond in JSON format with the following structure: "tickets": List[Object], 
Where each Object has the following keys:
title: str, body: str, labels: List[str]
Do not response with any code brackets like ```json ONLY respond in pure JSON.
"""


def load_templates(template_dir):
    templates = {}
    for filename in os.listdir(template_dir):
        if filename.endswith(".md"):
            with open(os.path.join(template_dir, filename), "r") as file:
                templates[filename[:-3]] = file.read()
    return templates


async def create_detailed_ticket(
    ticket, ticket_format, greptile, repository, remote, branch
):
    prompt = (
        DETAILED_TICKET_PROMPT.format(
            task_title=ticket["title"],
            task_body=ticket["body"],
            task_labels=", ".join(ticket["labels"]),
        )
        + "\n\n"
        + ticket_format
    )

    response_json = await greptile.query_async(
        messages=[{"content": prompt, "role": "user"}],
        repositories=[{"remote": remote, "repository": repository, "branch": branch}],
        genius=False,
    )

    # Save the response JSON in session state
    if "detailed_tickets_response_json" not in st.session_state:
        st.session_state.detailed_tickets_response_json = []
    st.session_state.detailed_tickets_response_json.append(response_json)

    message = response_json.get("message", "")

    try:
        ticket_data = json.loads(message)
        if "tickets" in ticket_data and len(ticket_data["tickets"]) > 0:
            detailed_ticket = ticket_data["tickets"][0]
            detailed_ticket["create_issue"] = True
            return detailed_ticket
        else:
            return None
    except json.JSONDecodeError:
        return None


async def create_detailed_tickets(
    selected_tickets, ticket_format, greptile, repository, remote, branch
):
    tasks = [
        create_detailed_ticket(
            ticket, ticket_format, greptile, repository, remote, branch
        )
        for ticket in selected_tickets
        if ticket["create_issue"]
    ]
    return await asyncio.gather(*tasks)


def display_and_edit_detailed_tickets(detailed_tickets, repository, github_token):
    st.subheader("Generated Detailed Tickets")

    # Display the full response JSON for each detailed ticket
    if "detailed_tickets_response_json" in st.session_state:
        for i, response_json in enumerate(
            st.session_state.detailed_tickets_response_json
        ):
            with st.expander(f"See Full Response JSON for Ticket {i+1}"):
                st.json(response_json)

    st.info("Double-click on a row to edit the ticket.")

    edited_tickets = st.data_editor(
        detailed_tickets,
        hide_index=True,
        column_config={
            "create_issue": st.column_config.CheckboxColumn("Create?", default=True),
            "title": st.column_config.TextColumn("Title", width="medium"),
            "body": st.column_config.TextColumn("Body", width="large"),
            "labels": st.column_config.ListColumn("Labels", width="medium"),
        },
        column_order=["create_issue", "title", "body", "labels"],
    )

    st.markdown(
        """
        Must have correct Github token permissions to create issues:
        https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#create-an-issue
        """
    )

    if st.button("Create Selected Detailed GitHub Issues"):
        create_github_issues(edited_tickets, repository, github_token)


def create_github_issues(tickets, repository, github_token):
    try:
        auth = Auth.Token(github_token)
        g = Github(auth=auth)
        repo = g.get_repo(repository)

        for ticket in tickets:
            if ticket.get("create_issue", True):
                body = (
                    ticket["body"]
                    + "\n\n---\nAuto-generated issue using Batch Ticket Generator 🎫 + Greptile"
                )
                issue = repo.create_issue(
                    title=ticket["title"], body=body, labels=ticket["labels"]
                )
                st.success(f"Created detailed issue: {issue.html_url}")
    except Exception as e:
        st.error(f"An error occurred while creating GitHub issues: {str(e)}")


def display_detailed_tickets(
    num_tickets,
    are_api_keys_provided,
    greptile,
    repository,
    remote,
    branch,
    github_token,
):
    st.markdown("---")

    st.markdown("""
        ## Phase 2 - Generate Detailed Tickets
        We will now use multiple separate Greptile queries for each selected ticket using an issue template for comprehensive ticket generation.
    """)

    ticket_templates = load_templates("ticket_templates")

    with st.container(border=True):
        st.header("Github Issue Format")

        selected_template = st.selectbox(
            "Select a template:",
            list(ticket_templates.keys()),
            index=list(ticket_templates.keys()).index("task"),
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

    if "detailed_tickets" not in st.session_state:
        st.session_state.detailed_tickets = []

    is_generate_disabled = not are_api_keys_provided() or not st.session_state.get(
        "edited_tickets", []
    )

    help_text = (
        "Please generate and select tickets in Phase 1 first."
        if is_generate_disabled
        else ""
    )
    if st.button(
        "Generate Detailed Tickets", disabled=is_generate_disabled, help=help_text
    ):
        if "edited_tickets" in st.session_state and st.session_state.edited_tickets:
            selected_tickets = [
                ticket
                for ticket in st.session_state.edited_tickets
                if ticket["create_issue"]
            ]
            st.session_state.detailed_tickets = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            async def process_tickets():
                with st.spinner("Generating detailed tickets..."):
                    detailed_tickets = await create_detailed_tickets(
                        selected_tickets,
                        ticket_format,
                        greptile,
                        repository,
                        remote,
                        branch,
                    )
                for i, ticket in enumerate(detailed_tickets):
                    if ticket:
                        st.session_state.detailed_tickets.append(ticket)
                        progress = (i + 1) / len(selected_tickets)
                        progress_bar.progress(progress)
                        status_text.text(
                            f"Processed {i + 1}/{len(selected_tickets)} tickets"
                        )
                    else:
                        st.warning(
                            f"Failed to generate detailed ticket for: {selected_tickets[i]['title']}"
                        )

            asyncio.run(process_tickets())

            status_text.text("All tickets processed!")
            st.success("Detailed tickets generation completed!")
        else:
            st.error(
                "No tickets selected from Phase 1. Please generate and select tickets in Phase 1 first."
            )

    if st.session_state.detailed_tickets:
        display_and_edit_detailed_tickets(
            st.session_state.detailed_tickets, repository, github_token
        )
