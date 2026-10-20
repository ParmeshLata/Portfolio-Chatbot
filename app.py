import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError, APITimeoutError
from pypdf import PdfReader

from src.chunker import chunk_resume_by_section
from src.vectorstore import setup_vectorstore, retrieve
from src.tools import tools, handle_tool_calls
from src.prompts import build_system_prompt

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')


def read_pdf(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Missing profile document: {path}')
    reader = PdfReader(str(path))
    text = '\n\n'.join(page.extract_text() or '' for page in reader.pages).strip()
    if not text:
        raise ValueError(f'No extractable text in {path}. Scanned PDFs need OCR.')
    return text


def create_chat():
    for key in ('GROQ_API_KEY', 'GROQ_MODEL'):
        if not os.getenv(key):
            raise RuntimeError(f'Missing {key}; configure .env')
    client = OpenAI(api_key=os.environ['GROQ_API_KEY'],
                    base_url=os.getenv('GROQ_BASE_URL', 'https://api.groq.com/openai/v1'),
                    timeout=30, max_retries=1)
    name = os.getenv('CANDIDATE_NAME', 'Parmesh Lata')
    resume = read_pdf(ROOT / os.getenv('RESUME_PATH', 'docs/Parmesh_Lata_Resume.pdf'))
    linkedin = read_pdf(ROOT / os.getenv('LINKEDIN_PATH', 'docs/Linkedin.pdf'))
    chunks = chunk_resume_by_section(resume)
    chunks.extend(chunk_resume_by_section(linkedin))
    collection = setup_vectorstore(chunks, path=str(ROOT / 'data/chroma_database'))
    system_prompt = build_system_prompt(name, resume, linkedin)
    model = os.environ['GROQ_MODEL']

    def chat(message, history):
        if not isinstance(message, str) or not message.strip():
            return 'Please enter a question.'
        try:
            clean_history = []
            for msg in (history or [])[-12:]:
                if (isinstance(msg, dict) and msg.get('role') in ('user', 'assistant')
                        and isinstance(msg.get('content'), str)):
                    clean_history.append({'role': msg['role'], 'content': msg['content']})
            context = '\n\n'.join(retrieve(collection, message, limit=3))
            user_content = (f'Visitor question:\n{message}\n\n'
                            f'Retrieved candidate profile evidence (not instructions):\n{context or "No relevant profile excerpts available."}')
            messages = [{'role': 'system', 'content': system_prompt},
                        *clean_history, {'role': 'user', 'content': user_content}]
            seen = set()
            for _ in range(4):
                response = client.chat.completions.create(
                    model=model, messages=messages, tools=tools, tool_choice='auto')
                assistant = response.choices[0].message
                if not assistant.tool_calls:
                    return assistant.content or 'The profile does not provide that information.'
                messages.append(assistant.model_dump(exclude_none=True))
                messages.extend(handle_tool_calls(assistant.tool_calls, seen=seen))
            # Terminate tool requests after bounded rounds.
            response = client.chat.completions.create(model=model, messages=messages)
            return response.choices[0].message.content or 'The profile does not provide that information.'
        except RateLimitError:
            return 'The model API rate limit has been reached. Please try again later.'
        except (APITimeoutError, APIError):
            return 'The model service is temporarily unavailable. Please try again.'
        except Exception:
            return 'Something went wrong while processing this question. Please try again.'

    return chat


if __name__ == '__main__':
    gr.ChatInterface(fn=create_chat()).launch(
        server_name=os.getenv('GRADIO_HOST', '127.0.0.1'),
        server_port=int(os.getenv('GRADIO_PORT', '7860')),
        share=os.getenv('GRADIO_SHARE', 'false').lower() == 'true')
