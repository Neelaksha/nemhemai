// Tools API Functions for LLM-powered productivity tools

import { API_BASE_URL, getToken } from './api';

export interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
}

export interface ToolRequest {
  text?: string;
  file_path?: string;
  length?: string;
  format?: string;
  model?: string;
}

export interface TranslateRequest {
  text: string;
  source_lang?: string;
  target_lang: string;
  model?: string;
}

export interface ContentGenerationRequest {
  topic: string;
  content_type?: string;
  length?: string;
  style?: string;
  keywords?: string[];
  model?: string;
}

export interface EmailDraftRequest {
  purpose: string;
  recipient: string;
  recipient_name?: string;
  sender_name?: string;
  tone?: string;
  key_points: string[];
  additional_context?: string;
  include_subject?: boolean;
  model?: string;
}

export interface MeetingNotesRequest {
  transcript?: string;
  discussion_points?: string[];
  attendees?: string[];
  meeting_title?: string;
  date?: string;
  extract_actions?: boolean;
  extract_decisions?: boolean;
  model?: string;
}

export interface TaskListRequest {
  project_description: string;
  goals?: string[];
  include_subtasks?: boolean;
  prioritize?: boolean;
  estimate_time?: boolean;
  model?: string;
}

export interface CitationRequest {
  source_type: string;
  authors: string[];
  title: string;
  year?: number;
  publisher?: string;
  url?: string;
  access_date?: string;
  volume?: string;
  issue?: string;
  pages?: string;
  doi?: string;
  format?: string;
}

// Helper to get response reader
async function* processStreamResponse(response: Response): AsyncGenerator<{ type: string; content?: string; error?: string; done?: boolean }> {
  if (!response.ok || !response.body) {
    // Try to surface server response text for easier debugging
    let txt = '';
    try {
      txt = await response.text();
    } catch (e) {
      txt = `status ${response.status}`;
    }
    throw new Error(`API request failed: ${txt}`);
  }
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    let lines = buffer.split('\n');
    buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (line.trim()) {
        try {
          yield JSON.parse(line);
        } catch (e) {
          console.error('Failed to parse streaming response:', e);
        }
      }
    }
  }
}

// Get available tools
export async function getToolsAPI(): Promise<{ tools: Tool[] }> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/tools`, {
    method: 'GET',
    credentials: 'include',
    headers,
  });
  
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

// Document Summarization
export async function* summarizeDocumentAPI(
  request: ToolRequest,
  file?: File
): AsyncGenerator<{ type: string; content?: string; error?: string; done?: boolean }> {
  let response: Response;
  const token = getToken();
  
  if (file) {
    // File upload version
    const formData = new FormData();
    formData.append('file', file);
    if (request.text) formData.append('text', request.text);
    if (request.length) formData.append('length', request.length);
    if (request.format) formData.append('format', request.format);
    if (request.model) formData.append('model', request.model);
    
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    response = await fetch(`${API_BASE_URL}/tools/summarize`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
      headers,
    });
  } else {
    // Text-only version
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    response = await fetch(`${API_BASE_URL}/tools/summarize`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
      credentials: 'include',
    });
  }
  
  yield* processStreamResponse(response);
}

// Translation
export async function* translateTextAPI(request: TranslateRequest): AsyncGenerator<{ type: string; content?: string; error?: string; done?: boolean }> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}/tools/translate`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    credentials: 'include',
  });
  
  yield* processStreamResponse(response);
}

// Content Generation
export async function* generateContentAPI(request: ContentGenerationRequest): AsyncGenerator<{ type: string; content?: string; error?: string; done?: boolean }> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}/tools/generate-content`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    credentials: 'include',
  });
  
  yield* processStreamResponse(response);
}

// Email Drafting
export async function* draftEmailAPI(request: EmailDraftRequest): AsyncGenerator<{ type: string; content?: string; error?: string; done?: boolean }> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}/tools/email-draft`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    credentials: 'include',
  });
  
  yield* processStreamResponse(response);
}

// Meeting Notes
export async function* meetingNotesAPI(request: MeetingNotesRequest): AsyncGenerator<{ type: string; content?: string; error?: string; done?: boolean }> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}/tools/meeting-notes`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    credentials: 'include',
  });
  
  yield* processStreamResponse(response);
}

// Task List Generation
export async function* taskListAPI(request: TaskListRequest): AsyncGenerator<{ type: string; content?: string; error?: string; done?: boolean }> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}/tools/task-list`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    credentials: 'include',
  });
  
  yield* processStreamResponse(response);
}

// Paper Summary
export async function* paperSummaryAPI(
  text?: string,
  url?: string,
  model?: string
): AsyncGenerator<{ type: string; content?: string; error?: string; done?: boolean }> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}/tools/paper-summary`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ text, url, model: model || 'llama3.2:1b' }),
    credentials: 'include',
  });
  
  yield* processStreamResponse(response);
}

// Fact Check
export async function* factCheckAPI(statement: string, model?: string): AsyncGenerator<{ type: string; content?: string; error?: string; done?: boolean }> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}/tools/fact-check`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ statement, model: model || 'llama3.2:1b' }),
    credentials: 'include',
  });
  
  yield* processStreamResponse(response);
}

// Citation Generator
export async function generateCitationAPI(request: CitationRequest): Promise<{ citation: string; format: string; source_info: object }> {
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}/tools/citation-generate`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    credentials: 'include',
  });
  
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

// Language options for translation
export const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'ar', name: 'Arabic' },
  { code: 'bn', name: 'Bengali' },
  { code: 'ta', name: 'Tamil' },
  { code: 'te', name: 'Telugu' },
  { code: 'mr', name: 'Marathi' },
  { code: 'gu', name: 'Gujarati' },
  { code: 'kn', name: 'Kannada' },
  { code: 'ml', name: 'Malayalam' },
  { code: 'pa', name: 'Punjabi' },
];

// Citation formats
export const CITATION_FORMATS = [
  { id: 'apa', name: 'APA' },
  { id: 'mla', name: 'MLA' },
  { id: 'chicago', name: 'Chicago' },
  { id: 'harvard', name: 'Harvard' },
  { id: 'ieee', name: 'IEEE' },
];

// Content types for generation
export const CONTENT_TYPES = [
  { id: 'blog', name: 'Blog Post' },
  { id: 'social', name: 'Social Media' },
  { id: 'product', name: 'Product Description' },
  { id: 'ad', name: 'Advertisement' },
  { id: 'article', name: 'Article' },
];

// Tone options for email
export const TONE_OPTIONS = [
  { id: 'formal', name: 'Formal' },
  { id: 'casual', name: 'Casual' },
  { id: 'persuasive', name: 'Persuasive' },
  { id: 'friendly', name: 'Friendly' },
];

