# 🎫 Bulk Ticket Generator

A simple Streamlit app allowing the bulk generation of Github issues using Greptile codebase context.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://support-tickets-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

## TODO
* [X] Integrate Github for actual issue creation
* [ ] Add the Issue Templates to the original prompt

## Roadmap Improvements
* [ ] Retry Handling for LLM to ensure correct JSON response.
* [ ] Save API keys in a secure manner on the server
* [ ] Integrate Github for pre-filled dropdown menus for repository inputs.
* [ ] Allow for dynamic issue templates depending on the category of the issue.
* [ ] Can generate tickets for alternate platforms like JIRA, Trello, etc.


## Additional Greptile follow-up ideas:
* Code Editor Bot
* Display High Level Software Architecture (UML or Mermaid Flowcharts)
* Bot that helps with Dependency Upgrades and Migrations
