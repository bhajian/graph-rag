import { ChatPanel } from "@/components/ChatPanel";
import { IngestForm } from "@/components/IngestForm";

export default function HomePage() {
  return (
    <main>
      <header style={{ marginBottom: "2rem" }}>
        <p
          style={{
            textTransform: "uppercase",
            letterSpacing: "0.2rem",
            fontSize: "0.85rem",
            color: "rgba(255,255,255,0.5)",
          }}
        >
          LangGraph + Neo4j
        </p>
        <h1 style={{ fontSize: "2.8rem", marginBottom: "0.5rem" }}>
          Omnichannel Graph RAG Workbench
        </h1>
        <p style={{ color: "rgba(255,255,255,0.65)", maxWidth: "720px" }}>
          Configure ingestion and retrieval pipelines powered by five coordinating agents:
          Query analyzer, Entity resolver, Data loader, Traversal scout, and Omnichannel
          responder. Neo4j acts as the shared tool across the graph.
        </p>
      </header>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "1.5rem",
        }}
      >
        <IngestForm />
        <ChatPanel />
      </section>
    </main>
  );
}
