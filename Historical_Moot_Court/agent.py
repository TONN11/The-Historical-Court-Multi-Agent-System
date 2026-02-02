import os
import logging
import google.cloud.logging

from callback_logging import log_query_to_model, log_model_response
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents import SequentialAgent, LoopAgent, ParallelAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.langchain_tool import LangchainTool  # import
from google.genai import types
from google.adk.tools import exit_loop

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

load_dotenv()

model_name = os.getenv("MODEL")
print(model_name)

### Tools ###

def append_to_specific_state(
    tool_context: ToolContext, key: str, content: str
) -> dict[str, str]:
    """Appends found information to a specific state key (e.g., pos_data or neg_data).

    Args:
        key (str): The state key to append to ('pos_data' or 'neg_data').
        content (str): The information found.

    Returns:
        dict[str, str]: Status message.
    """
    existing_data = tool_context.state.get(key, [])
    # Check if it's a list, if not make it one, or append string
    if isinstance(existing_data, str):
        existing_data = [existing_data]
    
    updated_data = existing_data + [content]
    tool_context.state[key] = updated_data
    logging.info(f"[Added to {key}] {content[:50]}...")
    return {"status": "success"}

def write_verdict_file(
    tool_context: ToolContext,
    filename: str,
    content: str
) -> dict[str, str]:
    """Writes the final verdict to a text file."""
    directory = "verdicts"
    target_path = os.path.join(directory, filename)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"status": f"File saved to {target_path}"}

def set_topic(
    tool_context: ToolContext, topic: str
) -> dict[str, str]:
    """Sets the historical topic in the state."""
    tool_context.state["TOPIC"] = topic
    return {"status": "success"}

### Agents ###

# The Admirer (Agent A)
admirer = Agent(
    name="admirer",
    model=model_name,
    description="Researches positive aspects, achievements, and legacy.",
    instruction="""
    ROLE: You are 'The Admirer'. You only see the good in history.
    TOPIC: { TOPIC? }
    FEEDBACK: { judge_feedback? }

    INSTRUCTIONS:
    1. Search Wikipedia for the TOPIC. **IMPORTANT**: Modify your search query to include positive keywords like "achievements", "success", "legacy", "honors", "reforms".
    2. If there is 'judge_feedback', use it to refine your search (e.g., if the judge says we need more detail on early life, search for that).
    3. Use the 'append_to_specific_state' tool to save your findings.
       - key: 'pos_data'
       - content: A summary of the positive facts found.
    4. Do NOT report controversies or failures.
    """,
    tools=[
        LangchainTool(tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())),
        append_to_specific_state
    ]
)

# The Critic (Agent B)
critic = Agent(
    name="critic",
    model=model_name,
    description="Researches negative aspects, controversies, and failures.",
    instruction="""
    ROLE: You are 'The Critic'. You act as the prosecutor of history.
    TOPIC: { TOPIC? }
    FEEDBACK: { judge_feedback? }

    INSTRUCTIONS:
    1. Search Wikipedia for the TOPIC. **IMPORTANT**: Modify your search query to include negative keywords like "controversy", "war crimes", "failures", "criticism", "scandals".
    2. If there is 'judge_feedback', use it to refine your search.
    3. Use the 'append_to_specific_state' tool to save your findings.
       - key: 'neg_data'
       - content: A summary of the negative facts found.
    4. Do NOT report achievements or awards.
    """,
    tools=[
        LangchainTool(tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())),
        append_to_specific_state
    ]
)

# Parallel Execution for Step 2
investigation_team = ParallelAgent(
    name="investigation_team",
    sub_agents=[admirer, critic],
    description="Simultaneously investigates both sides of the history."
)

# The Judge (Agent C)
judge = Agent(
    name="judge",
    model=model_name,
    description="Evaluates the evidence and controls the loop.",
    instruction="""
    ROLE: You are the Judge. You ensure a fair trial.
    
    EVIDENCE POSITIVE: { pos_data? }
    EVIDENCE NEGATIVE: { neg_data? }
    TOPIC: { TOPIC? }

    INSTRUCTIONS:
    1. Analyze the 'pos_data' and 'neg_data'.
    2. Check for Balance & Depth:
       - Is there enough information on both sides?
       - Are the facts specific enough?
    3. DECISION:
       - IF the data is sufficient and balanced: Use the 'exit_loop' tool to finish the trial.
       - IF the data is lacking or unbalanced: Use 'append_to_specific_state' (key='judge_feedback') to give specific instructions to the Admirer or Critic on what to search for next (e.g., "Critic, find more about the later years scandals").
    """,
    tools=[append_to_specific_state, exit_loop]
)

# Loop for Step 3 (Trial & Review)
court_session = LoopAgent(
    name="court_session",
    description=" The cycle of investigation and judicial review.",
    sub_agents=[
        investigation_team, # Research first
        judge               # Then evaluate
    ],
    max_iterations=5 # Safety limit
)

# 4. The Scribe (Step 4 - Verdict)
scribe = Agent(
    name="scribe",
    model=model_name,
    description="Writes the final neutral report.",
    instruction="""
    ROLE: You are the Court Scribe.
    TOPIC: { TOPIC? }
    POS_DATA: { pos_data? }
    NEG_DATA: { neg_data? }

    INSTRUCTIONS:
    1. Synthesize the conflicting information into a neutral "Historical Verdict".
    2. Compare the achievements against the controversies.
    3. Write a comprehensive report.
    4. Use the 'write_verdict_file' tool to save the report.
       - filename: "{TOPIC}_verdict.txt" (Replace spaces with underscores)
       - content: The full report.
    """,
    tools=[write_verdict_file]
)

# Sequential Workflow
historical_trial_system = SequentialAgent(
    name="historical_trial_system",
    description="The full workflow of the historical court.",
    sub_agents=[
        court_session,
        scribe
    ]
)

### Root Agent ###
root_agent = Agent(
    name="greeter",
    model=model_name,
    description="Starts the Historical Moot Court.",
    instruction="""
    Welcome the user to the Historical Moot Court.
    Ask them for a historical figure or event they want to put on trial.
    When they answer, use the 'set_topic' tool to save their input as 'TOPIC'.
    Then, handoff to the 'historical_trial_system'.
    """,
    tools=[set_topic],
    sub_agents=[historical_trial_system]
)