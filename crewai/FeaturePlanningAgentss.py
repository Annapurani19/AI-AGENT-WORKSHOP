import json
import time
import os
from typing import Type
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from dotenv import load_dotenv
import streamlit as st
import re

# Load environment variables
load_dotenv()

# ---------- LLM Setup with Enhanced Retry Logic ----------
def create_llm_with_retry():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return LLM(
                model="gemini/gemini-2.0-flash",
                temperature=0.3,  # Lowered for stricter JSON output
                api_key=os.getenv("GEMINI_API_KEY")  # Load from .env
            )
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"LLM initialization failed: {e}. Retrying in 15 seconds...")
                time.sleep(15)
            else:
                raise Exception(f"Failed to initialize LLM after {max_retries} attempts: {e}")

llm = create_llm_with_retry()

# ---------- Tool Schemas ----------
class ProjectInput(BaseModel):
    input: str = Field(..., description="Project metadata and user feedback")

class JourneyInput(BaseModel):
    input: str = Field(..., description="Project context JSON")

# ---------- Custom Tools ----------
class RAGJourneyTool(BaseTool):
    name: str = "RAGJourneyAnalyzer"
    description: str = "Retrieves user behavior patterns for journey mapping."
    args_schema: Type[BaseModel] = JourneyInput

    def _run(self, input: str) -> str:
        try:
            context = json.loads(input)
            audience = context.get("audience", "user")
            if isinstance(audience, list):
                roles = [role.lower() for role in audience]
            else:
                roles = [audience.lower()]
            behavior_db = {
                "developer": ["Codes features", "Tests APIs", "Debugs errors"],
                "manager": ["Sets project goals", "Reviews progress", "Approves features"]
            }
            behaviors = []
            for role in roles:
                role_behaviors = behavior_db.get(role, ["Generic user tasks"])
                behaviors.extend(role_behaviors)
            return f"Retrieved Behaviors: {', '.join(behaviors)}"
        except json.JSONDecodeError:
            return "Error: Invalid JSON input for RAG tool"
        except AttributeError:
            return "Error: Invalid audience format in context"

# Tool Instances
rag_journey_tool = RAGJourneyTool()

# ---------- Agent Definitions ----------
project_context_interpreter = Agent(
    role="Project Context Interpreter",
    goal="Extract goals and product purpose from project metadata and feedback",
    backstory="Expert in parsing project data to define objectives and audience",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

user_journey_analyzer = Agent(
    role="User Journey Analyzer",
    goal="Analyze user engagement and map roles, intentions, and tasks using RAG",
    backstory="Specialist in user behavior analysis with RAG expertise",
    tools=[rag_journey_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)

task_plan_generator = Agent(
    role="Task Plan Generator",
    goal="Create feature and task plans linked to user outcomes",
    backstory="Experienced in translating user needs into developer tasks",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

user_action_mapper = Agent(
    role="User Action Mapper",
    goal="Generate specific, inclusive user actions from feature plans",
    backstory="Expert in crafting clear, user-focused action flows",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

planner_refiner = Agent(
    role="Planner Refiner",
    goal="Refine feature plans and action maps based on feedback",
    backstory="Senior coordinator ensuring high-quality deliverables",
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# ---------- Utility Function to Clean and Fix JSON ----------
def clean_json_output(raw_output: str, base_json: dict) -> dict:
    """Clean raw output and attempt to fix JSON, merging with base_json if needed."""
    try:
        raw_output = raw_output.strip()
        # Remove common LLM markers or text
        raw_output = re.sub(r'```json\s*|\s*```|^\s*Here is.*?:\s*|\n\s*Output.*?:\s*', '', raw_output, flags=re.IGNORECASE | re.DOTALL)
        # Fix common JSON issues: trailing commas, unescaped quotes
        raw_output = re.sub(r',\s*([\]}])', r'\1', raw_output)  # Remove trailing commas
        raw_output = re.sub(r'\\([^"\\])', r'\\\1', raw_output)  # Fix unescaped backslashes
        # Try to find the first valid JSON object
        start = raw_output.find('{')
        end = raw_output.rfind('}') + 1
        if start == -1 or end == 0:
            return base_json  # Return base_json if no JSON object found
        json_str = raw_output[start:end]
        try:
            parsed_json = json.loads(json_str)
            # Merge with base_json to ensure required fields
            merged_json = base_json.copy()
            merged_json.update(parsed_json)
            return merged_json
        except json.JSONDecodeError:
            return base_json  # Return base_json if parsing fails
    except Exception:
        return base_json

# ---------- Main CrewAI Workflow ----------
def run_feature_planning(project_metadata, user_feedback):
    # Base JSON for fallback
    base_json = {
        "application": project_metadata.get('project', 'Task Assignment and Tracking'),
        "user_roles": [
            {
                "role": "Manager",
                "intentions": [
                    "Efficiently assign tasks to team members.",
                    "Monitor task progress in real-time.",
                    "Ensure timely task completion.",
                    "Facilitate team collaboration.",
                    "Prioritize tasks based on deadlines and importance."
                ],
                "tasks": [
                    "Create and assign tasks with clear descriptions and deadlines.",
                    "Review and adjust task priorities based on project needs.",
                    "Monitor task status and identify potential roadblocks.",
                    "Communicate with developers to provide guidance and support.",
                    "Generate reports on team progress and task completion rates.",
                    "Approve completed tasks and provide feedback."
                ],
                "journey": [
                    {
                        "step": "Login to the application.",
                        "description": "Manager logs in using their credentials.",
                        "ui_elements": ["Username field", "Password field", "Login button"],
                        "expected_outcome": "Successful login and access to the dashboard."
                    },
                    {
                        "step": "Create a new task.",
                        "description": "Manager creates a new task, specifying details such as assignee, due date, and priority.",
                        "ui_elements": ["Create Task button", "Task Description field", "Assignee dropdown", "Due Date picker", "Priority dropdown"],
                        "expected_outcome": "Task is successfully created and assigned to the selected developer."
                    },
                    {
                        "step": "Monitor task progress.",
                        "description": "Manager tracks the progress of assigned tasks, viewing status updates and comments.",
                        "ui_elements": ["Task List", "Task Details view", "Status indicators", "Comment section"],
                        "expected_outcome": "Manager has a clear understanding of the current status of each task."
                    },
                    {
                        "step": "Communicate with developers.",
                        "description": "Manager communicates with developers through the application to provide feedback, answer questions, or offer assistance.",
                        "ui_elements": ["Comment section", "Direct messaging feature"],
                        "expected_outcome": "Clear and efficient communication between manager and developer."
                    },
                    {
                        "step": "Generate progress reports.",
                        "description": "Manager generates reports to track team performance and identify areas for improvement.",
                        "ui_elements": ["Reporting dashboard", "Report generation options"],
                        "expected_outcome": "Manager has access to data-driven insights on team progress."
                    }
                ]
            },
            {
                "role": "Developer",
                "intentions": [
                    "Receive and understand assigned tasks.",
                    "Update task status in real-time.",
                    "Collaborate with team members on task completion.",
                    "Prioritize tasks based on deadlines and importance.",
                    "Seek clarification or assistance when needed."
                ],
                "tasks": [
                    "Review task descriptions and requirements.",
                    "Update task status as progress is made.",
                    "Communicate with managers and team members to resolve issues.",
                    "Prioritize tasks based on deadlines and dependencies.",
                    "Request clarification or assistance from managers when needed.",
                    "Complete assigned tasks and submit for review."
                ],
                "journey": [
                    {
                        "step": "Login to the application.",
                        "description": "Developer logs in using their credentials.",
                        "ui_elements": ["Username field", "Password field", "Login button"],
                        "expected_outcome": "Successful login and access to the dashboard."
                    },
                    {
                        "step": "View assigned tasks.",
                        "description": "Developer views a list of tasks assigned to them.",
                        "ui_elements": ["Task List", "Task Details view"],
                        "expected_outcome": "Developer has a clear understanding of their assigned tasks."
                    },
                    {
                        "step": "Update task status.",
                        "description": "Developer updates the status of a task as they make progress.",
                        "ui_elements": ["Status dropdown", "Progress bar"],
                        "expected_outcome": "Task status is updated in real-time, providing visibility to the manager."
                    },
                    {
                        "step": "Communicate with manager.",
                        "description": "Developer communicates with the manager to ask questions, provide updates, or request assistance.",
                        "ui_elements": ["Comment section", "Direct messaging feature"],
                        "expected_outcome": "Efficient communication and resolution of issues."
                    },
                    {
                        "step": "Mark task as complete.",
                        "description": "Developer marks a task as complete and submits it for review.",
                        "ui_elements": ["Complete button", "Submit for review button"],
                        "expected_outcome": "Task is marked as complete and awaits manager approval."
                    }
                ]
            }
        ],
        "objectives": project_metadata.get('goal', 'Streamline task assignment and tracking'),
        "feedback": project_metadata.get('feedback', 'Users want intuitive UI, real-time updates, and easy task prioritization'),
        "target_outcomes": {
            "ui": "Reduce onboarding time by 50%, achieve 4.5/5 satisfaction, decrease support requests by 40%",
            "realtime_updates": "Updates within 1 second, increase daily active users by 30%, reduce manual updates by 60%",
            "task_prioritization": "Prioritize within 3 clicks, improve team efficiency by 20%, increase adoption by 75%, decrease missed deadlines by 35%"
        }
    }

    # Task 1: Extract project context
    task1 = Task(
        description=f"Extract goals, audience, and outcomes from: {json.dumps(project_metadata, ensure_ascii=False)}. Output a valid JSON string without any additional text or markers.",
        expected_output="JSON with objectives, audience, and target outcomes",
        agent=project_context_interpreter
    )

    # Task 2: Analyze user journey with RAG
    task2 = Task(
        description=f"""
Analyze user journey based on project context and feedback. Use RAGJourneyAnalyzer tool with the following JSON input: 
{json.dumps({
    'objectives': project_metadata.get('goal', 'Streamline task assignment and tracking'), 
    'audience': project_metadata.get('audience', ['Developers', 'Managers']), 
    'feedback': project_metadata.get('feedback', 'Users want intuitive UI, real-time updates, and easy task prioritization')
}, ensure_ascii=False)}
Output a valid JSON string without any additional text or markers.
""",
        expected_output="JSON with user roles, intentions, and tasks",
        agent=user_journey_analyzer
    )

    # Task 3: Generate feature and task plan
    task3 = Task(
        description=f"""
Create a feature and task plan based on user journey and project context: {json.dumps(project_metadata, ensure_ascii=False)}.
Generate a JSON structure with application, user_roles, objectives, feedback, and target_outcomes. Ensure the plan includes:
1. Intuitive UI: Drag-and-drop functionality, clear visual cues, tooltips.
2. Real-time Updates: Status indicators, live comment feeds, notification badges.
3. Easy Task Prioritization: Drag-and-drop prioritization, customizable filters, visual priority indicators (e.g., color-coding, icons).
Output a valid JSON string without any additional text or markers.
""",
        expected_output="JSON with application, user_roles (including intentions, tasks, journey with ui_elements), objectives, feedback, and target_outcomes",
        agent=task_plan_generator
    )

    # Task 4: Map user actions
    task4 = Task(
        description="Generate specific user actions from feature plan and journey map, ensuring actions are detailed for both Manager and Developer roles. Output a valid JSON string without any additional text or markers.",
        expected_output="JSON with user action descriptions for each role",
        agent=user_action_mapper
    )

    # Task 5: Refine plan based on feedback
    task5 = Task(
        description=f"""
Refine the feature plan and action map based on feedback: {user_feedback}.
Use the following JSON as the base and enhance the 'ui_elements' in the 'journey' sections for both Manager and Developer roles to address:
1. Intuitive UI: Add drag-and-drop functionality, clear visual cues, and tooltips.
2. Real-time Updates: Include status indicators, live comment feeds, and notification badges.
3. Easy Task Prioritization: Add drag-and-drop prioritization, customizable filters, and visual priority indicators (e.g., color-coding, icons).
Ensure the refined JSON maintains the structure: application, user_roles, objectives, feedback, target_outcomes, and includes a change_log with entries like "Added drag-and-drop for task prioritization".
Output ONLY a valid JSON string with no additional text, explanations, or markers (e.g., no ```json ```, no "Here is the output:"). Example:
{{
  "application": "Task Assignment and Tracking",
  "user_roles": [...],
  "objectives": "...",
  "feedback": "...",
  "target_outcomes": {{...}},
  "change_log": ["Added drag-and-drop for task prioritization", "..."]
}}
Base JSON:
{json.dumps(base_json, ensure_ascii=False)}
""",
        expected_output="Refined JSON with enhanced ui_elements, maintained structure, and a change_log",
        agent=planner_refiner
    )

    # Create and run Crew with sequential process
    crew = Crew(
        agents=[project_context_interpreter, user_journey_analyzer, task_plan_generator, user_action_mapper, planner_refiner],
        tasks=[task1, task2, task3, task4, task5],
        process=Process.sequential,
        verbose=True
    )

    # Log task outputs for debugging
    task_outputs = []
    for task in crew.tasks:
        result = task.execute_sync()
        task_outputs.append({"task": task.description, "output": str(result)})
    
    task_output_path = os.path.join("C:\\Users\\HP\\Desktop\\crew ai\\FeaturePlanningAI", "task_outputs.txt")
    with open(task_output_path, "w", encoding="utf-8") as f:
        for i, output in enumerate(task_outputs, 1):
            f.write(f"Task {i}:\nDescription: {output['task']}\nOutput: {output['output']}\n{'-'*50}\n")

    result = crew.kickoff()
    return result, base_json, task_output_path

# ---------- Streamlit UI ----------
def main():
    st.set_page_config(page_title="Task Management App Planner", layout="wide")
    st.title("Task Management App Feature Planner")
    st.subheader("Enter Project Details and Generate Feature Plan")

    # Input fields for project metadata
    st.subheader("Project Metadata")
    project_name = st.text_input("Project Name", value="Task Management App")
    project_goal = st.text_input("Project Goal", value="Streamline task assignment and tracking")
    audience = st.text_input("Audience (comma-separated)", value="Developers, Managers")
    project_feedback = st.text_area("Project Feedback", value="Users want intuitive UI, real-time updates, and easy task prioritization")
    
    # Input field for mentor/user feedback
    st.subheader("Mentor/User Feedback")
    user_feedback = st.text_area("Feedback", value="Mentor Feedback: Prioritize real-time notifications over complex UI animations.\nUser Feedback: Need simple task creation and status tracking.")

    # Validate inputs
    if not project_name or not project_goal or not audience or not project_feedback or not user_feedback:
        st.error("All input fields must be filled.")
        return

    # Convert audience to list
    audience_list = [role.strip() for role in audience.split(",") if role.strip()]
    if not audience_list:
        st.error("Audience must contain at least one role.")
        return

    # Create project metadata dictionary
    project_metadata = {
        "project": project_name,
        "goal": project_goal,
        "audience": audience_list,
        "feedback": project_feedback
    }

    # Add a button to trigger the workflow
    if st.button("Generate Feature Plan"):
        with st.spinner("Running CrewAI workflow to generate and refine the feature plan..."):
            try:
                # Run the CrewAI workflow with user inputs
                final_output, base_json, task_output_path = run_feature_planning(project_metadata, user_feedback)

                # Save raw output for debugging
                raw_output_path = os.path.join("C:\\Users\\HP\\Desktop\\crew ai\\FeaturePlanningAI", "raw_output.txt")
                with open(raw_output_path, "w", encoding="utf-8") as f:
                    f.write(str(final_output.raw))

                # Extract JSON from CrewOutput
                if hasattr(final_output, 'json_dict') and final_output.json_dict:
                    output_json = final_output.json_dict
                elif hasattr(final_output, 'raw'):
                    output_json = clean_json_output(final_output.raw, base_json)
                    if output_json == base_json:
                        st.warning("JSON parsing failed, using fallback JSON.")
                        st.subheader("Raw Output for Debugging")
                        st.text_area("Raw Output", final_output.raw, height=300)
                        st.info(f"Raw output saved to {raw_output_path}")
                        st.info(f"Task outputs saved to {task_output_path}")
                else:
                    st.error("Final output is not in a recognizable format.")
                    st.text_area("Raw Output", str(final_output), height=300)
                    output_json = base_json
                    st.info(f"Raw output saved to {raw_output_path}")
                    st.info(f"Task outputs saved to {task_output_path}")

                # Display the JSON in a formatted way
                st.subheader("Full Feature Plan")
                st.json(output_json)

                # Extract and display key sections
                st.subheader("Key Details")
                st.write(f"**Application**: {output_json.get('application', 'N/A')}")
                st.write(f"**Objectives**: {output_json.get('objectives', 'N/A')}")
                st.write(f"**Feedback**: {output_json.get('feedback', 'N/A')}")

                # Display user roles and journeys
                st.subheader("User Roles and Journeys")
                for role in output_json.get("user_roles", []):
                    st.write(f"### Role: {role.get('role', 'N/A')}")
                    st.write("**Intentions**:")
                    for intention in role.get("intentions", []):
                        st.write(f"- {intention}")
                    st.write("**Tasks**:")
                    for task in role.get("tasks", []):
                        st.write(f"- {task}")
                    st.write("**Journey**:")
                    for step in role.get("journey", []):
                        st.write(f"**Step**: {step.get('step', 'N/A')}")
                        st.write(f"**Description**: {step.get('description', 'N/A')}")
                        st.write(f"**UI Elements**: {', '.join(step.get('ui_elements', []))}")
                        st.write(f"**Expected Outcome**: {step.get('expected_outcome', 'N/A')}")
                        st.write("---")

                # Display target outcomes
                st.subheader("Target Outcomes")
                outcomes = output_json.get("target_outcomes", {})
                for key, value in outcomes.items():
                    st.write(f"**{key.replace('_', ' ').title()}**: {value}")

                # Display change log if present
                if "change_log" in output_json:
                    st.subheader("Change Log")
                    for change in output_json.get("change_log", []):
                        st.write(f"- {change}")

                # Save output to file
                output_path = os.path.join("C:\\Users\\HP\\Desktop\\crew ai\\FeaturePlanningAI", "output.json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(output_json, f, indent=2, ensure_ascii=False)
                st.success(f"Output saved to {output_path}")
                st.info(f"Raw output saved to {raw_output_path}")
                st.info(f"Task outputs saved to {task_output_path}")

            except Exception as e:
                st.error(f"Workflow failed: {e}")
                st.text_area("Error Details", str(e), height=200)
                st.subheader("Fallback JSON")
                st.json(base_json)
                output_path = os.path.join("C:\\Users\\HP\\Desktop\\crew ai\\FeaturePlanningAI", "output.json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(base_json, f, indent=2, ensure_ascii=False)
                st.success(f"Fallback JSON saved to {output_path}")
                raw_output_path = os.path.join("C:\\Users\\HP\\Desktop\\crew ai\\FeaturePlanningAI", "raw_output.txt")
                with open(raw_output_path, "w", encoding="utf-8") as f:
                    f.write(str(final_output.raw) if hasattr(final_output, 'raw') else str(final_output))
                st.info(f"Raw output saved to {raw_output_path}")
                st.info(f"Task outputs saved to {task_output_path}")

if __name__ == "__main__":
    main()