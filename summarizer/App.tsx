

import React, { useState, useEffect, useRef } from 'react';
import { SummaryFormat, SummaryRecord, AppState, ModelType } from './types';
import { extractArticle, summarizeArticle } from './services/api';
import { Button } from './components/Button';
import { SummaryCard } from './components/SummaryCard';


const HISTORY_KEY = 'brief_synthesis_v5';

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    url: '',
    format: SummaryFormat.BULLET_POINTS,
    maxWords: 250,
    selectedModel: ModelType.GPT,
    isLoading: false,
    error: null,
    history: [],
    currentSummary: null
  });

  const summaryRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem(HISTORY_KEY);
    if (saved) {
      try { setState(prev => ({ ...prev, history: JSON.parse(saved) })); } catch (e) { }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(state.history));
  }, [state.history]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!state.url) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      new URL(state.url);
      const { title, content } = await extractArticle(state.url);
      const summaryText = await summarizeArticle(
        title,
        content,
        state.format,
        state.maxWords,
        state.selectedModel
      );

      const newRecord: SummaryRecord = {
        id: crypto.randomUUID(),
        url: state.url,
        title,
        content: content.substring(0, 500) + "...",
        summary: summaryText,
        format: state.format,
        maxWords: state.maxWords,
        model: state.selectedModel,
        timestamp: Date.now(),
      };

      setState(prev => ({
        ...prev,
        isLoading: false,
        currentSummary: newRecord,
        history: [newRecord, ...prev.history].slice(0, 10),
        url: ''
      }));

      setTimeout(() => {
        summaryRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err) {
      console.error(err);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Analysis failed. Please check the URL."
      }));
    }
  };

  const selectHistoryItem = (record: SummaryRecord) => {
    setState(prev => ({ ...prev, currentSummary: record }));
    summaryRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const deleteHistoryItem = (id: string) => {
    setState(prev => ({
      ...prev,
      history: prev.history.filter(item => item.id !== id),
      currentSummary: prev.currentSummary?.id === id ? null : prev.currentSummary
    }));
  };

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="h-20 sm:h-24 flex items-center justify-between px-4 sm:px-6 md:px-12 max-w-7xl mx-auto">
        <div className="text-2xl font-bold tracking-tighter flex items-center gap-1">
          <span>Brief</span><span className="text-orange-600">.</span>
        </div>
        <div className="hidden sm:flex gap-8 text-[10px] font-bold uppercase tracking-[0.25em] text-slate-500">
          <a href="#" className="hover:text-orange-600 transition-colors">Archive</a>
          <a href="#" className="hover:text-orange-600 transition-colors">Methods</a>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-16 sm:pt-24 pb-24 sm:pb-48">
        {/* Header Section */}
        <header className="mb-16 sm:mb-28 text-center">
          <h1 className="text-5xl sm:text-7xl md:text-9xl font-normal leading-none mb-6 sm:mb-10 serif italic tracking-tight text-slate-900">
            Distil clarity.
          </h1>
          <p className="text-base sm:text-xl text-slate-600 max-w-xl mx-auto leading-relaxed font-light">
            An editorial canvas for article synthesis. Pure intelligence focused on the essence of reading.
          </p>
        </header>

        {/* Input Interface */}
        <section className="mb-20 sm:mb-32">
          <form onSubmit={handleSubmit} className="space-y-8 sm:space-y-12">
            <div className="relative group">
              <input
                type="url"
                required
                placeholder="Enter article URL to synthesize"
                className="w-full text-lg sm:text-2xl py-5 sm:py-8 bg-transparent border-b border-slate-200 focus:border-orange-500 transition-all focus:outline-none placeholder:text-slate-300 placeholder:italic"
                value={state.url}
                onChange={(e) => setState(prev => ({ ...prev, url: e.target.value }))}
              />
              <div className="absolute bottom-0 left-0 h-0.5 w-0 bg-orange-500 group-focus-within:w-full transition-all duration-700"></div>
            </div>

            <div className="flex flex-col md:flex-row items-center justify-between gap-8 sm:gap-10 pt-2 sm:pt-4">
              <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-6 sm:gap-12 w-full">
                <div className="flex flex-col gap-2 w-full sm:w-auto">
                  <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-slate-400">AI Model</span>
                  <div className="flex flex-wrap gap-4 sm:gap-6">
                    {(Object.keys(ModelType) as Array<keyof typeof ModelType>).map((key) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setState(prev => ({ ...prev, selectedModel: ModelType[key] }))}
                        className={`text-[11px] sm:text-xs font-bold uppercase tracking-widest transition-colors ${state.selectedModel === ModelType[key] ? 'text-orange-600' : 'text-slate-400 hover:text-slate-900'}`}
                      >
                        {key}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex flex-col gap-2 w-full sm:w-auto">
                  <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-slate-400">Synthesis Mode</span>
                  <div className="flex flex-wrap gap-4 sm:gap-6">
                    {(Object.keys(SummaryFormat) as Array<keyof typeof SummaryFormat>).map((key) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setState(prev => ({ ...prev, format: SummaryFormat[key] }))}
                        className={`text-[11px] sm:text-xs font-bold uppercase tracking-widest transition-colors ${state.format === SummaryFormat[key] ? 'text-orange-600' : 'text-slate-400 hover:text-slate-900'}`}
                      >
                        {key.replace('_', ' ')}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex flex-col gap-2 w-full sm:w-auto">
                  <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-slate-400">Word Budget</span>
                  <select
                    className="bg-transparent text-[11px] sm:text-xs font-bold cursor-pointer focus:outline-none text-slate-900"
                    value={state.maxWords}
                    onChange={(e) => setState(prev => ({ ...prev, maxWords: parseInt(e.target.value) }))}
                  >
                    <option value={150}>150 Words</option>
                    <option value={300}>300 Words</option>
                    <option value={500}>500 Words</option>
                  </select>
                </div>
              </div>

              <Button type="submit" isLoading={state.isLoading} className="w-full md:w-80 h-14 sm:h-16 bg-orange-600 hover:bg-orange-500 rounded-none uppercase text-[11px] sm:text-xs tracking-[0.3em] font-bold shadow-2xl shadow-orange-900/20">
                Run Analysis
              </Button>
            </div>
          </form>

          {state.error && (
            <div className="mt-8 sm:mt-12 p-6 sm:p-8 border border-red-100 bg-red-50/50 text-red-800 text-sm italic text-center rounded-sm">
              {state.error}
            </div>
          )}
        </section>

        {/* Synthesis Result */}
        <div ref={summaryRef} className="space-y-24 sm:space-y-40">
          {state.isLoading ? (
            <div className="flex flex-col items-center justify-center py-24 sm:py-40 space-y-8 sm:space-y-12">
              <div className="relative w-56 sm:w-80 h-px bg-slate-100 overflow-hidden">
                <div className="absolute inset-0 bg-orange-600 origin-left animate-[synthesis_2s_infinite]"></div>
              </div>
              <p className="text-[10px] font-bold uppercase tracking-[0.6em] text-orange-700 animate-pulse">Extracting Intelligence</p>
            </div>
          ) : state.currentSummary ? (
            <SummaryCard
              record={state.currentSummary}
              onDelete={deleteHistoryItem}
            />
          ) : null}

          {/* Archive History */}
          {!state.isLoading && state.history.length > 0 && (
            <section className="pt-16 sm:pt-24">
              <div className="flex items-center gap-6 sm:gap-10 mb-12 sm:mb-20">
                <h3 className="text-[10px] font-bold uppercase tracking-[0.5em] text-slate-400 whitespace-nowrap">Synthesis Archive</h3>
                <div className="h-px w-full bg-slate-100"></div>
              </div>
              <div className="grid gap-6">
                {state.history.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => selectHistoryItem(item)}
                    className={`bg-white/60 backdrop-blur-md border p-5 sm:p-12 text-left transition-all flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 sm:gap-0 group ${state.currentSummary?.id === item.id ? 'border-orange-500 shadow-xl shadow-orange-900/5' : 'border-slate-100 hover:border-orange-200 hover:bg-white'}`}
                  >
                    <div className="max-w-xl">
                      <div className="text-[10px] font-bold text-slate-400 mb-5 uppercase tracking-widest flex items-center gap-3">
                        <span>{new Date(item.timestamp).toLocaleDateString()}</span>
                        <span className="w-1 h-1 rounded-full bg-slate-200"></span>
                        <span className="text-orange-500">{item.model.toUpperCase()}</span>
                        <span className="w-1 h-1 rounded-full bg-slate-200"></span>
                        <span className="text-orange-500">{item.format.replace('_', ' ')}</span>
                      </div>
                      <h4 className="text-2xl sm:text-3xl serif italic leading-tight text-slate-900 group-hover:text-orange-950 transition-colors">
                        {item.title}
                      </h4>
                    </div>
                    <div className="flex items-center gap-4 sm:gap-8">
                      <span className="hidden sm:inline text-[10px] font-bold uppercase tracking-widest text-orange-600 opacity-0 group-hover:opacity-100 transition-all translate-x-4 group-hover:translate-x-0">View Brief</span>
                      <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full border border-slate-100 flex items-center justify-center group-hover:border-orange-200 transition-colors">
                        <i className="fas fa-arrow-right text-[10px] text-orange-600"></i>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>

      {/* Deep Footer */}
      <footer className="border-t border-slate-100 py-20 sm:py-40 px-4 sm:px-6 bg-slate-50/50">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 sm:gap-24 mb-20 sm:mb-32">
            <div className="space-y-6 sm:space-y-10">
              <div className="text-3xl font-bold tracking-tighter">Brief<span className="text-orange-600">.</span></div>
              <p className="text-base sm:text-lg text-slate-500 leading-relaxed font-light">
                An open laboratory for information synthesis. We believe in the efficiency of core ideas and the power of distilled thought.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-10 sm:gap-20">
              <div className="space-y-6 sm:space-y-8">
                <h5 className="text-[10px] font-bold uppercase tracking-widest text-slate-900">Protocols</h5>
                <ul className="text-[11px] sm:text-xs text-slate-500 space-y-4 sm:space-y-5">
                  <li><a href="#" className="hover:text-orange-600 transition-colors">Extraction Engine</a></li>
                  <li><a href="#" className="hover:text-orange-600 transition-colors">Gemini Flash-Lite</a></li>
                  <li><a href="#" className="hover:text-orange-600 transition-colors">Semantic Flow</a></li>
                </ul>
              </div>
              <div className="space-y-6 sm:space-y-8">
                <h5 className="text-[10px] font-bold uppercase tracking-widest text-slate-900">Lab</h5>
                <ul className="text-[11px] sm:text-xs text-slate-500 space-y-4 sm:space-y-5">
                  <li><a href="#" className="hover:text-orange-600 transition-colors">Ethics Board</a></li>
                  <li><a href="#" className="hover:text-orange-600 transition-colors">Privacy Shield</a></li>
                  <li><a href="#" className="hover:text-orange-600 transition-colors">Github Repo</a></li>
                </ul>
              </div>
            </div>
          </div>
          <div className="pt-10 sm:pt-16 border-t border-slate-200 flex flex-col md:flex-row justify-between items-center gap-6 sm:gap-8 text-[9px] sm:text-[10px] font-bold text-slate-400 uppercase tracking-[0.3em] sm:tracking-[0.4em]">
            <div className="flex items-center gap-4">
              <div className="w-2 h-2 rounded-full bg-orange-600 animate-pulse"></div>
              <span>Synthesis Operational v0.1.5</span>
            </div>
            <span>© 2025 Synthetic Laboratory Tokyo</span>
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes synthesis {
          0% { transform: scaleX(0); transform-origin: left; }
          45% { transform: scaleX(1); transform-origin: left; }
          50% { transform: scaleX(1); transform-origin: right; }
          100% { transform: scaleX(0); transform-origin: right; }
        }
      `}</style>
    </div>
  );
};

export default App;
