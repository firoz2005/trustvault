import React, { useEffect, useState } from "react";
import { api, getToken, setTokens, logout, downloadDocument } from "./api";

function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  function fillDemoAccount(username, password) {
  setMode("login");
  setUsername(username);
  setPassword(password);
  setError("");
}
  async function submit(e) {
    e.preventDefault(); setError("");
    try {
      if (mode === "register") {
        await api("/auth/register/", { method: "POST", body: JSON.stringify({ username, email, password }) });
      }
      const tokens = await api("/auth/token/", { method: "POST", body: JSON.stringify({ username, password }) });
      setTokens(tokens); onLogin();
    } catch (err) { setError(err.message); }
  }
  return <main className="auth-wrap"><section className="auth-card">
    <div className="brand-mark">TV</div><p className="eyebrow">PRIVATE DOCUMENT WORKSPACE</p>
    <h1>{mode === "login" ? "Welcome back." : "Create your account."}</h1>
    <p className="muted">Your files stay private. Access is checked on the server.</p>
    <form onSubmit={submit} className="stack">
      <label>Username<input required value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" /></label>
      {mode === "register" && <label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} /></label>}
      <label>Password<input required minLength={mode === "register" ? 10 : 1} type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>
      {error && <div className="error">{error}</div>}
      <button className="primary" type="submit">{mode === "login" ? "Sign in" : "Create account"}</button>
    </form>
    <button className="link-button" onClick={()=>{setMode(mode==="login"?"register":"login");setError("");}}>
      {mode === "login" ? "New to TrustVault? Create an account" : "Already registered? Sign in"}
    </button>
  
</section>


<section className="demo-accounts">
  <div className="demo-heading">
    <div>
      <p className="eyebrow">QUICK ACCESS</p>
      <h2>Demo accounts</h2>
      <p className="muted">Choose an account to explore TrustVault.</p>
    </div>
    <span className="demo-count">5 accounts</span>
  </div>

  <div className="demo-list">
    {[
      ["Administrator", "demo_admin", "TVAdmin@2026Demo!", "admin"],
      ["Document owner", "demo_owner", "TVOwner@2026Demo!", "owner"],
      ["Viewer 1", "trail1", "TrailOne@2026Demo!", "viewer"],
      ["Viewer 2", "trail2", "TrailTwo@2026Demo!", "viewer"],
      ["Viewer 3", "trail3", "TrailThree@2026Demo!", "viewer"],
    ].map(([role, username, password, type]) => (
      <div
  className="demo-account"
  key={username}
  role="button"
  tabIndex={0}
  onClick={() => fillDemoAccount(username, password)}
  onKeyDown={(e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fillDemoAccount(username, password);
    }
  }}
  style={{ cursor: "pointer" }}
>
        <div className="demo-account-info">
          <span className={`demo-role ${type}`}>{role}</span>
          <strong>{username}</strong>
          <span className="demo-password">{password}</span>
        </div>
      </div>
    ))}
  </div>

  <p className="demo-note">
    <span>ⓘ</span> These credentials are for the college demonstration only.
  </p>
</section>

</main>;

}

function Landing({ onLoginClick }) {
  const features = [
    {
      icon: "🔐",
      title: "Secure document access",
      description:
        "Your documents stay private. Only authorized users can access them."
    },
    {
      icon: "🛡️",
      title: "You control sharing",
      description:
        "Grant read or edit permissions and revoke access when needed."
    },
    {
      icon: "📋",
      title: "Real audit trail",
      description:
        "Track document activity, permission changes, and recorded actions."
    },
    {
      icon: "📁",
      title: "Simple document management",
      description:
        "Upload, organize, search, download, and manage your documents."
    }
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f6f8fc",
        color: "#172033",
        fontFamily: "inherit"
      }}
    >
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "22px 7%",
          background: "#ffffff",
          borderBottom: "1px solid #e6eaf2"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span
            style={{
              background: "#243b80",
              color: "#ffffff",
              borderRadius: 12,
              padding: "11px 12px",
              fontWeight: 800
            }}
          >
            TV
          </span>
          <span style={{ fontSize: 22, fontWeight: 750 }}>
            TrustVault
          </span>
        </div>

        <button
          className="primary"
          onClick={onLoginClick}
          style={{ padding: "12px 25px", cursor: "pointer" }}
        >
          Login
        </button>
      </header>

      <main style={{ maxWidth: 1180, margin: "0 auto", padding: "75px 7% 55px" }}>
        <section style={{ textAlign: "center", padding: "25px 0 65px" }}>
          <p
            style={{
              color: "#3555a5",
              fontWeight: 750,
              letterSpacing: 2,
              fontSize: 13
            }}
          >
            PRIVATE DOCUMENT SHARING
          </p>

          <h1
            style={{
              fontSize: "clamp(38px, 6vw, 66px)",
              lineHeight: 1.12,
              letterSpacing: "-2px",
              maxWidth: 850,
              margin: "20px auto"
            }}
          >
            Your documents.
            <br />
            <span style={{ color: "#3555a5" }}>Your control.</span>
          </h1>

          <p
            style={{
              maxWidth: 680,
              margin: "0 auto 30px",
              color: "#647089",
              fontSize: 18,
              lineHeight: 1.8
            }}
          >
            Share documents confidently with permission-based access,
            controlled sharing, and an audit trail that records important
            activity.
          </p>

          <button
            className="primary"
            onClick={onLoginClick}
            style={{
              padding: "15px 30px",
              fontSize: 16,
              cursor: "pointer"
            }}
          >
            Get started →
          </button>

          <p style={{ color: "#7b8497", fontSize: 13, marginTop: 18 }}>
            PRIVATE BY DEFAULT · ACCESS CONTROLLED ON THE SERVER
          </p>
        </section>

        <section>
          <div style={{ textAlign: "center", marginBottom: 30 }}>
            <h2 style={{ fontSize: 30, marginBottom: 10 }}>
              Everything your documents need
            </h2>
            <p style={{ color: "#647089" }}>
              Security and control built into your document workflow.
            </p>
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 20 }}>
            {features.map((feature) => (
              <article
                key={feature.title}
                style={{
                  flex: "1 1 220px",
                  background: "#ffffff",
                  border: "1px solid #e5eaf3",
                  borderRadius: 16,
                  padding: 25,
                  boxShadow: "0 8px 25px rgba(25, 42, 80, 0.04)"
                }}
              >
                <div style={{ fontSize: 30, marginBottom: 16 }}>
                  {feature.icon}
                </div>
                <h3 style={{ fontSize: 18, marginBottom: 10 }}>
                  {feature.title}
                </h3>
                <p style={{ color: "#647089", lineHeight: 1.7, margin: 0 }}>
                  {feature.description}
                </p>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer
        style={{
          textAlign: "center",
          padding: 25,
          borderTop: "1px solid #e6eaf2",
          color: "#7b8497",
          fontSize: 12,
          letterSpacing: 1
        }}
      >
        TRUSTVAULT · PRIVATE BY DEFAULT · EVERY REQUEST AUTHORIZED
      </footer>
    </div>
  );
}

function App() {
  const [loggedIn, setLoggedIn] = useState(Boolean(getToken()));
  const [showLogin, setShowLogin] = useState(false);
  const [me, setMe] = useState(null);
  const [docs, setDocs] = useState([]);
  const [audit, setAudit] = useState([]);
  const [auditMode, setAuditMode] = useState("audit");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [filters, setFilters] = useState({name:"", owner:"", category:"", date_from:"", date_to:""});
  const [upload, setUpload] = useState({title:"", category:"", file:null});
  const [active, setActive] = useState(null);
  const [grants, setGrants] = useState([]);
  const [grantUser, setGrantUser] = useState("");
  const [grantLevel, setGrantLevel] = useState("read");
  const [tab, setTab] = useState("documents");

  async function load() {
    setError("");
    try {
      const user = await api("/me/");
      setMe(user);
      const params = new URLSearchParams(Object.entries(filters).filter(([,v])=>v));
      const [documents, events] = await Promise.all([
        api(`/documents/${params.size ? `?${params}` : ""}`),
        api("/audit/")
      ]);
      setDocs(documents); setAudit(events);
    } catch (err) { setError(err.message); if (String(err.message).includes("401")) { logout(); setLoggedIn(false); } }
  }
  useEffect(()=>{ if(loggedIn) load(); }, [loggedIn]);
  async function search(e) { e?.preventDefault(); await load(); }
  async function doUpload(e) {
    e.preventDefault(); setError(""); setNotice("");
    if (!upload.file) { setError("Choose a file first."); return; }
    const form = new FormData(); form.append("title", upload.title); form.append("category", upload.category); form.append("file", upload.file);
    try { await api("/documents/", {method:"POST", body:form}); setUpload({title:"",category:"",file:null}); e.target.reset(); setNotice("Document uploaded."); await load(); }
    catch(err) { setError(err.message); }
  }
  async function openShare(doc) {
    setActive(doc); setError(""); setNotice("");
    try { setGrants(await api(`/documents/${doc.id}/permissions/`)); }
    catch(err) { setGrants([]); setError(err.message); }
  }
  async function addGrant(e) {
    e.preventDefault();
    try {
      await api(`/documents/${active.id}/permissions/`, {method:"POST", body:JSON.stringify({username:grantUser,level:grantLevel})});
      setGrantUser(""); setNotice("Permission saved."); setGrants(await api(`/documents/${active.id}/permissions/`)); await load();
    } catch(err) { setError(err.message); }
  }
  async function revoke(grantId) {
    try { await api(`/documents/${active.id}/permissions/${grantId}/`, {method:"DELETE"}); setGrants(await api(`/documents/${active.id}/permissions/`)); setNotice("Access revoked."); await load(); }
    catch(err) { setError(err.message); }
  }
  async function editDoc(doc) {
    const title = window.prompt("New document title", doc.title);
    if (title === null) return;
    try { await api(`/documents/${doc.id}/`, {method:"PATCH", body:JSON.stringify({title})}); setNotice("Document updated."); await load(); }
    catch(err) { setError(err.message); }
  }
  async function deleteDoc(doc) {
    if (!window.confirm(`Permanently delete "${doc.title}"?`)) return;
    try { await api(`/documents/${doc.id}/`, {method:"DELETE"}); setNotice("Document deleted."); await load(); }
    catch(err) { setError(err.message); }
  }
  async function showAdminActivity() {
  setError("");
  try {
    setAudit(await api("/admin/activity/"));
    setAuditMode("admin");
    setTab("audit");
  } catch (err) {
    setError(err.message);
  }
}
  async function verifyAudit() {
    try { const result = await api("/admin/audit/verify/"); setNotice(result.valid ? `Audit chain valid (${result.checked} events checked).` : `Audit chain invalid. Event IDs: ${result.invalid_event_ids.join(", ")}`); }
    catch(err) { setError(err.message); }
  }
  if (!loggedIn) {
  return showLogin
    ? <Login onLogin={() => setLoggedIn(true)} />
    : <Landing onLoginClick={() => setShowLogin(true)} />;
}

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="logo"><span className="brand-mark small">TV</span><span>TrustVault</span></div>
      <div className="side-label">WORKSPACE</div>
      <button className={tab==="documents"?"nav active":"nav"} onClick={()=>setTab("documents")}>▤ <span>Documents</span></button>
      <button
  className={tab==="audit" && auditMode==="audit" ? "nav active" : "nav"}
  onClick={async () => {
    setTab("audit");
    setAuditMode("audit");
    setError("");
    try {
      setAudit(await api("/audit/"));
    } catch (err) {
      setError(err.message);
    }
  }}
>
  ◷ <span>Audit trail</span>
</button>
      {me?.role==="admin" && <button className="nav" onClick={showAdminActivity}>⌘ <span>Admin activity</span></button>}
      <div className="sidebar-bottom"><div className="avatar">{me?.username?.slice(0,1).toUpperCase() || "U"}</div><div className="user-meta"><strong>{me?.username}</strong><span>{me?.role || "viewer"}</span></div><button title="Sign out" className="logout" onClick={() => {
  logout();
  setLoggedIn(false);
  setMe(null);
  setShowLogin(false);
}}>↪</button></div>
    </aside>
    <main className="main">
      <header className="topbar"><div><p className="eyebrow">SECURE WORKSPACE / {tab.toUpperCase()}</p><h1>
  {tab === "documents"
    ? "Your documents"
    : auditMode === "admin"
      ? "Admin activities"
      : "Audit trail"}
</h1></div><div className="secure-pill"><span className="dot"></span> Server-side access control</div></header>
      {error && <div className="alert error">{error}<button onClick={()=>setError("")}>×</button></div>}
      {notice && <div className="alert success">{notice}<button onClick={()=>setNotice("")}>×</button></div>}
      {tab==="documents" ? <>
        
  {(me?.role === "admin" || me?.role === "owner") && (
  <section className="upload-panel">
    <div className="section-heading"><div><h2>Upload a document</h2><p>Private by default. Only you can access it until you share it.</p></div><span className="lock-icon">▣</span></div>
    <form className="upload-form" onSubmit={doUpload}>
      <label>Document title<input required maxLength="200" placeholder="e.g. Project proposal" value={upload.title} onChange={e=>setUpload({...upload,title:e.target.value})}/></label>
      <label>Category<input maxLength="80" placeholder="e.g. Finance" value={upload.category} onChange={e=>setUpload({...upload,category:e.target.value})}/></label>
      <label className="file-label">Choose file<input required type="file" accept=".pdf,.txt,.png,.jpg,.jpeg,.docx,.xlsx,.csv" onChange={e=>setUpload({...upload,file:e.target.files?.[0]||null})}/><span className="file-hint">{upload.file ? upload.file.name : "PDF, TXT, images, DOCX, XLSX, CSV · max 10 MB"}</span></label>
      <button className="primary" type="submit">＋ Upload document</button>
    </form>
      </section>
)}

        <section className="documents-panel">
          <div className="section-heading"><div><h2>Document library <span className="count">{docs.length}</span></h2><p>Search only returns documents you are allowed to access.</p></div><button
  className="ghost"
  onClick={auditMode === "admin" ? showAdminActivity : load}
>
  ↻ Refresh
</button></div>
          <form className="filters" onSubmit={search}>
            <input placeholder="Search by document name" value={filters.name} onChange={e=>setFilters({...filters,name:e.target.value})}/>
            <input placeholder="Owner username" value={filters.owner} onChange={e=>setFilters({...filters,owner:e.target.value})}/>
            <input placeholder="Category" value={filters.category} onChange={e=>setFilters({...filters,category:e.target.value})}/>
            <input aria-label="From date" type="date" value={filters.date_from} onChange={e=>setFilters({...filters,date_from:e.target.value})}/>
            <input aria-label="To date" type="date" value={filters.date_to} onChange={e=>setFilters({...filters,date_to:e.target.value})}/>
            <button className="primary" type="submit">Search</button>
          </form>
          <div className="table-wrap"><table><thead><tr><th>DOCUMENT</th><th>OWNER</th><th>CATEGORY</th><th>UPDATED</th><th>ACCESS</th><th>ACTIONS</th></tr></thead>
            <tbody>{docs.map(doc=><tr key={doc.id}><td><div className="doc-cell"><span className="file-icon">▤</span><div><strong>{doc.title}</strong><small>{doc.original_filename} · {formatBytes(doc.size_bytes)}</small></div></div></td><td>{doc.owner.username}</td><td><span className="category">{doc.category || "Uncategorized"}</span></td><td>{new Date(doc.updated_at).toLocaleDateString()}</td><td><span className={doc.can_edit?"access edit":"access"}>{doc.can_edit?"Can edit":"Read only"}</span></td><td><div className="actions"><button title="Download" onClick={()=>downloadDocument(doc.id,doc.original_filename).catch(e=>setError(e.message))}>↓</button>{doc.can_edit&&<button title="Edit title" onClick={()=>editDoc(doc)}>✎</button>}{doc.can_delete&&<button title="Manage sharing" onClick={()=>openShare(doc)}>♧</button>}{doc.can_delete&&<button title="Delete" onClick={()=>deleteDoc(doc)} className="danger-button">×</button>}</div></td></tr>)}
              {!docs.length&&<tr><td colSpan="6" className="empty">No documents found. Upload a document or adjust your search.</td></tr>}</tbody></table></div>
        </section>
        {active && <div className="modal-backdrop" onClick={()=>setActive(null)}><section className="modal" onClick={e=>e.stopPropagation()}><button className="modal-close" onClick={()=>setActive(null)}>×</button><p className="eyebrow">ACCESS CONTROL</p><h2>Share “{active.title}”</h2><p className="muted">Grant access to a registered username. Revocation blocks future server requests.</p>
          <form className="share-form" onSubmit={addGrant}><label>Username<input required value={grantUser} onChange={e=>setGrantUser(e.target.value)} placeholder="e.g. alice"/></label><label>Permission<select value={grantLevel} onChange={e=>setGrantLevel(e.target.value)}><option value="read">Read</option><option value="edit">Edit</option></select></label><button className="primary">Grant access</button></form>
          <h3>People with access</h3>{grants.length ? grants.map(g=><div className="grant-row" key={g.id}><div><strong>{g.user.username}</strong><span>{g.level} access</span></div><button className="revoke" onClick={()=>revoke(g.id)}>Revoke</button></div>) : <p className="empty">No one else has access.</p>}
        </section></div>}
      </> : <section className="documents-panel"><div className="section-heading"><div><h2>
  {auditMode === "admin" ? "All system activities" : "Recorded activity"}
  {" "}
  <span className="count">{audit.length}</span>
</h2>
<p>
  {auditMode === "admin"
    ? "Administrator view of recorded system activity, including actions across users."
    : "Activity related to documents you own or have been granted access to."}
</p></div><div className="button-row">{me?.role==="admin"&&<button className="ghost" onClick={verifyAudit}>Verify hash chain</button>}<button
  className="ghost"
  onClick={auditMode === "admin" ? showAdminActivity : async () => {
    try {
      setAudit(await api("/audit/"));
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }}
>
  ↻ Refresh
</button></div></div>
        <div className="table-wrap"><table><thead><tr><th>TIME</th><th>ACTOR</th><th>ACTION</th><th>DOCUMENT</th><th>RESULT</th><th>DETAILS</th></tr></thead><tbody>{audit.map(ev=><tr key={ev.id}><td>{new Date(ev.created_at).toLocaleString()}</td><td>{ev.actor_label}</td><td><span className="category">{ev.action}</span></td><td>{ev.document_title || "—"}</td><td><span className={`outcome ${ev.outcome}`}>{ev.outcome}</span></td><td className="details-cell">{JSON.stringify(ev.details)}</td></tr>)}{!audit.length&&<tr><td colSpan="6" className="empty">No audit events available.</td></tr>}</tbody></table></div>
      </section>}
      <footer>TRUSTVAULT <span>•</span> PRIVATE BY DEFAULT <span>•</span> EVERY REQUEST AUTHORIZED</footer>
    </main>
  </div>;
}
function formatBytes(bytes) { if(bytes < 1024) return `${bytes} B`; if(bytes < 1024*1024) return `${(bytes/1024).toFixed(1)} KB`; return `${(bytes/1024/1024).toFixed(1)} MB`; }
export default App;
