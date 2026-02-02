
# The Historical Court (Multi-Agent System) 

> **Note:** This project was developed for **educational purposes** to demonstrate the capabilities of Multi-Agent Systems and Google ADK.

**The Historical Court** is an advanced Multi-Agent System built with **Google Agent Development Kit (ADK)** and **LangChain**. It simulates a historical "Moot Court" where AI agents assume opposing roles to dialectically analyze historical figures or events, reducing bias and synthesizing a neutral verdict.

---

##  System Architecture

The system follows a dialectical workflow: **Inquiry** $\to$ **Parallel Investigation** $\to$ **Judicial Review (Loop)** $\to$ **Synthesis**.

```mermaid
graph LR
    subgraph "Start"
        RootAgent["root_agent (Greeter)"]
    end

    subgraph "Historical Trial System"
        direction TB
        CourtSession["court_session (Loop)"]
        Scribe["scribe (Verdict Writer)"]
    end

    subgraph "Court Session"
        direction TB
        InvestigationTeam["investigation_team (Parallel)"]
        Judge["judge"]
    end

    subgraph "Investigation Team"
        direction LR
        Admirer["admirer"]
        Critic["critic"]
    end

    %% Connections
    RootAgent -- "1. set_topic & Handoff" --> CourtSession
    
    CourtSession -- "2. Investigation & Review Cycle" --> InvestigationTeam
    InvestigationTeam --> Admirer
    InvestigationTeam --> Critic
    
    InvestigationTeam -- "Findings" --> Judge
    Judge -- "Feedback / Exit Loop" --> CourtSession
    
    CourtSession -- "3. After Loop Finishes" --> Scribe
    Scribe -- "4. write_verdict_file" --> Finish((End))
   ```
   ## Project Structure
    The-Historical-Court-Multi-Agent-System/
    ├── Historical_Moot_Court/ 
	│   ├── __init__.py
	│   └── agent.py              # Main application code
	├── verdicts/                 # Generated verdicts stored here
	│   └── Napoleon_Bonaparte_verdict.txt
	├── logs/                     # Execution logs for debugging/grading
	│   └── output_logs.json 
	├── assets/                   # Project assets and diagrams
	│   └── architecture_diagram.png
	├── .env.example              # Environment variables template
	├── requirements.txt          # Python dependencies
	└── README.md                 # Documentation

## Agents & Roles

1.  **Greeter (Root Agent):**
    
    -   Welcomes the user and captures the historical `TOPIC`.
        
2.  **Investigation Team (Parallel):**
    
    -    **The Admirer:** Searches for achievements, legacy, and positive reforms using specific Wikipedia queries.
        
    -    **The Critic:** Searches for controversies, failures, and war crimes using opposing queries.
        
    -   _Note: Both agents run in parallel to optimize performance._
        
3.  **The Judge:**
    
    -    Evaluates the gathered evidence (`pos_data` vs `neg_data`) for balance and depth.
        
    -   Triggers a feedback loop if information is insufficient.
        
    -   Executes `exit_loop` when the evidence is satisfactory.
        
4.  **The Scribe:**
    
    -   Synthesizes the conflicting data into a neutral "Historical Verdict".
        
    -   Writes the final report to a text file.

## Environment Variables

Create a `.env` file in the root directory and add your credentials:
   ```
   GOOGLE_GENAI_USE_VERTEXAI=TRUE 
   GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
   GOOGLE_CLOUD_LOCATION=global
   GOOGLE_CLOUD_LOCATION=global MODEL=gemini-2.5-flash
  ```
  
  ## Tools Used

-   **Google ADK:** Core framework for building sequential, parallel, and loop agents.
    
-   **LangChain (WikipediaQueryRun):** For real-time fact retrieval.
    
-   **Custom Tools:**
    
    -   `append_to_specific_state`: Manages structured memory (`pos_data`/`neg_data`).
        
    -   `write_verdict_file`: Handles file I/O for the final report.
        

## Outputs

-   **Verdicts:** Check the `verdicts/` folder for the final text reports.
    
-   **Logs:** Execution traces are available in `logs/output_logs.json`.
   
