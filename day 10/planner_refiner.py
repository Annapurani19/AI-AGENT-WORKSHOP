from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from utils.db import save_to_mongo
import json

# ✅ Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    convert_system_message_to_human=True
)

# ✅ Prompt Template
prompt = ChatPromptTemplate.from_template("""
Given the feature plan: {feature_plan}, user actions: {user_actions}, and feedback: {feedback}, 
Refine and reprioritize features/actions. Prepare a final dev-ready version.
Log changes clearly.
Return the final result in **plain text** format, not JSON.
""")

planner_chain: Runnable = prompt | llm | StrOutputParser()

# ✅ Agent returning plain text output
def planner_refiner_agent(inputs: dict) -> dict:
    try:
        feature_plan = inputs.get("task_plan", "")
        user_actions = inputs.get("action_map", "")
        feedback = inputs.get("feedback", "")

        llm_inputs = {
            "feature_plan": feature_plan,
            "user_actions": user_actions,
            "feedback": feedback
        }

        output_text = planner_chain.invoke(llm_inputs)

    except Exception as e:
        output_text = f"❌ Planner failed: {str(e)}"

    # Optional: Save to DB
    save_to_mongo({
        "agent": "planner_refiner",
        "input": inputs,
        "output": output_text
    }, collection_name="refinements")

    return {
        "refined_plan": output_text  # Now contains plain text
    }
