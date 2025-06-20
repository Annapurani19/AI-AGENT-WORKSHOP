import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from utils.db import save_to_mongo

# ✅ Initialize the Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    convert_system_message_to_human=True
)

# ✅ Prompt to generate user actions
prompt = ChatPromptTemplate.from_template("""
Given the feature plan: {feature_plan}, map each feature to likely user actions and UI touchpoints.
Return JSON with keys: user_actions, assumptions.
""")

# ✅ Create the LangChain runnable chain
action_mapper_chain: Runnable = prompt | llm | StrOutputParser()

# ✅ LangGraph-compatible agent function
def action_mapper_agent(inputs: dict) -> dict:
    try:
        raw_output = action_mapper_chain.invoke(inputs)
        parsed_output = json.loads(raw_output)
    except Exception as e:
        parsed_output = {"error": str(e), "raw_output": raw_output if 'raw_output' in locals() else ""}

    # ✅ Log output to MongoDB
    save_to_mongo({
        "agent": "action_mapper",
        "input": inputs,
        "output": parsed_output
    }, collection_name="action_mappings")

    # ✅ Return dict with key matching AgentState
    return {"action_map": parsed_output}
