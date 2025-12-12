"use client";

import { useState } from "react";
import { ChatMessage, sendChat } from "@/lib/api";

export function ChatPanel() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [context, setContext] = useState<
    Array<{ source: string; target: string; relationship: string; summary?: string | null }>
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async () => {
    if (!input.trim()) return;
    const newHistory: ChatMessage[] = [
      ...history,
      { role: "user", content: input.trim() },
    ];
    setHistory(newHistory);
    setLoading(true);
    setError(null);

    try {
      const result = await sendChat({ message: input.trim(), history: newHistory });
      const updatedHistory: ChatMessage[] = [
        ...newHistory,
        {
          role: "assistant",
          content: result.reply,
        },
      ];
      setHistory(updatedHistory);
      setContext(result.context);
      setInput("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to chat");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ marginBottom: "1rem" }}>
        <h2 style={{ margin: 0, fontSize: "1.35rem" }}>Omnichannel Agent</h2>
        <p style={{ color: "rgba(255,255,255,0.6)", marginTop: "0.4rem" }}>
          Ask questions about your knowledge graph. The traversal agent collects
          context, and Omnichannel crafts the reply.
        </p>
      </div>

      <div style={{ flex: 1, overflowY: "auto", marginBottom: "1rem" }}>
        {history.length === 0 && (
          <p style={{ color: "rgba(255,255,255,0.4)" }}>
            Start a conversation to see responses and graph context here.
          </p>
        )}
        {history.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`chat-bubble ${message.role}`}>
            <strong style={{ display: "block", marginBottom: "0.25rem" }}>
              {message.role === "user" ? "You" : "Omnichannel"}
            </strong>
            <span>{message.content}</span>
          </div>
        ))}
      </div>

      {context.length > 0 && (
        <div>
          <h3 style={{ marginBottom: "0.5rem" }}>Graph Context</h3>
          {context.map((chunk, idx) => (
            <div key={idx} className="context-card">
              <div style={{ fontWeight: 600 }}>{chunk.relationship}</div>
              <div style={{ fontSize: "0.9rem", opacity: 0.8 }}>
                {chunk.source} → {chunk.target}
              </div>
              {chunk.summary && (
                <div style={{ marginTop: "0.4rem", fontSize: "0.85rem", opacity: 0.7 }}>
                  {chunk.summary}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {error && (
        <div style={{ color: "#ff8a8a", marginBottom: "0.75rem" }}>{error}</div>
      )}

      <div>
        <label htmlFor="chat-input">Ask anything</label>
        <textarea
          id="chat-input"
          rows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g., What relationships exist between Kubernetes and OpenShift?"
        />
        <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
          <button className="primary" onClick={handleSend} disabled={loading}>
            {loading ? "Thinking..." : "Send to Agents"}
          </button>
          <button
            type="button"
            onClick={() => {
              setHistory([]);
              setContext([]);
              setError(null);
            }}
            style={{
              background: "none",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: "999px",
              color: "inherit",
              padding: "0.65rem 1.5rem",
            }}
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}
