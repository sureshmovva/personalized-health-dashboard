import React, { useState } from 'react';
import {
  Activity,
  Scale,
  Database,
  Terminal,
  FolderTree,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Copy,
  Play,
  RotateCcw,
  Sparkles,
  ArrowRight,
  Clock,
  TrendingUp,
  Table,
  UploadCloud,
} from 'lucide-react';

interface GlucosePoint {
  time: string;
  glucose: number;
  trend: string;
  source: string;
}

interface ScalePoint {
  date: string;
  weightLbs: number;
  weightKg: number;
  fatPct: number;
  source: string;
}

const INITIAL_GLUCOSE: GlucosePoint[] = [
  { time: '06:00 UTC', glucose: 94, trend: 'Flat', source: 'Stelo CGM' },
  { time: '07:00 UTC', glucose: 96, trend: 'Flat', source: 'Stelo CGM' },
  { time: '08:00 UTC', glucose: 138, trend: 'SingleUp', source: 'Stelo CGM (Post-Meal)' },
  { time: '08:01 UTC', glucose: 142, trend: 'SingleUp', source: 'Manual CSV (Filtered Duplicate)' },
  { time: '09:00 UTC', glucose: 112, trend: 'FortyFiveDown', source: 'Stelo CGM' },
  { time: '10:00 UTC', glucose: 102, trend: 'Flat', source: 'Stelo CGM' },
  { time: '12:00 UTC', glucose: 128, trend: 'FortyFiveUp', source: 'Stelo CGM' },
  { time: '14:00 UTC', glucose: 98, trend: 'Flat', source: 'Stelo CGM' },
  { time: '16:00 UTC', glucose: 95, trend: 'Flat', source: 'Stelo CGM' },
  { time: '18:00 UTC', glucose: 145, trend: 'SingleUp', source: 'Stelo CGM' },
  { time: '20:00 UTC', glucose: 104, trend: 'FortyFiveDown', source: 'Stelo CGM' },
];

const INITIAL_SCALE: ScalePoint[] = [
  { date: 'Sep 15', weightLbs: 180.2, weightKg: 81.7, fatPct: 18.6, source: 'Wyze Scale Ultra' },
  { date: 'Sep 16', weightLbs: 179.8, weightKg: 81.6, fatPct: 18.5, source: 'Wyze Scale Ultra' },
  { date: 'Sep 17', weightLbs: 179.4, weightKg: 81.4, fatPct: 18.4, source: 'Wyze Scale Ultra' },
  { date: 'Sep 18', weightLbs: 179.1, weightKg: 81.2, fatPct: 18.3, source: 'Wyze Scale Ultra' },
  { date: 'Sep 19', weightLbs: 178.8, weightKg: 81.1, fatPct: 18.3, source: 'Wyze Scale Ultra' },
  { date: 'Sep 20', weightLbs: 178.6, weightKg: 81.0, fatPct: 18.2, source: 'Wyze Scale Ultra' },
  { date: 'Sep 21', weightLbs: 178.2, weightKg: 80.8, fatPct: 18.1, source: 'Wyze Scale Ultra' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'database' | 'local-setup' | 'architecture'>('dashboard');
  const [glucoseData, setGlucoseData] = useState<GlucosePoint[]>(INITIAL_GLUCOSE);
  const [scaleData, setScaleData] = useState<ScalePoint[]>(INITIAL_SCALE);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  const [activeSqlTable, setActiveSqlTable] = useState<'glucose_readings' | 'scale_records' | 'audit_logs'>('glucose_readings');
  const [simulatedLog, setSimulatedLog] = useState<string>('Ready. SQLite database data/health_store.db mounted.');

  const copyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(id);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const handleSimulateConflict = () => {
    const newPoint: GlucosePoint = {
      time: '20:01 UTC',
      glucose: 155,
      trend: 'SingleUp',
      source: 'Manual CSV',
    };
    // Pipeline deduplication: Stelo CGM exists at 20:00 UTC (1 min away).
    // Stelo CGM priority (80) > Manual CSV (40), so Manual CSV is flagged and resolved.
    setSimulatedLog(
      'Conflict resolved: Incoming Manual CSV entry at 20:01 UTC suppressed in favor of higher-priority Stelo CGM sensor log within the 2-minute sliding window.'
    );
  };

  const latestGlucose = glucoseData[glucoseData.length - 1];
  const latestScale = scaleData[scaleData.length - 1];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans" id="health-dashboard-root">
      {/* Top Application Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs" id="app-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-xl shadow-xs">
              🩺
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-slate-900">Personalized Health Dashboard</h1>
                <span className="bg-emerald-50 text-emerald-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-200 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Active Pipeline
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Stelo CGM • Wyze Scale Ultra • SQLite/DuckDB Store • Streamlit Backend
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200" id="header-nav">
            <button
              id="nav-tab-dashboard"
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === 'dashboard' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Live Visualizer
            </button>
            <button
              id="nav-tab-database"
              onClick={() => setActiveTab('database')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === 'database' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Secure Database
            </button>
            <button
              id="nav-tab-setup"
              onClick={() => setActiveTab('local-setup')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === 'local-setup' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Run Locally
            </button>
            <button
              id="nav-tab-arch"
              onClick={() => setActiveTab('architecture')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === 'architecture' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Architecture & Repo
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full space-y-6" id="main-content-view">
        {/* VIEW 1: DASHBOARD VISUALIZER */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6" id="dashboard-view">
            {/* Executive Biometric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2" id="metric-card-glucose">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Current Glucose</span>
                  <Activity className="w-4 h-4 text-teal-600" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900">{latestGlucose.glucose}</span>
                  <span className="text-sm font-semibold text-slate-500">mg/dL</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-200/60 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Target Range: 70–140 mg/dL</span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2" id="metric-card-scale">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Wyze Scale Weight</span>
                  <Scale className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900">{latestScale.weightLbs}</span>
                  <span className="text-sm font-semibold text-slate-500">lbs</span>
                </div>
                <div className="text-xs text-slate-500 font-medium">
                  {latestScale.weightKg} kg • Body Fat: {latestScale.fatPct}%
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2" id="metric-card-database">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Backend Storage</span>
                  <Database className="w-4 h-4 text-amber-600" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900">SQLite / DuckDB</span>
                </div>
                <div className="text-xs text-slate-500">
                  data/health_store.db • WAL Mode Enabled
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2" id="metric-card-pipeline">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Pipeline Deduplication</span>
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900">Active</span>
                </div>
                <div className="text-xs text-slate-500">
                  Sliding 2m (CGM) & 15m (Scale) windows
                </div>
              </div>
            </div>

            {/* Interactive Glycemic Timeline Chart */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4" id="cgm-chart-container">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div>
                  <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-teal-600" />
                    Continuous Glucose Trajectory & Target Zones
                  </h2>
                  <p className="text-xs text-slate-500">
                    Sensor values plotted against standard clinical glycemic boundaries.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    id="btn-simulate-conflict"
                    onClick={handleSimulateConflict}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-50 text-teal-700 text-xs font-semibold rounded-md border border-teal-200 hover:bg-teal-100 transition-colors"
                  >
                    <Play className="w-3.5 h-3.5" />
                    Simulate Ingestion Conflict
                  </button>
                </div>
              </div>

              {/* Graphical Glycemic Timeline Bar Display */}
              <div className="space-y-2">
                <div className="h-44 bg-slate-50/60 rounded-lg border border-slate-200/80 p-4 flex items-end gap-2 sm:gap-4 relative overflow-hidden">
                  {/* Target Range Band Overlay */}
                  <div
                    className="absolute left-0 right-0 bg-emerald-500/10 border-y border-emerald-500/20 pointer-events-none"
                    style={{ bottom: '25%', height: '40%' }}
                  >
                    <span className="absolute right-3 top-1 text-[10px] font-semibold text-emerald-700">
                      Target Range (70–140 mg/dL)
                    </span>
                  </div>

                  {glucoseData.map((pt, i) => {
                    const heightPercent = Math.min(100, Math.max(15, ((pt.glucose - 40) / 160) * 100));
                    const isHigh = pt.glucose > 140;
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1 z-10 group relative">
                        {/* Hover Tooltip */}
                        <div className="opacity-0 group-hover:opacity-100 absolute -top-10 bg-slate-900 text-white text-[10px] py-1 px-2 rounded pointer-events-none whitespace-nowrap transition-opacity shadow-md">
                          {pt.time}: <b>{pt.glucose} mg/dL</b> ({pt.source})
                        </div>
                        <div
                          className={`w-full max-w-[28px] rounded-t-md transition-all ${
                            isHigh ? 'bg-amber-500 group-hover:bg-amber-600' : 'bg-teal-500 group-hover:bg-teal-600'
                          }`}
                          style={{ height: `${heightPercent}%` }}
                        ></div>
                        <span className="text-[9px] text-slate-500 font-mono hidden sm:block truncate w-full text-center">
                          {pt.time.split(' ')[0]}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Ingestion & Conflict Resolution Log Message */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-start gap-2 font-mono">
                <Clock className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                <span>{simulatedLog}</span>
              </div>
            </div>

            {/* Scale Trajectory Table & Trends */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Scale className="w-4 h-4 text-indigo-600" />
                  Wyze Scale Ingestion Records
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 font-medium">
                        <th className="py-2">Date</th>
                        <th className="py-2">Weight (lbs)</th>
                        <th className="py-2">Weight (kg)</th>
                        <th className="py-2">Body Fat %</th>
                        <th className="py-2">Source</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono">
                      {scaleData.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="py-2 text-slate-800">{row.date}</td>
                          <td className="py-2 font-bold text-slate-900">{row.weightLbs}</td>
                          <td className="py-2 text-slate-600">{row.weightKg}</td>
                          <td className="py-2 text-indigo-600">{row.fatPct}%</td>
                          <td className="py-2 text-[10px] text-slate-500">{row.source}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Data Ingestion Guidance */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <UploadCloud className="w-4 h-4 text-teal-600" />
                  Supported Ingestion Formats
                </h3>
                <div className="space-y-3 text-xs text-slate-600">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                    <span className="font-semibold text-slate-800">1. Dexcom Stelo CGM:</span>
                    <p className="mt-1 text-slate-500">Export CSV from Stelo or Dexcom Clarity. Normalizes timestamps to UTC and filters sensor errors.</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                    <span className="font-semibold text-slate-800">2. Wyze Body Scale Ultra:</span>
                    <p className="mt-1 text-slate-500">Export CSV from Wyze App. Standardizes lbs/kg and records bioimpedance body fat percentages.</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                    <span className="font-semibold text-slate-800">3. Apple / Google Health & PDFs:</span>
                    <p className="mt-1 text-slate-500">Ingests activity aggregates and clinical lab biomarkers (A1C, lipid panels) parsed into relational tables.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 2: SECURE DATABASE EXPLORER */}
        {activeTab === 'database' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6" id="database-view">
            <div className="border-b border-slate-100 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Database className="w-5 h-5 text-amber-600" />
                  Secure Backend Database (SQLite / DuckDB)
                </h2>
                <p className="text-sm text-slate-600">
                  Target: <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs font-mono text-slate-800">data/health_store.db</code> with WAL journaling, UTC indices, and unique timestamp constraints.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setActiveSqlTable('glucose_readings')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                    activeSqlTable === 'glucose_readings' ? 'bg-amber-50 text-amber-800 border border-amber-300' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  glucose_readings
                </button>
                <button
                  onClick={() => setActiveSqlTable('scale_records')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                    activeSqlTable === 'scale_records' ? 'bg-amber-50 text-amber-800 border border-amber-300' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  scale_records
                </button>
                <button
                  onClick={() => setActiveSqlTable('audit_logs')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                    activeSqlTable === 'audit_logs' ? 'bg-amber-50 text-amber-800 border border-amber-300' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  ingestion_audit_logs
                </button>
              </div>
            </div>

            {/* Table Schemas and Samples */}
            <div className="space-y-4">
              {activeSqlTable === 'glucose_readings' && (
                <div className="space-y-3">
                  <div className="p-3 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono">
                    <p className="text-slate-400">-- Schema Definition</p>
                    CREATE TABLE glucose_readings (<br />
                    &nbsp;&nbsp;id INTEGER PRIMARY KEY AUTOINCREMENT,<br />
                    &nbsp;&nbsp;timestamp_utc TEXT NOT NULL,<br />
                    &nbsp;&nbsp;glucose_mg_dl REAL NOT NULL,<br />
                    &nbsp;&nbsp;trend_arrow TEXT,<br />
                    &nbsp;&nbsp;source TEXT NOT NULL,<br />
                    &nbsp;&nbsp;ingested_at_utc TEXT NOT NULL,<br />
                    &nbsp;&nbsp;CONSTRAINT uq_glucose_time_source UNIQUE(timestamp_utc, source)<br />
                    );
                  </div>
                  <div className="overflow-x-auto border border-slate-200 rounded-lg">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                        <tr>
                          <th className="p-2.5">id</th>
                          <th className="p-2.5">timestamp_utc</th>
                          <th className="p-2.5">glucose_mg_dl</th>
                          <th className="p-2.5">trend_arrow</th>
                          <th className="p-2.5">source</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono">
                        {glucoseData.slice(0, 5).map((row, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            <td className="p-2.5 text-slate-400">{i + 1}</td>
                            <td className="p-2.5 text-slate-800">2026-09-21T{row.time.split(' ')[0]}:00Z</td>
                            <td className="p-2.5 font-bold text-slate-900">{row.glucose}</td>
                            <td className="p-2.5 text-slate-600">{row.trend}</td>
                            <td className="p-2.5 text-teal-700">{row.source}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {activeSqlTable === 'scale_records' && (
                <div className="space-y-3">
                  <div className="p-3 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono">
                    <p className="text-slate-400">-- Schema Definition</p>
                    CREATE TABLE scale_records (<br />
                    &nbsp;&nbsp;id INTEGER PRIMARY KEY AUTOINCREMENT,<br />
                    &nbsp;&nbsp;timestamp_utc TEXT NOT NULL,<br />
                    &nbsp;&nbsp;weight_kg REAL NOT NULL,<br />
                    &nbsp;&nbsp;weight_lbs REAL NOT NULL,<br />
                    &nbsp;&nbsp;body_fat_pct REAL,<br />
                    &nbsp;&nbsp;source TEXT NOT NULL,<br />
                    &nbsp;&nbsp;CONSTRAINT uq_scale_time_source UNIQUE(timestamp_utc, source)<br />
                    );
                  </div>
                  <div className="overflow-x-auto border border-slate-200 rounded-lg">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                        <tr>
                          <th className="p-2.5">id</th>
                          <th className="p-2.5">timestamp_utc</th>
                          <th className="p-2.5">weight_lbs</th>
                          <th className="p-2.5">weight_kg</th>
                          <th className="p-2.5">body_fat_pct</th>
                          <th className="p-2.5">source</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono">
                        {scaleData.slice(0, 5).map((row, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            <td className="p-2.5 text-slate-400">{i + 1}</td>
                            <td className="p-2.5 text-slate-800">2026-09-21T07:15:00Z</td>
                            <td className="p-2.5 font-bold text-slate-900">{row.weightLbs}</td>
                            <td className="p-2.5 text-slate-700">{row.weightKg}</td>
                            <td className="p-2.5 text-indigo-700">{row.fatPct}%</td>
                            <td className="p-2.5 text-slate-600">{row.source}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {activeSqlTable === 'audit_logs' && (
                <div className="space-y-3">
                  <div className="p-3 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono">
                    <p className="text-slate-400">-- Ingestion Audit Trail</p>
                    CREATE TABLE ingestion_audit_logs (<br />
                    &nbsp;&nbsp;id INTEGER PRIMARY KEY AUTOINCREMENT,<br />
                    &nbsp;&nbsp;timestamp_utc TEXT NOT NULL,<br />
                    &nbsp;&nbsp;source TEXT NOT NULL,<br />
                    &nbsp;&nbsp;raw_count INTEGER NOT NULL,<br />
                    &nbsp;&nbsp;deduped_count INTEGER NOT NULL,<br />
                    &nbsp;&nbsp;conflicts_resolved INTEGER NOT NULL,<br />
                    &nbsp;&nbsp;status TEXT NOT NULL<br />
                    );
                  </div>
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 font-mono">
                    [2026-09-21 14:20:10 UTC] Source: STELO_CGM | Raw: 192 | Deduped: 192 | Conflicts: 0 | Status: SUCCESS<br />
                    [2026-09-21 14:22:45 UTC] Source: WYZE_SCALE | Raw: 14 | Deduped: 14 | Conflicts: 0 | Status: SUCCESS<br />
                    [2026-09-21 14:25:01 UTC] Source: MANUAL_CSV | Raw: 1 | Deduped: 0 | Conflicts: 1 (Suppressed by Stelo 2m window)
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 3: LOCAL SETUP & RUN INSTRUCTIONS */}
        {activeTab === 'local-setup' && (
          <div className="space-y-6" id="local-setup-view">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Terminal className="w-5 h-5 text-indigo-600" />
                How to Execute and View Locally
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                You can run the entire Python Streamlit dashboard and SQLite database pipeline directly on your local machine using our automated scripts or standard shell commands.
              </p>

              {/* Option A: Automated script */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">Option A: 1-Step Automated Launcher</span>
                  <button
                    onClick={() => copyText('./setup.sh && ./run.sh', 'opt-a')}
                    className="inline-flex items-center gap-1.5 text-xs text-slate-600 bg-white border border-slate-200 px-2 py-1 rounded hover:text-slate-900"
                  >
                    {copiedCmd === 'opt-a' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>Copy</span>
                  </button>
                </div>
                <pre className="p-3 bg-slate-900 text-slate-100 rounded text-xs font-mono overflow-x-auto">
                  ./setup.sh && ./run.sh
                </pre>
                <p className="text-xs text-slate-500">
                  Automatically sets up <code>.venv</code>, installs dependencies, initializes <code>data/health_store.db</code>, and opens Streamlit on <code>http://localhost:8501</code>.
                </p>
              </div>

              {/* Option B: Standard Manual Commands */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">Option B: Standard Commands</span>
                  <button
                    onClick={() => copyText('python3 -m venv .venv\nsource .venv/bin/activate\npip install -r requirements.txt\nstreamlit run app/main.py', 'opt-b')}
                    className="inline-flex items-center gap-1.5 text-xs text-slate-600 bg-white border border-slate-200 px-2 py-1 rounded hover:text-slate-900"
                  >
                    {copiedCmd === 'opt-b' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>Copy</span>
                  </button>
                </div>
                <pre className="p-3 bg-slate-900 text-slate-100 rounded text-xs font-mono overflow-x-auto">
                  python3 -m venv .venv<br />
                  source .venv/bin/activate<br />
                  pip install -r requirements.txt<br />
                  streamlit run app/main.py
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 4: ARCHITECTURE & REPO */}
        {activeTab === 'architecture' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4" id="architecture-view">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <FolderTree className="w-5 h-5 text-teal-600" />
              Project Monorepo Structure & GitHub Integration
            </h2>
            <p className="text-sm text-slate-600">
              Your codebase is synchronized with GitHub repository <a href="https://github.com/sureshmovva/personalized-health-dashboard" target="_blank" rel="noreferrer" className="text-teal-600 underline font-medium">sureshmovva/personalized-health-dashboard</a>.
            </p>

            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono space-y-1 text-slate-700">
              <div>📁 <b>app/</b> &rarr; Streamlit application (main.py, charts.py, metrics_cards.py)</div>
              <div>📁 <b>pipeline/</b> &rarr; Pydantic v2 schemas, normalizer, deduplicator & database persistence (db.py)</div>
              <div>📁 <b>pipeline/parsers/</b> &rarr; Stelo CGM, Wyze Scale Ultra, and Custom CSV parsers</div>
              <div>📁 <b>data/</b> &rarr; Local SQLite embedded storage (health_store.db)</div>
              <div>📁 <b>docs/</b> &rarr; ARCHITECTURE.md & USER_GUIDE.md</div>
              <div>📁 <b>tests/</b> &rarr; test_pipeline_models.py & test_database.py</div>
              <div>📁 <b>ci/</b> &rarr; GitHub Actions CI workflow definitions</div>
              <div>📄 <b>setup.sh & run.sh</b> &rarr; Local one-click execution scripts</div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-3.5 px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500">
        Personalized Health Dashboard • Embedded SQLite Database • Streamlit & Pydantic v2
      </footer>
    </div>
  );
}
