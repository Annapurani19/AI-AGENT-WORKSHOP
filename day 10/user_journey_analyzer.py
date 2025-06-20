import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from utils.db import save_to_mongo

# ✅ Initialize Gemini Flash with system message fix
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    convert_system_message_to_human=True
)

# ✅ Define prompt for extracting pain points and journeys
prompt = ChatPromptTemplate.from_template("""
Given user feedback: {feedback} and project context: {metadata}, 
extract key pain points and common user journeys. 
Return structured JSON with keys: pain_points, user_journeys.
""")

# ✅ Create the runnable chain
journey_chain: Runnable = prompt | llm | StrOutputParser()

# ✅ LangGraph agent function
def journey_agent(inputs: dict) -> dict:
    try:
        raw_output = journey_chain.invoke(inputs)
        parsed_output = json.loads(raw_output)
    except Exception as e:
        parsed_output = {"error": str(e), "raw_output": raw_output if 'raw_output' in locals() else ""}

    save_to_mongo({
        "agent": "journey_analyzer",
        "input": inputs,
        "output": parsed_output
    }, collection_name="journey_analysis")

    return {"user_journey_map": parsed_output}
