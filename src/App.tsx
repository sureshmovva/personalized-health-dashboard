import React, { useState } from 'react';
import {
  Activity,
  Scale,
  Database,
  Layers,
  ShieldCheck,
  CheckCircle2,
  Copy,
  Clock,
  Award,
  FileText,
  Binary,
  ArrowRight,
  ExternalLink,
  Search,
  Filter,
} from 'lucide-react';

interface UnifiedRecord {
  id: string;
  user_id: string;
  timestamp: string;
  source_type: string;
  source_name: string;
  metric_category: string;
  data: Record<string, any>;
  metadata: {
    raw_file_id: string;
    confidence_score: number;
    original_filename?: string;
  };
}

interface DenormalizedDaily {
  date: string;
  meanGlucose: number;
  tirPct: number;
  weightLbs: number;
  bodyFatPct: number;
  steps: number;
  sources: string[];
}

const SAMPLE_UNIFIED_RECORDS: UnifiedRecord[] = [
  {
    id: 'rec_001',
    user_id: 'usr_987654',
    timestamp: '2026-09-21T16:00:00Z',
    source_type: 'cgm',
    source_name: 'Stelo CGM',
    metric_category: 'blood_glucose',
    data: {
      value: 105,
      unit: 'mg/dL',
      trend_arrow: 'flat',
    },
    metadata: {
      raw_file_id: 'stelo_cgm_a48f91.csv',
      confidence_score: 0.99,
      original_filename: 'stelo_export_sep2026.csv',
    },
  },
  {
    id: 'rec_002',
    user_id: 'usr_987654',
    timestamp: '2026-09-21T07:15:00Z',
    source_type: 'scale',
    source_name: 'Wyze Scale Ultra',
    metric_category: 'body_weight',
    data: {
      value: 178.2,
      unit: 'lbs',
      value_kg: 80.8,
      body_fat_pct: 18.1,
      muscle_mass_kg: 62.6,
    },
    metadata: {
      raw_file_id: 'wyze_scale_3f02bd.csv',
      confidence_score: 1.0,
      original_filename: 'wyze_scale_ultra_history.csv',
    },
  },
  {
    id: 'rec_003',
    user_id: 'usr_987654',
    timestamp: '2026-09-18T14:30:00Z',
    source_type: 'clinical_lab',
    source_name: 'Teladoc PDF Note',
    metric_category: 'hba1c',
    data: {
      value: 5.4,
      unit: '%',
      reference_range: '< 5.7%',
      interpretation: 'Normal glycemic regulation',
    },
    metadata: {
      raw_file_id: 'teladoc_pdf_77e012.pdf',
      confidence_score: 0.98,
      original_filename: 'teladoc_visit_lab_report.pdf',
    },
  },
];

const SAMPLE_DENORMALIZED_DAILY: DenormalizedDaily[] = [
  {
    date: '2026-09-21',
    meanGlucose: 104.2,
    tirPct: 92.4,
    weightLbs: 178.2,
    bodyFatPct: 18.1,
    steps: 8940,
    sources: ['Stelo CGM', 'Wyze Scale Ultra'],
  },
  {
    date: '2026-09-20',
    meanGlucose: 102.8,
    tirPct: 94.1,
    weightLbs: 178.6,
    bodyFatPct: 18.2,
    steps: 10450,
    sources: ['Stelo CGM', 'Wyze Scale Ultra'],
  },
  {
    date: '2026-09-19',
    meanGlucose: 108.5,
    tirPct: 89.6,
    weightLbs: 178.8,
    bodyFatPct: 18.3,
    steps: 7620,
    sources: ['Stelo CGM', 'Wyze Scale Ultra'],
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'document-store' | 'daily-rollups' | 'traceability' | 'raw-vault'>('document-store');
  const [selectedRecord, setSelectedRecord] = useState<UnifiedRecord>(SAMPLE_UNIFIED_RECORDS[0]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans" id="app-root">
      {/* Top Application Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs" id="header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-xl shadow-xs">
              🩺
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-slate-900">Personalized Health Dashboard</h1>
                <span className="bg-teal-50 text-teal-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-teal-200">
                  Layer 2 Document Store
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Layer 1: Raw Vault ──► Layer 2: Normalized JSON Documents ──► Fast Denormalized Daily Rollups
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200" id="nav-tabs">
            <button
              onClick={() => setActiveTab('document-store')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === 'document-store' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Unified JSON Store
            </button>
            <button
              onClick={() => setActiveTab('daily-rollups')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === 'daily-rollups' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Denormalized Daily View
            </button>
            <button
              onClick={() => setActiveTab('traceability')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === 'traceability' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Traceability Link
            </button>
            <button
              onClick={() => setActiveTab('raw-vault')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === 'raw-vault' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Layer 1 Raw Vault
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full space-y-6" id="main-content">
        {/* TAB 1: UNIFIED JSON DOCUMENT STORE */}
        {activeTab === 'document-store' && (
          <div className="space-y-6">
            {/* Architecture Card */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Layer 2: Normalized Document Store (Unified JSON Records)</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Flexible semi-structured metric storage with composite B-Tree indexing on <code className="bg-slate-100 px-1 py-0.5 rounded font-mono font-bold text-teal-700">(user_id, timestamp_utc)</code>.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-slate-700">
                <span>Active Partition:</span>
                <span className="font-bold text-teal-700">usr_987654</span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Record List Table */}
              <div className="lg:col-span-7 bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
                <h3 className="text-sm font-bold text-slate-900 flex items-center justify-between">
                  <span>Standardized Records (Indexed by User &amp; Time)</span>
                  <span className="text-xs font-normal text-slate-500">Click a record to inspect JSON</span>
                </h3>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 font-medium">
                        <th className="py-2.5 px-2">Timestamp (UTC)</th>
                        <th className="py-2.5 px-2">Metric Category</th>
                        <th className="py-2.5 px-2">Value &amp; Unit</th>
                        <th className="py-2.5 px-2">Source</th>
                        <th className="py-2.5 px-2">Traceability</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono">
                      {SAMPLE_UNIFIED_RECORDS.map((rec) => {
                        const isSelected = selectedRecord.id === rec.id;
                        return (
                          <tr
                            key={rec.id}
                            onClick={() => setSelectedRecord(rec)}
                            className={`cursor-pointer transition-colors ${
                              isSelected ? 'bg-teal-50/70 border-l-2 border-teal-600' : 'hover:bg-slate-50'
                            }`}
                          >
                            <td className="py-2.5 px-2 text-slate-800">{rec.timestamp.replace('T', ' ').replace('Z', '')}</td>
                            <td className="py-2.5 px-2 text-teal-700 font-semibold">{rec.metric_category}</td>
                            <td className="py-2.5 px-2 font-bold text-slate-900">
                              {rec.data.value} {rec.data.unit}
                            </td>
                            <td className="py-2.5 px-2 text-slate-600 font-sans">{rec.source_name}</td>
                            <td className="py-2.5 px-2 text-[10px] text-slate-500 underline truncate max-w-[120px]">
                              {rec.metadata.raw_file_id}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* JSON Document Inspector */}
              <div className="lg:col-span-5 bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900">Standardized JSON Schema Layout</h3>
                  <button
                    onClick={() => copyToClipboard(JSON.stringify(selectedRecord, null, 2), 'json')}
                    className="inline-flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900 bg-slate-50 px-2 py-1 rounded border border-slate-200"
                  >
                    {copiedId === 'json' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedId === 'json' ? 'Copied' : 'Copy JSON'}</span>
                  </button>
                </div>

                <div className="p-3 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono overflow-x-auto max-h-[380px]">
                  <pre>{JSON.stringify(selectedRecord, null, 2)}</pre>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>
                    Indexed under <b>(user_id, timestamp_utc)</b> with flexible semi-structured metric payload.
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: DENORMALIZED DAILY DASHBOARD VIEW */}
        {activeTab === 'daily-rollups' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Database className="w-4 h-4 text-indigo-600" />
                  Denormalized Daily Health Summary
                </h2>
                <p className="text-xs text-slate-500">
                  Pre-aggregated daily rows in <code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-800">unified_daily_rollups</code> allow the UI to load metrics in a single roundtrip without runtime joins.
                </p>
              </div>
              <div className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-200">
                Single Fetch • Zero Runtime Joins
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-medium">
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Mean Glucose</th>
                    <th className="py-2.5 px-3">Time in Range (70–140)</th>
                    <th className="py-2.5 px-3">Scale Weight</th>
                    <th className="py-2.5 px-3">Body Fat %</th>
                    <th className="py-2.5 px-3">Daily Steps</th>
                    <th className="py-2.5 px-3">Unified Source Streams</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {SAMPLE_DENORMALIZED_DAILY.map((d, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3 font-bold text-slate-900">{d.date}</td>
                      <td className="py-2.5 px-3 text-teal-700 font-semibold">{d.meanGlucose} mg/dL</td>
                      <td className="py-2.5 px-3 text-emerald-700 font-semibold">{d.tirPct}%</td>
                      <td className="py-2.5 px-3 text-indigo-700 font-semibold">{d.weightLbs} lbs</td>
                      <td className="py-2.5 px-3 text-slate-600">{d.bodyFatPct}%</td>
                      <td className="py-2.5 px-3 text-slate-700">{d.steps.toLocaleString()}</td>
                      <td className="py-2.5 px-3 text-slate-500 font-sans text-[11px]">{d.sources.join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: TRACEABILITY LINK */}
        {activeTab === 'traceability' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-4 h-4 text-teal-600" />
                End-to-End Traceability: Chart Metric ──► Layer 1 Vault File
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Every extracted metric embeds a <code className="bg-slate-100 px-1 py-0.5 rounded font-mono font-bold text-slate-800">raw_file_id</code> pointing directly back to the original unmodified document in Layer 1.
              </p>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-4">
              <div className="text-xs font-bold text-slate-800 uppercase tracking-wider">Simulated Metric Click on Dashboard</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs space-y-2">
                  <span className="text-[11px] font-semibold text-slate-500">Selected Metric Point</span>
                  <div className="text-xl font-bold text-teal-700">105 mg/dL</div>
                  <div className="text-xs text-slate-600 font-mono">Timestamp: 2026-09-21T16:00:00Z</div>
                  <div className="text-xs text-slate-500">Source: Stelo Continuous Glucose Monitor</div>
                </div>

                <div className="bg-teal-50/50 p-4 rounded-lg border border-teal-200 space-y-2">
                  <span className="text-[11px] font-semibold text-teal-800">Resolved Layer 1 Vault Provenance</span>
                  <div className="text-sm font-bold text-slate-900">stelo_cgm_a48f91.csv</div>
                  <div className="text-xs text-slate-600 font-mono">
                    SHA-256: a48f918cb41e97d195208f238d21b790d5402ef0...
                  </div>
                  <div className="text-xs text-emerald-700 font-medium flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Direct link to immutable source file
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: LAYER 1 RAW VAULT */}
        {activeTab === 'raw-vault' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Binary className="w-4 h-4 text-amber-600" />
                Layer 1: Unstructured Raw Vault (Object Storage)
              </h2>
              <p className="text-xs text-slate-500">
                Preserving immutable originals (PDFs, raw CSVs) so parsing and AI models can be re-run whenever updated.
              </p>
            </div>

            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 font-mono text-xs text-slate-700 space-y-1">
              <div>📁 <b>data/bronze/manifest.json</b> &rarr; Cryptographic provenance catalog</div>
              <div>📁 <b>data/bronze/stelo_cgm/2026/09/21/</b> &rarr; Original Dexcom Clarity CSVs</div>
              <div>📁 <b>data/bronze/wyze_scale/2026/09/21/</b> &rarr; Original Wyze Scale Ultra CSVs</div>
              <div>📁 <b>data/bronze/teladoc_pdf/2026/09/21/</b> &rarr; Raw Clinical Lab &amp; Visit PDFs</div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-3.5 px-4 text-center text-xs text-slate-500">
        Personalized Health Dashboard • Layer 1 Object Vault &amp; Layer 2 Unified Document Store
      </footer>
    </div>
  );
}
