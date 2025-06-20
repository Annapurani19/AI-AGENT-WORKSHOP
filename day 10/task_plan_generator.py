import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from utils.db import save_to_mongo

# ✅ Initialize Gemini 1.5 Flash with compatibility fix
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    convert_system_message_to_human=True
)

# ✅ Prompt Template
prompt = ChatPromptTemplate.from_template("""
Based on the project goals and user journeys: {metadata} and {feedback}, generate a feature plan.
Group features by user goals and prioritize them.
Return JSON with keys: "feature_plan" and "priorities".
""")

# ✅ Build chain
task_plan_chain: Runnable = prompt | llm | StrOutputParser()

# ✅ Agent function
def task_plan_agent(inputs: dict) -> dict:
    try:
        output_text = task_plan_chain.invoke(inputs)

        # Attempt to parse model output as JSON
        parsed_output = json.loads(output_text)

        # ✅ Save structured result
        save_to_mongo({
            "agent": "task_planner",
            "input": inputs,
            "output": parsed_output
        }, collection_name="task_plans")

        return {"task_plan": parsed_output}

    except Exception as e:
        return {"task_plan": f"❌ Task Plan Agent Error: {str(e)}"}
