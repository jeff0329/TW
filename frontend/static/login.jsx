/* global React */
const { useState } = React;

function LoginPage({ onLogin }) {
  const [mode, setMode] = useState("login");   // login | signup
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [remember, setRemember] = useState(true);
  const [busy, setBusy] = useState(false);
  const [errMsg, setErrMsg] = useState("");
  const [notice, setNotice] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrMsg("");
    setNotice("");
    if (!email || !password) { setErrMsg("請輸入電子郵件與密碼"); return; }
    if (mode === "signup" && !name) { setErrMsg("請輸入暱稱"); return; }
    if (mode === "signup" && password.length < 8) { setErrMsg("密碼至少需要 8 個字元"); return; }
    setBusy(true);
    try {
      const response = await fetch(`/api/auth/${mode === "signup" ? "register" : "login"}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, remember }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "操作失敗");
      setBusy(false);
      onLogin(payload.user);
    } catch (error) {
      setBusy(false);
      setErrMsg(error.message);
    }
  };

  const handleGuest = () => {
    onLogin({ name: "訪客", email: "guest@trace.tw", initial: "G", guest: true });
  };

  const handleForgot = async () => {
    setErrMsg("");
    setNotice("");
    if (!email) { setErrMsg("請先輸入電子郵件"); return; }
    const response = await fetch("/api/auth/forgot-password", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }),
    });
    const payload = await response.json();
    if (!response.ok) setErrMsg(payload.error || "操作失敗");
    else setNotice(payload.message);
  };

  return (
    <div className="login">
      {/* Left: Brand panel */}
      <div className="login__brand">
        <div className="login__brand-top">
          <div className="login__brand-logo">
            <div className="login__brand-mark">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="10" r="3"/>
                <path d="M12 21s-7-7-7-12a7 7 0 0 1 14 0c0 5-7 12-7 12z"/>
              </svg>
            </div>
            <div>
              <div className="login__brand-name">遊跡</div>
              <div className="login__brand-sub">TRACE · 預算驅動旅遊規劃</div>
            </div>
          </div>
        </div>

        <div className="login__brand-center">
          <h1 className="login__hero-title">把預算交給 AI，<br/>讓旅程<span className="login__hero-em">回到享受</span>。</h1>
          <p className="login__hero-sub">
            輸入總預算、天數與偏好，AI 幫你在台灣 12,000＋ 景點中挑出最契合的組合，
            每一筆花費都清楚透明，超支前就先提醒。
          </p>

          <div className="login__features">
            <div className="login__feature">
              <span className="login__feature-ic">💰</span>
              <div>
                <div className="login__feature-title">預算精準分配</div>
                <div className="login__feature-sub">住宿、餐飲、交通、景點 自動最佳化</div>
              </div>
            </div>
            <div className="login__feature">
              <span className="login__feature-ic">🗺</span>
              <div>
                <div className="login__feature-title">動線最佳化</div>
                <div className="login__feature-sub">最小化交通時間，避開公休與排隊</div>
              </div>
            </div>
            <div className="login__feature">
              <span className="login__feature-ic">🔒</span>
              <div>
                <div className="login__feature-title">隱私至上</div>
                <div className="login__feature-sub">行程資料留在你的裝置，離線可用</div>
              </div>
            </div>
          </div>
        </div>

        {/* Decorative map route */}
        <svg className="login__map-art" viewBox="0 0 540 260" preserveAspectRatio="none">
          <defs>
            <pattern id="lgrid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="540" height="260" fill="url(#lgrid)" />
          <path d="M 0 180 Q 120 140 220 170 T 420 150 T 540 180"
            stroke="rgba(232,122,79,0.5)" strokeWidth="2" strokeDasharray="6 5" fill="none" />
          {[[60, 175], [180, 155], [300, 165], [400, 145], [500, 175]].map(([x, y], i) => (
            <g key={i}>
              <circle cx={x} cy={y} r="9" fill="rgba(255,255,255,0.1)" />
              <circle cx={x} cy={y} r="5" fill={i === 0 ? "#e87a4f" : "rgba(255,255,255,0.6)"} />
            </g>
          ))}
        </svg>

        <div className="login__brand-bottom">
          <span>© 2026 遊跡 Trace</span>
          <span>v0.4.2</span>
        </div>
      </div>

      {/* Right: Form */}
      <div className="login__form-wrap">
        <div className="login__form">
          <div className="login__form-header">
            <div className="login__mode-switch">
              <button className={mode === "login" ? "is-active" : ""} onClick={() => setMode("login")}>登入</button>
              <button className={mode === "signup" ? "is-active" : ""} onClick={() => setMode("signup")}>建立帳號</button>
            </div>
            <h2>{mode === "login" ? "歡迎回來" : "開始你的旅程"}</h2>
            <p>{mode === "login" ? "登入以繼續規劃你的下一段冒險" : "免費註冊，享受 AI 旅遊規劃"}</p>
          </div>

          <form onSubmit={handleSubmit}>
            {mode === "signup" && (
              <div className="login__field">
                <label>暱稱</label>
                <input type="text" placeholder="例：小明"
                  value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
              </div>
            )}

            <div className="login__field">
              <label>電子郵件</label>
              <input type="email" placeholder="name@example.com"
                value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
            </div>

            <div className="login__field">
              <label style={{ display:"flex", justifyContent:"space-between" }}>
                <span>密碼</span>
                {mode === "login" && (
                  <button type="button" className="login__forgot" onClick={handleForgot}>忘記密碼？</button>
                )}
              </label>
              <input type="password" placeholder={mode === "signup" ? "至少 8 個字元" : "輸入你的密碼"}
                value={password} onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === "login" ? "current-password" : "new-password"} />
            </div>

            {mode === "login" && (
              <label className="login__remember">
                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                <span>記住我這 30 天</span>
              </label>
            )}

            {errMsg && <div className="login__err">{errMsg}</div>}
            {notice && <div className="login__notice">{notice}</div>}

            <button type="submit" className="btn btn--cta login__submit" disabled={busy}>
              {busy ? "處理中..." : mode === "login" ? "登入" : "建立帳號"}
            </button>
          </form>

          <button className="login__guest" onClick={handleGuest} disabled={busy}>
            以訪客模式進入（不儲存帳號資料）
          </button>
        </div>
      </div>
    </div>
  );
}

window.LoginPage = LoginPage;
