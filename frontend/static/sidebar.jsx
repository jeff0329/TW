/* global React */
const { useState } = React;

function Sidebar({ route, setRoute, user, onLogout }) {
  const nav = [
    { id: "trips", icon: "🗂", label: "我的行程" },
    { id: "plan",  icon: "✨", label: "AI 規劃" },
    { id: "saved", icon: "♡", label: "收藏清單" },
    { id: "settings", icon: "⚙", label: "設定" },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__brand-mark">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="10" r="3"/>
            <path d="M12 21s-7-7-7-12a7 7 0 0 1 14 0c0 5-7 12-7 12z"/>
          </svg>
        </div>
        <div style={{ display:"flex", flexDirection:"column", lineHeight:1.1 }}>
          <span style={{ fontSize:17, letterSpacing:"0.02em" }}>遊跡</span>
          <span style={{ fontSize:9.5, fontWeight:500, color:"rgba(230,239,233,0.55)", letterSpacing:"0.22em", marginTop:2 }}>TRACE</span>
        </div>
      </div>

      <div className="sidebar__section-label">主選單</div>
      <nav className="sidebar__nav">
        {nav.map(item => (
          <button
            key={item.id}
            className={`sidebar__nav-item ${route === item.id ? "sidebar__nav-item--active" : ""}`}
            onClick={() => setRoute(item.id)}
          >
            <span className="ic">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar__spacer" />

      <div className="sidebar__user">
        <div className="sidebar__avatar">{user?.initial || "J"}</div>
        <div className="sidebar__user-info" style={{ minWidth:0, flex:1 }}>
          <div className="sidebar__user-name">{user?.name || "使用者"}</div>
          <div className="sidebar__user-meta" style={{ overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{user?.email || "guest@trace.tw"}</div>
        </div>
        <button onClick={onLogout} title="登出"
          style={{ background:"transparent", border:0, color:"rgba(230,239,233,0.55)", cursor:"pointer", padding:6, borderRadius:6, fontSize:14 }}>
          ⎋
        </button>
      </div>
    </aside>
  );
}

window.Sidebar = Sidebar;
