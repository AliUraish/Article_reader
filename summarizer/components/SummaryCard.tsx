
import React, { useState } from 'react';
import { SummaryRecord, SummaryFormat } from '../types';

interface SummaryCardProps {
  record: SummaryRecord;
  onDelete?: (id: string) => void;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({ record, onDelete }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(record.summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white border border-slate-100 p-10 md:p-20 shadow-2xl shadow-slate-200/50 rounded-sm">
      <div className="max-w-3xl mx-auto">
        <header className="mb-14 pb-14 border-b border-slate-100">
          <div className="flex justify-between items-start gap-4 mb-10">
            <div className="px-3 py-1 bg-orange-50 rounded-full">
              <span className="text-[10px] font-bold uppercase tracking-[0.25em] text-orange-600">
                {record.format === SummaryFormat.BULLET_POINTS ? 'Atomic Synthesis' : 'Narrative Distillation'}
              </span>
            </div>
            <div className="flex gap-10">
              <button 
                onClick={handleCopy}
                className="text-slate-400 hover:text-orange-600 text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 transition-all"
              >
                <i className={`fas ${copied ? 'fa-check' : 'fa-copy'}`}></i>
                {copied ? 'Copied' : 'Copy'}
              </button>
              {onDelete && (
                <button 
                  onClick={() => onDelete(record.id)}
                  className="text-slate-300 hover:text-red-500 text-[10px] font-bold uppercase tracking-widest transition-colors"
                >
                  Discard
                </button>
              )}
            </div>
          </div>
          
          <h2 className="text-5xl md:text-7xl font-normal text-slate-900 leading-[1.1] mb-8 serif italic">
            {record.title}
          </h2>
          
          <div className="flex items-center gap-6 text-[10px] text-slate-400 font-bold uppercase tracking-[0.3em]">
            <a href={record.url} target="_blank" className="hover:text-orange-600 transition-colors border-b border-slate-200 hover:border-orange-300 pb-0.5">
              Source Origin
            </a>
            <span className="opacity-30">•</span>
            <span>{new Date(record.timestamp).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}</span>
          </div>
        </header>

        <article className="prose prose-slate max-w-none">
          <div className="text-slate-800 leading-[2] text-xl font-[400] whitespace-pre-wrap selection:bg-orange-100 selection:text-orange-950">
            {record.summary}
          </div>
        </article>

        <footer className="mt-20 pt-10 border-t border-slate-50 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-4 text-[10px] text-slate-400 font-bold uppercase tracking-[0.4em]">
            <div className="w-1.5 h-1.5 rounded-full bg-orange-500"></div>
            <span>Generated via Gemini Synthesis</span>
          </div>
          <div className="px-4 py-1.5 border border-slate-100 rounded-sm text-[10px] text-slate-400 font-bold uppercase tracking-widest">
            {record.maxWords} Word Constraint
          </div>
        </footer>
      </div>
    </div>
  );
};
