import os
import re
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from pypdf import PdfReader
import gradio as gr

from src.chunker import chunk_resume_by_section
from src.vectorstore import setup_vectorstore
from src.tools import tools, handle_tool_calls
from src.prompts import build_system_prompt

load_dotenv(override=True)

openai = OpenAI(base_url=os.getenv("GROQ_BASE_URL"), api_key=os.getenv("GROQ_API_KEY"))

RATE_LIMIT_MSG = ("**Gemini API daily limit reached.** This is not a code error — "
    "the free-tier quota has been exhausted for today. "
    "Please try again after midnight Pacific Time (when the quota resets), "
    "or switch to a different API key.")

def read_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n\n"
    return text

resume = read_pdf("docs/Parmesh_Lata_Resume.pdf")
linkedin = read_pdf("docs/Linkedin.pdf")
name = "Parmesh Lata"

chunks = chunk_resume_by_section(resume)
collection = setup_vectorstore(chunks)
system_prompt = build_system_prompt(name, resume, linkedin)


def clean_gemini_output(text: str) -> str:
    text = re.sub(r'tool_code\s*\n.*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'thought\s*\n.*?\n\n', '', text, flags=re.DOTALL)
    text = re.sub(r'^(thought|tool_code)\s*\n', '', text.strip(), flags=re.IGNORECASE)
    return text.strip()


def chat(message, history):
    try:
        clean_history = [{"role": msg["role"], "content": msg["content"] or ""} for msg in history]

        user_query = collection.query(query_texts=[message], n_results=3)
        context = "\n\n".join(user_query["documents"][0])
        user_prompt = f"Here is the message from the user:\n{message}\n\nRelevant context:\n{context}"

        messages = [{"role": "system", "content": system_prompt}] + clean_history + [{"role": "user", "content": user_prompt}]

        done = False
        while not done:
            response = openai.chat.completions.create(model=os.getenv("GROQ_MODEL"), messages=messages, tools=tools, tool_choice="auto")
            finish_reason = response.choices[0].finish_reason
            assistant_message=response.choices[0].message

            if finish_reason == "tool_calls" or assistant_message.tool_calls:
                tool_calls = assistant_message.tool_calls
                results = handle_tool_calls(tool_calls)
                messages.append(assistant_message)
                messages.extend(results)
            else:
                done = True
        content = response.choices[0].message.content

        if content is None:
            forced=openai.chat.completions.create(model=os.getenv("GROQ_MODEL"), messages=messages)
            content=forced.choices[0].message.content
            
        return content if content is not None else "I don't have that in my profile yet — but it's a good question. What made you ask?"
    
    except RateLimitError:
        return RATE_LIMIT_MSG

gr.ChatInterface(chat).launch(server_name="0.0.0.0", server_port=7860)