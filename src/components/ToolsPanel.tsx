import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import {
  getToolsAPI,
  LANGUAGES,
  CITATION_FORMATS,
  CONTENT_TYPES,
  TONE_OPTIONS,
  summarizeDocumentAPI,
  translateTextAPI,
  generateContentAPI,
  draftEmailAPI,
  meetingNotesAPI,
  taskListAPI,
  factCheckAPI,
  generateCitationAPI,
} from '../lib/toolsApi';

interface ToolsPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onToolResult?: (result: string, toolName: string) => void;
  selectedModel?: string;
}

type ToolCategory = 'file' | 'productivity' | 'research';

interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
}

export function ToolsPanel({ open, onOpenChange, onToolResult, selectedModel }: ToolsPanelProps) {
  const [activeTab, setActiveTab] = useState<string>('file');
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string>('');

  // Form states
  const [textInput, setTextInput] = useState('');
  const [targetLang, setTargetLang] = useState('en');
  const [summaryLength, setSummaryLength] = useState('medium');
  const [contentTopic, setContentTopic] = useState('');
  const [contentType, setContentType] = useState('blog');
  const [contentStyle, setContentStyle] = useState('professional');
  const [emailPurpose, setEmailPurpose] = useState('');
  const [emailRecipient, setEmailRecipient] = useState('');
  const [emailTone, setEmailTone] = useState('professional');
  const [keyPoints, setKeyPoints] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('');
  const [meetingTranscript, setMeetingTranscript] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [factStatement, setFactStatement] = useState('');
  const [citationTitle, setCitationTitle] = useState('');
  const [citationAuthors, setCitationAuthors] = useState('');
  const [citationYear, setCitationYear] = useState('');
  const [citationFormat, setCitationFormat] = useState('apa');

  const tools: Tool[] = [
    // File Tools
    { id: 'summarize', name: 'Summarizer', description: 'Summarize documents or text', category: 'file' },
    { id: 'translate', name: 'Translator', description: 'Translate between languages', category: 'file' },
    { id: 'generate-content', name: 'Content Generator', description: 'Generate blog posts, social media, ads', category: 'file' },
    // Productivity Tools
    { id: 'email-draft', name: 'Email Writer', description: 'Draft professional emails', category: 'productivity' },
    { id: 'meeting-notes', name: 'Meeting Notes', description: 'Create structured meeting notes', category: 'productivity' },
    { id: 'task-list', name: 'Task Planner', description: 'Generate organized task lists', category: 'productivity' },
    // Research Tools
    { id: 'paper-summary', name: 'Paper Summarizer', description: 'Summarize academic papers', category: 'research' },
    { id: 'fact-check', name: 'Fact Checker', description: 'Verify statements and claims', category: 'research' },
    { id: 'citation-generate', name: 'Citation Generator', description: 'Generate citations in various formats', category: 'research' },
  ];

  const filteredTools = tools.filter(tool => tool.category === activeTab);

  const handleToolSelect = (toolId: string) => {
    setSelectedTool(toolId);
    setResult('');
  };

  const handleSubmit = async () => {
    setLoading(true);
    setResult('');

    try {
      let response = '';
      let toolDisplayName = '';

      switch (selectedTool) {
        case 'summarize':
          toolDisplayName = 'Document Summarizer';
          for await (const chunk of summarizeDocumentAPI({ text: textInput, length: summaryLength, format: 'paragraph', model: selectedModel })) {
            if (chunk.content) response += chunk.content;
            setResult(response);
          }
          break;
          
        case 'translate':
          toolDisplayName = 'Translator';
          for await (const chunk of translateTextAPI({ text: textInput, target_lang: targetLang, model: selectedModel })) {
            if (chunk.content) response += chunk.content;
            setResult(response);
          }
          break;
          
        case 'generate-content':
          toolDisplayName = 'Content Generator';
          for await (const chunk of generateContentAPI({ topic: contentTopic, content_type: contentType, style: contentStyle, model: selectedModel })) {
            if (chunk.content) response += chunk.content;
            setResult(response);
          }
          break;
          
        case 'email-draft':
          toolDisplayName = 'Email Writer';
          const emailPoints = keyPoints.split('\n').filter(p => p.trim());
          for await (const chunk of draftEmailAPI({ purpose: emailPurpose, recipient: emailRecipient, tone: emailTone, key_points: emailPoints, model: selectedModel })) {
            if (chunk.content) response += chunk.content;
            setResult(response);
          }
          break;
          
        case 'meeting-notes':
          toolDisplayName = 'Meeting Notes';
          const notesDiscussionPoints = meetingTranscript.split('\n').filter(p => p.trim());
          for await (const chunk of meetingNotesAPI({ transcript: meetingTranscript, meeting_title: meetingTitle, discussion_points: notesDiscussionPoints, model: selectedModel })) {
            if (chunk.content) response += chunk.content;
            setResult(response);
          }
          break;
          
        case 'task-list':
          toolDisplayName = 'Task Planner';
          for await (const chunk of taskListAPI({ project_description: projectDesc, model: selectedModel })) {
            if (chunk.content) response += chunk.content;
            setResult(response);
          }
          break;
          
        case 'fact-check':
          toolDisplayName = 'Fact Checker';
          for await (const chunk of factCheckAPI(factStatement, selectedModel)) {
            if (chunk.content) response += chunk.content;
            setResult(response);
          }
          break;
          
        case 'citation-generate':
          toolDisplayName = 'Citation Generator';
          const citationResult = await generateCitationAPI({
            title: citationTitle,
            authors: citationAuthors.split(',').map(a => a.trim()).filter(a => a),
            year: parseInt(citationYear) || undefined,
            format: citationFormat,
            source_type: 'article'
          });
          response = citationResult.citation;
          setResult(response);
          break;
          
        default:
          response = 'Please select a tool to use.';
      }

      if (onToolResult && response) {
        onToolResult(response, toolDisplayName || selectedTool);
      }
    } catch (error: any) {
      console.error('Tool error:', error);
      const msg = error?.message || JSON.stringify(error) || 'Failed to process request.';
      setResult(`Error: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  const renderToolForm = () => {
    switch (selectedTool) {
      case 'summarize':
        return (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Text to Summarize</label>
              <Textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Enter text to summarize..."
                className="mt-1"
                rows={6}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Summary Length</label>
              <Select value={summaryLength} onValueChange={setSummaryLength}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="brief">Brief (2-3 sentences)</SelectItem>
                  <SelectItem value="medium">Medium (one paragraph)</SelectItem>
                  <SelectItem value="detailed">Detailed (multiple paragraphs)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 'translate':
        return (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Text to Translate</label>
              <Textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Enter text to translate..."
                className="mt-1"
                rows={4}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Target Language</label>
              <Select value={targetLang} onValueChange={setTargetLang}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGES.map(lang => (
                    <SelectItem key={lang.code} value={lang.code}>{lang.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 'generate-content':
        return (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Topic</label>
              <Input
                value={contentTopic}
                onChange={(e) => setContentTopic(e.target.value)}
                placeholder="Enter topic for content..."
                className="mt-1"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Content Type</label>
                <Select value={contentType} onValueChange={setContentType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CONTENT_TYPES.map(type => (
                      <SelectItem key={type.id} value={type.id}>{type.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Style</label>
                <Select value={contentStyle} onValueChange={setContentStyle}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="formal">Formal</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="persuasive">Persuasive</SelectItem>
                    <SelectItem value="technical">Technical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        );

      case 'email-draft':
        return (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Purpose</label>
              <Input
                value={emailPurpose}
                onChange={(e) => setEmailPurpose(e.target.value)}
                placeholder="e.g., Request meeting, Follow up..."
                className="mt-1"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Recipient</label>
                <Input
                  value={emailRecipient}
                  onChange={(e) => setEmailRecipient(e.target.value)}
                  placeholder="Recipient name/email"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Tone</label>
                <Select value={emailTone} onValueChange={setEmailTone}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TONE_OPTIONS.map(tone => (
                      <SelectItem key={tone.id} value={tone.id}>{tone.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Key Points (one per line)</label>
              <Textarea
                value={keyPoints}
                onChange={(e) => setKeyPoints(e.target.value)}
                placeholder="Enter key points to include..."
                className="mt-1"
                rows={4}
              />
            </div>
          </div>
        );

      case 'meeting-notes':
        return (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Meeting Title</label>
              <Input
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                placeholder="Enter meeting title..."
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Transcript / Discussion Points</label>
              <Textarea
                value={meetingTranscript}
                onChange={(e) => setMeetingTranscript(e.target.value)}
                placeholder="Paste meeting transcript or discussion points..."
                className="mt-1"
                rows={6}
              />
            </div>
          </div>
        );

      case 'task-list':
        return (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Project Description</label>
              <Textarea
                value={projectDesc}
                onChange={(e) => setProjectDesc(e.target.value)}
                placeholder="Describe your project or goal..."
                className="mt-1"
                rows={4}
              />
            </div>
          </div>
        );

      case 'fact-check':
        return (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Statement to Verify</label>
              <Textarea
                value={factStatement}
                onChange={(e) => setFactStatement(e.target.value)}
                placeholder="Enter statement or claim to fact-check..."
                className="mt-1"
                rows={4}
              />
            </div>
          </div>
        );

      case 'citation-generate':
        return (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Title</label>
              <Input
                value={citationTitle}
                onChange={(e) => setCitationTitle(e.target.value)}
                placeholder="Enter title..."
                className="mt-1"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Authors (comma separated)</label>
                <Input
                  value={citationAuthors}
                  onChange={(e) => setCitationAuthors(e.target.value)}
                  placeholder="John Doe, Jane Smith"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Year</label>
                <Input
                  value={citationYear}
                  onChange={(e) => setCitationYear(e.target.value)}
                  placeholder="2024"
                  className="mt-1"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Format</label>
              <Select value={citationFormat} onValueChange={setCitationFormat}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CITATION_FORMATS.map(fmt => (
                    <SelectItem key={fmt.id} value={fmt.id}>{fmt.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      default:
        return <p className="text-muted-foreground">Select a tool to get started.</p>;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>AI Tools</DialogTitle>
          <DialogDescription>
            Use these powerful tools powered by AI to boost your productivity
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="file">📄 File Tools</TabsTrigger>
            <TabsTrigger value="productivity">💼 Productivity</TabsTrigger>
            <TabsTrigger value="research">🔬 Research</TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab} className="space-y-4">
            {/* Tool Selection */}
            <div className="grid grid-cols-3 gap-2">
              {filteredTools.map(tool => (
                <Card
                  key={tool.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    selectedTool === tool.id ? 'ring-2 ring-primary' : ''
                  }`}
                  onClick={() => handleToolSelect(tool.id)}
                >
                  <CardHeader className="p-3">
                    <CardTitle className="text-sm">{tool.name}</CardTitle>
                    <CardDescription className="text-xs">{tool.description}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>

            {/* Tool Form */}
            {selectedTool && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">
                    {tools.find(t => t.id === selectedTool)?.name}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {renderToolForm()}

                  {loading && !result && (
                    <div className="mb-4">
                      <Card className="bg-muted/30">
                        <CardContent className="flex items-center gap-3">
                          <svg className="h-5 w-5 animate-spin text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                          </svg>
                          <span className="text-sm">Generating... please wait</span>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  <Button
                    onClick={handleSubmit}
                    disabled={loading || !selectedTool}
                    className="w-full mt-4"
                  >
                    {loading ? (
                      <div className="flex items-center gap-2">
                        <svg className="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                        </svg>
                        <span>Processing...</span>
                      </div>
                    ) : 'Generate'}
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Result */}
            {result && (
              <Card className="bg-muted">
                <CardHeader>
                  <CardTitle className="text-sm">Result</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="whitespace-pre-wrap text-sm">{result}</pre>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

export default ToolsPanel;

