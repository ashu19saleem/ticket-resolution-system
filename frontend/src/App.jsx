import { useState } from "react";

const API_BASE = "http://localhost:8000";

const CONFIDENCE_COLOR = (label) => {
  if (label === "High") return "#22C55E";
  if (label === "Medium") return "#F59E0B";
  return "#EF4444";
};

const CATEGORY_ICON = (cat) => {
  const icons = {
    "Server Down": "🔴",
    "Performance Issue": "🟡",
    "Network Issue": "🌐",
    "Login Problem": "🔐",
    "Database Error": "🗄️",
    "Email Issue": "📧",
    "VPN Issue": "🔒",
    Other: "📋",
  };
  return icons[cat] || "📋";
};

function ConfidenceMeter({ value, label }) {
  const color = CONFIDENCE_COLOR(label);
  const pct = Math.round(value * 100);
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ color: "#94A3B8", fontSize: 13, fontFamily: "Inter, sans-serif" }}>
          Confidence Score
        </span>
        <span style={{ color, fontWeight: 700, fontSize: 15, fontFamily: "JetBrains Mono, monospace" }}>
          {pct}% — {label}
        </span>
      </div>
      <div style={{ background: "#1E293B", borderRadius: 6, height: 8, overflow: "hidden" }}>
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: `linear-gradient(90deg, ${color}99, ${color})`,
            borderRadius: 6,
            transition: "width 1s cubic-bezier(0.4,0,0.2,1)",
          }}
        />
      </div>
    </div>
  );
}

function SourcePill({ source, sourceType, similarity }) {
  const isTicket = sourceType === "ticket";
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        background: "#1E293B",
        border: "1px solid #334155",
        borderRadius: 20,
        padding: "4px 12px",
        margin: "4px",
        fontSize: 12,
        fontFamily: "JetBrains Mono, monospace",
        color: "#94A3B8",
      }}
    >
      <span>{isTicket ? "🎫" : "📄"}</span>
      <span style={{ color: "#E2E8F0" }}>{source}</span>
      <span style={{ color: "#3B82F6" }}>{Math.round(similarity * 100)}%</span>
    </div>
  );
}

function ResultCard({ data }) {
  return (
    <div
      style={{
        background: "#0F172A",
        border: "1px solid #1E293B",
        borderRadius: 16,
        padding: 28,
        marginTop: 24,
        animation: "fadeIn 0.4s ease",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 20,
          flexWrap: "wrap",
          gap: 10,
        }}
      >
        <div>
          <div style={{ color: "#475569", fontSize: 11, fontFamily: "Inter, sans-serif", marginBottom: 4 }}>
            ORIGINAL QUERY
          </div>
          <div style={{ color: "#CBD5E1", fontSize: 14, fontFamily: "Inter, sans-serif" }}>
            {data.original_query}
          </div>
        </div>
        <div
          style={{
            background: "#1E293B",
            borderRadius: 8,
            padding: "6px 14px",
            fontSize: 13,
            fontFamily: "Inter, sans-serif",
            color: "#E2E8F0",
          }}
        >
          {CATEGORY_ICON(data.category)} {data.category}
          <span style={{ color: "#475569", marginLeft: 8 }}>
            {Math.round(data.category_confidence * 100)}%
          </span>
        </div>
      </div>

      {/* Rewritten query */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ color: "#475569", fontSize: 11, fontFamily: "Inter, sans-serif", marginBottom: 4 }}>
          OPTIMIZED SEARCH QUERY
        </div>
        <div
          style={{
            color: "#3B82F6",
            fontSize: 13,
            fontFamily: "JetBrains Mono, monospace",
            background: "#1E293B",
            padding: "8px 12px",
            borderRadius: 8,
            borderLeft: "3px solid #3B82F6",
          }}
        >
          {data.rewritten_query}
        </div>
      </div>

      {/* Confidence meter */}
      <ConfidenceMeter value={data.confidence} label={data.confidence_label} />

      {/* Answer */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ color: "#475569", fontSize: 11, fontFamily: "Inter, sans-serif", marginBottom: 8 }}>
          RESOLUTION
        </div>
        <div
          style={{
            color: "#E2E8F0",
            fontSize: 14,
            fontFamily: "Inter, sans-serif",
            lineHeight: 1.75,
            background: "#1E293B",
            borderRadius: 10,
            padding: 16,
            whiteSpace: "pre-wrap",
          }}
        >
          {data.answer}
        </div>
      </div>

      {/* Sources */}
      {data.sources?.length > 0 && (
        <div>
          <div style={{ color: "#475569", fontSize: 11, fontFamily: "Inter, sans-serif", marginBottom: 8 }}>
            SOURCES ({data.sources.length})
          </div>
          <div>
            {data.sources.map((s, i) => (
              <SourcePill key={i} {...s} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [summarizeText, setSummarizeText] = useState("");
  const [summary, setSummary] = useState(null);
  const [activeTab, setActiveTab] = useState("query");

  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, use_hybrid_search: false }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSummarize = async () => {
    if (!summarizeText.trim()) return;
    setLoading(true);
    setSummary(null);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: summarizeText }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setSummary(data.summary);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const tabStyle = (tab) => ({
    padding: "8px 20px",
    borderRadius: 8,
    border: "none",
    cursor: "pointer",
    fontFamily: "Inter, sans-serif",
    fontSize: 13,
    fontWeight: 500,
    background: activeTab === tab ? "#3B82F6" : "transparent",
    color: activeTab === tab ? "#fff" : "#64748B",
    transition: "all 0.2s",
  });

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#020817",
        padding: "40px 20px",
        fontFamily: "Inter, sans-serif",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes spin { to { transform: rotate(360deg); } }
        textarea:focus, input:focus { outline: none; }
        * { box-sizing: border-box; }
      `}</style>

      <div style={{ maxWidth: 760, margin: "0 auto" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontSize: 12, color: "#3B82F6", fontWeight: 600, letterSpacing: 3, marginBottom: 12 }}>
            INTELLIGENT TICKET RESOLUTION
          </div>
          <h1
            style={{
              fontSize: 36,
              fontWeight: 700,
              color: "#F8FAFC",
              margin: 0,
              lineHeight: 1.2,
            }}
          >
            IT Support AI
          </h1>
          <p style={{ color: "#475569", marginTop: 10, fontSize: 14 }}>
            Describe your issue — get a grounded resolution in seconds
          </p>
        </div>

        {/* Tabs */}
        <div
          style={{
            display: "flex",
            gap: 4,
            background: "#0F172A",
            borderRadius: 10,
            padding: 4,
            marginBottom: 24,
            border: "1px solid #1E293B",
          }}
        >
          <button style={tabStyle("query")} onClick={() => setActiveTab("query")}>
            🔍 Resolve Ticket
          </button>
          <button style={tabStyle("summarize")} onClick={() => setActiveTab("summarize")}>
            📝 Summarize
          </button>
        </div>

        {/* Query Tab */}
        {activeTab === "query" && (
          <div>
            <div
              style={{
                background: "#0F172A",
                border: "1px solid #1E293B",
                borderRadius: 14,
                padding: 4,
                transition: "border-color 0.2s",
              }}
            >
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleQuery())}
                placeholder="Describe the issue... e.g. Cannot connect to VPN after password reset"
                style={{
                  width: "100%",
                  background: "transparent",
                  border: "none",
                  color: "#E2E8F0",
                  fontSize: 15,
                  padding: "16px",
                  resize: "none",
                  minHeight: 100,
                  fontFamily: "Inter, sans-serif",
                  lineHeight: 1.6,
                }}
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 12px",
                  borderTop: "1px solid #1E293B",
                }}
              >
                <span style={{ color: "#334155", fontSize: 12 }}>Press Enter to search</span>
                <button
                  onClick={handleQuery}
                  disabled={loading || !query.trim()}
                  style={{
                    background: loading || !query.trim() ? "#1E293B" : "#3B82F6",
                    color: loading || !query.trim() ? "#475569" : "#fff",
                    border: "none",
                    borderRadius: 8,
                    padding: "8px 20px",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: loading || !query.trim() ? "not-allowed" : "pointer",
                    fontFamily: "Inter, sans-serif",
                    transition: "all 0.2s",
                  }}
                >
                  {loading ? "Resolving..." : "Get Resolution →"}
                </button>
              </div>
            </div>

            {/* Loading spinner */}
            {loading && (
              <div style={{ textAlign: "center", padding: 40, color: "#475569" }}>
                <div
                  style={{
                    width: 32,
                    height: 32,
                    border: "3px solid #1E293B",
                    borderTop: "3px solid #3B82F6",
                    borderRadius: "50%",
                    animation: "spin 0.8s linear infinite",
                    margin: "0 auto 12px",
                  }}
                />
                <div style={{ fontSize: 13 }}>Retrieving similar tickets and generating resolution...</div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div
                style={{
                  background: "#1E0A0A",
                  border: "1px solid #7F1D1D",
                  borderRadius: 10,
                  padding: 16,
                  marginTop: 16,
                  color: "#FCA5A5",
                  fontSize: 13,
                }}
              >
                ⚠️ {error}. Make sure the backend server is running at localhost:8000.
              </div>
            )}

            {/* Result */}
            {result && <ResultCard data={result} />}
          </div>
        )}

        {/* Summarize Tab */}
        {activeTab === "summarize" && (
          <div>
            <div
              style={{
                background: "#0F172A",
                border: "1px solid #1E293B",
                borderRadius: 14,
                padding: 4,
              }}
            >
              <textarea
                value={summarizeText}
                onChange={(e) => setSummarizeText(e.target.value)}
                placeholder="Paste a long incident report or ticket description here..."
                style={{
                  width: "100%",
                  background: "transparent",
                  border: "none",
                  color: "#E2E8F0",
                  fontSize: 15,
                  padding: "16px",
                  resize: "none",
                  minHeight: 160,
                  fontFamily: "Inter, sans-serif",
                  lineHeight: 1.6,
                }}
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  padding: "8px 12px",
                  borderTop: "1px solid #1E293B",
                }}
              >
                <button
                  onClick={handleSummarize}
                  disabled={loading || !summarizeText.trim()}
                  style={{
                    background: loading || !summarizeText.trim() ? "#1E293B" : "#3B82F6",
                    color: loading || !summarizeText.trim() ? "#475569" : "#fff",
                    border: "none",
                    borderRadius: 8,
                    padding: "8px 20px",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: loading || !summarizeText.trim() ? "not-allowed" : "pointer",
                    fontFamily: "Inter, sans-serif",
                  }}
                >
                  {loading ? "Summarizing..." : "Summarize →"}
                </button>
              </div>
            </div>

            {summary && (
              <div
                style={{
                  background: "#0F172A",
                  border: "1px solid #1E293B",
                  borderRadius: 14,
                  padding: 24,
                  marginTop: 16,
                  animation: "fadeIn 0.4s ease",
                }}
              >
                <div style={{ color: "#475569", fontSize: 11, marginBottom: 10 }}>SUMMARY</div>
                <div style={{ color: "#E2E8F0", fontSize: 14, lineHeight: 1.75 }}>{summary}</div>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div style={{ textAlign: "center", marginTop: 48, color: "#1E293B", fontSize: 12 }}>
          Intelligent Ticket Resolution System • RAG + DistilBERT + Llama 3.3
        </div>
      </div>
    </div>
  );
}
