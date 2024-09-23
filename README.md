# 🎫 Bulk Ticket Generator

A simple Streamlit app allowing the bulk generation of Github issues using Greptile codebase context.

## Features:

🧠 Leverages Greptile to provide codebase context to LLM queries for more relevant ticket generation
🚀 Runs queries in parallel for faster overall response time
📝 Includes templates for prompts and tasks to streamline the process
🎨 Allows custom prompts and GitHub issue creation for flexibility
🔄 Supports bulk generation of issues, saving time and effort
🔍 Provides detailed ticket generation with step-by-step implementation details
🏷️ Supports custom labeling for better organization of issues
🔧 Allows editing of generated tickets before final submission

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
* [X] Add the Issue Templates to the original prompt

## Roadmap Improvements
* [ ] Retry Handling for LLM to ensure correct JSON response.
* [ ] Use encrypted local storage to hold user API keys such so they persist on page refresh.
* [ ] Integrate Greptile "sources" in a way that is brief and relevant to the tasks (filename-only for example).
* [ ] Integrate Monitoring tools for better error monitoring.
* [ ] Save API keys in a secure manner on the server
* [ ] Integrate Github for pre-filled dropdown menus for repository inputs.
* [ ] Allow for dynamic issue templates depending on the category of the issue.
* [ ] Integrate other platforms like JIRA, Trello, etc.


## Additional Greptile follow-up ideas:
* Code Editor Bot
* Display High Level Software Architecture (UML or Mermaid Flowcharts)
  * Improve architecture of the codebase with recommendations
* Bot that helps with Dependency Upgrades and Migrations
