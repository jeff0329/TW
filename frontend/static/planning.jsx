/* global React */
const { useState, useMemo, useEffect, useRef } = React;

// Budget allocation logic — shifts as tier changes
function getAllocation(budget) {
  let lodging, food, transport, attractions;
  if (budget < 15000) {
    [lodging, food, transport, attractions] = [0.30, 0.32, 0.22, 0.16];
  } else if (budget < 50000) {
    [lodging, food, transport, attractions] = [0.38, 0.28, 0.18, 0.16];
  } else if (budget < 100000) {
    [lodging, food, transport, attractions] = [0.42, 0.26, 0.18, 0.14];
  } else {
    [lodging, food, transport, attractions] = [0.46, 0.24, 0.16, 0.14];
  }
  return [
    { key:"lodging",     label:"住宿",   color:"#2a3a64", ratio:lodging },
    { key:"food",        label:"餐飲",   color:"#e87a4f", ratio:food },
    { key:"transport",   label:"交通",   color:"#6b85ad", ratio:transport },
    { key:"attractions", label:"景點門票", color:"#b89758", ratio:attractions },
  ];
}

function getTier(budget) {
  if (budget < 15000)  return { name:"經濟實惠", cls:"budget-slider__tier--low",  desc:"節省、青旅、小吃為主" };
  if (budget < 50000)  return { name:"適中",     cls:"budget-slider__tier--mid",  desc:"商務酒店、平衡體驗" };
  if (budget < 100000) return { name:"舒適",     cls:"budget-slider__tier--mid",  desc:"4 星酒店、特色餐飲" };
  return { name:"豪華", cls:"budget-slider__tier--high", desc:"高檔酒店、米其林級餐飲" };
}

// Donut chart
function Donut({ items, total }) {
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  const segments = items.map((s) => {
    const len = s.ratio * circumference;
    const seg = { ...s, dasharray: `${len} ${circumference - len}`, dashoffset: -offset };
    offset += len;
    return seg;
  });

  return (
    <div className="donut">
      <svg viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#ebe6d8" strokeWidth="18" />
        {segments.map((s) => (
          <circle key={s.key} cx="70" cy="70" r={radius} fill="none" stroke={s.color} strokeWidth="18"
            strokeDasharray={s.dasharray} strokeDashoffset={s.dashoffset}
            style={{ transition: "stroke-dasharray 0.5s ease, stroke-dashoffset 0.5s ease" }}
          />
        ))}
      </svg>
      <div className="donut__center">
        <div className="donut__center-label">總預算</div>
        <div className="donut__center-value">NT${total.toLocaleString()}</div>
        <div className="donut__center-sub">已分配 100%</div>
      </div>
    </div>
  );
}

function BudgetSlider({ value, onChange, min=5000, max=150000 }) {
  const pct = Math.min(1, Math.max(0, (value - min) / (max - min)));
  return (
    <div className="budget-slider">
      <div className="budget-slider__track" />
      <div className="budget-slider__fill" style={{ width: `${pct * 100}%` }} />
      <div className="budget-slider__thumb" style={{ left: `${pct * 100}%` }} />
      <input type="range" min={min} max={max} step="500" value={value} onChange={(e) => onChange(parseInt(e.target.value))} />
    </div>
  );
}

function DaysSlider({ value, onChange }) {
  // 1 - 14 days
  const min = 1, max = 14;
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div className="days-slider">
      <div className="days-slider__bar">
        <div className="days-slider__track" />
        <div className="days-slider__fill" style={{ width: `${pct}%` }} />
        <div className="days-slider__thumb" style={{ left: `${pct}%` }}>
          <span>{value}</span>
        </div>
        <input type="range" min={min} max={max} step={1} value={value} onChange={(e) => onChange(parseInt(e.target.value))} />
      </div>
      <div className="days-slider__ticks">
        {[1, 3, 5, 7, 10, 14].map(t => (
          <button
            key={t}
            className={`days-slider__tick ${value === t ? "is-active" : ""}`}
            onClick={() => onChange(t)}
          >{t} 天</button>
        ))}
      </div>
    </div>
  );
}

function PlanningPage({ onGenerate, initialForm }) {
  const [form, setForm] = useState({
    destination: "台北",
    days: 5,
    style: "moderate",
    transports: ["local", "hsr"],   // multi-select
    interests: ["美食", "文化", "自然"],
    groupSize: 2,
    splitMode: true,
    budget: 28000,
    currency: "TWD",
  });

  React.useEffect(() => {
    if (initialForm) setForm(initialForm);
  }, [initialForm]);

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const toggleInterest = (it) => {
    setForm(f => ({ ...f, interests: f.interests.includes(it) ? f.interests.filter(x => x !== it) : [...f.interests, it] }));
  };
  const toggleTransport = (id) => {
    setForm(f => {
      const has = f.transports.includes(id);
      if (has && f.transports.length === 1) return f; // keep at least one
      return { ...f, transports: has ? f.transports.filter(x => x !== id) : [...f.transports, id] };
    });
  };

  const allocation = useMemo(() => getAllocation(form.budget), [form.budget]);
  const tier = useMemo(() => getTier(form.budget), [form.budget]);
  const perDay = Math.round(form.budget / form.days);
  const perPerson = Math.round(form.budget / form.groupSize);

  const dayBudgets = useMemo(() => {
    const base = form.budget / form.days;
    const weights = [1.05, 1.12, 0.95, 0.92, 0.96, 1.0, 1.0, 1.04, 0.92, 1.0, 0.95, 1.02, 0.94, 0.98];
    return Array.from({ length: form.days }).map((_, i) => Math.round(base * (weights[i] || 1)));
  }, [form.budget, form.days]);

  // Taiwan destinations
  const popular = ["台北", "台中", "台南", "高雄", "花蓮", "宜蘭", "台東", "墊丁", "南投"];
  const interests = ["美食", "文化", "自然", "購物", "夜生活", "歷史", "冒險", "放鬆", "親子", "攝影"];

  const styles = [
    { id:"leisurely", title:"悠閒慢遊", sub:"3-4 點/日", ic:"☕" },
    { id:"moderate",  title:"適中節奏", sub:"4-5 點/日", ic:"🌿" },
    { id:"packed",    title:"緊湊充實", sub:"6-7 點/日", ic:"⚡" },
  ];

  // Taiwan transport options
  const transports = [
    { id:"hsr",     title:"高鐵",     sub:"快速、跨縣市", ic:"🚄" },
    { id:"tra",     title:"台鐵",     sub:"經濟、彈性",   ic:"🚆" },
    { id:"coach",   title:"客運",     sub:"長途巴士",     ic:"🚌" },
    { id:"local",   title:"捷運/公車", sub:"市區運輸",   ic:"🚍" },
    { id:"car",     title:"租車自駕", sub:"自由探索",   ic:"🚗" },
    { id:"walk",    title:"步行",     sub:"近距離",     ic:"🚶" },
  ];

  return (
    <>
      <div className="page-header">
        <div className="page-header__title">
          <div className="breadcrumb">
            <span>我的行程</span>
            <span>›</span>
            <span style={{ color: "var(--green-700)", fontWeight: 600 }}>AI 規劃</span>
          </div>
          <h1>用 <span className="accent">AI</span> 打造你的專屬行程</h1>
          <div className="page-header__sub">輸入目的地與需求，AI 為你規劃台灣行程 — 每一站都依照你的偏好安排。</div>
        </div>
        <div className="page-header__stat">
          <span className="dot" />
          全台 12,408 個景點 · 即時票價
        </div>
      </div>

      <div className="planner-grid">
        {/* LEFT */}
        <div style={{ display:"flex", flexDirection:"column", gap:16 }}>

          {/* Destination */}
          <div className="card">
            <div className="section-title">
              <h3><span className="num">1</span>目的地與日期</h3>
              <span className="section-title__hint">AI 會評估到目的地的交通成本</span>
            </div>

            <div style={{ display:"grid", gridTemplateColumns:"1.4fr 1fr", gap:16 }}>
              <div>
                <div className="field-label" style={{ marginBottom:6 }}>📍 目的地</div>
                <input className="text-input" placeholder="輸入城市、國家或地區"
                  value={form.destination}
                  onChange={(e) => setF("destination", e.target.value)} />
                <div className="suggest-row" style={{ marginTop:10 }}>
                  <span className="suggest-row__label">熱門</span>
                  {popular.map(p => (
                    <button key={p} className="suggest-pill" onClick={() => setF("destination", p)}>{p}</button>
                  ))}
                </div>
              </div>

              <div>
                <div className="field-label" style={{ marginBottom:6 }}>📅 旅遊天數</div>
                <DaysSlider value={form.days} onChange={(d) => setF("days", d)} />
              </div>
            </div>
          </div>

          {/* Budget */}
          <div className="card budget-card" style={{ background: "linear-gradient(180deg, #ffffff 0%, #faf6ee 100%)" }}>
            <div className="section-title">
              <h3><span className="num">2</span>預算範圍</h3>
              <span className={`budget-slider__tier ${tier.cls}`}>{tier.name}</span>
            </div>

            <div className="budget-card__value-row" style={{ marginTop:6 }}>
              <span className="budget-card__currency">NT$</span>
              <input className="budget-input" type="text" value={form.budget.toLocaleString()}
                onChange={(e) => {
                  const n = parseInt(e.target.value.replace(/[^0-9]/g, ""), 10) || 0;
                  setF("budget", Math.min(200000, Math.max(0, n)));
                }} />
            </div>
            <div className="budget-card__sub">
              <span>{tier.desc}</span>
              <span>平均 <strong style={{ color:"var(--ink-900)" }}>NT$ {perDay.toLocaleString()}</strong> / 天</span>
            </div>

            <BudgetSlider value={form.budget} onChange={(v) => setF("budget", v)} />
            <div className="budget-slider__ticks">
              <span>5K</span>
              <span>40K</span>
              <span>80K</span>
              <span>120K</span>
              <span>150K+</span>
            </div>
          </div>

          {/* Style + transport (now multi-select) */}
          <div className="card">
            <div className="section-title">
              <h3><span className="num">3</span>節奏 & 交通組合</h3>
              <span className="section-title__hint">交通組合直接影響你的預算配比</span>
            </div>

            <div className="field-label" style={{ marginTop:8, marginBottom:8 }}>旅遊節奏</div>
            <div className="option-grid option-grid--3">
              {styles.map(s => (
                <button key={s.id}
                  className={`option-card ${form.style === s.id ? "option-card--selected" : ""}`}
                  onClick={() => setF("style", s.id)}>
                  <div className="option-card__ic">{s.ic}</div>
                  <div className="option-card__title">{s.title}</div>
                  <div className="option-card__sub">{s.sub}</div>
                </button>
              ))}
            </div>

            <div className="field-label" style={{ marginTop:18, marginBottom:6, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <span>主要交通方式（可複選 / 混合）</span>
              <span style={{ fontWeight:500, color:"var(--ink-500)" }}>已選 {form.transports.length} 項</span>
            </div>
            <div className="option-grid option-grid--6">
              {transports.map(t => {
                const sel = form.transports.includes(t.id);
                return (
                  <button key={t.id}
                    className={`option-card option-card--multi ${sel ? "option-card--selected" : ""}`}
                    onClick={() => toggleTransport(t.id)}>
                    {sel && <span className="option-card__check">✓</span>}
                    <div className="option-card__ic">{t.ic}</div>
                    <div className="option-card__title">{t.title}</div>
                    <div className="option-card__sub">{t.sub}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Interests + group */}
          <div className="card">
            <div className="section-title">
              <h3><span className="num">4</span>興趣偏好 & 同行人數</h3>
              <span className="section-title__hint">選 2-4 個 AI 表現最好</span>
            </div>

            <div className="field-label" style={{ marginTop:8, marginBottom:8 }}>興趣標籤</div>
            <div className="chip-row">
              {interests.map(it => (
                <button key={it}
                  className={`chip ${form.interests.includes(it) ? "chip--selected" : ""}`}
                  onClick={() => toggleInterest(it)}>{it}</button>
              ))}
            </div>

            <div className="divider-soft" />

            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, alignItems:"center" }}>
              <div>
                <div className="field-label">👥 同行人數</div>
                <div className="field-hint" style={{ marginBottom:8 }}>用於分攤預算與選擇住宿房型</div>
                <div className="stepper">
                  <button onClick={() => setF("groupSize", Math.max(1, form.groupSize - 1))}>−</button>
                  <span className="stepper__value">{form.groupSize}</span>
                  <button onClick={() => setF("groupSize", Math.min(8, form.groupSize + 1))}>+</button>
                </div>
              </div>

              <label style={{ display:"flex", alignItems:"flex-start", gap:10, padding:"12px 14px", borderRadius:10, background:"var(--surface-2)", border:"1px solid var(--border)", cursor:"pointer" }}>
                <input type="checkbox" checked={form.splitMode} onChange={(e) => setF("splitMode", e.target.checked)} style={{ marginTop:3 }} />
                <div>
                  <div className="field-label">啟用人均分攤</div>
                  <div className="field-hint">行程內每筆花費自動顯示每人應付金額</div>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* RIGHT — Budget Panel */}
        <aside className="budget-panel">
          <div className="card" style={{ padding:22 }}>
            <div className="budget-card__header">
              <div>
                <div className="budget-card__label">預算分配</div>
                <div style={{ fontSize:14, fontWeight:600, color:"var(--ink-900)", marginTop:2 }}>{tier.name}方案配比</div>
              </div>
              <div style={{ fontSize:11, color:"var(--ink-500)", textAlign:"right" }}>
                <div>共 {form.days} 天</div>
                <div style={{ marginTop:2 }}>{form.groupSize} 人同行</div>
              </div>
            </div>

            <div className="donut-wrap">
              <Donut items={allocation} total={form.budget} />
              <div className="legend">
                {allocation.map(a => (
                  <div className="legend__row" key={a.key}>
                    <span className="legend__dot" style={{ background: a.color }} />
                    <span className="legend__label">{a.label}</span>
                    <span className="legend__pct">{Math.round(a.ratio * 100)}%</span>
                    <span className="legend__amt">NT${Math.round(form.budget * a.ratio).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="divider-soft" />

            <div className="field-label" style={{ marginBottom:10 }}>每日預算分布</div>
            <div className="day-bars">
              {dayBudgets.slice(0, Math.min(form.days, 10)).map((amt, i) => {
                const maxAmt = Math.max(...dayBudgets);
                return (
                  <div className="day-bar" key={i}>
                    <span className="day-bar__label">Day {i+1}</span>
                    <div className="day-bar__track">
                      <div className="day-bar__fill" style={{ width: `${(amt/maxAmt) * 100}%` }} />
                    </div>
                    <span className="day-bar__amt">${amt.toLocaleString()}</span>
                  </div>
                );
              })}
              {form.days > 10 && (
                <div className="day-bar" style={{ opacity:0.6 }}>
                  <span className="day-bar__label">…</span>
                  <div style={{ fontSize:11, color:"var(--ink-500)" }}>{form.days - 10} 天未顯示</div>
                  <span />
                </div>
              )}
            </div>

            {form.splitMode && form.groupSize > 1 && (
              <>
                <div className="divider-soft" />
                <div className="split-row">
                  <span className="split-row__label">人均花費（{form.groupSize} 人分攤）</span>
                  <span className="split-row__amount">NT${perPerson.toLocaleString()}</span>
                </div>
              </>
            )}
          </div>

          <div className="ai-brief">
            <div className="ai-brief__label">
              <span className="sparkle" style={{ color:"var(--accent)" }} />
              AI 即將為你做
            </div>
            <div className="ai-brief__heading">
              在 <strong>{form.destination}</strong> 安排 {form.days} 天，
              控制在 <strong>NT$ {form.budget.toLocaleString()}</strong> 內
            </div>
            <div className="ai-brief__bullets">
              <div className="ai-brief__bullet">
                <span className="check">✓</span>
                從 12,408 個景點中挑選 {form.interests.length || 3} 類偏好
              </div>
              <div className="ai-brief__bullet">
                <span className="check">✓</span>
                混合 {form.transports.length} 種交通方式評估實際花費
              </div>
              <div className="ai-brief__bullet">
                <span className="check">✓</span>
                每日不超過 NT$ {perDay.toLocaleString()} · 保留 5% 緩衝
              </div>
            </div>
          </div>

          <button className="btn btn--primary" style={{ width:"100%" }} onClick={() => onGenerate(form)}>
            開始 AI 規劃行程
          </button>
        </aside>
      </div>
    </>
  );
}

window.PlanningPage = PlanningPage;
window.getTier = getTier;
window.getAllocation = getAllocation;
