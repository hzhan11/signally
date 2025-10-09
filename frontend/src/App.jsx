import React, { useState, useEffect } from 'react';
import { TrendingUp, ChevronLeft, ChevronRight } from 'lucide-react';

export default function SignallyApp() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [stocks, setStocks] = useState([]); // array of {id,name,metadata}
  const [selectedTab, setSelectedTab] = useState(''); // will store id string
  const [loadingStocks, setLoadingStocks] = useState(true);
  const [stocksError, setStocksError] = useState(null);
  const [beijingNow, setBeijingNow] = useState(null); // store server string OR Date
  // highlights related state
  const [highlights, setHighlights] = useState([]); // raw items
  const [hitTrueDays, setHitTrueDays] = useState(new Set());
  const [hitFalseDays, setHitFalseDays] = useState(new Set());
  const [todayYMD, setTodayYMD] = useState(null); // 'YYYY-MM-DD'
  // New state for clicked date highlight details
  const [selectedHighlightDate, setSelectedHighlightDate] = useState(null); // 'YYYYMMDD'
  const [expandedReasons, setExpandedReasons] = useState(new Set()); // store highlight ids with expanded reason
  const [navView, setNavView] = useState('main'); // 'main' | 'about'

  // helper to normalize server time string to desired format
  const formatBeijingDisplay = (raw) => {
    if (!raw || typeof raw !== 'string') return '加载中...';
    // If ISO format like 2025-09-27T05:10:50.462245+08:00
    // 1. Replace 'T' with space
    // 2. Remove fractional seconds and timezone
    let s = raw.trim();
    if (s.includes('T')) {
      s = s.replace('T', ' ');
      // remove timezone part starting with '+' or 'Z'
      s = s.replace(/([.,]\d+)?([+\-]\d{2}:?\d{2}|Z)$/i, '');
    }
    // Now ensure we have at least YYYY-MM-DD HH:MM:SS
    // If fractional remains (in case different pattern), cut at first '.' after seconds
    const match = s.match(/^(\d{4}-\d{2}-\d{2})[\s](\d{2}:\d{2}:\d{2})/);
    if (match) {
      return `北京时间：${match[1]} ${match[2]}`;
    }
    // Fallback: if already space separated and length >=19
    if (s.length >= 19 && s[10] === ' ') {
      return `北京时间：${s.slice(0,19)}`;
    }
    return `北京时间：${s}`;
  };

  const formatHighlightDate = (ymd) => {
    if (!ymd || ymd.length !== 8) return ymd || '';
    return `${ymd.slice(0,4)}-${ymd.slice(4,6)}-${ymd.slice(6,8)}`;
  };

  const latestHighlight = (() => {
    if (!highlights || !highlights.length) return null;
    const sorted = [...highlights].sort((a,b)=> (b.datetime||'').localeCompare(a.datetime||''));
    return sorted[0];
  })();

  // Compute historical hit stats (exclude unavailable where hit is not boolean)
  const hitStats = (() => {
    if (!highlights || !highlights.length) return { total:0, hit:0 };
    let total = 0; let hit = 0;
    for (const h of highlights) {
      if (h && typeof h.hit === 'boolean') { total++; if (h.hit) hit++; }
    }
    return { total, hit };
  })();

  // Toggle reason expansion
  const toggleReason = (id) => {
    setExpandedReasons(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  // Filter highlights for selected date
  const selectedDateHighlights = selectedHighlightDate
    ? highlights.filter(h => h.datetime === selectedHighlightDate)
    : [];

  const renderLatestHighlightLine = () => {
    if (!selectedStock || !selectedStock.metadata || selectedStock.metadata.status !== 'active') return null;
    const snapshotDateDisplay = latestHighlight?.datetime ? formatHighlightDate(latestHighlight.datetime) : (todayYMD || '');
    if (!latestHighlight) {
      return (
        <div className="mx-auto w-full">
          <div className="bg-white border border-orange-300 rounded shadow-sm overflow-hidden">
            <div className="bg-orange-500 text-white px-3 py-2 text-sm font-semibold">{snapshotDateDisplay} 预测快照</div>
            <div className="px-4 py-6 text-center text-sm text-gray-400">敬请期待...</div>
          </div>
        </div>
      );
    }
    const { open_15min_price, last_close_price, conclusion, confidence, hit, reason } = latestHighlight;
    const openStr = (typeof open_15min_price === 'number' && open_15min_price !== -1) ? open_15min_price.toFixed(2) : '--';
    const closeStr = (typeof last_close_price === 'number' && last_close_price !== -1) ? last_close_price.toFixed(2) : '--';
    const confPct = (typeof confidence === 'number' && !isNaN(confidence)) ? `${Math.round(confidence * 100)}%` : '--';
    let hitLabel = '数据不足';
    let hitColor = 'text-gray-500';
    if (hit === true) { hitLabel = '命中'; hitColor = 'text-green-600 font-semibold'; }
    else if (hit === false) { hitLabel = '未中'; hitColor = 'text-red-600 font-semibold'; }
    const reasonText = reason || '--';

    return (
      <div className="mx-auto w-full">
        <div className="bg-white border border-orange-300 rounded shadow-sm overflow-hidden">
          {/* 标题栏: 预测快照 */}
          <div className="bg-orange-500 text-white px-3 py-2 text-sm font-semibold">
            {snapshotDateDisplay} 预测快照
          </div>
          {/* 内容主体 */}
          <div className="px-4 py-3 text-left">
            {/* 行1: 预测 / 置信度 / 结论 */}
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
              <div className="flex items-baseline gap-2 min-w-[90px]">
                <span className="text-gray-500">预测</span>
                <span className="font-semibold text-blue-600">{conclusion || '--'}</span>
              </div>
              <div className="flex items-baseline gap-2 min-w-[90px]">
                <span className="text-gray-500">置信度</span>
                <span className="font-semibold text-gray-800">{confPct}</span>
              </div>
              <div className="flex items-baseline gap-2 min-w-[90px]">
                <span className="text-gray-500">结论</span>
                <span className={hitColor}>{hitLabel}</span>
              </div>
            </div>
            {/* 行2: 预测依据 */}
            <div className="mt-3 text-xs sm:text-[13px] leading-relaxed text-gray-700">
              <span className="text-gray-500 mr-1">预测依据</span>{reasonText}
            </div>
            {/* 行3: 价格 (移至最后) */}
            <div className="mt-3 text-sm flex flex-wrap items-baseline gap-x-6 gap-y-1 tracking-wide">
              <div className="flex items-baseline gap-2">
                <span className="text-gray-500">开盘15分钟均值</span>
                <span className="font-semibold text-gray-800">{openStr}</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-gray-500">前交易日收盘</span>
                <span className="font-semibold text-gray-800">{closeStr}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // 优先使用环境变量；否则如果不是本机域名，尝试用当前访问域名推断后端端口 8000
  const derivedHost = (() => {
    try {
      if (typeof window !== 'undefined' && window.location) {
        const h = window.location.hostname;
        if (h && !['localhost','127.0.0.1','::1'].includes(h)) {
          return `${window.location.protocol}//${h}:8000`;
        }
      }
    } catch(_) {}
    return 'http://localhost:8000';
  })();
  const API_BASE = import.meta.env.VITE_API_BASE || derivedHost;

  // Fetch Beijing time from server /time (returns {"value": "YYYY-MM-DD HH:MM:SS"})
  useEffect(() => {
    let mounted = true;
    let initialized = false;
    async function fetchServerTime() {
      try {
        const res = await fetch(`${API_BASE}/time`, { cache: 'no-store' });
        if (!res.ok) throw new Error('time api error');
        const data = await res.json();
        const value = data?.value; // expected Beijing local string
        if (mounted) {
          setBeijingNow(value);
          if (value) setTodayYMD(value.split(' ')[0]);
          if (!initialized && value) {
            // set calendar base date
            const datePart = value.split(' ')[0]; // YYYY-MM-DD
            const [y,m,d] = datePart.split('-').map(Number);
            if (y && m && d) setCurrentDate(new Date(y, m-1, d));
            initialized = true;
          }
        }
      } catch (e) {
        if (mounted && beijingNow === null) {
          // fallback to client Beijing guess
          const now = new Date();
          const bj = new Date(now.getTime() + (8 * 60 + now.getTimezoneOffset()) * 60000);
            const pad = n => String(n).padStart(2,'0');
            const fallbackStr = `${bj.getFullYear()}-${pad(bj.getMonth()+1)}-${pad(bj.getDate())} ${pad(bj.getHours())}:${pad(bj.getMinutes())}:${pad(bj.getSeconds())}`;
            setBeijingNow(fallbackStr);
            setTodayYMD(`${bj.getFullYear()}-${pad(bj.getMonth()+1)}-${pad(bj.getDate())}`);
            setCurrentDate(new Date(bj.getFullYear(), bj.getMonth(), bj.getDate()));
        }
      }
    }
    // initial fetch
    fetchServerTime();
    // periodic refresh every 5s (adjust if needed)
    const id = setInterval(fetchServerTime, 5000);
    return () => { mounted = false; clearInterval(id); };
  }, [API_BASE]);

  // Fetch stocks (unchanged)
  useEffect(() => {
    let mounted = true;
    async function fetchStocks() {
      setLoadingStocks(true);
      setStocksError(null);
      try {
        const res = await fetch(`${API_BASE}/api/v1/stocks/list`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const list = Array.isArray(data) ? data : Object.values(data);
        const normalized = list.map(item => {
          if (!item) return null;
            if (typeof item === 'string') return { id: item, name: item, metadata: {} };
            return {
              id: item.id ?? (item.metadata && item.metadata.id) ?? String(item.name ?? ''),
              name: item.name ?? (item.metadata && item.metadata.name) ?? String(item.id ?? ''),
              metadata: item.metadata ?? {},
            };
        }).filter(Boolean);
        if (mounted) {
          setStocks(normalized);
          if (!selectedTab && normalized.length > 0) setSelectedTab(normalized[0].id);
        }
      } catch (err) {
        if (mounted) setStocksError(err.message || String(err));
      } finally {
        if (mounted) setLoadingStocks(false);
      }
    }
    fetchStocks();
    return () => { mounted = false };
  }, [API_BASE, selectedTab]);

  // Fetch highlights when selectedTab changes
  useEffect(() => {
    let mounted = true;
    if (!selectedTab) return;
    async function fetchHighlights() {
      try {
        // primary path
        let res = await fetch(`${API_BASE}/api/v1/highlights/${selectedTab}`);
        if (!res.ok) {
          // fallback path (user example had /list/)
            res = await fetch(`${API_BASE}/api/v1/highlights/list/${selectedTab}`);
        }
        if (!res.ok) throw new Error('highlights fetch failed');
        const data = await res.json();
        if (!mounted) return;
        const items = data?.items || [];
        setHighlights(items);
      } catch (e) {
        if (mounted) setHighlights([]);
      }
    }
    fetchHighlights();
    return () => { mounted = false };
  }, [API_BASE, selectedTab]);

  // Derive colored day sets whenever month, highlights, or currentDate change
  useEffect(() => {
    const trueSet = new Set();
    const falseSet = new Set();
    if (highlights && highlights.length) {
      highlights.forEach(h => {
        const dt = h.datetime; // 'YYYYMMDD'
        if (!dt || dt.length !== 8) return;
        const y = Number(dt.slice(0,4));
        const m = Number(dt.slice(4,6));
        const d = Number(dt.slice(6,8));
        if (y === currentDate.getFullYear() && (m-1) === currentDate.getMonth()) {
          if (h.hit === true) trueSet.add(d);
          else if (h.hit === false) falseSet.add(d);
        }
      });
    }
    setHitTrueDays(trueSet);
    setHitFalseDays(falseSet);
  }, [highlights, currentDate]);

  const formatDate = (date) => {
    const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
  };

  // Calendar helpers
  const getDaysInMonth = (date) => new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  const getFirstWeekdayOfMonth = (date) => new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  const navigateMonth = (direction) => setCurrentDate(prev => { const nd = new Date(prev); nd.setMonth(prev.getMonth()+direction); return nd; });

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(currentDate);
    const firstWeekday = getFirstWeekdayOfMonth(currentDate);
    const cells = [];
    for (let i=0;i<firstWeekday;i++) cells.push(<div key={`e-${i}`} className="h-10"/>);
    // Determine today day number (only if in same displayed month)
    let todayDay = null;
    if (todayYMD) {
      const [ty,tm,td] = todayYMD.split('-').map(Number);
      if (ty === currentDate.getFullYear() && (tm-1) === currentDate.getMonth()) todayDay = td;
    }
    for (let day=1; day<=daysInMonth; day++) {
      let baseClass = "h-10 flex items-center justify-center text-xs sm:text-[13px] font-medium rounded transition-colors select-none";
      let colorClass = "text-gray-700";
      let interactive = false;
      if (todayDay === day) { colorClass = "bg-black text-white"; interactive = true; }
      else if (hitTrueDays.has(day)) { colorClass = "bg-green-500 text-white"; interactive = true; }
      else if (hitFalseDays.has(day)) { colorClass = "bg-red-500 text-white"; interactive = true; }
      const isSelected = selectedHighlightDate && interactive && selectedHighlightDate === `${currentDate.getFullYear()}${String(currentDate.getMonth()+1).padStart(2,'0')}${String(day).padStart(2,'0')}`;
      if (isSelected) colorClass += " ring-2 ring-offset-2 ring-orange-400";
      const handleClick = () => {
        if (!interactive) return;
        const ymd = `${currentDate.getFullYear()}${String(currentDate.getMonth()+1).padStart(2,'0')}${String(day).padStart(2,'0')}`;
        setSelectedHighlightDate(prev => prev === ymd ? null : ymd);
      };
      cells.push(
        <div
          key={day}
          className={`${baseClass} ${colorClass} ${interactive ? 'cursor-pointer hover:brightness-110' : ''}`}
          onClick={handleClick}
          title={interactive ? '查看当日预测详情' : ''}
        >
          {day}
        </div>
      );
    }
    return cells;
  };

  const selectedStock = stocks.find(s => s.id === selectedTab) || null;

  const renderHighlightsTable = () => {
    if (!selectedHighlightDate || !selectedDateHighlights.length) return null;
    return (
      <div className="px-4 pb-6">
        <div className="bg-white border border-orange-300 rounded shadow-sm overflow-hidden">
          {/* 标题栏改为居中显示 */}
          <div className="bg-orange-500 text-white px-3 py-2 text-sm font-semibold relative">
            <div className="text-center">{formatHighlightDate(selectedHighlightDate)} 预测详情</div>
            <button
              onClick={() => setSelectedHighlightDate(null)}
              className="text-xs bg-white/20 hover:bg-white/30 px-2 py-1 rounded absolute right-3 top-1/2 -translate-y-1/2"
            >关闭</button>
          </div>
          <div className="divide-y divide-orange-100">
            {selectedDateHighlights.map(h => {
              const confPct = (typeof h.confidence === 'number' && !isNaN(h.confidence)) ? `${Math.round(h.confidence*100)}%` : '--';
              const openStr = (typeof h.open_15min_price === 'number' && h.open_15min_price !== -1) ? h.open_15min_price.toFixed(2) : '--';
              const closeStr = (typeof h.last_close_price === 'number' && h.last_close_price !== -1) ? h.last_close_price.toFixed(2) : '--';
              let hitLabel = '数据不足';
              let hitColor = 'text-gray-500';
              if (h.hit === true) { hitLabel = '命中'; hitColor = 'text-green-600 font-semibold'; }
              else if (h.hit === false) { hitLabel = '未中'; hitColor = 'text-red-600 font-semibold'; }
              const full = h.reason || '';
              const truncated = full.length > 80 ? full.slice(0,80) + '…' : full;
              const expanded = expandedReasons.has(h.id);
              return (
                <div key={h.id} className="px-4 py-3 bg-white hover:bg-orange-50/40 transition-colors">
                  {/* 行1: 预测 / 置信度 / 命中 */}
                  <div className="flex flex-wrap gap-x-10 gap-y-2 text-sm">
                    <div className="flex items-baseline gap-2">
                      <span className="text-gray-500">预测</span>
                      <span className="font-semibold text-blue-600">{h.conclusion || '--'}</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-gray-500">置信度</span>
                      <span className="font-semibold text-gray-800">{confPct}</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-gray-500">结论</span>
                      <span className={hitColor}>{hitLabel}</span>
                    </div>
                  </div>
                  {/* 行2: 预测依据 */}
                  <div className="mt-3 text-xs sm:text-[13px] leading-relaxed text-gray-700">
                    <span className="text-gray-500 mr-2">预测依据</span>
                    {expanded ? full || '--' : truncated || '--'}
                    {full.length > 80 && (
                      <button
                        onClick={() => toggleReason(h.id)}
                        className="ml-2 text-orange-600 hover:text-orange-500 underline"
                      >{expanded ? '收起' : '展开'}</button>
                    )}
                  </div>
                  {/* 行3: 价格 (移到最后) */}
                  <div className="mt-3 text-sm flex flex-wrap items-baseline gap-x-6 gap-y-1">
                    <div className="flex items-baseline gap-2">
                      <span className="text-gray-500">开盘15分钟均值</span>
                      <span className="font-semibold text-gray-800">{openStr}</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-gray-500">前交易日收盘</span>
                      <span className="font-semibold text-gray-800">{closeStr}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const AboutContent = () => (
    <div className="px-5 py-4 text-sm text-gray-800 leading-relaxed space-y-4">
      <h1 className="text-center text-lg font-semibold text-orange-600">关于心歌 · Signally 简介</h1>
      <p>Signally 是一个围绕日内与短周期市场信号评估的轻量级展示与验证系统，目标是以极低摩擦让使用者快速获知：今天系统关注什么、结论是什么、过去命中率如何。它把“生成→展示→验证”串成闭环：最新预测快照突出当前判断；彩色日历以命中/未中/今日三色编码历史；日期点选即可下钻查看当日多条预测详情；顶部实时显示统一的北京时间，保证多端一致性。</p>
      <p>前端采用 React + Vite + TailwindCSS，单页结构紧凑：Tab 切换标的；“总命中率”即时反馈整体可靠度；预测快照包含方向结论、置信度、命中回填、开盘 15 分钟均值与前收盘对比，以及精炼的预测依据。未激活标的给出“建设中”占位，支持按阶段逐步扩容。所有字号与间距经过统一收敛，使移动端阅读更聚焦。</p>
      <p>后端使用 FastAPI 暴露 /time、/api/v1/stocks、/api/v1/highlights 等 REST 接口，并通过 CORS 全开放以支持前后端独立部署。多进程启动脚本整合了数据存储 (ChromaDB)、信息采集、信号预测、交易执行等潜在子服务，为未来丰富策略与数据来源预留了结构。ChromaDB 可承载向量化特征或语义检索，为引入新闻情绪、公告要素、LLM 解释打下基础。</p>
      <p>系统的数据结构以最小必要字段（结论、置信度、价格基线、命中标记、理由文本、日期键）表达核心信息，有利于后续增加：更精细的命中分类（方向/幅度/时效）、多模型融合得分、风险异常提示、用户反馈闭环、策略回测可视化组件及多语言输出。前端动态推断后端地址（若非 localhost 自动绑定当前域名:8000），加上服务监听 0.0.0.0，方便局域网手机调试。</p>
      <p>价值体现在三点：1）透明：任何一条预测都被时间戳与命中结果固化，可回顾、可审计；2）轻量：不强制复杂的账户、工作流，即开即看；3）可扩展：松耦合接口 + 语义/向量层预留，使“加一个数据源或策略”保持低成本。未来将探索：理由自动摘要、多层置信度拆解、实时异常波动提醒、细粒度结果标签、以及人机协同迭代。</p>
      <p>总体而言，Signally 已形成一个清晰、紧凑、可演进的“预测洞察面板”，为快速试错和策略迭代提供持续反馈底座。欢迎提出想法或加入共建。</p>
      <div className="pt-2 text-center">
        <button onClick={() => setNavView('main')} className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded text-sm">返回主页</button>
      </div>
    </div>
  );

  const ContactContent = () => (
    <div className="px-6 py-8 text-center text-sm text-gray-800 space-y-4">
      <h1 className="text-lg font-semibold text-orange-600">联系作者</h1>
      <div className="inline-block bg-orange-50 border border-orange-200 rounded px-6 py-4 text-left shadow-sm">
        <p className="font-medium">QQ: <span className="font-mono">22321262</span></p>
      </div>
      <div>
        <button onClick={() => setNavView('main')} className="mt-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded text-sm">返回主页</button>
      </div>
    </div>
  );

  // Conditional rendering based on navView state
  return (
    <div className="min-h-screen bg-gray-50 flex justify-center">
      <div className="w-full max-w-md bg-white shadow-lg">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-400 to-orange-500 px-4 text-white">
          <div className="flex items-center justify-between gap-4 min-h-[56px]">
            <div className="flex items-center gap-2 leading-none">
              <span className="text-xl font-bold leading-none flex items-center">Signally</span>
            </div>
            <div className="text-xs sm:text-sm font-mono tracking-tight text-white/90">
              {formatBeijingDisplay(beijingNow)}
            </div>
          </div>
        </div>
        {/* Navigation */}
        <div className="bg-orange-50 px-4 py-3 border-b flex justify-between items-center">
          <div className="flex gap-6 text-sm">
            <button onClick={() => setNavView('about')} className={`text-orange-600 font-medium hover:underline ${navView==='about'?'underline':''}`}>关于心歌</button>
            <button onClick={() => window.open('https://github.com/hzhan11/signally','_blank','noopener,noreferrer')} className="text-orange-600 hover:underline">获取源码</button>
            <button onClick={() => setNavView('contact')} className={`text-orange-600 hover:underline ${navView==='contact'?'underline':''}`}>联系作者</button>
          </div>
          <div className="text-orange-600 text-sm ml-auto">版本: v1.03</div>
        </div>
        <div className="h-6" />
        {/* Conditional Main vs About */}
        {navView === 'about' ? (
          <div className="pb-8">{AboutContent()}</div>
        ) : navView === 'contact' ? (
          <div className="pb-8">{ContactContent()}</div>
        ) : (
        <>
        {/* Tabs */}
        <div className="px-4 py-2">
          <div className="flex items-center justify-between gap-3">
            <div className="flex gap-1 flex-wrap">
              {loadingStocks ? <div className="text-sm text-gray-500">Loading...</div> : stocksError ? <div className="text-sm text-red-500">Error: {stocksError}</div> : (
                (stocks.length ? stocks : [{ id: '(no)', name: '(no stocks)', metadata: {} }]).map((stock, idx) => {
                  const id = stock.id ?? String(idx);
                  const name = stock.name ?? id;
                  const isSelected = selectedTab === id;
                  return (
                    <button key={id+idx} onClick={() => setSelectedTab(id)} className={`px-4 py-2 rounded text-sm font-medium transition-colors ${isSelected ? 'bg-orange-500 text-white' : idx===0 ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' : 'bg-gray-200 text-gray-400 hover:bg-gray-300'}`}>{name}</button>
                  );
                })
              )}
            </div>
            <div className="text-xs sm:text-[13px] text-orange-600 whitespace-nowrap ml-auto pl-2">
              {selectedStock && hitStats.total > 0 ? (
                <span className="font-bold">总命中率 {hitStats.hit}/{hitStats.total} ({Math.round(hitStats.hit / hitStats.total * 100)}%)</span>
              ) : selectedStock ? <span className="text-gray-400 font-bold">总命中率 --</span> : null}
            </div>
          </div>
        </div>
        {/* Prediction / Latest Highlight */}
        {selectedStock && selectedStock.metadata && selectedStock.metadata.status === 'active' ? (
          <div className="px-4 py-4 text-center">
            {renderLatestHighlightLine()}
          </div>
        ) : selectedStock && selectedStock.metadata && selectedStock.metadata.status !== 'active' ? (
          <div className="px-4 py-4">
            <div className="bg-white border border-orange-300 rounded shadow-sm overflow-hidden">
              <div className="bg-orange-500 text-white px-3 py-2 text-sm font-semibold">提示</div>
              <div className="px-4 py-6 text-center text-sm text-gray-500">建设中，敬请期待...</div>
            </div>
          </div>
        ) : null}
        {/* Calendar */}
        {selectedStock && selectedStock.metadata && selectedStock.metadata.status === 'active' && (
          <div className="px-4 pb-2">
            <div className="bg-orange-500 rounded-t px-4 py-2 flex items-center justify-between text-white">
              <button onClick={() => navigateMonth(-1)} className="p-1 hover:bg-orange-600 rounded"><ChevronLeft className="w-4 h-4" /></button>
              <span className="font-semibold text-sm">{`${currentDate.getFullYear()}-${String(currentDate.getMonth()+1).padStart(2,'0')} 预计日历`}</span>
              <button onClick={() => navigateMonth(1)} className="p-1 hover:bg-orange-600 rounded"><ChevronRight className="w-4 h-4" /></button>
            </div>
            <div className="bg-orange-100 px-4 py-2">
              <div className="grid grid-cols-7 gap-1 text-center text-xs sm:text-[13px] font-medium text-gray-700"><div>Su</div><div>Mo</div><div>Tu</div><div>We</div><div>Th</div><div>Fr</div><div>Sa</div></div>
            </div>
            <div className="bg-orange-50 px-4 py-2 rounded-b">
              <div className="grid grid-cols-7 gap-1">{renderCalendar()}</div>
            </div>
          </div>
        )}
        {/* Highlights Table (if a colored date selected) */}
        {renderHighlightsTable()}
        </>
        )}
        {/* Footer */}
        <div className="mt-6 px-4 pb-6 text-center text-[11px] text-gray-400 border-t border-orange-100 pt-4">
          © 2025 Signally · All Rights Reserved
        </div>
      </div>
    </div>
  );
}
