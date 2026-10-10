/* global React */
const { useState, useEffect, useRef } = React;

function GeneratingOverlay({ form, onDone }) {
  const [stepIdx, setStepIdx] = useState(0);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const timersRef = useRef([]);

  const steps = [
    {
      title: "搜尋符合的景點資料",
      detail: `從台灣景點資料庫中，過濾 ${form.destination} 附近的景點、餐廳與住宿`,
      logs: [
        "✓ 載入台灣旅遊資料庫",
        `→ 過濾「${form.destination}」周邊 24 公里內的資源`,
        "✓ 載入 2,184 個景點 / 1,672 間餐廳 / 318 間住宿",
        `→ 比對偏好標籤：${(form.interests || []).join(" · ")}`,
        "✓ 篩選出 218 個高匹配候選",
      ],
    },
    {
      title: "分析預算與最佳配置",
      detail: `將 NT$ ${form.budget.toLocaleString()} 分配到住宿 / 餐飲 / 交通 / 景點`,
      logs: [
        `→ 依「${window.getTier(form.budget).name}」等級套用配比`,
        `✓ 住宿池：篩選 NT$ ${Math.round(form.budget * 0.38 / form.days).toLocaleString()}/晚 以下選項`,
        "✓ 計算高鐵 / 捷運 / 公車 實際票價",
        "→ 預留 5% 機動緩衝",
        "✓ 預算配置完成",
      ],
    },
    {
      title: "排程每日行程與動線",
      detail: `安排 ${form.days * 4} 個景點，最小化交通時間`,
      logs: [
        `→ 對 ${form.days} 天進行最佳化排序`,
        "✓ 套用路徑最佳化演算法",
        `✓ 每日插入 ${form.style === "packed" ? "6-7" : form.style === "leisurely" ? "3-4" : "4-5"} 個景點`,
        "→ 對齊開放時間 / 用餐時段",
        "✓ 行程生成完成 — 為你打開預覽",
      ],
    },
  ];

  useEffect(() => {
    const totalDuration = 6800;            // total ms
    const perStep = totalDuration / steps.length;

    const start = Date.now();
    const progressTimer = setInterval(() => {
      const elapsed = Date.now() - start;
      setProgress(Math.min(100, (elapsed / totalDuration) * 100));
    }, 60);
    timersRef.current.push(progressTimer);

    steps.forEach((step, sIdx) => {
      const stepStart = sIdx * perStep;
      const t1 = setTimeout(() => setStepIdx(sIdx), stepStart);
      timersRef.current.push(t1);

      step.logs.forEach((line, lIdx) => {
        const t = stepStart + ((lIdx + 1) / step.logs.length) * perStep * 0.9;
        const t2 = setTimeout(() => {
          setLogs(prev => [...prev.slice(-3), { line, sIdx, lIdx }]);
        }, t);
        timersRef.current.push(t2);
      });
    });

    const finish = setTimeout(() => {
      setProgress(100);
      setStepIdx(steps.length); // all done
      onDone();
    }, totalDuration + 200);
    timersRef.current.push(finish);

    return () => timersRef.current.forEach(clearTimeout);
  }, []);

  return (
    <div className="overlay">
      <div className="overlay__card">
        <div style={{ textAlign:"center", marginBottom:20 }}>
          <div style={{
            display:"inline-flex", alignItems:"center", gap:8,
            background:"var(--green-50)", color:"var(--green-700)",
            padding:"6px 14px", borderRadius:999,
            fontSize:11.5, fontWeight:700, letterSpacing:"0.14em", textTransform:"uppercase"
          }}>
            <span className="spinner" style={{ borderColor:"rgba(31,77,58,0.3)", borderTopColor:"var(--green-700)" }} />
            AI 規劃中
          </div>
        </div>
        <h2 className="overlay__title">為你客製 {form.destination} {form.days} 天行程</h2>
        <p className="overlay__sub">預算 NT$ {form.budget.toLocaleString()} · {form.groupSize} 人同行</p>

        <div className="gen-progress">
          <div className="gen-progress__bar" style={{ width: `${progress}%` }} />
        </div>

        <div className="gen-steps">
          {steps.map((s, i) => {
            const state = i === stepIdx ? "active" : i < stepIdx ? "done" : "pending";
            return (
              <div key={i} className={`gen-step gen-step--${state}`}>
                <div className="gen-step__ic">
                  {state === "done" ? "✓" : state === "active" ? <span className="spinner" /> : i + 1}
                </div>
                <div>
                  <div className="gen-step__title">{s.title}</div>
                  <div className="gen-step__detail">{s.detail}</div>
                </div>
                <div className="gen-step__count">
                  {state === "done" ? "完成" : state === "active" ? "進行中" : "等待"}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{
          background:"var(--surface-2)",
          border:"1px solid var(--border)",
          borderRadius:12,
          padding:"14px 16px"
        }}>
          <div className="gen-log">
            {logs.map((l, i) => (
              <div className="gen-log__line" key={`${l.sIdx}-${l.lIdx}`}>
                <span style={{ color: "var(--ink-400)" }}>{String(i).padStart(2, "0")} </span>
                <span className={l.line.startsWith("✓") ? "ok" : ""}>{l.line}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

window.GeneratingOverlay = GeneratingOverlay;
