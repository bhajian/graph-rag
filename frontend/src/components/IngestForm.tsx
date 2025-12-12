"use client";

import { useState } from "react";
import { ingestData } from "@/lib/api";

export function IngestForm() {
  const [text, setText] = useState("");
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ message: string; entities: string[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await ingestData({ text: text.trim(), source: source || undefined });
      setResult(response);
      setText("");
      setSource("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to ingest");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ marginBottom: "1rem" }}>
        <h2 style={{ margin: 0, fontSize: "1.35rem" }}>Ingestion Console</h2>
        <p style={{ color: "rgba(255,255,255,0.6)", marginTop: "0.4rem" }}>
          Send new knowledge into the graph. Query analyzer, entity resolver, and data
          loader collaborate automatically.
        </p>
      </div>

      <label htmlFor="source">Source label</label>
      <input
        id="source"
        type="text"
        placeholder="e.g., Wikipedia: Kubernetes"
        value={source}
        onChange={(e) => setSource(e.target.value)}
      />

      <label htmlFor="ingest-text" style={{ marginTop: "1rem" }}>
        Content
      </label>
      <textarea
        id="ingest-text"
        rows={10}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste unstructured text and let the agents build the graph."
      />

      {error && (
        <div style={{ color: "#ff8a8a", marginTop: "1rem" }}>{error}</div>
      )}
      {result && (
        <div className="context-card" style={{ marginTop: "1rem" }}>
          <div style={{ fontWeight: 600 }}>{result.message}</div>
          <div style={{ fontSize: "0.9rem", marginTop: "0.4rem" }}>
            Entities stored: {result.entities.join(", ") || "None"}
          </div>
        </div>
      )}

      <div style={{ marginTop: "1.25rem" }}>
        <button className="primary" onClick={handleSubmit} disabled={loading}>
          {loading ? "Processing..." : "Ingest Dataset"}
        </button>
      </div>
    </div>
  );
}
