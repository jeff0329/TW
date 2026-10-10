/* global React */
const { useState, useMemo, useEffect, useRef } = React;

function buildItinerary(form, places = []) {
  // Taipei-area itinerary with real coordinates
  const taipei = [
    [
      { id:"d1-1", name:"龍山寺",       cat:"文化", catLabel:"文化", catCls:"", time:"09:00", duration:"1 hr",   price:0,    transit:{ mode:"捷運", time:"15 分", cost:25 }, tags:["古蹟","祈福"], thumb:"⛩️", lat:25.0367, lng:121.4998 },
      { id:"d1-2", name:"鼎泰豐 信義店", cat:"美食", catLabel:"美食", catCls:"stop__category--food", time:"11:30", duration:"1.5 hr", price:850, transit:{ mode:"捷運", time:"22 分", cost:25 }, tags:["小籠包","必吃"], thumb:"🥟", lat:25.0335, lng:121.5648 },
      { id:"d1-3", name:"四四南村",     cat:"文化", catLabel:"文化", catCls:"", time:"14:00", duration:"1.5 hr", price:0, transit:{ mode:"步行", time:"6 分", cost:0 }, tags:["眷村","散步"], thumb:"🏘️", lat:25.0317, lng:121.5638 },
      { id:"d1-4", name:"象山步道",     cat:"自然", catLabel:"自然", catCls:"", time:"16:00", duration:"2 hr",   price:0,    transit:{ mode:"步行", time:"10 分", cost:0 }, tags:["夕陽","健行"], thumb:"⛰️", lat:25.0276, lng:121.5710 },
      { id:"d1-5", name:"西門町商圈",   cat:"購物", catLabel:"購物", catCls:"", time:"19:00", duration:"2 hr",   price:1200, transit:{ mode:"捷運", time:"18 分", cost:25 }, tags:["逛街","美食"], thumb:"🛍️", lat:25.0418, lng:121.5074 },
      { id:"d1-6", name:"晴光商旅",     cat:"住宿", catLabel:"住宿", catCls:"stop__category--hotel", time:"22:00", duration:"夜宿", price:2400, transit:{ mode:"捷運", time:"12 分", cost:25 }, tags:["商務","中山區"], thumb:"🏨", lat:25.0594, lng:121.5236 },
    ],
    [
      { id:"d2-1", name:"故宮博物院",   cat:"文化", catLabel:"文化", catCls:"", time:"09:30", duration:"3 hr",   price:350, transit:{ mode:"公車", time:"35 分", cost:30 }, tags:["國寶"], thumb:"🏛️", lat:25.1023, lng:121.5485 },
      { id:"d2-2", name:"陽明山國家公園", cat:"自然", catLabel:"自然", catCls:"", time:"13:30", duration:"3 hr",   price:0,   transit:{ mode:"公車", time:"45 分", cost:30 }, tags:["山景","花季"], thumb:"🌋", lat:25.1545, lng:121.5455 },
      { id:"d2-3", name:"士林夜市",     cat:"美食", catLabel:"美食", catCls:"stop__category--food", time:"18:30", duration:"2 hr", price:600, transit:{ mode:"捷運", time:"25 分", cost:25 }, tags:["小吃"], thumb:"🍢", lat:25.0884, lng:121.5247 },
      { id:"d2-4", name:"圓山大飯店",   cat:"住宿", catLabel:"住宿", catCls:"stop__category--hotel", time:"22:00", duration:"夜宿", price:3200, transit:{ mode:"步行", time:"10 分", cost:0 }, tags:["經典"], thumb:"🏨", lat:25.0795, lng:121.5258 },
    ],
    [
      { id:"d3-1", name:"九份老街",     cat:"文化", catLabel:"文化", catCls:"", time:"10:00", duration:"3 hr",   price:300, transit:{ mode:"客運", time:"90 分", cost:90 }, tags:["山城","美景"], thumb:"⛩️", lat:25.1080, lng:121.8447 },
      { id:"d3-2", name:"阿妹茶樓",     cat:"美食", catLabel:"美食", catCls:"stop__category--food", time:"14:00", duration:"1.5 hr", price:480, transit:{ mode:"步行", time:"3 分", cost:0 }, tags:["茶藝"], thumb:"🍵", lat:25.1085, lng:121.8443 },
      { id:"d3-3", name:"十分瀑布",     cat:"自然", catLabel:"自然", catCls:"", time:"16:00", duration:"2 hr",   price:80,  transit:{ mode:"火車", time:"50 分", cost:60 }, tags:["瀑布"], thumb:"🌊", lat:25.0479, lng:121.7794 },
      { id:"d3-4", name:"圓山大飯店",   cat:"住宿", catLabel:"住宿", catCls:"stop__category--hotel", time:"21:30", duration:"夜宿", price:3200, transit:{ mode:"客運", time:"80 分", cost:90 }, tags:[], thumb:"🏨", lat:25.0795, lng:121.5258 },
    ],
    [
      { id:"d4-1", name:"迪化街",       cat:"文化", catLabel:"文化", catCls:"", time:"09:30", duration:"2 hr",   price:0,   transit:{ mode:"捷運", time:"20 分", cost:25 }, tags:["老街","茶葉"], thumb:"🏮", lat:25.0560, lng:121.5099 },
      { id:"d4-2", name:"永康街美食",   cat:"美食", catLabel:"美食", catCls:"stop__category--food", time:"12:00", duration:"2 hr", price:720, transit:{ mode:"捷運", time:"18 分", cost:25 }, tags:["在地"], thumb:"🍜", lat:25.0322, lng:121.5294 },
      { id:"d4-3", name:"中正紀念堂",   cat:"歷史", catLabel:"歷史", catCls:"", time:"14:30", duration:"1.5 hr", price:0,   transit:{ mode:"步行", time:"5 分", cost:0 }, tags:["景點"], thumb:"🏛️", lat:25.0357, lng:121.5202 },
      { id:"d4-4", name:"信義商圈",     cat:"購物", catLabel:"購物", catCls:"", time:"17:00", duration:"3 hr",   price:1500, transit:{ mode:"捷運", time:"10 分", cost:25 }, tags:["逛街"], thumb:"🏙️", lat:25.0339, lng:121.5644 },
    ],
    [
      { id:"d5-1", name:"北投溫泉",     cat:"放鬆", catLabel:"放鬆", catCls:"", time:"10:00", duration:"3 hr",   price:800, transit:{ mode:"捷運", time:"40 分", cost:30 }, tags:["溫泉"], thumb:"♨️", lat:25.1376, lng:121.5063 },
      { id:"d5-2", name:"地熱谷",       cat:"自然", catLabel:"自然", catCls:"", time:"13:30", duration:"1 hr",   price:0,   transit:{ mode:"步行", time:"8 分", cost:0 }, tags:["地景"], thumb:"💨", lat:25.1373, lng:121.5097 },
      { id:"d5-3", name:"饒河夜市",     cat:"美食", catLabel:"美食", catCls:"stop__category--food", time:"18:00", duration:"2 hr", price:500, transit:{ mode:"捷運", time:"30 分", cost:30 }, tags:["小吃"], thumb:"🦞", lat:25.0511, lng:121.5775 },
    ],
  ];

  const databaseStops = places.map((place, index) => ({
    id: `db-${index}-${place.名稱}`,
    name: place.名稱,
    cat: "景點",
    catLabel: "景點",
    catCls: "",
    time: `${String(9 + (index % 8)).padStart(2, "0")}:00`,
    duration: "1.5 hr",
    price: Number.parseInt(String(place.票價 || "").replace(/[^0-9]/g, ""), 10) || 0,
    transit: { mode: "市區交通", time: "依地點調整", cost: 0 },
    tags: [place.縣市, place.區域, place.分類].filter(Boolean).slice(0, 2),
    thumb: "📍",
    lat: Number(place.緯度) || 25.0418,
    lng: Number(place.經度) || 121.535,
  }));
  const sourceStops = databaseStops;
  const dest = form.destination;
  const uniqueStops = [];
  const seenNames = new Set();
  for (const stop of sourceStops) {
    if (seenNames.has(stop.name)) continue;
    seenNames.add(stop.name);
    uniqueStops.push(stop);
  }
  const days = Array.from({ length: form.days }, () => []);
  const maxPerDay = form.style === "packed" ? 6 : form.style === "leisurely" ? 3 : 4;
  const budgetLimit = Math.max(0, Number(form.budget) || 0);
  let remainingBudget = budgetLimit;
  let candidateIndex = 0;
  for (let dayIndex = 0; dayIndex < days.length; dayIndex++) {
    while (days[dayIndex].length < maxPerDay && candidateIndex < uniqueStops.length) {
      const stop = uniqueStops[candidateIndex++];
      const cost = Math.max(0, Number(stop.price) || 0) + Math.max(0, Number(stop.transit?.cost) || 0);
      if (cost > remainingBudget) continue;
      days[dayIndex].push(stop);
      remainingBudget -= cost;
    }
  }
  return { destination: dest, days };
}

/* ============ Map View ============ */
function RealMapView({ stops }) {
  const mapRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current || !window.L) return undefined;
    const points = stops
      .map(stop => [Number(stop.lat), Number(stop.lng), stop])
      .filter(point => Number.isFinite(point[0]) && Number.isFinite(point[1]));
    if (!points.length) return undefined;

    const map = window.L.map(mapRef.current, { zoomControl: true, attributionControl: true });
    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    const latLngs = points.map(([lat, lng]) => [lat, lng]);
    window.L.polyline(latLngs, { color: "#e87a4f", weight: 4, dashArray: "8 7" }).addTo(map);
    points.forEach(([lat, lng, stop], index) => {
      window.L.marker([lat, lng])
        .addTo(map)
        .bindPopup(`<strong>${index + 1}. ${stop.name}</strong><br>${stop.time} · ${stop.duration}`);
    });
    map.fitBounds(window.L.latLngBounds(latLngs), { padding: [32, 32], maxZoom: 14 });
    return () => map.remove();
  }, [stops]);

  return <div ref={mapRef} className="leaflet-map" aria-label="真實地圖" />;
}

function MapView({ days, activeDay, onActiveDay }) {
  const stops = days[activeDay] || [];

  // Project lat/lng into the SVG box [40..960] x [40..480]
  const lats = stops.map(s => s.lat).filter(Boolean);
  const lngs = stops.map(s => s.lng).filter(Boolean);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  const pad = 0.005;
  const sx = (lng) => 60 + ((lng - minLng + pad) / (maxLng - minLng + pad * 2)) * 860;
  const sy = (lat) => 60 + (1 - (lat - minLat + pad) / (maxLat - minLat + pad * 2)) * 360;

  return (
    <div className="map-view">
      <div className="map-view__header">
        <div style={{ fontSize:14, fontWeight:700, color:"var(--ink-900)", display:"flex", alignItems:"center", gap:8 }}>
          <span style={{ fontSize:16 }}>🗺</span>
          Day {activeDay + 1} 路線地圖
        </div>
        <div style={{ fontSize:11.5, color:"var(--ink-500)" }}>
          {stops.length} 站 · 大圓圈為起點，依序連線
        </div>
      </div>

      <div className="map-canvas">
        <RealMapView stops={stops} />
        {/* Subtle grid background */}
        <svg viewBox="0 0 960 480" preserveAspectRatio="xMidYMid meet" className="map-canvas__svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#eae5d5" strokeWidth="1"/>
            </pattern>
            <pattern id="major" width="200" height="200" patternUnits="userSpaceOnUse">
              <path d="M 200 0 L 0 0 0 200" fill="none" stroke="#dad5c1" strokeWidth="1.2"/>
            </pattern>
          </defs>
          <rect width="960" height="480" fill="url(#grid)" />
          <rect width="960" height="480" fill="url(#major)" opacity="0.5" />

          {/* Decorative "rivers" — wavy lines */}
          <path d="M 0 280 Q 200 240 360 290 T 720 270 T 960 300"
            stroke="#cfe1de" strokeWidth="36" fill="none" opacity="0.5" strokeLinecap="round" />
          <path d="M 0 280 Q 200 240 360 290 T 720 270 T 960 300"
            stroke="#a0c4c0" strokeWidth="2" fill="none" opacity="0.7" strokeDasharray="4 4" />

          {/* Roads/major streets */}
          <line x1="160" y1="0" x2="160" y2="480" stroke="#ebe6d6" strokeWidth="3" />
          <line x1="540" y1="0" x2="540" y2="480" stroke="#ebe6d6" strokeWidth="3" />
          <line x1="0" y1="140" x2="960" y2="140" stroke="#ebe6d6" strokeWidth="3" />
          <line x1="0" y1="380" x2="960" y2="380" stroke="#ebe6d6" strokeWidth="3" />

          {/* Route line — dotted, accent colored */}
          {stops.length > 1 && (
            <polyline
              points={stops.map(s => `${sx(s.lng)},${sy(s.lat)}`).join(" ")}
              fill="none"
              stroke="var(--accent)"
              strokeWidth="3"
              strokeDasharray="8 6"
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity="0.9"
            />
          )}

          {/* Stops */}
          {stops.map((s, i) => (
            <g key={s.id} transform={`translate(${sx(s.lng)} ${sy(s.lat)})`}>
              <circle r="22" fill="#fff" stroke="var(--green-800)" strokeWidth="2.5" />
              <circle r="15" fill={i === 0 ? "var(--accent)" : "var(--green-800)"} />
              <text x="0" y="5" textAnchor="middle" fill="#fff" fontSize="14" fontWeight="700" fontFamily="Inter, sans-serif">{i + 1}</text>
            </g>
          ))}

          {/* First stop callout */}
          {stops[0] && (
            <g transform={`translate(${sx(stops[0].lng) + 30} ${sy(stops[0].lat) - 50})`}>
              <rect x="0" y="0" width="170" height="56" rx="8" fill="#fff" stroke="#e8e3d6" />
              <text x="14" y="22" fill="#14182a" fontSize="13" fontWeight="700">{stops[0].name}</text>
              <text x="14" y="42" fill="#6b7080" fontSize="11">起點 · {stops[0].time}</text>
            </g>
          )}
        </svg>

      </div>

      <div className="map-legend">
        <div><span className="map-legend__pin" style={{ background:"var(--accent)" }} /> 起點</div>
        <div><span className="map-legend__pin" style={{ background:"var(--green-800)" }} /> 中繼站</div>
        <div><span className="map-legend__line" /> 行程路線</div>
      </div>
    </div>
  );
}

function ListView({ days, activeDay, groupSize, splitMode, saved, onToggleSave, onRemove }) {
  const stops = days[activeDay] || [];
  return (
    <div className="list-view">
      <div style={{ display:"grid", gridTemplateColumns:"32px 1fr 80px 80px 100px 90px 60px", gap:14, padding:"10px 16px", fontSize:11, color:"var(--ink-500)", fontWeight:600, letterSpacing:"0.06em", textTransform:"uppercase", borderBottom:"1px solid var(--border)" }}>
        <span>#</span>
        <span>景點 / 餐廳</span>
        <span>類型</span>
        <span>時間</span>
        <span style={{ textAlign:"right" }}>費用</span>
        <span style={{ textAlign:"center" }}>動作</span>
      </div>
      {stops.map((s, i) => (
        <div key={s.id} className="list-view__row" style={{ display:"grid", gridTemplateColumns:"32px 1fr 80px 80px 100px 90px 60px", gap:14, padding:"14px 16px", alignItems:"center", borderBottom:"1px solid var(--border)" }}>
          <span style={{ fontFamily:"var(--font-display)", fontVariantNumeric:"tabular-nums", color:"var(--green-700)", fontWeight:700 }}>{String(i+1).padStart(2,"0")}</span>
          <div>
            <div style={{ fontWeight:600, fontSize:14, color:"var(--ink-900)" }}>{s.thumb} {s.name}</div>
            {s.tags.length > 0 && (
              <div style={{ fontSize:11.5, color:"var(--ink-500)", marginTop:2 }}>{s.tags.join(" · ")}</div>
            )}
          </div>
          <span className={`stop__category ${s.catCls || ""}`}>{s.catLabel}</span>
          <span style={{ fontSize:13, color:"var(--ink-700)", fontFamily:"var(--font-display)" }}>{s.time}</span>
          <span style={{ fontSize:12.5, color:"var(--ink-500)" }}>{s.duration}</span>
          <div style={{ textAlign:"right" }}>
            <div style={{ fontWeight:700, fontSize:14, color:"var(--ink-900)", fontFamily:"var(--font-display)" }}>
              {s.price > 0 ? `NT$${s.price.toLocaleString()}` : "免費"}
            </div>
            {splitMode && groupSize > 1 && s.price > 0 && (
              <div style={{ fontSize:10.5, color:"var(--ink-500)" }}>人均 ${Math.round(s.price/groupSize).toLocaleString()}</div>
            )}
          </div>
          <div style={{ display:"flex", gap:6, justifyContent:"center" }}>
            <button
              className={`icon-btn ${saved && saved.has(s.id) ? "icon-btn--active" : ""}`}
              title={saved && saved.has(s.id) ? "取消收藏" : "加入收藏"}
              onClick={() => onToggleSave && onToggleSave(s)}>
              {saved && saved.has(s.id) ? "♥" : "♡"}
            </button>
            <button
              className="icon-btn icon-btn--danger"
              title="從行程中移除"
              onClick={() => onRemove && onRemove(s, i)}>×</button>
          </div>
        </div>
      ))}
      {stops.length === 0 && (
        <div style={{ padding:"40px 24px", textAlign:"center", color:"var(--ink-500)", fontSize:13 }}>
          這一天還沒有景點 — 加幾個吧！
        </div>
      )}
    </div>
  );
}

/* ============ Timeline View ============ */
function TimelineView({ days, activeDay, groupSize, splitMode, onReorder }) {
  const dragRef = useRef({ from: null });
  const [dragIds, setDragIds] = useState({ dragging: null, over: null });
  const stops = days[activeDay] || [];

  const handleDragStart = (idx) => (e) => {
    dragRef.current.from = idx;
    setDragIds({ dragging: stops[idx].id, over: null });
    e.dataTransfer.effectAllowed = "move";
  };
  const handleDragOver = (idx) => (e) => {
    e.preventDefault();
    if (dragRef.current.from === null || dragRef.current.from === idx) return;
    setDragIds(prev => ({ ...prev, over: stops[idx].id }));
  };
  const handleDrop = (idx) => (e) => {
    e.preventDefault();
    const from = dragRef.current.from;
    if (from === null || from === idx) return;
    onReorder(from, idx);
    dragRef.current = { from: null };
    setDragIds({ dragging: null, over: null });
  };
  const handleDragEnd = () => {
    dragRef.current = { from: null };
    setDragIds({ dragging: null, over: null });
  };

  return (
    <div className="itinerary">
      {stops.map((stop, i) => (
        <React.Fragment key={stop.id}>
          <div className={`stop ${dragIds.dragging === stop.id ? "dragging" : ""} ${dragIds.over === stop.id ? "drag-over" : ""}`}
            draggable
            onDragStart={handleDragStart(i)}
            onDragOver={handleDragOver(i)}
            onDrop={handleDrop(i)}
            onDragEnd={handleDragEnd}>
            <div className="stop__index">{i + 1}</div>
            <div className="stop__handle">⠿</div>
            <div className="stop__thumb stop__thumb--stripe">
              <span style={{ fontSize:30 }}>{stop.thumb}</span>
            </div>
            <div className="stop__body">
              <div className="stop__title">
                <span>{stop.name}</span>
                <span className={`stop__category ${stop.catCls || ""}`}>{stop.catLabel}</span>
              </div>
              <div className="stop__meta">
                <span>🕘 {stop.time}</span>
                <span className="dot" />
                <span>{stop.duration}</span>
                {stop.tags.length > 0 && (
                  <>
                    <span className="dot" />
                    <span>{stop.tags.join(" · ")}</span>
                  </>
                )}
              </div>
            </div>
            <div style={{ textAlign:"right" }}>
              <div className="stop__price">{stop.price > 0 ? `NT$${stop.price.toLocaleString()}` : "免費"}</div>
              {splitMode && groupSize > 1 && stop.price > 0 && (
                <div className="stop__price-sub">人均 NT${Math.round(stop.price / groupSize).toLocaleString()}</div>
              )}
            </div>
          </div>

          {i < stops.length - 1 && stop.transit && (
            <div className="transit">
              <div className="transit__pill">
                <span>{stop.transit.mode === "步行" ? "🚶" : stop.transit.mode === "捷運" ? "🚇" : stop.transit.mode === "公車" || stop.transit.mode === "客運" ? "🚌" : stop.transit.mode === "火車" || stop.transit.mode === "台鐵" ? "🚆" : stop.transit.mode === "高鐵" ? "🚄" : "🚍"}</span>
                {stop.transit.mode} {stop.transit.time}
              </div>
              {stop.transit.cost > 0 && (
                <span style={{ fontSize:11.5, color:"var(--ink-500)" }}>NT${stop.transit.cost}</span>
              )}
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

/* ============ Results Page ============ */
function ResultsPage({ form, onBack, onSave, savedAlready, onToast }) {
  const [databasePlaces, setDatabasePlaces] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [hotelCount, setHotelCount] = useState(null);
  useEffect(() => {
    setDataLoading(true);
    fetch(`/api/data/places?destination=${encodeURIComponent(form.destination)}&limit=200`)
      .then(response => response.json())
      .then(payload => setDatabasePlaces(payload.places || []))
      .catch(() => setDatabasePlaces([]))
      .finally(() => setDataLoading(false));
  }, [form.destination]);
  useEffect(() => {
    fetch(`/api/data/places?destination=${encodeURIComponent(form.destination)}&type=${encodeURIComponent("飯店")}&limit=1`)
      .then(response => response.json())
      .then(payload => setHotelCount(payload.count || 0))
      .catch(() => setHotelCount(null));
  }, [form.destination]);
  const initialData = useMemo(() => buildItinerary(form, databasePlaces), [form, databasePlaces]);
  const [days, setDays] = useState(initialData.days);
  const [activeDay, setActiveDay] = useState(0);
  const [view, setView] = useState("timeline");      // timeline | map | list
  const [savedSpots, setSavedSpots] = useState(() => new Set());

  useEffect(() => {
    if (!dataLoading && databasePlaces.length > 0) {
      setDays(initialData.days);
      setActiveDay(0);
    }
  }, [dataLoading, databasePlaces, initialData]);

  const totalSpent = useMemo(() => {
    return days.reduce((sum, d) => sum + d.reduce((s, st) => s + st.price + (st.transit?.cost || 0), 0), 0);
  }, [days]);
  const spentPct = Math.min(100, (totalSpent / form.budget) * 100);
  const isOver = totalSpent > form.budget;
  const remaining = form.budget - totalSpent;

  const catTotals = useMemo(() => {
    const t = { lodging: 0, food: 0, transport: 0, attractions: 0 };
    days.forEach(d => d.forEach(s => {
      if (s.cat === "住宿") t.lodging += s.price;
      else if (s.cat === "美食") t.food += s.price;
      else t.attractions += s.price;
      t.transport += s.transit?.cost || 0;
    }));
    return t;
  }, [days]);

  const dayTotal = useMemo(() => {
    return (days[activeDay] || []).reduce((s, st) => s + st.price + (st.transit?.cost || 0), 0);
  }, [days, activeDay]);

  const handleReorder = (from, to) => {
    const updated = [...days];
    const list = [...updated[activeDay]];
    const [moved] = list.splice(from, 1);
    list.splice(to, 0, moved);
    updated[activeDay] = list;
    setDays(updated);
  };

  const handleToggleSave = (stop) => {
    setSavedSpots(prev => {
      const next = new Set(prev);
      if (next.has(stop.id)) {
        next.delete(stop.id);
        onToast && onToast(`已從收藏移除「${stop.name}」`);
      } else {
        next.add(stop.id);
        onToast && onToast(`已加入收藏：「${stop.name}」`);
      }
      return next;
    });
  };

  const handleRemoveStop = (stop, idx) => {
    const updated = [...days];
    updated[activeDay] = updated[activeDay].filter((_, i) => i !== idx);
    setDays(updated);
    onToast && onToast(`已從 Day ${activeDay + 1} 移除「${stop.name}」`);
  };

  return (
    <>
      <div className="page-header">
        <div className="page-header__title">
          <div className="breadcrumb">
            <button onClick={onBack} style={{ background:"transparent", border:0, color:"var(--ink-500)", cursor:"pointer", padding:0 }}>我的行程</button>
            <span>›</span>
            <button onClick={onBack} style={{ background:"transparent", border:0, color:"var(--ink-500)", cursor:"pointer", padding:0 }}>AI 規劃</button>
            <span>›</span>
            <span style={{ color: "var(--green-700)", fontWeight: 600 }}>行程結果</span>
          </div>
          <h1>{initialData.destination}{form.days === 1 ? "一日遊" : `${form.days}日經典遊`}</h1>
          <div className="page-header__sub">
            5/10 - 5/{10 + form.days - 1} · {form.days} 天 · {days.reduce((s,d) => s + d.length, 0)} 個景點 · {form.groupSize} 人同行 ·
            <span style={{ color: isOver ? "var(--warn)" : "var(--green-600)", fontWeight: 600 }}>
              {" "}
              {isOver ? `超支 NT$ ${Math.abs(remaining).toLocaleString()}` : `預算內 · 剩 NT$ ${remaining.toLocaleString()}`}
            </span>
          </div>
        </div>
        <div style={{ display:"flex", gap:8 }}>
          <button className="btn btn--ghost" onClick={onBack}>← 修改條件</button>
          <button className="btn btn--ghost">📤 分享</button>
          <button className="btn btn--primary" onClick={() => onSave && onSave({ form, days, totalSpent })} disabled={savedAlready}>
            {savedAlready ? "✓ 已儲存" : "★ 儲存行程"}
          </button>
        </div>
      </div>

      {/* View tabs — like reference image */}
      <div className="view-tabs">
        <button className={`view-tabs__btn ${view === "timeline" ? "view-tabs__btn--active" : ""}`} onClick={() => setView("timeline")}>
          <span>📜</span> 時間軸
        </button>
        <button className={`view-tabs__btn ${view === "map" ? "view-tabs__btn--active" : ""}`} onClick={() => setView("map")}>
          <span>🗺</span> 地圖
        </button>
        <button className={`view-tabs__btn ${view === "list" ? "view-tabs__btn--active" : ""}`} onClick={() => setView("list")}>
          <span>≡</span> 景點列表
        </button>
        <div className="view-tabs__hint">提示：在地圖視圖中查看路線最佳化</div>
      </div>

      <div className="results-grid">
        {/* LEFT: Content area */}
        <div>
          <div className="day-tabs">
            {days.map((d, i) => (
              <button key={i}
                className={`day-tabs__btn ${activeDay === i ? "day-tabs__btn--active" : ""}`}
                onClick={() => setActiveDay(i)}>
                Day {i + 1}
                <span className="count">{d.length}</span>
              </button>
            ))}
          </div>

          {dataLoading && (
            <div className="card" style={{ marginTop: 16, padding: 24, textAlign: "center", color: "var(--ink-500)" }}>
              正在查核 {form.destination} 的資料庫景點...
            </div>
          )}
          {!dataLoading && databasePlaces.length === 0 && (
            <div className="card" style={{ marginTop: 16, padding: 24, textAlign: "center", color: "var(--warn)" }}>
              資料庫目前沒有符合「{form.destination}」的景點，請修改目的地。
            </div>
          )}

          {view === "timeline" && (
            <TimelineView
              days={days}
              activeDay={activeDay}
              groupSize={form.groupSize}
              splitMode={form.splitMode}
              onReorder={handleReorder}
            />
          )}
          {view === "map" && (
            <MapView
              days={days}
              activeDay={activeDay}
              onActiveDay={setActiveDay}
            />
          )}
          {view === "list" && (
            <ListView
              days={days}
              activeDay={activeDay}
              groupSize={form.groupSize}
              splitMode={form.splitMode}
              saved={savedSpots}
              onToggleSave={handleToggleSave}
              onRemove={handleRemoveStop}
            />
          )}
        </div>

        {/* RIGHT: Budget & insights */}
        <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
          <div className="budget-gauge">
            <div className="budget-gauge__top">
              <div className="budget-gauge__used">NT${totalSpent.toLocaleString()}</div>
              <div className="budget-gauge__total">/ NT${form.budget.toLocaleString()}</div>
            </div>
            <div className="budget-gauge__bar">
              <div className="budget-gauge__fill" style={{ width: `${spentPct}%` }} />
            </div>
            <div className="budget-gauge__remain">
              <span>已使用 {Math.round(spentPct)}%</span>
              {isOver ? (
                <span className="over">超支 NT${Math.abs(remaining).toLocaleString()}</span>
              ) : (
                <span className="ok">剩餘 NT${remaining.toLocaleString()}</span>
              )}
            </div>
          </div>

          <div className="card">
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:10 }}>
              <div style={{ fontWeight:700, fontSize:14 }}>實際分配</div>
              <span style={{ fontSize:11, color:"var(--ink-500)" }}>Day {activeDay + 1} · NT${dayTotal.toLocaleString()}</span>
            </div>
            <div className="legend">
              <div className="legend__row">
                <span className="legend__dot" style={{ background: "#2a3a64" }} />
                <span className="legend__label">住宿</span>
                <span className="legend__pct">{Math.round((catTotals.lodging / form.budget) * 100)}%</span>
                <span className="legend__amt">NT${catTotals.lodging.toLocaleString()}</span>
              </div>
              <div className="legend__row">
                <span className="legend__dot" style={{ background: "#e87a4f" }} />
                <span className="legend__label">餐飲</span>
                <span className="legend__pct">{Math.round((catTotals.food / form.budget) * 100)}%</span>
                <span className="legend__amt">NT${catTotals.food.toLocaleString()}</span>
              </div>
              <div className="legend__row">
                <span className="legend__dot" style={{ background: "#6b85ad" }} />
                <span className="legend__label">交通</span>
                <span className="legend__pct">{Math.round((catTotals.transport / form.budget) * 100)}%</span>
                <span className="legend__amt">NT${catTotals.transport.toLocaleString()}</span>
              </div>
              <div className="legend__row">
                <span className="legend__dot" style={{ background: "#b89758" }} />
                <span className="legend__label">景點門票</span>
                <span className="legend__pct">{Math.round((catTotals.attractions / form.budget) * 100)}%</span>
                <span className="legend__amt">NT${catTotals.attractions.toLocaleString()}</span>
              </div>
            </div>
            {hotelCount === 0 && (
              <div style={{ marginTop: 12, padding: "10px 12px", borderRadius: 8, background: "var(--surface-2)", color: "var(--ink-500)", fontSize: 12 }}>
                此目的地目前沒有飯店資料，住宿費用未納入；請先更新住宿資料來源。
              </div>
            )}
          </div>

          <div className={`smart-hint ${isOver ? "smart-hint--over" : ""}`}>
            <div className="smart-hint__ic">{isOver ? "⚠" : "✓"}</div>
            <div>
              <div className="smart-hint__title">{isOver ? "預算超支提醒" : "預算控制良好"}</div>
              <div className="smart-hint__body">
                {isOver
                  ? "建議刪除 1-2 個高花費景點或改用大眾運輸。"
                  : "目前行程仍有緩衝空間，可加入 1-2 個熱門景點。"}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

window.ResultsPage = ResultsPage;
