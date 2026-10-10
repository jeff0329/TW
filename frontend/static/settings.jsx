/* global React */
const { useState } = React;

function Switch({ value, onChange }) {
  return (
    <button
      className={`switch ${value ? "switch--on" : ""}`}
      onClick={() => onChange(!value)}
      aria-pressed={value}
    />
  );
}

function SettingsPage({ user, onLogout, onUserUpdate }) {
  const [tab, setTab] = useState("privacy");
  const [shareTelemetry, setShareTelemetry] = useState(false);
  const [displayName, setDisplayName] = useState(user?.name || "使用者");
  const [email, setEmail] = useState(user?.email || "");
  const [message, setMessage] = useState("");
  const isGuest = !!user?.guest;

  React.useEffect(() => {
    if (isGuest) {
      try {
        const saved = JSON.parse(localStorage.getItem("trace-guest-settings") || "{}");
        setShareTelemetry(!!saved.shareTelemetry);
      } catch (_) { setMessage("訪客設定載入失敗"); }
      return;
    }
    fetch("/api/settings").then(response => response.json()).then(payload => {
      const settings = payload.settings || {};
      setShareTelemetry(!!settings.shareTelemetry);
    }).catch(() => setMessage("設定載入失敗"));
  }, [isGuest]);

  const saveSetting = async (key, value) => {
    if (isGuest) {
      const saved = { shareTelemetry, [key]: value };
      localStorage.setItem("trace-guest-settings", JSON.stringify(saved));
      setMessage("訪客設定已暫存於此瀏覽器");
      setTimeout(() => setMessage(""), 1800);
      return;
    }
    const response = await fetch("/api/settings", {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ [key]: value }),
    });
    if (!response.ok) { setMessage("設定儲存失敗"); return; }
    setMessage("已儲存");
    setTimeout(() => setMessage(""), 1800);
  };

  const exportData = () => {
    const payload = { user, settings: { shareTelemetry } };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a"); link.href = url; link.download = "trace-data.json"; link.click(); URL.revokeObjectURL(url);
  };

  const clearData = () => {
    if (!window.confirm("確定要清除本地行程與收藏資料嗎？")) return;
    localStorage.clear();
    setMessage("本地資料已清除");
  };

  const nav = [
    { id:"privacy",  icon:"🔒", label:"隱私與資料" },
    { id:"account",  icon:"👤", label:"帳號" },
    { id:"about",    icon:"ℹ",  label:"關於" },
  ];

  return (
    <>
      <div className="page-header">
        <div className="page-header__title">
          <h1>設定</h1>
          <div className="page-header__sub">管理你的隱私與帳號</div>
        </div>
      </div>

      <div className="settings-layout">
        <div className="settings-nav">
          {nav.map(n => (
            <button key={n.id}
              className={`settings-nav__btn ${tab === n.id ? "settings-nav__btn--active" : ""}`}
              onClick={() => setTab(n.id)}>
              <span>{n.icon}</span> {n.label}
            </button>
          ))}
        </div>

        <div>
          {tab === "privacy" && (
            <div className="settings-section">
              <h3 className="settings-section__title">隱私與資料</h3>
              <p className="settings-section__sub">所有行程資料儲存於你的裝置，離線可用</p>

              <div style={{ padding:"12px 14px", background:"var(--green-50)", borderRadius:10, border:"1px solid var(--green-100)", marginBottom:18 }}>
                <div style={{ display:"flex", gap:10 }}>
                  <span style={{ fontSize:20 }}>🔒</span>
                  <div>
                    <div style={{ fontSize:13, fontWeight:700, color:"var(--green-800)" }}>離線使用 · 完全私密</div>
                    <div style={{ fontSize:12, color:"var(--ink-700)", marginTop:2 }}>
                      你的行程、收藏與偏好都儲存在這台裝置上，不會傳送到任何雲端伺服器。
                    </div>
                  </div>
                </div>
              </div>

              <div className="settings-row">
                <div>
                  <div className="settings-row__label">匿名使用統計</div>
                  <div className="settings-row__hint">傳送（不含個資的）效能指標協助改進</div>
                </div>
                <Switch value={shareTelemetry} onChange={(value) => { setShareTelemetry(value); saveSetting("shareTelemetry", value); }} />
              </div>

              <div className="settings-row">
                <div>
                  <div className="settings-row__label">清除本地行程資料</div>
                  <div className="settings-row__hint">會刪除所有儲存的行程與收藏</div>
                </div>
                <button className="btn btn--ghost" onClick={clearData} style={{ padding:"7px 12px", fontSize:12.5, color:"var(--warn)", borderColor:"#ecc4b1" }}>清除資料…</button>
              </div>

              <div className="settings-row">
                <div>
                  <div className="settings-row__label">匯出我的資料</div>
                  <div className="settings-row__hint">下載 JSON 包含所有行程、收藏、設定</div>
                </div>
                <button className="btn btn--ghost" onClick={exportData} style={{ padding:"7px 12px", fontSize:12.5 }}>匯出 JSON</button>
              </div>
            </div>
          )}

          {tab === "account" && (
            <div className="settings-section">
              <h3 className="settings-section__title">帳號</h3>
              <p className="settings-section__sub">基本資料 — 僅儲存於本機</p>

              <div className="settings-row">
                <div>
                  <div className="settings-row__label">顯示名稱</div>
                </div>
                <input className="text-input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} style={{ width:260, padding:"7px 12px", fontSize:13 }} />
              </div>

              <div className="settings-row">
                <div>
                  <div className="settings-row__label">電子郵件</div>
                  <div className="settings-row__hint">用於行程備份（選填）</div>
                </div>
                <input className="text-input" value={email} readOnly style={{ width:260, padding:"7px 12px", fontSize:13 }} />
              </div>

              <button className="btn btn--cta" onClick={async () => { await saveSetting("displayName", displayName); if (onUserUpdate) onUserUpdate({ ...user, name: displayName }); }}>儲存帳號設定</button>
              {message && <div className="login__notice" style={{ marginTop: 12 }}>{message}</div>}

              <div className="settings-row" style={{ borderTopStyle:"solid", marginTop:8 }}>
                <div>
                  <div className="settings-row__label" style={{ color:"var(--warn)" }}>登出帳號</div>
                  <div className="settings-row__hint">會清除目前 session 並回到登入畫面</div>
                </div>
                <button className="btn btn--ghost" onClick={onLogout}
                  style={{ padding:"7px 14px", fontSize:12.5, color:"var(--warn)", borderColor:"#ecc4b1" }}>
                  ⎋ 登出
                </button>
              </div>
            </div>
          )}

          {tab === "about" && (
            <div className="settings-section">
              <h3 className="settings-section__title">關於 遊跡 Trace</h3>
              <p className="settings-section__sub">預算驅動的台灣旅遊行程規劃</p>

              <div className="settings-row">
                <div>
                  <div className="settings-row__label">版本</div>
                </div>
                <span style={{ fontFamily:"var(--font-mono)", fontSize:12.5, color:"var(--ink-700)" }}>0.4.2 · build 2026.05.18</span>
              </div>
              <div className="settings-row">
                <div>
                  <div className="settings-row__label">資料來源</div>
                  <div className="settings-row__hint" style={{ marginTop:6 }}>
                    <div className="tag-row">
                      <span className="tag">交通部 TDX</span>
                      <span className="tag">觀光署</span>
                      <span className="tag">縣市觀光局</span>
                      <span className="tag">公開景點資料</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="settings-row">
                <div>
                  <div className="settings-row__label">聯絡我們</div>
                  <div className="settings-row__hint">回報問題、提供建議</div>
                </div>
                <button className="btn btn--ghost" onClick={() => { window.location.href = "mailto:feedback@trace.tw?subject=遊跡%20使用回饋"; }} style={{ padding:"7px 12px", fontSize:12.5 }}>送出回饋</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

window.SettingsPage = SettingsPage;
