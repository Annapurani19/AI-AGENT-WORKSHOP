# -*- coding: utf-8 -*-
"""AI-powered study assistants.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1GL7aziC2wdx-2CrmED15RfaUuRvcrOFi
"""

!pip install langchain PyPDF2 google-generativeai

!pip install -U langchain langchain-community google-generativeai PyPDF2 --quiet

from langchain.llms.base import LLM
from typing import Optional, List, Any, Mapping
from pydantic import Field
import google.generativeai as genai

class GeminiLLM(LLM):
    model_name: str = Field(default="gemini-1.5-flash")  # ✅ Use flash version (free tier)
    temperature: float = Field(default=0.7)
    api_key: str = Field(default=None)
    model: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    @property
    def _llm_type(self) -> str:
        return "custom-gemini"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        response = self.model.generate_content(prompt)
        return response.text

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model_name": self.model_name, "temperature": self.temperature}

import PyPDF2

def extract_pdf_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize your Gemini LLM
llm = GeminiLLM(api_key="AIzaSyCmZoB_KgBCGKo_zq74lat2iQqeDEhujbs")  # 🔁 Replace with your actual key

# Summary Prompt
summary_prompt = PromptTemplate(
    input_variables=["text"],
    template="Summarize the following study material into concise bullet points:\n\n{text}"
)

summary_chain = LLMChain(llm=llm, prompt=summary_prompt)

# Quiz Prompt
quiz_prompt = PromptTemplate(
    input_variables=["summary"],
    template="""
You are a quiz generator. Based on the summary below, generate 2 multiple-choice questions (MCQs).
Each question should have 4 options (a-d) and mention the correct answer.

Summary:
{summary}
"""
)

quiz_chain = LLMChain(llm=llm, prompt=quiz_prompt)

!wget "https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-12.pdf" -O cybersecurity.pdf
pdf_path = "/content/cybersecurity.pdf"



# Step 1: Extract material
material = extract_pdf_text(pdf_path)

# Step 2: Summarize
summary = summary_chain.run(material)
print("📘 Summary:\n", summary)

# Step 3: Generate Quiz
quiz = quiz_chain.run(summary)
print("\n📝 Quiz Questions:\n", quiz)