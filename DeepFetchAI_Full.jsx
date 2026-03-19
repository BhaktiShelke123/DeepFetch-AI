import { useState, useRef, useEffect } from "react";

const T = {
  teal50: "#E1F5EE", teal100: "#9FE1CB", teal400: "#1D9E75", teal600: "#0F6E56", teal800: "#085041", teal900: "#04342C",
  gray50: "#F1EFE8", gray100: "#D3D1C7", gray400: "#888780", gray600: "#5F5E5A", gray800: "#444441",
  amber400: "#BA7517", amber50: "#FAEEDA",
  blue50: "#E6F1FB", blue400: "#378ADD", blue800: "#0C447C",
  red50: "#FCEBEB", red400: "#E24B4A",
  green50: "#EAF3DE", green400: "#639922", green800: "#27500A",
};

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'DM Sans', sans-serif; }
  ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--color-border-secondary); border-radius: 2px; }
  input[type=range] { accent-color: ${T.teal400}; cursor: pointer; }
  textarea:focus, input:focus { outline: none; }
  @keyframes fadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
  @keyframes pulse { 0%,100%{opacity:0.4;transform:scale(0.75)} 50%{opacity:1;transform:scale(1)} }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes shimmer { 0%{background-position:-400px 0} 100%{background-position:400px 0} }
  .nav-item { transition: all 0.15s; }
  .nav-item:hover { background: var(--color-background-secondary) !important; }
  .nav-item.active { background: ${T.teal50} !important; color: ${T.teal800} !important; }
  .result-card { transition: border-color 0.15s, transform 0.15s; }
  .result-card:hover { border-color: ${T.teal400} !important; transform: translateY(-1px); }
  .doc-row { transition: background 0.1s; }
  .doc-row:hover { background: var(--color-background-secondary) !important; }
  .btn-primary { background: ${T.teal400}; color: white; border: none; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: opacity 0.15s; }
  .btn-primary:hover { opacity: 0.88; }
  .btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
  .chip { background: var(--color-background-secondary); border: 0.5px solid var(--color-border-secondary); color: var(--color-text-secondary); cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.12s; }
  .chip:hover { border-color: ${T.teal400}; color: ${T.teal800}; background: ${T.teal50}; }
  .chip.active { background: ${T.teal50}; border-color: ${T.teal400}; color: ${T.teal800}; }
  .upload-zone { transition: all 0.15s; cursor: pointer; }
  .upload-zone.drag { border-color: ${T.teal400} !important; background: ${T.teal50} !important; }
  .stat-card { transition: transform 0.15s; }
  .stat-card:hover { transform: translateY(-2px); }
  .landing-cta { background: ${T.teal400}; color: white; border: none; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.15s; }
  .landing-cta:hover { background: ${T.teal600}; }
`;

const DEMO_DOCS = [
  { id: 1, name: "speech.txt", size: "2.1 KB", chunks: 32, status: "indexed", added: "2 min ago" },
  { id: 2, name: "ai_report_2024.pdf", size: "1.4 MB", chunks: 87, status: "indexed", added: "10 min ago" },
  { id: 3, name: "langchain_docs.pdf", size: "840 KB", chunks: 204, status: "indexed", added: "1 hr ago" },
];

const DEMO_RESULTS = {
  default: [
    { text: "Artificial intelligence is a transformative, general-purpose technology reshaping industries by enabling machines to learn, analyze data, and automate complex tasks.", score: 0.91, source: "speech.txt", chunk: 1 },
    { text: "The future depends on ensuring AI's productivity gains are shared widely and that the technology remains a tool under human guidance.", score: 0.78, source: "speech.txt", chunk: 24 },
    { text: "AI is not just a futuristic concept; it is a rapidly advancing tool transforming economics, finance, and daily life.", score: 0.69, source: "speech.txt", chunk: 7 },
    { text: "Energy Infrastructure: The physical, real-world energy infrastructure must be built to support AI advancement.", score: 0.61, source: "speech.txt", chunk: 27 },
  ],
  health: [
    { text: "Healthcare and Innovation: AI is revolutionizing medicine with faster, more accurate diagnostics.", score: 0.97, source: "speech.txt", chunk: 14 },
    { text: "Efficiency and Productivity: AI streamlines processes and improves supply chains, reducing costs and increasing productivity.", score: 0.82, source: "speech.txt", chunk: 12 },
    { text: "The goal is to foster innovation while managing risks through thoughtful, careful regulation.", score: 0.74, source: "speech.txt", chunk: 23 },
    { text: "The Challenges and Risks", score: 0.62, source: "speech.txt", chunk: 16 },
  ],
  risk: [
    { text: "Safety and Ethics: Short-term risks include surveillance, cyberattacks, and misinformation, while long-term risks involve potential loss of control over superior digital beings.", score: 0.95, source: "speech.txt", chunk: 20 },
    { text: "Economic Impact: Concerns exist regarding job displacement and the widening of inequality.", score: 0.89, source: "speech.txt", chunk: 17 },
    { text: "Resource Demands: AI requires significant energy and infrastructure, putting pressure on existing resources.", score: 0.81, source: "speech.txt", chunk: 18 },
    { text: "Balancing Regulation: Excessive regulation could stifle innovation, while too little could pose dangers.", score: 0.73, source: "speech.txt", chunk: 29 },
  ],
  auto: [
    { text: "Automation: AI allows for automation of customer support, data analysis, and complex decision-making.", score: 0.96, source: "speech.txt", chunk: 15 },
    { text: "Artificial intelligence is a transformative, general-purpose technology reshaping industries by enabling machines to learn, analyze data, and automate complex tasks.", score: 0.84, source: "speech.txt", chunk: 1 },
    { text: "Human-Centric Design: AI should enhance human capabilities rather than simply replacing them.", score: 0.77, source: "speech.txt", chunk: 31 },
    { text: "Efficiency and Productivity: AI streamlines processes and improves supply chains, reducing costs and increasing productivity.", score: 0.71, source: "speech.txt", chunk: 12 },
  ],
};

function getResults(q) {
  const s = q.toLowerCase();
  if (s.includes("health") || s.includes("med")) return DEMO_RESULTS.health;
  if (s.includes("risk") || s.includes("safe") || s.includes("ethic")) return DEMO_RESULTS.risk;
  if (s.includes("auto") || s.includes("job") || s.includes("replac")) return DEMO_RESULTS.auto;
  return DEMO_RESULTS.default;
}

const HISTORY = [
  { q: "What are the benefits of AI in healthcare?", k: 4, ts: "2 min ago" },
  { q: "Risks of automation on workforce", k: 3, ts: "15 min ago" },
  { q: "AI regulation and ethics overview", k: 4, ts: "1 hr ago" },
];

// ─── Icons ───────────────────────────────────────────────────────────────────
const Icon = ({ d, size = 16, color = "currentColor", stroke = 1.6 }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
    <path d={d} stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

// ─── Nav ─────────────────────────────────────────────────────────────────────
const NAV = [
  { id: "landing", label: "Home", icon: "M2 6l6-4 6 4v8H10V9H6v5H2z" },
  { id: "upload",  label: "Documents", icon: "M9 2H4a1 1 0 00-1 1v10a1 1 0 001 1h8a1 1 0 001-1V6M9 2l4 4M9 2v4h4" },
  { id: "search",  label: "Search", icon: "M7 12A5 5 0 107 2a5 5 0 000 10zM14 14l-3-3" },
  { id: "dashboard", label: "Dashboard", icon: "M2 10h4v4H2zM6 6h4v8H6zM10 2h4v12h-4z" },
];

function Sidebar({ active, setActive }) {
  return (
    <div style={{
      width: 200, minHeight: "100vh", background: "var(--color-background-primary)",
      borderRight: "0.5px solid var(--color-border-tertiary)",
      display: "flex", flexDirection: "column", padding: "0 10px",
      position: "sticky", top: 0, flexShrink: 0,
    }}>
      <div style={{ padding: "20px 10px 24px", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 8, background: T.teal400,
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
          }}>
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
              <path d="M2.5 7.5h10M7.5 2.5l5 5-5 5" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <div style={{ fontFamily: "Syne, sans-serif", fontSize: 14, fontWeight: 600, letterSpacing: "-0.3px", color: "var(--color-text-primary)" }}>DeepFetch</div>
            <div style={{ fontSize: 10, color: T.teal600, fontWeight: 500 }}>AI · RAG Pipeline</div>
          </div>
        </div>
      </div>

      <nav style={{ flex: 1, paddingTop: 12, display: "flex", flexDirection: "column", gap: 2 }}>
        {NAV.map(n => (
          <button key={n.id} className={`nav-item ${active === n.id ? "active" : ""}`}
            onClick={() => setActive(n.id)}
            style={{
              display: "flex", alignItems: "center", gap: 9, padding: "8px 10px",
              borderRadius: 8, border: "none", cursor: "pointer", width: "100%",
              background: "transparent", textAlign: "left", fontSize: 13,
              fontFamily: "DM Sans, sans-serif", fontWeight: 400,
              color: active === n.id ? T.teal800 : "var(--color-text-secondary)",
            }}>
            <Icon d={n.icon} size={14} color={active === n.id ? T.teal400 : "var(--color-text-secondary)"} />
            {n.label}
          </button>
        ))}
      </nav>

      <div style={{ padding: "12px 10px", borderTop: "0.5px solid var(--color-border-tertiary)" }}>
        <div style={{
          fontSize: 11, color: "var(--color-text-secondary)", display: "flex",
          alignItems: "center", gap: 6,
        }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: T.teal400, flexShrink: 0 }} />
          ChromaDB connected
        </div>
      </div>
    </div>
  );
}

// ─── Landing ─────────────────────────────────────────────────────────────────
function Landing({ setPage }) {
  const features = [
    { icon: "M4 6h8M4 9h5M9 2H4a1 1 0 00-1 1v10a1 1 0 001 1h8a1 1 0 001-1V6M9 2l4 4M9 2v4h4", title: "Smart ingestion", desc: "Upload any document and it's chunked, embedded, and stored in seconds." },
    { icon: "M7 12A5 5 0 107 2a5 5 0 000 10zM14 14l-3-3", title: "Semantic search", desc: "Query in natural language. Get the most relevant chunks back instantly." },
    { icon: "M2 10h4v4H2zM6 6h4v8H6zM10 2h4v12h-4z", title: "Live analytics", desc: "Monitor your vector DB — chunk counts, query latency, similarity scores." },
  ];
  return (
    <div style={{ padding: "48px 40px", maxWidth: 760, animation: "fadeUp 0.4s ease" }}>
      <div style={{
        display: "inline-flex", alignItems: "center", gap: 6, padding: "4px 12px",
        background: T.teal50, borderRadius: 20, marginBottom: 24,
        border: `0.5px solid ${T.teal100}`,
      }}>
        <div style={{ width: 6, height: 6, borderRadius: "50%", background: T.teal400 }} />
        <span style={{ fontSize: 12, fontWeight: 500, color: T.teal800 }}>LangChain · OpenAI · ChromaDB</span>
      </div>

      <h1 style={{
        fontFamily: "Syne, sans-serif", fontSize: 44, fontWeight: 700,
        color: "var(--color-text-primary)", lineHeight: 1.15, marginBottom: 16,
        letterSpacing: "-1px",
      }}>
        Retrieval-Augmented<br />
        <span style={{ color: T.teal400 }}>Generation</span> at scale
      </h1>

      <p style={{ fontSize: 16, color: "var(--color-text-secondary)", lineHeight: 1.7, marginBottom: 36, maxWidth: 520 }}>
        DeepFetch AI transforms unstructured text into a searchable, high-dimensional vector database.
        Upload documents, embed them with OpenAI, and retrieve the most relevant chunks instantly.
      </p>

      <div style={{ display: "flex", gap: 10, marginBottom: 56 }}>
        <button className="landing-cta" style={{ padding: "11px 22px", borderRadius: 10, fontSize: 14, fontWeight: 500 }}
          onClick={() => setPage("upload")}>
          Upload documents →
        </button>
        <button className="chip" style={{ padding: "11px 22px", borderRadius: 10, fontSize: 14 }}
          onClick={() => setPage("search")}>
          Try a search
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
        {features.map((f, i) => (
          <div key={i} className="stat-card" style={{
            background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)",
            borderRadius: 12, padding: "18px 16px",
          }}>
            <div style={{
              width: 34, height: 34, borderRadius: 8, background: T.teal50,
              display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12,
            }}>
              <Icon d={f.icon} size={15} color={T.teal400} />
            </div>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 5, color: "var(--color-text-primary)" }}>{f.title}</div>
            <div style={{ fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.55 }}>{f.desc}</div>
          </div>
        ))}
      </div>

      <div style={{
        marginTop: 32, display: "flex", gap: 32, padding: "20px 0",
        borderTop: "0.5px solid var(--color-border-tertiary)",
      }}>
        {[["323", "chunks indexed"], ["3", "documents"], ["1024", "embedding dims"], ["< 50ms", "avg latency"]].map(([v, l]) => (
          <div key={l}>
            <div style={{ fontFamily: "Syne, sans-serif", fontSize: 22, fontWeight: 700, color: "var(--color-text-primary)" }}>{v}</div>
            <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{l}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Upload ──────────────────────────────────────────────────────────────────
function Upload() {
  const [docs, setDocs] = useState(DEMO_DOCS);
  const [drag, setDrag] = useState(false);
  const [processing, setProcessing] = useState(null);
  const fileRef = useRef();

  const addFile = (file) => {
    const newDoc = { id: Date.now(), name: file.name, size: (file.size / 1024).toFixed(0) + " KB", chunks: 0, status: "processing", added: "just now" };
    setDocs(prev => [newDoc, ...prev]);
    setProcessing(newDoc.id);
    setTimeout(() => {
      setDocs(prev => prev.map(d => d.id === newDoc.id
        ? { ...d, chunks: Math.floor(Math.random() * 80) + 20, status: "indexed" }
        : d
      ));
      setProcessing(null);
    }, 2200);
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDrag(false);
    Array.from(e.dataTransfer.files).forEach(addFile);
  };

  const handleFile = (e) => Array.from(e.target.files).forEach(addFile);
  const removeDoc = (id) => setDocs(prev => prev.filter(d => d.id !== id));

  return (
    <div style={{ padding: "32px 40px", maxWidth: 820, animation: "fadeUp 0.3s ease" }}>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontFamily: "Syne, sans-serif", fontSize: 24, fontWeight: 600, color: "var(--color-text-primary)", marginBottom: 4 }}>Documents</h2>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>Upload files to chunk, embed, and index into ChromaDB</p>
      </div>

      <div
        className={`upload-zone ${drag ? "drag" : ""}`}
        style={{
          border: `1.5px dashed ${drag ? T.teal400 : "var(--color-border-secondary)"}`,
          borderRadius: 14, padding: "36px 24px", textAlign: "center",
          background: drag ? T.teal50 : "var(--color-background-secondary)",
          marginBottom: 24,
        }}
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current.click()}
      >
        <input ref={fileRef} type="file" style={{ display: "none" }} multiple accept=".txt,.pdf,.docx" onChange={handleFile} />
        <div style={{ width: 44, height: 44, borderRadius: 12, background: T.teal50, border: `1px solid ${T.teal100}`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 14V6M10 6L7 9M10 6l3 3" stroke={T.teal400} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M3 15v1.5A1.5 1.5 0 004.5 18h11a1.5 1.5 0 001.5-1.5V15" stroke={T.teal400} strokeWidth="1.6" strokeLinecap="round"/>
          </svg>
        </div>
        <div style={{ fontSize: 14, fontWeight: 500, color: "var(--color-text-primary)", marginBottom: 4 }}>Drop files here or click to browse</div>
        <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>Supports TXT · PDF · DOCX · MD</div>
      </div>

      <div style={{
        background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)",
        borderRadius: 12, overflow: "hidden",
      }}>
        <div style={{ padding: "12px 18px", borderBottom: "0.5px solid var(--color-border-tertiary)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.5px" }}>Indexed documents</span>
          <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{docs.length} files · {docs.reduce((s, d) => s + d.chunks, 0)} chunks</span>
        </div>

        {docs.map((doc, i) => (
          <div key={doc.id} className="doc-row" style={{
            display: "flex", alignItems: "center", gap: 12, padding: "12px 18px",
            borderBottom: i < docs.length - 1 ? "0.5px solid var(--color-border-tertiary)" : "none",
            animation: "fadeUp 0.3s ease",
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: 8, background: T.teal50,
              display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
            }}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect x="2.5" y="1.5" width="9" height="13" rx="1.5" stroke={T.teal400} strokeWidth="1.2"/>
                <path d="M5 5.5h6M5 8h6M5 10.5h3.5" stroke={T.teal400} strokeWidth="1" strokeLinecap="round"/>
              </svg>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)", marginBottom: 2 }}>{doc.name}</div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>{doc.size} · Added {doc.added}</div>
            </div>
            <div style={{ textAlign: "right", marginRight: 8 }}>
              {doc.status === "processing" ? (
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ width: 12, height: 12, border: `2px solid ${T.teal400}`, borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                  <span style={{ fontSize: 11, color: T.teal600 }}>Processing…</span>
                </div>
              ) : (
                <>
                  <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)" }}>{doc.chunks}</div>
                  <div style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>chunks</div>
                </>
              )}
            </div>
            <div style={{
              padding: "3px 8px", borderRadius: 20, fontSize: 11, fontWeight: 500,
              background: doc.status === "indexed" ? T.green50 : T.amber50,
              color: doc.status === "indexed" ? T.green800 : T.amber400,
            }}>
              {doc.status === "indexed" ? "indexed" : "processing"}
            </div>
            <button onClick={() => removeDoc(doc.id)} style={{
              width: 26, height: 26, borderRadius: 6, border: "0.5px solid var(--color-border-tertiary)",
              background: "transparent", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
              color: "var(--color-text-secondary)", flexShrink: 0, transition: "all 0.1s",
            }}>
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M2 2l6 6M8 2L2 8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {[["Embedding model", "text-embedding-3-large"], ["Chunk size", "100 tokens"], ["Overlap", "5 tokens"], ["Vector store", "ChromaDB (local)"]].map(([k, v]) => (
          <div key={k} style={{
            background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)",
            borderRadius: 10, padding: "12px 14px", display: "flex", justifyContent: "space-between",
          }}>
            <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{k}</span>
            <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)" }}>{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Search ──────────────────────────────────────────────────────────────────
function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [visible, setVisible] = useState(false);
  const [topK, setTopK] = useState(4);
  const [dims, setDims] = useState("1024");
  const [history, setHistory] = useState(HISTORY);
  const taRef = useRef();

  const run = (q = query) => {
    if (!q.trim()) return;
    setLoading(true); setSearched(false); setVisible(false);
    setTimeout(() => {
      setResults(getResults(q).slice(0, topK));
      setLoading(false); setSearched(true);
      setTimeout(() => setVisible(true), 40);
      setHistory(prev => [{ q, k: topK, ts: "just now" }, ...prev.slice(0, 4)]);
    }, 800);
  };

  const suggestions = ["Healthcare and AI diagnostics", "Job displacement risks", "AI regulation policy", "Automation in supply chains"];

  return (
    <div style={{ display: "flex", flex: 1, gap: 0, animation: "fadeUp 0.3s ease" }}>
      <div style={{ flex: 1, padding: "32px 32px 32px 40px", display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <h2 style={{ fontFamily: "Syne, sans-serif", fontSize: 24, fontWeight: 600, color: "var(--color-text-primary)", marginBottom: 4 }}>Semantic search</h2>
          <p style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>Retrieve relevant document chunks using vector similarity</p>
        </div>

        <div style={{
          background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-secondary)",
          borderRadius: 12, padding: "10px 12px", display: "flex", gap: 8, alignItems: "flex-end",
        }}>
          <textarea ref={taRef} rows={1} value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); run(); } }}
            placeholder="Ask anything about your documents…"
            style={{
              flex: 1, border: "none", background: "transparent", resize: "none",
              fontSize: 14, fontFamily: "DM Sans, sans-serif", color: "var(--color-text-primary)",
              lineHeight: 1.5, padding: "4px 0",
            }}
          />
          <button className="btn-primary" disabled={!query.trim() || loading}
            onClick={() => run()}
            style={{ width: 36, height: 36, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            {loading
              ? <div style={{ width: 14, height: 14, border: "2px solid rgba(255,255,255,0.4)", borderTopColor: "white", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
              : <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 12V2M7 2L3 6M7 2l4 4" stroke="white" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>
            }
          </button>
        </div>

        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {suggestions.map(s => (
            <button key={s} className="chip" style={{ fontSize: 12, padding: "4px 10px", borderRadius: 20 }} onClick={() => { setQuery(s); run(s); }}>{s}</button>
          ))}
        </div>

        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10 }}>
          {!loading && !searched && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "60px 0", gap: 10, color: "var(--color-text-secondary)", textAlign: "center" }}>
              <svg width="44" height="44" viewBox="0 0 44 44" fill="none"><circle cx="22" cy="22" r="21" stroke="var(--color-border-secondary)"/><circle cx="19" cy="19" r="8" stroke="var(--color-border-secondary)" strokeWidth="1.5"/><path d="M25 25l5.5 5.5" stroke="var(--color-border-secondary)" strokeWidth="1.5" strokeLinecap="round"/></svg>
              <div style={{ fontSize: 14, fontWeight: 500 }}>Ready to search</div>
              <div style={{ fontSize: 12 }}>Query your document corpus with natural language</div>
            </div>
          )}
          {loading && (
            <div style={{ display: "flex", gap: 6, justifyContent: "center", padding: 32 }}>
              {[0,1,2].map(i => <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: T.teal400, animation: `pulse 1s ease ${i * 0.18}s infinite` }} />)}
            </div>
          )}
          {!loading && searched && results.map((r, i) => (
            <div key={i} className="result-card" style={{
              background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)",
              borderRadius: 12, padding: "14px 16px",
              opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(8px)",
              transition: `opacity 0.3s ease ${i * 0.07}s, transform 0.3s ease ${i * 0.07}s`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ width: 18, height: 18, borderRadius: "50%", background: T.teal50, border: `1px solid ${T.teal100}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span style={{ fontSize: 9, fontWeight: 500, color: T.teal800 }}>{i + 1}</span>
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 500, color: T.teal600 }}>{(r.score * 100).toFixed(0)}% match</span>
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>{r.source} · chunk {r.chunk}</span>
                </div>
              </div>
              <p style={{ fontSize: 13.5, color: "var(--color-text-primary)", lineHeight: 1.65, marginBottom: 10 }}>{r.text}</p>
              <div style={{ height: 3, borderRadius: 2, background: "var(--color-background-secondary)", overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${r.score * 100}%`, background: T.teal400, borderRadius: 2, transition: "width 0.6s ease" }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ width: 220, borderLeft: "0.5px solid var(--color-border-tertiary)", padding: "32px 16px", flexShrink: 0 }}>
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>Settings</div>
          <div style={{ marginBottom: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>Top K</span>
              <span style={{ fontSize: 12, fontWeight: 500 }}>{topK}</span>
            </div>
            <input type="range" min={1} max={8} step={1} value={topK} onChange={e => setTopK(+e.target.value)} style={{ width: "100%" }} />
          </div>
          <div>
            <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 6 }}>Dimensions</div>
            <div style={{ display: "flex", gap: 4 }}>
              {["1024", "3072"].map(d => (
                <button key={d} className={`chip ${dims === d ? "active" : ""}`}
                  onClick={() => setDims(d)}
                  style={{ flex: 1, fontSize: 11, padding: "4px 0", borderRadius: 6, textAlign: "center" }}>
                  {d}d
                </button>
              ))}
            </div>
          </div>
        </div>

        <div>
          <div style={{ fontSize: 11, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 10 }}>Recent queries</div>
          {history.map((h, i) => (
            <div key={i} style={{ marginBottom: 8, cursor: "pointer" }} onClick={() => { setQuery(h.q); run(h.q); }}>
              <div style={{ fontSize: 11, color: "var(--color-text-primary)", lineHeight: 1.4, marginBottom: 2, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{h.q}</div>
              <div style={{ fontSize: 10, color: "var(--color-text-secondary)" }}>k={h.k} · {h.ts}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Dashboard ───────────────────────────────────────────────────────────────
function Dashboard() {
  const statCards = [
    { label: "Total documents", value: "3", sub: "+1 this session", color: T.teal400 },
    { label: "Total chunks", value: "323", sub: "avg 107 per doc", color: T.blue400 },
    { label: "Embedding dims", value: "1024", sub: "text-embedding-3-large", color: T.amber400 },
    { label: "Avg query latency", value: "48ms", sub: "similarity search", color: T.green400 },
  ];

  const docBreakdown = [
    { name: "speech.txt", chunks: 32, pct: 10 },
    { name: "ai_report_2024.pdf", chunks: 87, pct: 27 },
    { name: "langchain_docs.pdf", chunks: 204, pct: 63 },
  ];

  const latencyHistory = [38, 52, 44, 61, 48, 55, 42, 50, 46, 48];
  const maxL = Math.max(...latencyHistory);

  const recentQueries = [
    { q: "What are the benefits of AI in healthcare?", results: 4, latency: "44ms", score: "0.97" },
    { q: "Risks of automation on workforce", results: 3, latency: "51ms", score: "0.95" },
    { q: "AI regulation and ethics overview", results: 4, latency: "48ms", score: "0.88" },
  ];

  return (
    <div style={{ padding: "32px 40px", animation: "fadeUp 0.3s ease" }}>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontFamily: "Syne, sans-serif", fontSize: 24, fontWeight: 600, color: "var(--color-text-primary)", marginBottom: 4 }}>Dashboard</h2>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>Vector DB health, query analytics, and pipeline overview</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
        {statCards.map((s, i) => (
          <div key={i} className="stat-card" style={{
            background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)",
            borderRadius: 12, padding: "16px 18px",
          }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: s.color, marginBottom: 12 }} />
            <div style={{ fontSize: 26, fontWeight: 600, fontFamily: "Syne, sans-serif", color: "var(--color-text-primary)", letterSpacing: "-0.5px" }}>{s.value}</div>
            <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)", marginTop: 2 }}>{s.label}</div>
            <div style={{ fontSize: 11, color: "var(--color-text-secondary)", marginTop: 2 }}>{s.sub}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, padding: "18px 20px" }}>
          <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-secondary)", marginBottom: 16, textTransform: "uppercase", letterSpacing: "0.5px" }}>Chunks by document</div>
          {docBreakdown.map((d, i) => (
            <div key={i} style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                <span style={{ fontSize: 12, color: "var(--color-text-primary)", fontWeight: 500 }}>{d.name}</span>
                <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{d.chunks} chunks</span>
              </div>
              <div style={{ height: 5, borderRadius: 3, background: "var(--color-background-secondary)", overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${d.pct}%`, background: [T.teal400, T.blue400, T.amber400][i], borderRadius: 3, transition: "width 0.8s ease" }} />
              </div>
            </div>
          ))}
        </div>

        <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, padding: "18px 20px" }}>
          <div style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-secondary)", marginBottom: 16, textTransform: "uppercase", letterSpacing: "0.5px" }}>Query latency (last 10)</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 5, height: 80 }}>
            {latencyHistory.map((v, i) => (
              <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
                <div style={{
                  width: "100%", background: T.teal400, borderRadius: 3,
                  height: `${(v / maxL) * 72}px`, opacity: 0.7 + (i / latencyHistory.length) * 0.3,
                  transition: "height 0.6s ease",
                }} />
              </div>
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
            <span style={{ fontSize: 10, color: "var(--color-text-secondary)" }}>oldest</span>
            <span style={{ fontSize: 10, color: "var(--color-text-secondary)" }}>latest</span>
          </div>
        </div>
      </div>

      <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ padding: "12px 18px", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
          <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.5px" }}>Recent queries</span>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "var(--color-background-secondary)" }}>
              {["Query", "Results", "Latency", "Top score"].map(h => (
                <th key={h} style={{ padding: "8px 18px", textAlign: "left", fontSize: 11, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.4px" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {recentQueries.map((r, i) => (
              <tr key={i} style={{ borderTop: "0.5px solid var(--color-border-tertiary)" }}>
                <td style={{ padding: "11px 18px", fontSize: 13, color: "var(--color-text-primary)", maxWidth: 320 }}>{r.q}</td>
                <td style={{ padding: "11px 18px", fontSize: 13, color: "var(--color-text-secondary)" }}>{r.results}</td>
                <td style={{ padding: "11px 18px", fontSize: 13, color: "var(--color-text-secondary)", fontVariantNumeric: "tabular-nums" }}>{r.latency}</td>
                <td style={{ padding: "11px 18px" }}>
                  <span style={{ fontSize: 11, fontWeight: 500, padding: "2px 8px", borderRadius: 20, background: T.teal50, color: T.teal800 }}>{r.score}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState("landing");

  return (
    <>
      <style>{css}</style>
      <div style={{ display: "flex", minHeight: "100vh", background: "var(--color-background-tertiary)" }}>
        <Sidebar active={page} setActive={setPage} />
        <div style={{ flex: 1, overflow: "auto" }}>
          {page === "landing"   && <Landing setPage={setPage} />}
          {page === "upload"    && <Upload />}
          {page === "search"    && <Search />}
          {page === "dashboard" && <Dashboard />}
        </div>
      </div>
    </>
  );
}
