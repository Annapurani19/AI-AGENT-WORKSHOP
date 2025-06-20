import streamlit as st
from workflows.feature_mapping_graph import run_workflow
import json

def launch_ui():
    st.set_page_config(page_title="Agentic Feature Planner", layout="wide")
    
    st.markdown("""
        <style>
            body {
                background-color: #F0F2F6;
            }
            .main {
                background-color: #FFFFFF;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            textarea {
                font-size: 15px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚀 Agentic AI: Feature Planner")
    st.markdown("Provide **project metadata** and **user feedback** in plain text. The AI will analyze and generate a dev-ready feature plan.")

    with st.form("user_input_form"):
        metadata = st.text_area("📝 Project Metadata", height=200, placeholder="e.g. user goals, pain points, personas, market gaps...")
        feedback = st.text_area("💬 User/Stakeholder Feedback", height=150, placeholder="e.g. common complaints, feature requests, usability issues...")
        submit = st.form_submit_button("Run AI Workflow")

    if submit:
        if not metadata or not feedback:
            st.warning("Please fill in both metadata and feedback.")
        else:
            with st.spinner("🤖 Running the agentic AI workflow..."):
                results = run_workflow(metadata, feedback)

            st.success("✅ Workflow completed!")

            st.subheader("📌 Final Refined Plan (Text View)")

            refined = results.get("refined_plan", {})
            readable_output = ""

            try:
                if isinstance(refined, dict) and "refined_features" in refined and "logs" in refined:
                    readable_output += "📋 Log:\n\n"
                    for log in refined["logs"]:
                        readable_output += f"- {log['action']}: {log['details']}\n"

                    readable_output += "\n🛠️ Final Dev-Ready Feature Plan:\n"
                    for i, feat in enumerate(refined["refined_features"], 1):
                        readable_output += f"\n{i}. ✅ Feature: {feat['feature']}\n"
                        readable_output += f"   - Description: {feat['description']}\n"
                        readable_output += f"   - Priority: {feat['priority']}\n"
                        readable_output += f"   - Status: {feat.get('status', 'To Do')}\n"

                    readable_output += "\n🔧 Changes Made:\n"
                    readable_output += "- Added missing 'feature_plan' variable.\n"
                    readable_output += "- Created a structured feature plan with clear descriptions and priorities.\n"
                    readable_output += "- Prioritized features based on user feedback.\n"
                    readable_output += "- Refined feature descriptions to be more actionable for developers.\n"
                else:
                    readable_output = str(refined)

            except Exception as e:
                readable_output = f"❌ Failed to parse output: {e}"

            st.text_area("📄 Refined Output (Text)", value=readable_output, height=600)
