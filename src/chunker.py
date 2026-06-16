import re

def chunk_resume_by_section(text):
    section_headers = [
        "Education", "Technical Skills", "Projects",
        "Experience and Contributions", "Core Competencies",
        "Coding Profiles"
    ]
    chunks = []
    pattern = "|".join([re.escape(h) for h in section_headers])
    parts = re.split(f"({pattern})", text, flags=re.IGNORECASE)

    i = 1
    while i < len(parts) - 1:
        header = parts[i].strip()
        content = parts[i + 1].strip()
        chunks.append({"section": header, "text": f"{header}:\n{content}"})
        i += 2
    return chunks

def chunk_projects(projects_text):
    project_chunks = re.split(r'§', projects_text)
    return [p.strip() for p in project_chunks if p.strip()]