import re

HEADERS = ('Education', 'Technical Skills', 'Skills', 'Projects', 'Experience',
           'Experience and Contributions', 'Work Experience', 'Core Competencies',
           'Coding Profiles', 'Certifications', 'Achievements', 'Summary')
HEADER_RE = re.compile(r'^\s*(' + '|'.join(re.escape(h) for h in sorted(HEADERS, key=len, reverse=True)) + r')\s*:?\s*$', re.I)

def chunk_resume_by_section(text, max_chars=1400, overlap=160):
    """Preserve unmatched text and split long sections with overlap."""
    if not text or not text.strip():
        return []
    sections, heading, lines = [], 'Profile', []
    for line in text.splitlines():
        match = HEADER_RE.fullmatch(line.strip())
        if match:
            if '\n'.join(lines).strip():
                sections.append((heading, '\n'.join(lines).strip()))
            heading, lines = match.group(1), []
        else:
            lines.append(line)
    if '\n'.join(lines).strip():
        sections.append((heading, '\n'.join(lines).strip()))
    chunks = []
    for section, content in sections:
        start = 0
        while start < len(content):
            end = min(start + max_chars, len(content))
            if end < len(content):
                split = content.rfind('\n', start + max_chars // 2, end)
                if split > start:
                    end = split
            part = content[start:end].strip()
            if part:
                chunks.append({'section': section, 'text': f'{section}:\n{part}'})
            if end == len(content):
                break
            start = max(start + 1, end - overlap)
    return chunks


def chunk_projects(projects_text):
    return [p.strip() for p in re.split(r'§', projects_text) if p.strip()]
