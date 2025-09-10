import React, { useState, useEffect } from 'react';
import { Lightbulb, TrendingUp, ChevronLeft, ChevronRight } from 'lucide-react';

export default function SignallyApp() {
  const [currentDate, setCurrentDate] = useState(new Date(2012, 3, 22)); // April 22, 2012
  const [stocks, setStocks] = useState([]);
  const [selectedTab, setSelectedTab] = useState('');
  const [loadingStocks, setLoadingStocks] = useState(true);
  const [stocksError, setStocksError] = useState(null);

  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    let mounted = true;
    async function fetchStocks() {
      setLoadingStocks(true);
      setStocksError(null);
      try {
        const res = await fetch(`${API_BASE}/api/v1/stocks/list`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        // data might be an object/set; coerce to array
        const list = Array.isArray(data) ? data : Object.values(data);
        if (mounted) {
          setStocks(list);
          if (!selectedTab && list.length > 0) setSelectedTab(list[0]);
        }
      } catch (err) {
        if (mounted) setStocksError(err.message || String(err));
      } finally {
        if (mounted) setLoadingStocks(false);
      }
    }
    fetchStocks();
    return () => { mounted = false };
  }, []);

  const formatDate = (date) => {
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
  };

  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const navigateMonth = (direction) => {
    setCurrentDate(prev => {
      const newDate = new Date(prev);
      newDate.setMonth(prev.getMonth() + direction);
      return newDate;
    });
  };

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(currentDate);
    const firstDay = getFirstDayOfMonth(currentDate);
    const days = [];

    // Empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-10"></div>);
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      let dayClass = "h-10 flex items-center justify-center text-sm font-medium rounded";
      let bgClass = "";

      // Special styling for specific dates based on the image
      if (day === 9) bgClass = "bg-green-500 text-white";
      else if (day === 10) bgClass = "bg-red-500 text-white";
      else if (day === 11) bgClass = "bg-green-500 text-white";
      else if (day === 12) bgClass = "bg-green-500 text-white";
      else if (day === 22) bgClass = "bg-gray-800 text-white";
      else dayClass += " text-gray-700";

      days.push(
        <div key={day} className={`${dayClass} ${bgClass}`}>
          {day}
        </div>
      );
    }

    return days;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex justify-center">
      <div className="w-full max-w-md bg-white shadow-lg">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-400 to-orange-500 px-4 py-3 text-white">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <TrendingUp className="w-6 h-6 text-blue-600" />
              <span className="text-xl font-bold">Signally</span>
              <Lightbulb className="w-5 h-5 ml-1" />
            </div>
          </div>
          <div className="text-sm mt-1 opacity-90">
            你炒股智慧伴侣
          </div>
        </div>

        {/* Navigation */}
        <div className="bg-orange-50 px-4 py-3 border-b flex justify-between items-center">
          <div className="flex gap-6 text-sm">
            <span className="text-orange-600 font-medium">关于Signally</span>
            <span className="text-orange-600">加入社区</span>
            <span className="text-orange-600">联系作者</span>
          </div>
          <div className="text-orange-600 text-sm ml-auto">版本: v1.03</div>
        </div>

        {/* Add extra space between navigation and tabs */}
        <div className="h-6" />

        {/* Tabs */}
        <div className="px-4 py-2">
          <div className="flex gap-1">
            {loadingStocks ? (
              <div className="text-sm text-gray-500">Loading...</div>
            ) : stocksError ? (
              <div className="text-sm text-red-500">Error: {stocksError}</div>
            ) : (
              (stocks.length ? stocks : ['(no stocks)']).map((tab, idx) => (
                <button
                  key={String(tab) + idx}
                  onClick={() => setSelectedTab(tab)}
                  className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                    selectedTab === tab
                      ? 'bg-orange-500 text-white'
                      : idx === 0
                        ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        : 'bg-gray-200 text-gray-400 hover:bg-gray-300'
                  }`}
                >
                  {tab}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Prediction */}
        <div className="px-4 py-4 text-center">
          {selectedTab === '002594' ? (
            <>
              <div className="text-orange-600 text-lg font-medium">
                2025/11/2 开盘5分钟预测: <span className="text-blue-600 font-bold">涨</span> ，信心指数：<span className="text-blue-600 font-bold">75%</span>
              </div>
              <div className="text-orange-600 mt-2">
                <span className="font-medium">历史预测准确率: <span className="text-blue-600 font-bold">53%</span>，最新版本预测准确率: <span className="text-blue-600 font-bold">58%</span></span>
              </div>
            </>
          ) : (
            <div className="text-gray-400 text-lg font-medium">敬请期待...</div>
          )}
        </div>

        {/* Calendar */}
        {selectedTab === '002594' && (
          <div className="px-4 pb-6">
            <div className="bg-orange-500 rounded-t px-4 py-2 flex items-center justify-between text-white">
              <button
                onClick={() => navigateMonth(-1)}
                className="p-1 hover:bg-orange-600 rounded"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-medium">{formatDate(currentDate)}</span>
              <button
                onClick={() => navigateMonth(1)}
                className="p-1 hover:bg-orange-600 rounded"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-orange-100 px-4 py-2">
              <div className="grid grid-cols-7 gap-1 text-center text-sm font-medium text-gray-700">
                <div>Su</div>
                <div>Mo</div>
                <div>Tu</div>
                <div>We</div>
                <div>Th</div>
                <div>Fr</div>
                <div>Sa</div>
              </div>
            </div>

            <div className="bg-orange-50 px-4 py-2 rounded-b">
              <div className="grid grid-cols-7 gap-1">
                {renderCalendar()}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}