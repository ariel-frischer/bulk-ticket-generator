import streamlit as st
import uuid
import os
import json
import logging
import asyncio
from pathlib import Path


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
                logging.error("Repository indexing timed out after 15 minutes.")
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

        # Smart extraction of parsing partly JSON text the LLM message
        def extract_tickets(msg):
            if isinstance(msg, dict) and "tickets" in msg:
                return msg["tickets"]
            elif isinstance(msg, str):
                # Try to find JSON content within the string
                try:
                    # Look for the start and end of a JSON object
                    json_start = msg.find("{")
                    json_end = msg.rfind("}")
                    if json_start != -1 and json_end != -1 and json_end > json_start:
                        # Extract the JSON part and parse it
                        json_content = msg[json_start : json_end + 1]
                        parsed = json.loads(json_content)
                        if isinstance(parsed, dict) and "tickets" in parsed:
                            return parsed["tickets"]
                except json.JSONDecodeError:
                    # If JSON object parsing fails, try to find an array of tickets
                    try:
                        # Look for the start and end of a JSON array
                        array_start = msg.find("[")
                        array_end = msg.rfind("]")
                        if (
                            array_start != -1
                            and array_end != -1
                            and array_end > array_start
                        ):
                            # Extract the array part and parse it
                            array_content = msg[array_start : array_end + 1]
                            parsed = json.loads(array_content)
                            if isinstance(parsed, list):
                                return parsed
                    except json.JSONDecodeError:
                        logging.error("Failed to parse JSON array from message")
                except Exception as e:
                    logging.error(
                        f"Unexpected error while extracting tickets: {str(e)}"
                    )
            return None

        tickets = extract_tickets(message)

        if tickets is not None:
            if len(tickets) != num_tickets and not mock_file:
                st.warning(
                    f"Warning: The number of tickets generated ({len(tickets)}) does not match the requested number ({num_tickets})."
                )

            for ticket in tickets:
                ticket["create_issue"] = True

            logging.warning(f"Successfully extracted {len(tickets)} tickets")
            return tickets
        else:
            error_msg = "Unable to extract tickets from the response this may be due to the LLM providing invalid JSON."
            st.error(error_msg)
            logging.error(error_msg)
            logging.warning("Raw message received: %s", message)
            logging.warning(
                "Full response JSON: %s", st.session_state.ticket_list_response_json
            )
            return None
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        st.error(error_msg)
        logging.error(error_msg)
        return None


def display_and_edit_tickets(tickets):
    st.subheader("Generated Tickets")

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

    st.session_state.edited_tickets = edited_tickets

    return edited_tickets
