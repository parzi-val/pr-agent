'use client';

import React, { useState, useEffect, useRef } from 'react';

interface CodeIssue {
  file_path: string;
  line_number: number;
  issue_type: string;
  severity: string;
  tldr: string;
  description: string;
  suggestion: string;
}

interface LogEntry {
  message: string;
  status: 'active' | 'completed' | 'error';
  timestamp: string;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [issues, setIssues] = useState<CodeIssue[]>([]);
  const [error, setError] = useState('');
  
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const analyze = async () => {
    if (!url) return;
    setLoading(true);
    setError('');
    setIssues([]);
    setLogs([]);

    try {
      // We'll use fetch with a post request and then read the stream
      const response = await fetch('http://localhost:8080/api/v1/review/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo_url: url }),
      });

      if (!response.ok) {
        throw new Error('Failed to start analysis');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('ReadableStream not supported');

      let currentEvent = '';
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.replace('event: ', '').trim();
          } else if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              
              if (currentEvent === 'log') {
                setLogs(prev => [...prev, {
                  ...data,
                  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                }]);
              } else if (currentEvent === 'result') {
                setIssues(data.issues);
                setLoading(false);
              } else if (currentEvent === 'error') {
                setError(data.message);
                setLoading(false);
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e, dataStr);
            }
          }
        }
      }
    } catch (err: any) {
      console.error('Stream error:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const [posting, setPosting] = useState<Set<number>>(new Set());

  const postComment = async (issue: CodeIssue, index: number) => {
    setPosting(prev => new Set(prev).add(index));
    try {
      // Extract pr_number from url
      const prMatch = url.match(/pull\/(\d+)/);
      const prNumber = prMatch ? parseInt(prMatch[1]) : 0;

      const response = await fetch('http://localhost:8080/api/v1/comment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_url: url,
          pr_number: prNumber,
          file_path: issue.file_path,
          line_number: issue.line_number,
          body: `### [${issue.issue_type}]: ${issue.tldr}\n\n**Description:** ${issue.description}\n\n**Suggestion:**\n\`\`\`\n${issue.suggestion}\n\`\`\``
        }),
      });

      if (!response.ok) throw new Error('Failed to post comment');
      
      // Update logs for feedback
      setLogs(prev => [...prev, {
        message: `Successfully posted comment to ${issue.file_path}:${issue.line_number}`,
        status: 'completed',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      }]);
    } catch (err: any) {
      console.error(err);
      setError(`Failed to post comment: ${err.message}`);
    } finally {
      setPosting(prev => {
        const next = new Set(prev);
        next.delete(index);
        return next;
      });
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'text-red-400 border-red-500/20 bg-red-500/5';
      case 'high': return 'text-orange-400 border-orange-500/20 bg-orange-500/5';
      case 'medium': return 'text-yellow-400 border-yellow-500/20 bg-yellow-500/5';
      default: return 'text-blue-400 border-blue-500/20 bg-blue-500/5';
    }
  };

  return (
    <main className="min-h-screen bg-black text-zinc-300 font-sans selection:bg-white/10">
      <div className="max-w-4xl mx-auto px-6 py-20">
        {/* Header */}
        <div className="mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-zinc-800 bg-zinc-900/50 mb-6">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            <span className="text-[10px] uppercase tracking-widest font-semibold text-zinc-400">PR AGENT v0.1.0</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white mb-4">
            Automated PR Analysis
          </h1>
          <p className="text-lg text-zinc-500 max-w-2xl">
            Input a pull request URL to trigger a comprehensive AI-powered review with real-time feedback.
          </p>
        </div>

        {/* Input Area */}
        <div className="mb-12">
          <div className="flex gap-4 p-2 rounded-xl bg-zinc-900/30 border border-zinc-800 backdrop-blur-sm focus-within:border-zinc-700 transition-all">
            <input
              type="text"
              placeholder="https://github.com/owner/repo/pull/123"
              className="flex-1 bg-transparent border-none px-4 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && analyze()}
            />
            <button
              onClick={analyze}
              disabled={loading || !url}
              className="px-6 py-2 rounded-lg bg-white text-black text-sm font-semibold hover:bg-zinc-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Analyze
            </button>
          </div>
          {error && (
            <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono">
              Error: {error}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Progress / Logs Section */}
          <div className="lg:col-span-1">
            <div className="sticky top-10 rounded-2xl border border-zinc-800 bg-zinc-900/20 overflow-hidden flex flex-col h-[500px]">
              <div className="px-5 py-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/40">
                <h2 className="text-xs font-bold uppercase tracking-widest text-zinc-400">Process Logs</h2>
                {loading && <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>}
              </div>
              <div 
                ref={scrollRef}
                className="flex-1 p-5 overflow-y-auto space-y-4 font-mono text-[11px] leading-relaxed"
              >
                {logs.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center opacity-20 italic">
                    <p>No active session...</p>
                  </div>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} className="flex gap-3 group">
                      <span className="text-zinc-700 select-none">{log.timestamp}</span>
                      <div className="flex-1">
                        <span className={log.status === 'error' ? 'text-red-500' : 'text-zinc-400'}>
                          {log.message}
                          {log.status === 'active' && i === logs.length - 1 && <span className="inline-block animate-pulse ml-1">...</span>}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-sm font-semibold text-white">Review Results</h2>
              <span className="text-xs text-zinc-500">{issues.length} issues found</span>
            </div>

            {issues.length === 0 && !loading ? (
              <div className="h-64 rounded-2xl border border-dashed border-zinc-800 flex items-center justify-center text-zinc-600 text-sm">
                Analysis results will appear here.
              </div>
            ) : (
              issues.map((issue, i) => (
              <div key={i} className="rounded-2xl border border-zinc-800 bg-zinc-900/10 p-6 hover:bg-zinc-900/30 transition-all border-l-4" style={{ borderLeftColor: issue.severity.toLowerCase() === 'critical' ? '#f87171' : issue.severity.toLowerCase() === 'high' ? '#fb923c' : '#60a5fa' }}>
                <div className="flex flex-wrap items-center gap-2 mb-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getSeverityColor(issue.severity)}`}>
                    {issue.severity}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 text-[10px] font-bold uppercase tracking-wider">
                    {issue.issue_type}
                  </span>
                  <span className="text-[11px] text-zinc-500 font-mono">
                    {issue.file_path}:{issue.line_number}
                  </span>
                  
                  <div className="flex-1 flex justify-end">
                    <button
                      onClick={() => postComment(issue, i)}
                      disabled={posting.has(i)}
                      className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[10px] font-bold uppercase tracking-wider transition-all disabled:opacity-50"
                    >
                      {posting.has(i) ? (
                        <div className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                      ) : (
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.042-1.416-4.042-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                      )}
                      {posting.has(i) ? 'Posting...' : 'Post to PR'}
                    </button>
                  </div>
                </div>
                
                <h3 className="text-lg font-semibold text-white mb-2">{issue.tldr}</h3>
                <p className="text-sm text-zinc-400 mb-6 leading-relaxed">{issue.description}</p>
                
                <div className="rounded-xl bg-black/40 border border-zinc-800/50 p-4">
                  <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-2">Suggestion</p>
                  <p className="text-sm text-zinc-300 font-mono leading-relaxed">{issue.suggestion}</p>
                </div>
              </div>
            ))
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
