/* global React */
const { useState } = React;

function TripCardCover({ pinCount }) {
  return (
    <div className="trip-card__cover">
      <div className="trip-card__cover-pin">📍 {pinCount} 個景點</div>
      <svg className="trip-card__cover-route" viewBox="0 0 280 70" preserveAspectRatio="none">
        <path d="M 10 50 Q 60 10, 120 35 T 230 25 T 270 45"
          fill="none" stroke="rgba(255,255,255,0.7)"
          strokeWidth="2.5" strokeDasharray="5 4" strokeLinecap="round" />
        {[
          [10, 50], [70, 22], [120, 35], [180, 18], [230, 25], [270, 45]
        ].map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={i === 0 ? 5 : 3.5}
            fill={i === 0 ? "#e87a4f" : "rgba(255,255,255,0.85)"}
            stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
        ))}
      </svg>
    </div>
  );
}

function TripsPage({ trips, onOpenTrip, onNew, onDeleteTrip }) {
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState("recent");

  const visibleTrips = trips
    .filter(trip => `${trip.title} ${trip.dest}`.toLowerCase().includes(query.trim().toLowerCase()))
    .sort((a, b) => {
      if (sortBy === "dest") return a.dest.localeCompare(b.dest, "zh-Hant");
      if (sortBy === "budget") {
        const budget = trip => Number((trip.sub.match(/NT\$([\d,]+)/) || [0, 0])[1].replace(/,/g, ""));
        return budget(b) - budget(a);
      }
      return 0;
    });

  return (
    <>
      <div className="page-header">
        <div className="page-header__title">
          <h1>我的行程</h1>
          <div className="page-header__sub">管理你的旅行計畫，探索新的目的地</div>
        </div>
        <div style={{ display:"flex", gap:8 }}>
          <button className="btn btn--primary" onClick={onNew}>＋ 新建行程</button>
        </div>
      </div>

      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginTop:28, marginBottom:8 }}>
        <h2 style={{ margin:0, fontSize:18, fontWeight:700 }}>所有行程 <span style={{ fontSize:13, color:"var(--ink-500)", fontWeight:500 }}>· {visibleTrips.length} 筆</span></h2>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          <input className="text-input" placeholder="搜尋行程或目的地..." value={query}
            onChange={(e) => setQuery(e.target.value)} style={{ width:240, padding:"8px 12px", fontSize:13 }} />
          <select className="select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="recent">最近更新</option>
            <option value="dest">依目的地</option>
            <option value="budget">依預算</option>
          </select>
        </div>
      </div>

      {trips.length === 0 ? (
        <div style={{ padding:"60px 24px", textAlign:"center", background:"var(--surface)", border:"1px dashed var(--border)", borderRadius: "var(--radius)", color:"var(--ink-500)" }}>
          <div style={{ fontSize:32, marginBottom:8 }}>🗂</div>
          <div style={{ fontSize:14, fontWeight:600, color:"var(--ink-900)", marginBottom:4 }}>還沒有行程</div>
          <div style={{ fontSize:12.5, marginBottom:14 }}>點擊「新建行程」開始你的第一趟旅程</div>
          <button className="btn btn--primary" onClick={onNew}>＋ 新建行程</button>
        </div>
      ) : (
        <div className="trip-grid">
          {visibleTrips.map(t => (
            <div className="trip-card" key={t.id} onClick={() => onOpenTrip(t)}>
              <TripCardCover pinCount={t.pin} />
              <div className="trip-card__body">
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:8 }}>
                  <div className="trip-card__title">{t.title}</div>
                  {t.isNew && <span style={{ fontSize:10, fontWeight:700, color:"#fff", background:"var(--accent)", padding:"2px 8px", borderRadius:999, letterSpacing:"0.06em" }}>NEW</span>}
                </div>
                <div className="trip-card__meta">
                  <span>{t.sub}</span>
                  <button className="btn btn--ghost" onClick={(e) => { e.stopPropagation(); onDeleteTrip(t); }}
                    style={{ padding:"4px 8px", fontSize:11, color:"var(--warn)", borderColor:"#ecc4b1" }}>
                    刪除
                  </button>
                </div>
                <div className="trip-card__spots">
                  {t.spots.map((sp, i) => (
                    <span className="trip-card__spot" key={i}>{sp}</span>
                  ))}
                  <span className="trip-card__spot-more">+{t.more}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

window.TripsPage = TripsPage;
