import streamlit as st
import uuid
import os
import time
import json
from pathlib import Path
from github import Auth
from github import Github


async def create_ticket_list(
    repository, remote, branch, greptile, greptile_content, num_tickets
):
    is_prod = os.environ.get("STREAMLIT_ENV", "development") == "production"
    try:
        mock_file = os.environ.get("MOCK_FILE")
        if not is_prod and mock_file and Path(mock_file).is_file():
            st.toast(f"Using mock data from {mock_file}")
            with open(mock_file, "r") as f:
                response_json = json.load(f)
        else:
            with st.spinner("Ensuring repository is indexed..."):
                await greptile.ensure_repository_indexed(remote, repository, branch)

            indexing_status = False
            with st.spinner("Checking if repository is indexed..."):
                for _ in range(90):  # 15 minutes timeout (90 * 10 seconds)
                    if await greptile.is_repository_indexed(remote, repository, branch):
                        indexing_status = True
                        break
                    await asyncio.sleep(10)

            if not indexing_status:
                st.error(
                    "Repository indexing timed out after 15 minutes. Check your email to see if the repository has been indexed then try again."
                )
                return None

            st.toast("Repository is indexed.")

            with st.spinner("Querying Greptile..."):
                message_id = str(uuid.uuid4())
                response_json = await greptile.query_async(
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

        # Save the response JSON in session state
        st.session_state.ticket_list_response_json = response_json

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

            for ticket in tickets:
                ticket["create_issue"] = True

            return tickets
        else:
            st.error(
                "Unable to extract tickets from the response. Please check the Greptile API response format."
            )
            print("Debug: Raw message received:", message)
            print(
                "Debug: Full response JSON:", st.session_state.ticket_list_response_json
            )
            return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None


def display_and_edit_tickets(tickets, repository, github_token):
    st.subheader("Generated Tickets")

    # Display the full response JSON
    if "ticket_list_response_json" in st.session_state:
        with st.expander("See Full Response JSON"):
            st.json(st.session_state.ticket_list_response_json)

    st.info("Double-click on a row to edit the ticket.")

    edited_tickets = st.data_editor(
        tickets,
        hide_index=True,
        column_config={
            "create_issue": st.column_config.CheckboxColumn("Create?", default=True),
            "title": st.column_config.TextColumn("Title", width="medium"),
            "body": st.column_config.TextColumn("Body", width="large"),
            "labels": st.column_config.ListColumn("Labels", width="medium"),
        },
        column_order=["create_issue", "title", "body", "labels"],
    )

    # Save edited tickets to session state
    st.session_state.edited_tickets = edited_tickets


    return edited_tickets
