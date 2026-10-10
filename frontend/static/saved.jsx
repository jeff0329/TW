/* global React */
const { useState } = React;

function AddToTripModal({ place, trips, onAdd, onClose }) {
  return (
    <div className="overlay" style={{ alignItems:"flex-start", paddingTop:"10vh" }} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="overlay__card" style={{ width:"min(460px, 100%)", padding:0, overflow:"hidden" }}>
        <div style={{ padding:"20px 22px 14px", borderBottom:"1px solid var(--border)", display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:12 }}>
          <div>
            <div style={{ fontSize:11, fontWeight:700, color:"var(--accent)", letterSpacing:"0.14em", textTransform:"uppercase" }}>加入景點</div>
            <div style={{ fontSize:18, fontWeight:700, marginTop:4 }}>{place.icon} {place.name}</div>
            <div style={{ fontSize:12, color:"var(--ink-500)", marginTop:2 }}>{place.city} · {place.area} · {place.price === 0 ? "免費" : `NT$${place.price.toLocaleString()}`}</div>
          </div>
          <button onClick={onClose} style={{ width:28, height:28, borderRadius:8, border:"1px solid var(--border)", background:"var(--surface)", color:"var(--ink-500)", cursor:"pointer", fontSize:14 }}>×</button>
        </div>

        <div style={{ padding:"14px 22px 6px", fontSize:12, color:"var(--ink-500)" }}>選擇要加入的行程：</div>

        <div style={{ maxHeight:340, overflowY:"auto", padding:"0 14px 14px" }}>
          {trips.length === 0 ? (
            <div style={{ textAlign:"center", padding:"24px 12px", color:"var(--ink-500)", fontSize:13 }}>
              還沒有行程，先到「AI 規劃」建立一個吧
            </div>
          ) : trips.map(t => (
            <button key={t.id}
              onClick={() => onAdd(t.id)}
              style={{
                display:"grid", gridTemplateColumns:"32px 1fr auto", gap:12,
                width:"100%", padding:"12px 14px",
                borderRadius:10, border:"1px solid var(--border)",
                background:"var(--surface-2)",
                marginBottom:6,
                cursor:"pointer", textAlign:"left",
              }}>
              <div style={{ width:32, height:32, borderRadius:8, background:"var(--green-100)", display:"grid", placeItems:"center", fontSize:14 }}>📍</div>
              <div>
                <div style={{ fontSize:13.5, fontWeight:600, color:"var(--ink-900)" }}>{t.title}</div>
                <div style={{ fontSize:11.5, color:"var(--ink-500)", marginTop:2 }}>{t.sub}</div>
              </div>
              <span style={{ fontSize:12, color:"var(--green-700)", fontWeight:600, alignSelf:"center" }}>加入 →</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function SavedPage({ trips, onAddToTrip }) {
  const [tab, setTab] = useState("all");
  const [picking, setPicking] = useState(null);   // place being added
  const [removedIds, setRemovedIds] = useState(() => new Set());

  const items = [
    { id:"p1", type:"culture",name:"龍山寺",     city:"台北", area:"萬華區", tags:["古蹟","必訪"], rating:4.7, price:0, icon:"⛩️" },
    { id:"p2", type:"food",   name:"鼎泰豐 信義店", city:"台北", area:"信義區", tags:["小籠包","米其林"], rating:4.6, price:850, icon:"🥟" },
    { id:"p3", type:"culture",name:"故宮博物院", city:"台北", area:"士林區", tags:["國寶"], rating:4.6, price:350, icon:"🏛️" },
    { id:"p4", type:"nature", name:"陽明山國家公園", city:"台北", area:"士林區", tags:["山景","賞花"], rating:4.5, price:0, icon:"🌋" },
    { id:"p5", type:"shop",   name:"西門町商圈",   city:"台北", area:"萬華區", tags:["購物","美食"], rating:4.3, price:0, icon:"🛍️" },
    { id:"p6", type:"hotel",  name:"圓山大飯店",   city:"台北", area:"中山區", tags:["經典"], rating:4.5, price:3200, icon:"🏨" },
    { id:"p7", type:"food",   name:"士林夜市",     city:"台北", area:"士林區", tags:["小吃","必訪"], rating:4.4, price:300, icon:"🍢" },
    { id:"p8", type:"nature", name:"九份老街",     city:"新北", area:"瑞芳區", tags:["山城","美景"], rating:4.6, price:300, icon:"⛩️" },
    { id:"p9", type:"culture",name:"中正紀念堂",   city:"台北", area:"中正區", tags:["歷史"], rating:4.4, price:0, icon:"🏛️" },
    { id:"p10",type:"food",   name:"永康街美食",   city:"台北", area:"大安區", tags:["在地"], rating:4.5, price:720, icon:"🍜" },
    { id:"p11",type:"nature", name:"太魯閣國家公園", city:"花蓮", area:"秀林鄉", tags:["峽谷"], rating:4.8, price:0, icon:"🏔️" },
    { id:"p12",type:"nature", name:"墾丁國家公園", city:"屏東", area:"恆春鎮", tags:["海岸","沙灘"], rating:4.6, price:0, icon:"🏖️" },
  ];

  const visibleItems = items.filter(item => !removedIds.has(item.id));
  const tabs = [
    { id:"all",     label:"全部",   count: visibleItems.length },
    { id:"culture", label:"文化古蹟", count: visibleItems.filter(i => i.type === "culture").length },
    { id:"food",    label:"美食餐廳", count: visibleItems.filter(i => i.type === "food").length },
    { id:"nature",  label:"自然景觀", count: visibleItems.filter(i => i.type === "nature").length },
    { id:"shop",    label:"購物商圈", count: visibleItems.filter(i => i.type === "shop").length },
    { id:"hotel",   label:"住宿",     count: visibleItems.filter(i => i.type === "hotel").length },
  ];

  const typeLabel = { culture:"文化", food:"美食", nature:"自然", shop:"購物", hotel:"住宿" };

  const filtered = tab === "all" ? visibleItems : visibleItems.filter(i => i.type === tab);

  const handleAdd = (tripId) => {
    onAddToTrip && onAddToTrip(picking, tripId);
    setPicking(null);
  };

  return (
    <>
      <div className="page-header">
        <div className="page-header__title">
          <h1>收藏清單</h1>
          <div className="page-header__sub">已收藏 {visibleItems.length} 個景點 · 點「加入行程」直接加進你的任一行程</div>
        </div>
        <div style={{ display:"flex", gap:8 }}>
          <button className="btn btn--primary">＋ 加入新景點</button>
        </div>
      </div>

      <div className="saved-tabs">
        {tabs.map(t => (
          <button key={t.id}
            className={`saved-tabs__btn ${tab === t.id ? "saved-tabs__btn--active" : ""}`}
            onClick={() => setTab(t.id)}>
            {t.label}
            <span className="count">{t.count}</span>
          </button>
        ))}
      </div>

      <div className="saved-grid">
        {filtered.map(p => (
          <div className="saved-card" key={p.id}>
            <div className={`saved-card__cover saved-card__cover--${p.type}`}>
              <span>{p.icon}</span>
              <div className="saved-card__cover-tag">{typeLabel[p.type] || ""}</div>
              <button className="saved-card__cover-fav" title="取消收藏"
                onClick={() => setRemovedIds(prev => new Set([...prev, p.id]))}>♥</button>
            </div>
            <div className="saved-card__body">
              <div className="saved-card__title">{p.name}</div>
              <div className="saved-card__sub">{p.city} · {p.area}</div>
              <div className="tag-row" style={{ marginTop:4 }}>
                {p.tags.map(t => <span className="tag" key={t}>{t}</span>)}
              </div>
              <div className="saved-card__rating">
                <span className="star">★</span> {p.rating.toFixed(1)} · {(1000 + p.name.charCodeAt(0) * 7).toLocaleString()} 評論
              </div>
            </div>
            <div className="saved-card__meta">
              <span>{p.price === 0 ? "價格未提供" : "票價 NT$" + p.price.toLocaleString()}</span>
              <button onClick={() => setPicking(p)} style={{ background:"transparent", border:0, color:"var(--green-700)", fontWeight:600, fontSize:12, cursor:"pointer", padding:0 }}>
                ＋ 加入行程
              </button>
            </div>
          </div>
        ))}
      </div>

      {picking && (
        <AddToTripModal
          place={picking}
          trips={trips}
          onAdd={handleAdd}
          onClose={() => setPicking(null)}
        />
      )}
    </>
  );
}

window.SavedPage = SavedPage;
