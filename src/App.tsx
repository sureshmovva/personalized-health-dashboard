import React, { useState } from 'react';
import {
  Activity,
  Scale,
  Database,
  Layers,
  ShieldCheck,
  CheckCircle2,
  Copy,
  Play,
  Clock,
  Award,
  FileText,
  Binary,
  ArrowRight,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';

interface BronzeReceipt {
  fileId: string;
  filename: string;
  source: string;
  sha256: string;
  sizeBytes: number;
  timeUtc: string;
}

const SAMPLE_BRONZE: BronzeReceipt[] = [
  {
    fileId: 'stelo_cgm_a48f91',
    filename: 'stelo_cgm_export_sep2026.csv',
    source: 'Stelo CGM',
    sha256: 'a48f918cb41e97d195208f238d21b790d5402ef0a98b184288cb43105f28c89b',
    sizeBytes: 18450,
    timeUtc: '2026-09-21 14:15 UTC',
  },
  {
    fileId: 'wyze_scale_3f02bd',
    filename: 'wyze_scale_ultra_history.csv',
    source: 'Wyze Scale Ultra',
    sha256: '3f02bd598c1998f0293dbac29e18b0244cf58231804bcde401b2a95e01f52d91',
    sizeBytes: 4210,
    timeUtc: '2026-09-21 14:16 UTC',
  },
  {
    fileId: 'teladoc_pdf_77e012',
    filename: 'teladoc_lipid_panel_a1c.pdf',
    source: 'Teladoc PDF',
    sha256: '77e012a951d8b746c10ea69550b7194602f32190cd915be52467d0180a52f4a1',
    sizeBytes: 89400,
    timeUtc: '2026-09-21 14:17 UTC',
  },
];

export default function App() {
  const [activeTier, setActiveTier] = useState<'overview' | 'bronze' | 'silver' | 'gold'>('overview');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans" id="medallion-app-root">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs" id="app-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-xl shadow-xs">
              🩺
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-slate-900">Personalized Health Dashboard</h1>
                <span className="bg-teal-50 text-teal-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-teal-200">
                  Medallion Storage Architecture
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Bronze (Raw Blobs) ──► Silver (Normalized SQLite) ──► Gold (Clinical Analytics)
              </p>
            </div>
          </div>

          {/* Medallion Tier Navigation */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200" id="tier-nav">
            <button
              onClick={() => setActiveTier('overview')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTier === 'overview' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Pipeline Flow
            </button>
            <button
              onClick={() => setActiveTier('bronze')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTier === 'bronze' ? 'bg-amber-50 text-amber-900 shadow-xs font-semibold border border-amber-200/80' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              🥉 Bronze (Raw Blobs)
            </button>
            <button
              onClick={() => setActiveTier('silver')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTier === 'silver' ? 'bg-slate-200 text-slate-900 shadow-xs font-semibold border border-slate-300' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              🥈 Silver (Enforced Relational)
            </button>
            <button
              onClick={() => setActiveTier('gold')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTier === 'gold' ? 'bg-yellow-50 text-yellow-900 shadow-xs font-semibold border border-yellow-200' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              🥇 Gold (Clinical Analytics)
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full space-y-6" id="main-view">
        {/* OVERVIEW TAB */}
        {activeTier === 'overview' && (
          <div className="space-y-6">
            {/* Visual Medallion Flow Banner */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
              <div>
                <h2 className="text-base font-bold text-slate-900">Multi-Layer Medallion Storage Strategy</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Solving heterogeneous health data ingestion across unstructured documents and continuous wearable streams.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Bronze Card */}
                <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/40 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-800 uppercase tracking-wider">Bronze Layer (Raw)</span>
                    <Binary className="w-4 h-4 text-amber-700" />
                  </div>
                  <div className="text-sm font-semibold text-slate-900">Immutable Blob Archive</div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Preserves original raw PDFs, CSVs, and JSON feeds verbatim at <code className="bg-amber-100/60 px-1 py-0.5 rounded font-mono text-[11px]">data/bronze/</code> with SHA-256 audit receipts. Enables reprocessing whenever extraction algorithms evolve.
                  </p>
                  <div className="text-[11px] font-mono text-amber-900 bg-amber-100/50 p-2 rounded">
                    SHA-256 • Raw Receipts • Zero Data Loss
                  </div>
                </div>

                {/* Silver Card */}
                <div className="p-4 rounded-xl border border-slate-300 bg-slate-100/60 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Silver Layer (Cleaned)</span>
                    <Database className="w-4 h-4 text-slate-600" />
                  </div>
                  <div className="text-sm font-semibold text-slate-900">Schema Enforcement & Dedup</div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Pydantic v2 validation converts string dates to ISO-8601 UTC and standardizes units (mg/dL, kg/lbs). Sliding-window heuristics eliminate overlapping device records in <code className="bg-slate-200/80 px-1 py-0.5 rounded font-mono text-[11px]">data/health_store.db</code>.
                  </p>
                  <div className="text-[11px] font-mono text-slate-800 bg-slate-200/60 p-2 rounded">
                    SQLite WAL • Indices • Strict Constraints
                  </div>
                </div>

                {/* Gold Card */}
                <div className="p-4 rounded-xl border border-yellow-200 bg-yellow-50/50 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-yellow-800 uppercase tracking-wider">Gold Layer (Insights)</span>
                    <Award className="w-4 h-4 text-yellow-700" />
                  </div>
                  <div className="text-sm font-semibold text-slate-900">Unified Clinical Analytics</div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    High-performance materialized analytical rollups for dashboards: Time-in-Range (TIR 70–140 mg/dL), Glycemic Variability (CV%), 7-day weight moving averages, and clinical biomarker aggregates.
                  </p>
                  <div className="text-[11px] font-mono text-yellow-900 bg-yellow-100/50 p-2 rounded">
                    TIR % • Glycemic CV% • Moving Averages
                  </div>
                </div>
              </div>
            </div>

            {/* Live Gold Analytics Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="text-xs text-slate-500 font-medium">Time-In-Range (70–140 mg/dL)</div>
                <div className="text-3xl font-extrabold text-slate-900">92.4%</div>
                <div className="text-xs text-emerald-600 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Optimal Target (&gt;70%)
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="text-xs text-slate-500 font-medium">Mean Glucose</div>
                <div className="text-3xl font-extrabold text-slate-900">104.2 <span className="text-sm font-normal text-slate-500">mg/dL</span></div>
                <div className="text-xs text-slate-500 font-medium">Std Dev: 14.8 mg/dL</div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="text-xs text-slate-500 font-medium">Glycemic Variability (CV%)</div>
                <div className="text-3xl font-extrabold text-slate-900">14.2%</div>
                <div className="text-xs text-emerald-600 font-medium">High Stability (&lt;36%)</div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="text-xs text-slate-500 font-medium">7-Day Weight Moving Avg</div>
                <div className="text-3xl font-extrabold text-slate-900">178.6 <span className="text-sm font-normal text-slate-500">lbs</span></div>
                <div className="text-xs text-indigo-600 font-medium flex items-center gap-1">
                  <TrendingDown className="w-3.5 h-3.5" /> -1.8 lbs over 14 days
                </div>
              </div>
            </div>
          </div>
        )}

        {/* BRONZE TIER TAB */}
        {activeTier === 'bronze' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Binary className="w-5 h-5 text-amber-700" />
                Bronze Layer: Immutable Raw Blob Ingestion
              </h2>
              <p className="text-xs text-slate-500">
                Directory: <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-slate-800">data/bronze/&#123;source&#125;/YYYY/MM/DD/</code>
              </p>
            </div>

            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="p-3">File ID</th>
                    <th className="p-3">Original Filename</th>
                    <th className="p-3">Source</th>
                    <th className="p-3">SHA-256 Checksum</th>
                    <th className="p-3">Size</th>
                    <th className="p-3">Ingested At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {SAMPLE_BRONZE.map((rec) => (
                    <tr key={rec.fileId} className="hover:bg-slate-50">
                      <td className="p-3 font-semibold text-slate-800">{rec.fileId}</td>
                      <td className="p-3 text-slate-700">{rec.filename}</td>
                      <td className="p-3 text-teal-700 font-sans font-medium">{rec.source}</td>
                      <td className="p-3 text-slate-500 text-[10px]">{rec.sha256.substring(0, 16)}...</td>
                      <td className="p-3 text-slate-600">{(rec.sizeBytes / 1024).toFixed(1)} KB</td>
                      <td className="p-3 text-slate-500">{rec.timeUtc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* SILVER TIER TAB */}
        {activeTier === 'silver' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Database className="w-5 h-5 text-slate-700" />
                Silver Layer: Schema Enforced Relational Tables
              </h2>
              <p className="text-xs text-slate-500">
                Engine: SQLite / DuckDB at <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-slate-800">data/health_store.db</code> with WAL journaling.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2 text-xs">
                <div className="font-semibold text-slate-800">Table: glucose_readings</div>
                <div className="text-[11px] font-mono text-slate-600 space-y-1">
                  <div>• timestamp_utc TEXT (Indexed)</div>
                  <div>• glucose_mg_dl REAL (20.0–600.0)</div>
                  <div>• trend_arrow TEXT</div>
                  <div>• source TEXT</div>
                  <div>• CONSTRAINT uq_time_src UNIQUE(timestamp_utc, source)</div>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2 text-xs">
                <div className="font-semibold text-slate-800">Table: scale_records</div>
                <div className="text-[11px] font-mono text-slate-600 space-y-1">
                  <div>• timestamp_utc TEXT (Indexed)</div>
                  <div>• weight_lbs REAL &amp; weight_kg REAL</div>
                  <div>• body_fat_pct REAL</div>
                  <div>• muscle_mass_kg REAL</div>
                  <div>• metabolic_age INTEGER</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* GOLD TIER TAB */}
        {activeTier === 'gold' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Award className="w-5 h-5 text-yellow-600" />
                Gold Layer: Clinical Ambulatory Glucose Profile (AGP)
              </h2>
              <p className="text-xs text-slate-500">
                Materialized rollups calculated on-demand or refreshed on ingestion batches.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-lg space-y-1">
                <div className="text-xs text-emerald-800 font-semibold">Time In Range (TIR)</div>
                <div className="text-2xl font-bold text-emerald-950">92.4%</div>
                <div className="text-[11px] text-emerald-700">70–140 mg/dL target zone</div>
              </div>

              <div className="p-4 bg-amber-50/50 border border-amber-200 rounded-lg space-y-1">
                <div className="text-xs text-amber-800 font-semibold">Time Above Range (TAR)</div>
                <div className="text-2xl font-bold text-amber-950">6.8%</div>
                <div className="text-[11px] text-amber-700">&gt; 140 mg/dL post-meal spikes</div>
              </div>

              <div className="p-4 bg-rose-50/50 border border-rose-200 rounded-lg space-y-1">
                <div className="text-xs text-rose-800 font-semibold">Time Below Range (TBR)</div>
                <div className="text-2xl font-bold text-rose-950">0.8%</div>
                <div className="text-[11px] text-rose-700">&lt; 70 mg/dL hypoglycemia safety</div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-3.5 px-4 text-center text-xs text-slate-500">
        Personalized Health Dashboard • Medallion Architecture (Bronze / Silver / Gold) • Python 3.10+
      </footer>
    </div>
  );
}
