# Tools API Routes
# Simple tools powered by LLM for productivity, research, and file operations

import json
import os
import requests
import io
import tempfile
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime

# Import from main app
from models import get_db, User
from auth import get_current_user

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:1b"

# ============================================================================
# Pydantic Models
# ============================================================================

# Document Summarization
class SummarizeRequest(BaseModel):
    text: Optional[str] = None
    file_path: Optional[str] = None
    length: str = "medium"  # brief, medium, detailed
    format: str = "paragraph"  # bullet, paragraph
    model: str = DEFAULT_MODEL

# Translation
class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "en"
    model: str = DEFAULT_MODEL

# Content Generation
class ContentGenerationRequest(BaseModel):
    topic: str
    content_type: str = "blog"  # blog, social, product, ad, article
    length: str = "medium"  # short, medium, long
    style: str = "professional"  # formal, casual, persuasive, technical
    keywords: Optional[List[str]] = None
    model: str = DEFAULT_MODEL

# Email Drafting
class EmailDraftRequest(BaseModel):
    purpose: str
    recipient: str
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    tone: str = "professional"  # formal, casual, persuasive, friendly
    key_points: List[str]
    additional_context: Optional[str] = None
    include_subject: bool = True
    model: str = DEFAULT_MODEL

# Meeting Notes
class MeetingNotesRequest(BaseModel):
    transcript: Optional[str] = None
    discussion_points: Optional[List[str]] = None
    attendees: Optional[List[str]] = None
    meeting_title: Optional[str] = None
    date: Optional[str] = None
    extract_actions: bool = True
    extract_decisions: bool = True
    model: str = DEFAULT_MODEL

# Task List
class TaskListRequest(BaseModel):
    project_description: str
    goals: Optional[List[str]] = None
    include_subtasks: bool = True
    prioritize: bool = True
    estimate_time: bool = True
    model: str = DEFAULT_MODEL

# Paper Summary
class PaperSummaryRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    include_abstract: bool = True
    include_findings: bool = True
    include_methodology: bool = True
    model: str = DEFAULT_MODEL

# Fact Check
class FactCheckRequest(BaseModel):
    statement: str
    check_sources: bool = True
    model: str = DEFAULT_MODEL

# Citation Generate
class CitationRequest(BaseModel):
    source_type: str  # book, article, website, video
    authors: List[str]
    title: str
    year: Optional[int] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    access_date: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    format: str = "apa"  # apa, mla, chicago, harvard, ieee


# ============================================================================
# Helper Functions
# ============================================================================

def query_ollama(prompt: str, model: str = DEFAULT_MODEL, stream: bool = False):
    """Query Ollama API for text generation"""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 4096
        }
    }
    
    if stream:
        return url, headers, data
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")


def extract_text_from_file(file_path: str) -> str:
    """Extract text from various file formats"""
    from PIL import Image
    import pytesseract
    import PyPDF2
    import docx
    
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
        elif ext == '.docx':
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")


# ============================================================================
# Tool Endpoints
# ============================================================================

def register_tools_routes(app: FastAPI):
    
    # -------------------------------------------------------------------------
    # FILE TOOLS: Document Summarization
    # -------------------------------------------------------------------------
    @app.post("/tools/summarize")
    async def summarize_document(
        request: SummarizeRequest,
        file: UploadFile = File(None),
        current_user: User = Depends(get_current_user)
    ):
        """Summarize documents using LLM"""
        
        text = request.text
        file_path = None
        
        # Handle file upload
        if file:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                content = await file.read()
                tmp.write(content)
                file_path = tmp.name
            
            try:
                text = extract_text_from_file(file_path)
            finally:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
        
        if not text:
            raise HTTPException(status_code=400, detail="No text content provided")
        
        # Determine summary length
        length_map = {
            "brief": "2-3 sentences",
            "medium": "one paragraph",
            "detailed": "multiple paragraphs"
        }
        length_instruction = length_map.get(request.length, "one paragraph")
        
        format_instruction = "Use bullet points" if request.format == "bullet" else "Use flowing paragraph format"
        
        prompt = f"""You are a document summarization expert. Please summarize the following text.

Instructions:
- Summary length: {length_instruction}
- Format: {format_instruction}
- Make it clear and concise
- Preserve key information

Text to summarize:
{text}

Summary:"""
        
        def stream_summary():
            url, headers, data = query_ollama(prompt, request.model, stream=True)
            data["stream"] = True
            
            try:
                with requests.post(url, headers=headers, json=data, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                resp = chunk.get("response", "")
                                done = chunk.get("done", False)
                                yield json.dumps({"type": "summary", "content": resp, "done": done}) + "\n"
                                if done:
                                    break
                            except Exception:
                                continue
            except Exception as e:
                yield json.dumps({"type": "error", "error": str(e), "done": True}) + "\n"
        
        return StreamingResponse(stream_summary(), media_type="application/jsonl")
    
    # -------------------------------------------------------------------------
    # FILE TOOLS: Translation
    # -------------------------------------------------------------------------
    @app.post("/tools/translate")
    def translate_text(
        request: TranslateRequest,
        current_user: User = Depends(get_current_user)
    ):
        """Translate text between languages"""
        
        # Language code mapping
        lang_names = {
            "en": "English", "hi": "Hindi", "es": "Spanish", "fr": "French",
            "de": "German", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
            "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "ar": "Arabic",
            "bn": "Bengali", "ta": "Tamil", "te": "Telugu", "mr": "Marathi",
            "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi",
            "th": "Thai", "vi": "Vietnamese", "id": "Indonesian", "tr": "Turkish",
            "pl": "Polish", "nl": "Dutch", "sv": "Swedish", "da": "Danish",
            "fi": "Finnish", "no": "Norwegian", "cs": "Czech", "el": "Greek",
            "he": "Hebrew", "hu": "Hungarian", "ro": "Romanian", "uk": "Ukrainian"
        }
        
        source = lang_names.get(request.target_lang, request.target_lang)
        target = lang_names.get(request.target_lang, request.target_lang)
        
        if request.source_lang != "auto":
            source = lang_names.get(request.source_lang, request.source_lang)
        
        prompt = f"""You are a professional translator. Translate the following text from {source} to {target}.

Rules:
- Maintain the original meaning and tone
- Preserve formatting where possible
- Do not add explanations or commentary

Text to translate:
{request.text}

Translation:"""
        
        def stream_translation():
            url, headers, data = query_ollama(prompt, request.model, stream=True)
            data["stream"] = True
            
            try:
                with requests.post(url, headers=headers, json=data, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                resp = chunk.get("response", "")
                                done = chunk.get("done", False)
                                yield json.dumps({"type": "translation", "content": resp, "done": done}) + "\n"
                                if done:
                                    break
                            except Exception:
                                continue
            except Exception as e:
                yield json.dumps({"type": "error", "error": str(e), "done": True}) + "\n"
        
        return StreamingResponse(stream_translation(), media_type="application/jsonl")
    
    # -------------------------------------------------------------------------
    # FILE TOOLS: Content Generation
    # -------------------------------------------------------------------------
    @app.post("/tools/generate-content")
    def generate_content(
        request: ContentGenerationRequest,
        current_user: User = Depends(get_current_user)
    ):
        """Generate various types of content using LLM"""
        
        length_words = {"short": "100-150", "medium": "300-500", "long": "800-1200"}
        word_count = length_words.get(request.length, "300-500")
        
        style_instruction = {
            "formal": "Use formal, professional language",
            "casual": "Use casual, friendly tone",
            "persuasive": "Use persuasive, compelling language",
            "technical": "Use technical, precise language"
        }.get(request.style, "Use professional language")
        
        content_type_guide = {
            "blog": "Blog post format with engaging introduction, body, and conclusion",
            "social": "Social media post - concise, engaging, with appropriate hashtags",
            "product": "Product description - highlight features and benefits",
            "ad": "Advertising copy - attention-grabbing, persuasive",
            "article": "Article format with title and well-structured sections"
        }.get(request.content_type, "Article format")
        
        keywords_text = f"\nInclude these keywords: {', '.join(request.keywords)}" if request.keywords else ""
        
        prompt = f"""You are a content generation expert. Generate content based on the following request.

Topic: {request.topic}
Content Type: {content_type_guide}
Length: approximately {word_count} words
Style: {style_instruction}{keywords_text}

Generate the content:"""
        
        def stream_content():
            url, headers, data = query_ollama(prompt, request.model, stream=True)
            data["stream"] = True
            
            try:
                with requests.post(url, headers=headers, json=data, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                resp = chunk.get("response", "")
                                done = chunk.get("done", False)
                                yield json.dumps({"type": "content", "content": resp, "done": done}) + "\n"
                                if done:
                                    break
                            except Exception:
                                continue
            except Exception as e:
                yield json.dumps({"type": "error", "error": str(e), "done": True}) + "\n"
        
        return StreamingResponse(stream_content(), media_type="application/jsonl")
    
    # -------------------------------------------------------------------------
    # PRODUCTIVITY TOOLS: Email Drafting
    # -------------------------------------------------------------------------
    @app.post("/tools/email-draft")
    def draft_email(
        request: EmailDraftRequest,
        current_user: User = Depends(get_current_user)
    ):
        """Draft professional emails using LLM"""
        
        tone_guide = {
            "formal": "Use formal, professional language with proper greetings and sign-offs",
            "casual": "Use friendly, casual tone while remaining professional",
            "persuasive": "Use compelling, persuasive language to encourage action",
            "friendly": "Use warm, friendly tone to build rapport"
        }.get(request.tone, "Use professional language")
        
        key_points_text = "\n".join([f"- {point}" for point in request.key_points])
        
        greeting = f"Dear {request.recipient_name}," if request.recipient_name else f"Dear {request.recipient},"
        closing = f"\nBest regards,\n{request.sender_name}" if request.sender_name else "\nBest regards,"
        
        context_text = f"\nAdditional context: {request.additional_context}" if request.additional_context else ""
        
        prompt = f"""You are a professional email writer. Draft an email based on the following details.

Email Details:
- Purpose: {request.purpose}
- Recipient: {request.recipient}
- Tone: {tone_guide}
- Include subject line: {request.include_subject}

Key points to include:
{key_points_text}{context_text}

Format the email professionally:"""
        
        def stream_email():
            url, headers, data = query_ollama(prompt, request.model, stream=True)
            data["stream"] = True
            
            try:
                with requests.post(url, headers=headers, json=data, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                resp = chunk.get("response", "")
                                done = chunk.get("done", False)
                                yield json.dumps({"type": "email", "content": resp, "done": done}) + "\n"
                                if done:
                                    break
                            except Exception:
                                continue
            except Exception as e:
                yield json.dumps({"type": "error", "error": str(e), "done": True}) + "\n"
        
        return StreamingResponse(stream_email(), media_type="application/jsonl")
    
    # -------------------------------------------------------------------------
    # PRODUCTIVITY TOOLS: Meeting Notes
    # -------------------------------------------------------------------------
    @app.post("/tools/meeting-notes")
    def meeting_notes(
        request: MeetingNotesRequest,
        current_user: User = Depends(get_current_user)
    ):
        """Generate structured meeting notes from transcript or points"""
        
        transcript = request.transcript or ""
        discussion = "\n".join([f"- {point}" for point in (request.discussion_points or [])])
        attendees = ", ".join(request.attendees) if request.attendees else "Not specified"
        
        action_instruction = "Identify and list all action items with responsible persons" if request.extract_actions else "Skip action items"
        decision_instruction = "Highlight key decisions made during the meeting" if request.extract_decisions else "Skip decisions"
        
        title = request.meeting_title or "Meeting"
        date = request.date or datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""You are a meeting notes specialist. Create structured meeting notes.

Meeting Information:
- Title: {title}
- Date: {date}
- Attendees: {attendees}

Discussion Points:
{discussion}

Meeting Transcript (if available):
{transcript}

Instructions:
- Create a structured summary
- {action_instruction}
- {decision_instruction}
- Use clear headings and bullet points

Generate meeting notes:"""
        
        def stream_notes():
            url, headers, data = query_ollama(prompt, request.model, stream=True)
            data["stream"] = True
            
            try:
                with requests.post(url, headers=headers, json=data, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                resp = chunk.get("response", "")
                                done = chunk.get("done", False)
                                yield json.dumps({"type": "notes", "content": resp, "done": done}) + "\n"
                                if done:
                                    break
                            except Exception:
                                continue
            except Exception as e:
                yield json.dumps({"type": "error", "error": str(e), "done": True}) + "\n"
        
        return StreamingResponse(stream_notes(), media_type="application/jsonl")
    
    # -------------------------------------------------------------------------
    # PRODUCTIVITY TOOLS: Task List Generation
    # -------------------------------------------------------------------------
    @app.post("/tools/task-list")
    def generate_task_list(
        request: TaskListRequest,
        current_user: User = Depends(get_current_user)
    ):
        """Generate organized task lists from project descriptions"""
        
        goals_text = "\n".join([f"- {goal}" for goal in (request.goals or [])])
        
        subtask_instruction = "Break down each task into smaller subtasks" if request.include_subtasks else "Keep tasks at main level"
        priority_instruction = "Assign priority levels (High/Medium/Low) to each task" if request.prioritize else "No priority needed"
        time_instruction = "Estimate time required for each task" if request.estimate_time else "No time estimates needed"
        
        prompt = f"""You are a project management expert. Create a structured task list.

Project Description:
{request.project_description}

Project Goals:
{goals_text}

Instructions:
- {subtask_instruction}
- {priority_instruction}
- {time_instruction}
- Organize tasks in logical order
- Use clear numbering and formatting

Generate task list:"""
        
        def stream_tasks():
            url, headers, data = query_ollama(prompt, request.model, stream=True)
            data["stream"] = True
            
            try:
                with requests.post(url, headers=headers, json=data, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                resp = chunk.get("response", "")
                                done = chunk.get("done", False)
                                yield json.dumps({"type": "tasks", "content": resp, "done": done}) + "\n"
                                if done:
                                    break
                            except Exception:
                                continue
            except Exception as e:
                yield json.dumps({"type": "error", "error": str(e), "done": True}) + "\n"
        
        return StreamingResponse(stream_tasks(), media_type="application/jsonl")
    
    # -------------------------------------------------------------------------
    # RESEARCH TOOLS: Paper Summary
    # -------------------------------------------------------------------------
    @app.post("/tools/paper-summary")
    async def summarize_paper(
        request: PaperSummaryRequest,
        file: UploadFile = File(None),
        current_user: User = Depends(get_current_user)
    ):
        """Summarize academic papers"""
        
        text = request.text
        file_path = None
        
        # Handle file upload
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                content = await file.read()
                tmp.write(content)
                file_path = tmp.name
            
            try:
                text = extract_text_from_file(file_path)
            finally:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
        
        # Try to fetch from URL if provided
        if request.url and not text:
            try:
                response = requests.get(request.url, timeout=30)
                if response.ok:
                    # Simple extraction - in production use proper HTML parsing
                    text = response.text[:5000]  # Limit text length
            except:
                pass
        
        if not text:
            raise HTTPException(status_code=400, detail="No paper content provided")
        
        sections = []
        if request.include_abstract:
            sections.append("Abstract: A brief overview of the paper")
        if request.include_findings:
            sections.append("Key Findings: Main results and discoveries")
        if request.include_methodology:
            sections.append("Methodology: Research methods used")
        
        sections_text = "\n".join(sections)
        
        prompt = f"""You are an academic research assistant. Summarize the following academic paper.

Required Sections:
{sections_text}

Rules:
- Use clear, academic language
- Focus on essential information
- Avoid unnecessary details

Paper Content:
{text}

Generate the summary:"""
        
        def stream_summary():
            url, headers, data = query_ollama(prompt, request.model, stream=True)
            data["stream"] = True
            
            try:
                with requests.post(url, headers=headers, json=data, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                resp = chunk.get("response", "")
                                done = chunk.get("done", False)
                                yield json.dumps({"type": "paper_summary", "content": resp, "done": done}) + "\n"
                                if done:
                                    break
                            except Exception:
                                continue
            except Exception as e:
                yield json.dumps({"type": "error", "error": str(e), "done": True}) + "\n"
        
        return StreamingResponse(stream_summary(), media_type="application/jsonl")
    
    # -------------------------------------------------------------------------
    # RESEARCH TOOLS: Fact-Checking
    # -------------------------------------------------------------------------
    @app.post("/tools/fact-check")
    def fact_check(
        request: FactCheckRequest,
        current_user: User = Depends(get_current_user)
    ):
        """Check facts and verify statements"""
        
        prompt = f"""You are a fact-checking assistant. Verify the following statement.

Statement to verify:
{request.statement}

Instructions:
- Check the accuracy of the statement
- Provide a confidence level (High/Medium/Low)
- If false or partially true, explain why
- Use evidence-based reasoning

Analysis:"""
        
        def stream_factcheck():
            url, headers, data = query_ollama(prompt, request.model, stream=True)
            data["stream"] = True
            # Increase response length for fact-checking
            data["options"]["num_predict"] = 512
            
            try:
                with requests.post(url, headers=headers, json=data, stream=True, timeout=180) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                resp = chunk.get("response", "")
                                done = chunk.get("done", False)
                                yield json.dumps({"type": "factcheck", "content": resp, "done": done}) + "\n"
                                if done:
                                    break
                            except Exception:
                                continue
            except Exception as e:
                yield json.dumps({"type": "error", "error": str(e), "done": True}) + "\n"
        
        return StreamingResponse(stream_factcheck(), media_type="application/jsonl")
    
    # -------------------------------------------------------------------------
    # RESEARCH TOOLS: Citation Generator
    # -------------------------------------------------------------------------
    @app.post("/tools/citation-generate")
    def generate_citation(
        request: CitationRequest,
        current_user: User = Depends(get_current_user)
    ):
        """Generate formatted citations"""
        
        authors_str = ", ".join(request.authors)
        
        # Generate citation based on format
        if request.format == "apa":
            authors_apa = f"{request.authors[0]} et al." if len(request.authors) > 2 else ", ".join(request.authors)
            citation = f"{authors_apa} ({request.year}). {request.title}"
            if request.publisher:
                citation += f". {request.publisher}."
            if request.doi:
                citation += f" https://doi.org/{request.doi}"
                
        elif request.format == "mla":
            citation = f"{request.authors[0]}, et al. \"{request.title}.\""
            if request.publisher:
                citation += f" {request.publisher},"
            citation += f" {request.year}."
                
        elif request.format == "chicago":
            citation = f"{request.authors[0]}. \"{request.title}.\""
            if request.publisher:
                citation += f" {request.publisher},"
            citation += f" {request.year}."
                
        elif request.format == "harvard":
            citation = f"{request.authors[0]} ({year}) '{request.title}'"
            if request.publisher:
                citation += f", {request.publisher}"
            citation += "."
                
        elif request.format == "ieee":
            authors_ieee = ", ".join([a.split()[-1] for a in request.authors])
            citation = f"{authors_ieee}, \"{request.title},\""
            if request.publisher:
                citation += f" {request.publisher},"
            citation += f" {request.year}."
        
        return {
            "citation": citation,
            "format": request.format,
            "source_info": {
                "authors": request.authors,
                "title": request.title,
                "year": request.year,
                "publisher": request.publisher,
                "url": request.url,
                "doi": request.doi
            }
        }
    
    # -------------------------------------------------------------------------
    # Get Available Tools
    # -------------------------------------------------------------------------
    @app.get("/tools")
    def get_tools(current_user: User = Depends(get_current_user)):
        """Get list of available tools"""
        return {
            "tools": [
                {
                    "id": "summarize",
                    "name": "Document Summarizer",
                    "description": "Summarize documents, articles, or long texts",
                    "category": "file"
                },
                {
                    "id": "translate",
                    "name": "Translator",
                    "description": "Translate text between 30+ languages",
                    "category": "file"
                },
                {
                    "id": "generate-content",
                    "name": "Content Generator",
                    "description": "Generate blog posts, social media, ads, and more",
                    "category": "file"
                },
                {
                    "id": "email-draft",
                    "name": "Email Writer",
                    "description": "Draft professional emails for any purpose",
                    "category": "productivity"
                },
                {
                    "id": "meeting-notes",
                    "name": "Meeting Notes",
                    "description": "Convert transcripts to structured notes",
                    "category": "productivity"
                },
                {
                    "id": "task-list",
                    "name": "Task Planner",
                    "description": "Generate organized task lists from project goals",
                    "category": "productivity"
                },
                {
                    "id": "paper-summary",
                    "name": "Paper Summarizer",
                    "description": "Summarize academic papers and research",
                    "category": "research"
                },
                {
                    "id": "fact-check",
                    "name": "Fact Checker",
                    "description": "Verify statements and claims",
                    "category": "research"
                },
                {
                    "id": "citation-generate",
                    "name": "Citation Generator",
                    "description": "Generate citations in APA, MLA, Chicago, and more",
                    "category": "research"
                }
            ]
        }

