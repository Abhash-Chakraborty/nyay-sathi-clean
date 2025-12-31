"use client";

import { useState } from "react";
import Image from "next/image";
import { Scale, Info } from "lucide-react";
import QueryInput from "@/components/QueryInput";
import ResultCard from "@/components/ResultCard";
import Disclaimer from "@/components/Disclaimer";
import { submitQuery, QueryResponse } from "@/lib/api";

export default function Home() {
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setHasSearched(true);
    setResult(null);

    // Scroll specific element into view if needed, but for mobile stickiness we keep the header

    try {
      const data = await submitQuery(query);
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setHasSearched(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2" onClick={handleReset}>
            <div className="bg-indigo-600 p-1.5 rounded-lg text-white">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900 tracking-tight leading-none">Nyay Sathi</h1>
              <p className="text-[10px] text-slate-500 font-medium">Legal Guidance Simplified</p>
            </div>
          </div>

          <button className="text-slate-400 hover:text-slate-600">
            <Info className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-md mx-auto p-4 flex flex-col items-center">

        {!hasSearched && (
          <div className="text-center py-10 animate-in fade-in zoom-in duration-500">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              Understand Indian Law <br />
              <span className="text-indigo-600">In Simple Language</span>
            </h2>
            <p className="text-slate-500 text-sm max-w-[280px] mx-auto">
              Describe your legal situation below, and our AI will help you find the relevant laws and sections.
            </p>
          </div>
        )}

        {/* Input Area - Moves up when searched */}
        <div className={`w-full transition-all duration-500 ${hasSearched ? 'mb-4' : 'mb-8'}`}>
          {!result && <QueryInput onSearch={handleSearch} isLoading={isLoading} />}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="w-full space-y-4 animate-pulse">
            <div className="bg-white h-48 rounded-2xl w-full"></div>
            <div className="bg-slate-200 h-24 rounded-xl w-full"></div>
            <div className="bg-slate-200 h-24 rounded-xl w-full"></div>
          </div>
        )}

        {/* Results */}
        {result && (
          <>
            {/* Show a "New Search" button or allow editing? For now, we rely on a reset or just refresh */}
            <ResultCard {...result} />

            <button
              onClick={() => {
                setHasSearched(false);
                setResult(null);
              }}
              className="mt-6 text-indigo-600 text-sm font-semibold hover:underline"
            >
              Ask Another Question
            </button>
          </>
        )}

      </main>

      {/* Footer Disclaimer */}
      <Disclaimer />
    </div>
  );
}
