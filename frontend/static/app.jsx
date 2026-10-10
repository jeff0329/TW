/* global React, ReactDOM */
const { useState, useRef } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#e87a4f",
  "headingFont": "Noto Sans TC",
  "showAIBrief": true
}/*EDITMODE-END*/;

// Demo trips that exist before any user activity
const INITIAL_TRIPS = [
  { id:"t1", title:"台北經典 5 日", sub:"5/10 - 5/14 · 5 天 · NT$28,000", spots:["⛩️","🥟","⛰️"], more:16, pin:19, dest:"台北", status:"planning",
    form:{ destination:"台北", days:5, style:"moderate", transports:["local","hsr"], interests:["美食","文化","自然"], groupSize:2, splitMode:true, budget:28000 } },
  { id:"t2", title:"花蓮自然 4 日", sub:"3/14 - 3/17 · 4 天 · NT$22,000", spots:["🏔️","🌊","🦞"], more:12, pin:15, dest:"花蓮", status:"drafting",
    form:{ destination:"花蓮", days:4, style:"leisurely", transports:["car"], interests:["自然","美食","放鬆"], groupSize:2, splitMode:true, budget:22000 } },
  { id:"t3", title:"墾丁海岸 5 日", sub:"6/1 - 6/5 · 5 天 · NT$32,000", spots:["🏖️","🐠","🌴"], more:14, pin:17, dest:"墾丁", status:"booked",
    form:{ destination:"墾丁", days:5, style:"leisurely", transports:["car"], interests:["自然","放鬆","冒險"], groupSize:4, splitMode:true, budget:32000 } },
  { id:"t4", title:"台南古都 3 日", sub:"4/15 - 4/17 · 3 天 · NT$18,000", spots:["🏯","🍜","🥟"], more:11, pin:14, dest:"台南", status:"planning",
    form:{ destination:"台南", days:3, style:"moderate", transports:["hsr","local"], interests:["美食","歷史","文化"], groupSize:2, splitMode:true, budget:18000 } },
  { id:"t5", title:"九份老街一日遊", sub:"已完成 · 1 天 · NT$3,500", spots:["⛩️","🍵"], more:4, pin:6, dest:"九份", status:"done",
    form:{ destination:"九份", days:1, style:"leisurely", transports:["coach"], interests:["文化","美食"], groupSize:2, splitMode:true, budget:3500 } },
  { id:"t6", title:"台中宜居 4 日", sub:"已完成 · NT$24,000", spots:["🌳","🦁","🚊"], more:8, pin:11, dest:"台中", status:"done",
    form:{ destination:"台中", days:4, style:"moderate", transports:["hsr","local"], interests:["美食","購物","自然"], groupSize:3, splitMode:true, budget:24000 } },
];

function Toast({ msg, onAction, actionLabel, onClose }) {
  if (!msg) return null;
  return (
    <div className="toast">
      <div className="toast__msg">{msg}</div>
      {actionLabel && <button className="toast__action" onClick={onAction}>{actionLabel}</button>}
      <button className="toast__close" onClick={onClose}>×</button>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);   // null = logged out
    const [authReady, setAuthReady] = useState(false);
  const [route, setRoute] = useState("plan");
  const [generating, setGenerating] = useState(false);
  const [planForm, setPlanForm] = useState(null);
  const [aiPlanResult, setAiPlanResult] = useState(null);
  const [currentTripId, setCurrentTripId] = useState(null);
  const [trips, setTrips] = useState(INITIAL_TRIPS);
  const [toast, setToast] = useState(null);
  const toastTimerRef = useRef(null);

  const [t, setTweak] = window.useTweaks(TWEAK_DEFAULTS);

  React.useEffect(() => {
    fetch("/api/auth/me")
      .then(response => response.json())
      .then(payload => setUser(payload.user))
      .catch(() => setUser(null))
      .finally(() => setAuthReady(true));
  }, []);


  const TweaksPanel = window.TweaksPanel;
  const TweakSection = window.TweakSection;
  const TweakColor = window.TweakColor;
  const TweakSelect = window.TweakSelect;
  const TweakToggle = window.TweakToggle;

  React.useEffect(() => {
    document.documentElement.style.setProperty("--accent", t.accent);
    document.documentElement.style.setProperty("--accent-soft", hexToSoft(t.accent));
    document.documentElement.style.setProperty("--accent-deep", hexToDeep(t.accent));
    document.documentElement.style.setProperty("--font-sans",
      `"${t.headingFont}", "PingFang TC", "Microsoft JhengHei", -apple-system, sans-serif`);
  }, [t.accent, t.headingFont]);

  const showToast = (msg, action) => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToasts({ msg, ...action });
    toastTimerRef.current = setTimeout(() => setToast(null), 4200);
  };

  const handleGenerate = (form) => {
    setPlanForm(form);
    setAiPlanResult(null);
    setCurrentTripId(null);   // generated, not yet saved
    setGenerating(true);

    const transportMap = {
      hsr: "高鐵",
      tra: "台鐵",
      coach: "客運",
      local: "捷運/公車",
      car: "租車",
      walk: "步行",
    };

    const transportModes = (form.transports || []).map((t) => transportMap[t] || t);

    fetch("/api/plan/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        destination: form.destination,
        days: form.days,
        budget: form.budget,
        interests: form.interests || [],
        start_spot: form.startSpot || "",
        transport_modes: transportModes,
        style: form.style || "moderate",
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data && data.status === "success") {
          setAiPlanResult(data.itinerary || null);
        } else {
          setAiPlanResult({ plan: data?.error || "AI 行程生成失敗" });
        }
      })
      .catch((err) => {
        setAiPlanResult({ plan: `API 呼叫失敗：${err?.message || err}` });
      });
  };

  const handleDone = () => {
    setGenerating(false);
    setRoute("results");
  };

  const handleBackToPlan = () => {
    setRoute("plan");
  };

  // Save current itinerary as a new trip
  const handleSaveTrip = ({ form, days, totalSpent }) => {
    // If already saved (currentTripId set), no-op
    if (currentTripId) return;
    const id = "t" + Date.now();
    const startDate = "5/10";
    const endDate = `5/${10 + form.days - 1}`;
    const spotIcons = [];
    for (const d of days) for (const s of d) if (spotIcons.length < 3) spotIcons.push(s.thumb);
    const totalSpots = days.reduce((a, d) => a + d.length, 0);
    const newTrip = {
      id, title: `${form.destination}${form.days === 1 ? "一日遊" : `${form.days}日遊`}`,
      sub: `${startDate} - ${endDate} · ${form.days} 天 · NT$${form.budget.toLocaleString()}`,
      spots: spotIcons,
      more: Math.max(0, totalSpots - 3),
      pin: totalSpots,
      dest: form.destination,
      status: "planning",
      form,
      savedDays: days,
      isNew: true,
    };
    setTrips(prev => [newTrip, ...prev]);
    setCurrentTripId(id);
    showToast(`已儲存「${newTrip.title}」到我的行程`, {
      actionLabel: "前往查看",
      onAction: () => { setRoute("trips"); setToast(null); },
    });
  };

  const handleOpenTrip = (trip) => {
    setPlanForm(trip.form);
    setCurrentTripId(trip.id);
    setRoute("results");
  };

  const handleDeleteTrip = (trip) => {
    setTrips(prev => prev.filter(item => item.id !== trip.id));
    if (currentTripId === trip.id) {
      setCurrentTripId(null);
      setRoute("trips");
    }
    showToast(`已刪除「${trip.title}」`);
  };

  const handleAddToTrip = (place, tripId) => {
    const trip = trips.find(t => t.id === tripId);
    if (!trip) return;
    setTrips(prev => prev.map(t => t.id === tripId ? {
      ...t,
      pin: t.pin + 1,
      more: t.more + 1,
    } : t));
    showToast(`已加入「${place.name}」到「${trip.title}」`, {
      actionLabel: "打開行程",
      onAction: () => { handleOpenTrip(trip); setToast(null); },
    });
  };

  const handleNewTripFromPlace = (place) => {
    setRoute("plan");
    showToast(`已將「${place.name}」設為新行程起點，請填寫預算 & 天數`);
  };

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
    setRoute("plan");
    setPlanForm(null);
    setCurrentTripId(null);
  };

  const onNav = (id) => {
    if (id === "plan") setRoute("plan");
    else setRoute(id);
  };

  const navActive = route === "results" ? "trips" : route;

  // If not logged in, show login page
  if (!authReady) return <div className="login__loading">載入中...</div>;

  if (!user) {
    return (
      <>
        <LoginPage onLogin={(u) => { setUser(u); setRoute("plan"); }} />
        <Toast {...toast} onClose={() => setToast(null)} />
      </>
    );
  }

  return (
    <div className="app" data-screen-label={
      route === "plan" ? "AI 規劃" :
      route === "results" ? "行程結果" :
      route === "trips" ? "我的行程" :
      route === "saved" ? "收藏清單" :
      route === "settings" ? "設定" : route
    }>
      <Sidebar route={navActive} setRoute={onNav} user={user} onLogout={handleLogout} />
      <main className="main">
        {route === "plan" && <PlanningPage onGenerate={handleGenerate} initialForm={planForm} />}
        {route === "results" && planForm && (
          <ResultsPage form={planForm}
            onBack={handleBackToPlan}
            onSave={handleSaveTrip}
            onToast={showToast}
            savedAlready={!!currentTripId}
            aiPlanResult={aiPlanResult} />
        )}
        {route === "trips" && (
          <TripsPage trips={trips}
            onOpenTrip={handleOpenTrip}
            onNew={() => setRoute("plan")}
            onDeleteTrip={handleDeleteTrip} />
        )}
        {route === "saved" && (
          <SavedPage trips={trips}
            onAddToTrip={handleAddToTrip} />
        )}
        {route === "settings" && <SettingsPage user={user} onLogout={handleLogout} onUserUpdate={setUser} />}
      </main>
      {generating && planForm && <GeneratingOverlay form={planForm} onDone={handleDone} />}

      <Toast {...toast} onClose={() => setToast(null)} />

      <TweaksPanel title="Tweaks" noDeckControls={true}>
        <TweakSection label="主視覺">
          <TweakColor
            label="Accent 色"
            value={t.accent}
            onChange={(v) => setTweak("accent", v)}
            options={["#e87a4f","#c25f4a","#d4a958","#6b85ad","#7a6ba8"]}
          />
          <TweakSelect
            label="字型"
            value={t.headingFont}
            onChange={(v) => setTweak("headingFont", v)}
            options={[
              { value: "Noto Sans TC",   label: "Noto Sans TC" },
              { value: "Noto Serif TC",  label: "Noto Serif TC" },
              { value: "LXGW WenKai TC", label: "霞鶩文楷" },
            ]}
          />
        </TweakSection>
        <TweakSection label="行為">
          <TweakToggle
            label="顯示 AI 解釋面板"
            value={t.showAIBrief}
            onChange={(v) => setTweak("showAIBrief", v)}
          />
        </TweakSection>
        <TweakSection label="快速導覽">
          <div style={{ display:"flex", flexDirection:"column", gap:6, padding:"0 14px 6px" }}>
            <button className="btn btn--ghost" onClick={() => setRoute("trips")}>我的行程</button>
            <button className="btn btn--ghost" onClick={() => setRoute("plan")}>AI 規劃輸入</button>
            <button className="btn btn--ghost" onClick={() => {
              if (!planForm) {
                setPlanForm({ destination:"台北", days:5, style:"moderate", transports:["local","hsr"], interests:["美食","文化","自然"], groupSize:2, splitMode:true, budget:28000 });
              }
              setCurrentTripId(null);
              setRoute("results");
            }}>行程結果頁</button>
            <button className="btn btn--ghost" onClick={() => setRoute("saved")}>收藏清單</button>
            <button className="btn btn--ghost" onClick={() => setRoute("settings")}>設定</button>
            <button className="btn btn--ghost" onClick={() => {
              const f = planForm || { destination:"台北", days:5, style:"moderate", transports:["local","hsr"], interests:["美食","文化","自然"], groupSize:2, splitMode:true, budget:28000 };
              setPlanForm(f);
              setCurrentTripId(null);
              setGenerating(true);
            }}>預覽 AI 生成動畫</button>
          </div>
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

function hexToSoft(hex) { return mixHex(hex, "#fbfaf6", 0.78); }
function hexToDeep(hex) { return mixHex(hex, "#000000", 0.28); }
function mixHex(a, b, t) {
  const pa = parseInt(a.slice(1), 16);
  const pb = parseInt(b.slice(1), 16);
  const ar = (pa >> 16) & 0xff, ag = (pa >> 8) & 0xff, ab = pa & 0xff;
  const br = (pb >> 16) & 0xff, bg = (pb >> 8) & 0xff, bb = pb & 0xff;
  const r = Math.round(ar + (br - ar) * t);
  const g = Math.round(ag + (bg - ag) * t);
  const bl = Math.round(ab + (bb - ab) * t);
  return "#" + ((1 << 24) | (r << 16) | (g << 8) | bl).toString(16).slice(1);
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
