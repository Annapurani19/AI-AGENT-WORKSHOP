import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from utils.db import save_to_mongo

# ✅ LLM setup
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    convert_system_message_to_human=True
)

# ✅ Prompt template
prompt = ChatPromptTemplate.from_template("""
You are an AI product strategist. Given the following project metadata, extract key problems, goals, and user types.
Return structured JSON with keys: problems, goals, users.
{metadata}
""")

# ✅ Chain
context_chain: Runnable = prompt | llm | StrOutputParser()

# ✅ Agent function for LangGraph
def context_agent(inputs: dict) -> dict:
    try:
        raw_output = context_chain.invoke(inputs)
        parsed_output = json.loads(raw_output)  # Try parsing model output as JSON
    except json.JSONDecodeError:
        parsed_output = {
            "error": "Invalid JSON returned by model",
            "raw_output": raw_output
        }

    # ✅ Save to DB
    save_to_mongo({
        "agent": "project_context",
        "input": inputs,
        "output": parsed_output
    }, collection_name="context_analysis")

    # ✅ Return properly formatted output
    return {"project_context": parsed_output}
