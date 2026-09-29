import React, { useState, useEffect, useRef } from "react";
import { Bot, Send, User, Sparkles, ShieldAlert, Terminal, RefreshCw, BookOpen, ChevronRight } from "lucide-react";

export default function AiChatbot({ activeReport, token, apiBaseUrl = "" }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "👋 Hello! I am **InvisiBot**, your AI SOC Analyst & Security Advisor.\n\nI can analyze your scan reports, suggest Metasploit exploit commands, query historical audit data via RAG, and provide remediation steps.\n\nHow can I assist your security operation today?",
      sources: []
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const quickPrompts = [
    "⚔️ Suggest Metasploit commands for open ports",
    "🛡️ How do I remediate SMB & RDP vulnerabilities?",
    "📊 Summarize active target vulnerability risk",
    "🔍 Query RAG Knowledge Base for SSH hardening"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryText = null) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg = { role: "user", content: textToSend };
    setMessages(prev => [...prev, userMsg]);
    if (!queryText) setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${apiBaseUrl}/api/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": token ? `Bearer ${token}` : ""
        },
        body: JSON.stringify({
          query: textToSend,
          history: messages.slice(-6).map(m => ({ role: m.role, content: m.content })),
          report: activeReport || null
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      if (data.ok) {
        setMessages(prev => [
          ...prev,
          {
            role: "assistant",
            content: data.answer,
            sources: data.rag_sources || []
          }
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          {
            role: "assistant",
            content: "⚠️ **Error:** Unable to reach AI SOC Assistant service.",
            sources: []
          }
        ]);
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ **AI Service Offline:** ${err.message}. Showing local offline guidance.`,
          sources: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = (content) => {
    // Simple markdown formatting helper for code blocks and bold headers
    const parts = content.split(/(```[\s\S]*?```)/g);
    return parts.map((part, idx) => {
      if (part.startsWith("```")) {
        const lines = part.slice(3, -3).trim().split("\n");
        const lang = lines[0].match(/^[a-z]+$/i) ? lines[0] : "";
        const code = lang ? lines.slice(1).join("\n") : lines.join("\n");
        return (
          <div key={idx} className="my-3 rounded-lg overflow-hidden bg-slate-950 border border-emerald-500/30 text-xs font-mono">
            <div className="bg-slate-900/80 px-3 py-1 text-slate-400 border-b border-slate-800 flex justify-between items-center">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <Terminal className="w-3.5 h-3.5" />
                {lang || "command / snippet"}
              </span>
              <button
                onClick={() => navigator.clipboard.writeText(code)}
                className="text-[10px] hover:text-emerald-300 text-slate-400 transition"
              >
                Copy
              </button>
            </div>
            <pre className="p-3 text-emerald-300 overflow-x-auto whitespace-pre-wrap">{code}</pre>
          </div>
        );
      }
      return (
        <span key={idx} className="whitespace-pre-wrap leading-relaxed">
          {part.split("\n").map((line, lIdx) => {
            if (line.startsWith("### ")) {
              return <h3 key={lIdx} className="text-base font-semibold text-cyan-300 mt-2 mb-1">{line.replace("### ", "")}</h3>;
            }
            if (line.startsWith("- ")) {
              return <li key={lIdx} className="ml-4 list-disc text-slate-300 my-0.5">{line.replace("- ", "")}</li>;
            }
            return <span key={lIdx}>{line}<br /></span>;
          })}
        </span>
      );
    });
  };

  return (
    <div className="flex flex-col h-[650px] bg-slate-900/90 border border-cyan-500/30 rounded-xl shadow-2xl backdrop-blur-md overflow-hidden">
      {/* Header */}
      <div className="bg-slate-950/80 px-4 py-3 border-b border-cyan-500/30 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/40 text-cyan-400 animate-pulse">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              InvisiBot AI Assistant
              <span className="text-[10px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 px-2 py-0.5 rounded-full font-mono">
                RAG v1.0
              </span>
            </h2>
            <p className="text-[11px] text-slate-400">Context-Aware Penetration Testing & SOC Intelligence</p>
          </div>
        </div>
        {activeReport && (
          <div className="text-xs bg-slate-800/80 text-emerald-400 px-3 py-1 rounded-md border border-emerald-500/30 font-mono flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5" />
            Target: {activeReport.target}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-sm bg-gradient-to-b from-slate-900/40 to-slate-950/60">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-500/40 text-cyan-400 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-4 h-4" />
              </div>
            )}
            <div
              className={`max-w-[82%] rounded-xl p-3.5 shadow-lg ${
                msg.role === "user"
                  ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-br-none"
                  : "bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-bl-none"
              }`}
            >
              {renderContent(msg.content)}

              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t border-slate-700/60 flex flex-wrap items-center gap-1.5">
                  <span className="text-[10px] text-cyan-400 font-semibold flex items-center gap-1">
                    <BookOpen className="w-3 h-3" /> RAG Context:
                  </span>
                  {msg.sources.map((src, sIdx) => (
                    <span
                      key={sIdx}
                      className="text-[10px] bg-slate-900 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded font-mono"
                    >
                      {src.title}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center flex-shrink-0 mt-1 font-semibold">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-500/40 text-cyan-400 flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-slate-800/90 text-slate-400 p-3 rounded-xl border border-slate-700/60 text-xs flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
              Querying RAG vectors & analyzing attack surface...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts */}
      <div className="px-4 py-2 bg-slate-950/60 border-t border-slate-800 flex gap-2 overflow-x-auto">
        {quickPrompts.map((prompt, pIdx) => (
          <button
            key={pIdx}
            onClick={() => handleSend(prompt)}
            disabled={loading}
            className="text-[11px] bg-slate-800/80 hover:bg-cyan-950 hover:text-cyan-300 text-slate-300 border border-slate-700/60 hover:border-cyan-500/50 px-2.5 py-1 rounded-full whitespace-nowrap transition flex items-center gap-1"
          >
            {prompt}
            <ChevronRight className="w-3 h-3 text-cyan-400" />
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <div className="p-3 bg-slate-950 border-t border-slate-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask InvisiBot security advice, Metasploit syntax, or patch steps..."
            disabled={loading}
            className="flex-1 bg-slate-900 text-slate-100 placeholder-slate-500 text-xs px-3.5 py-2.5 rounded-lg border border-slate-700/80 focus:outline-none focus:border-cyan-500/80 font-sans"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-bold px-4 py-2.5 rounded-lg text-xs transition flex items-center gap-1.5 shadow-lg shadow-cyan-950"
          >
            <Send className="w-3.5 h-3.5" />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
