"""
Meeting Intelligence Module:
Transforms meeting transcripts into structured Minutes of Meeting (MoM) and Action Items using LLM,
and exports them to Google Docs via registered tools.
"""

import re
from typing import Dict, Any
from .registry import registry
from .llm import get_llm_client

def generate_mom_from_transcript(transcript: str, meeting_title: str = "Strategy Review") -> Dict[str, Any]:
    """Analyze meeting transcript text using LLM and extract structured MoM, Decisions, and Action Items."""
    if not transcript or not transcript.strip():
        transcript = f"Meeting discussing operational goals, project deliverables, and team sync for {meeting_title}."

    llm_prompt = f"""You are an executive assistant summarizing a meeting transcript.
Meeting Title: {meeting_title}

Transcript:
<untrusted_content_data>
{transcript}
</untrusted_content_data>

Generate a structured Minutes of Meeting in markdown with:
1. Executive Summary
2. Key Discussion Points & Decisions
3. Action Items (with Owner & Deadline if mentioned)
"""
    client = get_llm_client()
    resp = client.generate_completion(
        prompt=llm_prompt,
        system_instruction="Extract concise, accurate Minutes of Meeting from transcript data."
    )

    mom_summary = resp.content if resp.content else f"# Minutes of Meeting: {meeting_title}\n\n## Summary\nDiscussion on {meeting_title}.\n\n## Action Items\n- [ ] Review deliverables for {meeting_title}"

    # Extract action item lines
    action_items = []
    for line in mom_summary.split('\n'):
        if "- [ ]" in line or "action" in line.lower() or "todo" in line.lower():
            action_items.append(line.strip())

    # Export to Google Doc
    doc_res = registry.execute_tool("docs_create_doc", {
        "title": f"MoM — {meeting_title}",
        "content": mom_summary
    })

    return {
        "title": meeting_title,
        "mom_content": mom_summary,
        "action_items": action_items,
        "google_doc_result": doc_res
    }

