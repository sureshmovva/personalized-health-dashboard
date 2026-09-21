import React, { useState } from 'react';
import {
  FolderTree,
  Terminal,
  Activity,
  Scale,
  FileCode,
  ShieldCheck,
  CheckCircle2,
  Copy,
  BookOpen,
  GitBranch,
  Layers,
  ArrowRight,
} from 'lucide-react';

interface FileNode {
  path: string;
  name: string;
  type: 'file' | 'folder';
  description: string;
  badge?: string;
}

const REPO_TREE: FileNode[] = [
  { path: 'app/', name: 'app/', type: 'folder', description: 'Streamlit frontend UI application' },
  { path: 'app/main.py', name: 'main.py', type: 'file', description: 'Streamlit dashboard entry point with file uploaders & metrics', badge: 'Core' },
  { path: 'app/components/metrics_cards.py', name: 'metrics_cards.py', type: 'file', description: 'Executive metric cards (Current Glucose, 24h Avg, Weight)' },
  { path: 'app/components/charts.py', name: 'charts.py', type: 'file', description: 'Plotly charts for CGM glycemic bands & weight trends' },
  { path: 'pipeline/', name: 'pipeline/', type: 'folder', description: 'Pydantic v2 data pipeline and normalization engine' },
  { path: 'pipeline/models.py', name: 'models.py', type: 'file', description: 'Pydantic schemas: GlucoseReading, ScaleRecord, PriorityMap', badge: 'Pydantic' },
  { path: 'pipeline/normalizer.py', name: 'normalizer.py', type: 'file', description: 'ISO 8601 UTC timestamp converter & unit normalizers' },
  { path: 'pipeline/deduplicator.py', name: 'deduplicator.py', type: 'file', description: 'Sliding time-window heuristics & priority conflict resolution', badge: 'Logic' },
  { path: 'pipeline/parsers/base.py', name: 'base.py', type: 'file', description: 'Abstract parser interface BaseHealthParser' },
  { path: 'pipeline/parsers/stelo_cgm.py', name: 'stelo_cgm.py', type: 'file', description: 'Dexcom Stelo CGM CSV parser' },
  { path: 'pipeline/parsers/wyze_scale.py', name: 'wyze_scale.py', type: 'file', description: 'Wyze Body Scale Ultra CSV parser' },
  { path: 'pipeline/parsers/custom_csv.py', name: 'custom_csv.py', type: 'file', description: 'Generic manual tracker spreadsheet parser' },
  { path: 'docs/', name: 'docs/', type: 'folder', description: 'Technical and user documentation' },
  { path: 'docs/ARCHITECTURE.md', name: 'ARCHITECTURE.md', type: 'file', description: 'Full architectural data flow, priority models & schemas', badge: 'Docs' },
  { path: 'docs/USER_GUIDE.md', name: 'USER_GUIDE.md', type: 'file', description: 'Instructions for CSV exporting & glycemic zone interpretation' },
  { path: '.github/workflows/ci.yml', name: 'ci.yml', type: 'file', description: 'GitHub Actions: Ruff linting + pytest matrix across Python 3.10-3.12' },
  { path: 'tests/test_pipeline_models.py', name: 'test_pipeline_models.py', type: 'file', description: 'Automated test suite for normalization & deduplication' },
  { path: 'requirements.txt', name: 'requirements.txt', type: 'file', description: 'Pinned dependencies for Streamlit, Pydantic, Plotly, DuckDB' },
  { path: 'pyproject.toml', name: 'pyproject.toml', type: 'file', description: 'Modern packaging, Ruff linter rules, and Pytest configuration' },
];

const SETUP_STEPS = [
  {
    step: '1. Clone & Environment',
    cmd: 'git clone <repo-url> health-dashboard && cd health-dashboard\npython3 -m venv .venv\nsource .venv/bin/activate',
    note: 'Creates an isolated Python 3.10+ virtual environment.',
  },
  {
    step: '2. Install Dependencies',
    cmd: 'pip install -r requirements.txt',
    note: 'Installs Streamlit, Plotly, Pydantic v2, Pandas, Dateutil, and DuckDB.',
  },
  {
    step: '3. Run Unit Tests',
    cmd: 'pytest -v',
    note: 'Validates UTC conversion, boundary checks, and sliding-window conflict resolution.',
  },
  {
    step: '4. Start Streamlit Dashboard',
    cmd: 'streamlit run app/main.py',
    note: 'Launches the interactive dashboard locally at http://localhost:8501.',
  },
];

export default function App() {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'tree' | 'setup' | 'pipeline'>('overview');
  const [activePipelineTab, setActivePipelineTab] = useState<'cgm' | 'scale'>('cgm');

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans" id="health-dashboard-app">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs" id="app-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-xl shadow-xs">
              🩺
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-slate-900">Personalized Health Dashboard</h1>
                <span className="bg-teal-50 text-teal-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-teal-200">
                  Python + Streamlit
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Stelo CGM • Wyze Scale Ultra • Health Exports • Pydantic v2 Data Pipeline
              </p>
            </div>
          </div>

          {/* Navigation tabs */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200" id="main-nav-tabs">
            <button
              id="tab-btn-overview"
              onClick={() => setSelectedTab('overview')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                selectedTab === 'overview' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Overview
            </button>
            <button
              id="tab-btn-tree"
              onClick={() => setSelectedTab('tree')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                selectedTab === 'tree' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Repository Tree
            </button>
            <button
              id="tab-btn-setup"
              onClick={() => setSelectedTab('setup')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                selectedTab === 'setup' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Setup Commands
            </button>
            <button
              id="tab-btn-pipeline"
              onClick={() => setSelectedTab('pipeline')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                selectedTab === 'pipeline' ? 'bg-white text-slate-900 shadow-xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Pipeline Logic
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-8" id="main-content">
        {selectedTab === 'overview' && (
          <div className="space-y-8" id="overview-section">
            {/* Top Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Current Glucose</span>
                  <Activity className="w-4 h-4 text-teal-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900">98 mg/dL</div>
                <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Optimal In-Range (70-140)</span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Wyze Scale Ultra</span>
                  <Scale className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900">178.5 lbs</div>
                <div className="text-xs text-slate-500">80.9 kg • 18.2% Body Fat</div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Pipeline Architecture</span>
                  <Layers className="w-4 h-4 text-amber-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900">Pydantic v2</div>
                <div className="text-xs text-slate-500">ISO 8601 UTC + Unit Normalization</div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Quality & Tests</span>
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="text-2xl font-bold text-slate-900">Ruff + Pytest</div>
                <div className="text-xs text-slate-500">GitHub Actions CI Multi-Python Matrix</div>
              </div>
            </div>

            {/* Architecture Highlights */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
              <div className="border-b border-slate-100 pb-4">
                <h2 className="text-lg font-bold text-slate-900">System Architecture & Multi-Source Normalization</h2>
                <p className="text-sm text-slate-600 mt-1">
                  How incoming data from wearable sensors and clinical records is parsed, unified, and deduplicated.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/80 space-y-2">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                    <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-xs font-bold">1</span>
                    Sensor Ingestion
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Custom parsers handle raw Dexcom Stelo CGM CSV exports, Wyze Body Scale Ultra logs, Apple/Google Health XML/CSVs, and manual trackers.
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/80 space-y-2">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                    <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold">2</span>
                    Deduplication & Precedence
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Sliding 2-minute (CGM) and 15-minute (scale) windows resolve duplicate entries with deterministic priority rules: Direct Sensor &gt; Aggregator &gt; Manual Entry.
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/80 space-y-2">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                    <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-bold">3</span>
                    Streamlit Visuals
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    A lightweight, responsive web app featuring interactive Plotly curves, target glycemic zones (70-140 mg/dL), and automated audit logs.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'tree' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4" id="tree-section">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <FolderTree className="w-5 h-5 text-teal-600" />
                  Repository File Tree
                </h2>
                <p className="text-sm text-slate-600">
                  Clean, production-ready monorepo structure organized in <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-800">app/</code>, <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-800">pipeline/</code>, <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-800">docs/</code>, and <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-800">.github/</code>.
                </p>
              </div>
            </div>

            <div className="divide-y divide-slate-100">
              {REPO_TREE.map((node) => (
                <div key={node.path} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50/80 px-2 rounded-lg transition-colors">
                  <div className="flex items-center gap-2.5 font-mono text-xs">
                    {node.type === 'folder' ? (
                      <span className="text-teal-600 font-bold">📁 {node.path}</span>
                    ) : (
                      <span className="text-slate-800 pl-4">📄 {node.path}</span>
                    )}
                    {node.badge && (
                      <span className="font-sans text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200">
                        {node.badge}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 sm:text-right">
                    {node.description}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'setup' && (
          <div className="space-y-6" id="setup-section">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-indigo-600" />
                  Quickstart Setup Commands
                </h2>
                <p className="text-sm text-slate-600">
                  Follow these standard shell commands to configure your environment, install dependencies, run tests, and start Streamlit.
                </p>
              </div>

              <div className="space-y-4 mt-4">
                {SETUP_STEPS.map((item, idx) => (
                  <div key={item.step} className="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-700">{item.step}</span>
                      <button
                        onClick={() => copyToClipboard(item.cmd, idx)}
                        className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-2.5 py-1 rounded shadow-2xs transition-colors"
                      >
                        {copiedIndex === idx ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="text-emerald-700 font-medium">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    <pre className="bg-slate-900 text-slate-100 p-3 rounded-md text-xs font-mono overflow-x-auto">
                      {item.cmd}
                    </pre>
                    <p className="text-xs text-slate-500">{item.note}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'pipeline' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6" id="pipeline-section">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-teal-600" />
                Deduplication & Conflict Resolution Logic
              </h2>
              <p className="text-sm text-slate-600">
                Deterministic rules applied during ingestion when overlapping entries are found within the sliding window.
              </p>
            </div>

            <div className="flex gap-2 border-b border-slate-200 pb-2">
              <button
                onClick={() => setActivePipelineTab('cgm')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md ${
                  activePipelineTab === 'cgm' ? 'bg-teal-50 text-teal-700 border border-teal-200' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                CGM Window (2 min)
              </button>
              <button
                onClick={() => setActivePipelineTab('scale')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md ${
                  activePipelineTab === 'scale' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Scale Window (15 min)
              </button>
            </div>

            {activePipelineTab === 'cgm' && (
              <div className="space-y-4">
                <div className="bg-slate-50 border border-slate-200 p-4 rounded-lg space-y-2 text-xs">
                  <div className="font-semibold text-slate-800">Priority Hierarchy:</div>
                  <ol className="list-decimal list-inside space-y-1 text-slate-600">
                    <li><strong>Stelo Continuous Glucose Monitor (Priority 80):</strong> Direct continuous sensor hardware measurement.</li>
                    <li><strong>Apple / Google Health (Priority 60):</strong> Sync aggregator log.</li>
                    <li><strong>Manual Tracker CSV (Priority 40):</strong> Self-reported fingerstick or typed log.</li>
                  </ol>
                </div>
                <div className="text-xs text-slate-600 leading-relaxed">
                  If a user enters a manual glucose reading at 08:00 UTC and Stelo captures a reading at 08:01 UTC, the sliding 2-minute window identifies the conflict and preserves the Stelo sensor reading with full audit provenance.
                </div>
              </div>
            )}

            {activePipelineTab === 'scale' && (
              <div className="space-y-4">
                <div className="bg-slate-50 border border-slate-200 p-4 rounded-lg space-y-2 text-xs">
                  <div className="font-semibold text-slate-800">Weight & Body Composition Heuristic:</div>
                  <ol className="list-decimal list-inside space-y-1 text-slate-600">
                    <li><strong>Wyze Body Scale Ultra (Priority 80):</strong> Multi-frequency BIA measuring weight, fat %, muscle, metabolic age.</li>
                    <li><strong>Aggregator Sync (Priority 60):</strong> Third-party imported weight without bioimpedance telemetry.</li>
                    <li><strong>Manual Entry (Priority 40):</strong> Approximations entered in personal spreadsheets.</li>
                  </ol>
                </div>
                <div className="text-xs text-slate-600 leading-relaxed">
                  Duplicate weigh-ins recorded within 15 minutes retain the highest priority device and auto-convert pounds to kilograms (and vice-versa) to maintain unified dual-unit availability.
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500">
        Personalized Health Dashboard • Python 3.10+ • Streamlit • Pydantic v2 • Plotly
      </footer>
    </div>
  );
}
