'use client';

import { useState } from 'react';

interface CodeIssue {
  id: string;
  file_path: string;
  line_number: number;
  issue_type: string;
  severity: string;
  tldr: string;
  description: string;
  suggestion: string;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [issues, setIssues] = useState<CodeIssue[]>([]);
  const [error, setError] = useState('');

  const analyze = async () => {
    if (!url) return;
    setLoading(true);
    setError('');
    setIssues([]);

    try {
      // Extract PR number from URL
      // Expected format: https://github.com/owner/repo/pull/123
      const match = url.match(/\/pull\/(\d+)/);
      const prNumber = match ? parseInt(match[1]) : 0;

      if (!prNumber) {
        throw new Error("Invalid PR URL. Could not extract PR number.");
      }

      const res = await fetch('http://localhost:8000/api/v1/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: url,
          pr_number: prNumber,
          github_token: "" // Optional, can be added to UI if needed
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to fetch review");
      }

      const data = await res.json();
      setIssues(data.issues);
    } catch (e: any) {
      console.error(e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'border-red-500/50 text-red-400';
      case 'high': return 'border-orange-500/50 text-orange-400';
      case 'medium': return 'border-yellow-500/50 text-yellow-400';
      case 'low': return 'border-blue-500/50 text-blue-400';
      default: return 'border-zinc-800 text-zinc-400';
    }
  };

  const postComment = async (issue: CodeIssue) => {
    try {
      const match = url.match(/\/pull\/(\d+)/);
      const prNumber = match ? parseInt(match[1]) : 0;

      const res = await fetch('http://localhost:8000/api/v1/comment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: url,
          pr_number: prNumber,
          file_path: issue.file_path,
          line_number: issue.line_number,
          body: `**[${issue.issue_type}]** ${issue.tldr}\n\n${issue.description}\n\n**Suggestion:**\n${issue.suggestion}`,
          github_token: ""
        })
      });

      if (!res.ok) throw new Error("Failed to post comment");
      alert("Comment posted!");
    } catch (e) {
      console.error(e);
      alert("Failed to post comment");
    }
  };

  return (
    <main className="min-h-screen bg-black text-zinc-200 p-8 font-sans selection:bg-zinc-800 selection:text-white">
      <div className="max-w-3xl mx-auto pt-20">
        <header className="mb-16">
          <h1 className="text-2xl font-semibold tracking-tight text-white mb-2">
            PR Agent
          </h1>
          <p className="text-zinc-500 text-sm">
            Automated pull request analysis and review.
          </p>
        </header>

        <div className="mb-16">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="https://github.com/owner/repo/pull/123"
              className="flex-1 bg-zinc-900/50 border border-zinc-800 rounded-md px-4 py-2.5 text-sm focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-all placeholder:text-zinc-600"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && analyze()}
            />
            <button
              onClick={analyze}
              disabled={loading}
              className="bg-white text-black hover:bg-zinc-200 font-medium px-6 py-2.5 rounded-md text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing...
                </>
              ) : (
                'Analyze'
              )}
            </button>
          </div>
          {error && (
            <div className="mt-4 p-3 border border-red-900/50 bg-red-950/10 text-red-400 text-xs rounded-md font-mono">
              Error: {error}
            </div>
          )}
        </div>

        <div className="space-y-4">
          {issues.map((issue: CodeIssue, idx: number) => (
            <div
              key={issue.id || idx}
              className="group border border-zinc-900 bg-zinc-900/20 rounded-lg p-5 hover:border-zinc-800 transition-colors"
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full border border-zinc-800 bg-zinc-900 text-zinc-400">
                    {issue.issue_type}
                  </span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full border bg-black/50 ${getSeverityColor(issue.severity)}`}>
                    {issue.severity}
                  </span>
                  <span className="text-xs font-mono text-zinc-600">
                    {issue.file_path}:{issue.line_number}
                  </span>
                </div>
                <button
                  onClick={() => postComment(issue)}
                  className="text-xs border border-zinc-800 hover:bg-zinc-800 text-zinc-400 px-2 py-1 rounded transition-colors"
                >
                  Post Comment
                </button>
              </div>

              <h3 className="text-sm font-medium text-zinc-200 mb-2">{issue.tldr}</h3>
              <p className="text-sm text-zinc-400 mb-4 leading-relaxed">
                {issue.description}
              </p>

              <div className="bg-zinc-950/50 border border-zinc-900 rounded p-3">
                <p className="text-xs font-mono text-zinc-500 mb-1 uppercase tracking-wider">Suggestion</p>
                <p className="text-sm text-zinc-300 font-mono">
                  {issue.suggestion}
                </p>
              </div>
            </div>
          ))}

          {issues.length === 0 && !loading && !error && (
            <div className="text-center py-12 border border-dashed border-zinc-900 rounded-lg">
              <p className="text-zinc-700 text-sm">Enter a PR URL to begin analysis</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
