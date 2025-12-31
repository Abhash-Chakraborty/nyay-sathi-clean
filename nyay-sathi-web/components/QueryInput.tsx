"use client";

import { useState } from "react";
import { Send, Sparkles } from "lucide-react";
import clsx from "clsx";

interface QueryInputProps {
    onSearch: (query: string) => void;
    isLoading: boolean;
}

export default function QueryInput({ onSearch, isLoading }: QueryInputProps) {
    const [query, setQuery] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query);
        }
    };

    return (
        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl shadow-indigo-500/5 p-1 mb-6 border border-slate-100">
            <form onSubmit={handleSubmit} className="relative">
                <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Describe your situation here...
Example: 'My landlord is refusing to return my security deposit even though I gave proper notice.'"
                    className="w-full min-h-[140px] p-5 pb-16 rounded-xl text-slate-700 placeholder:text-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/10 text-base"
                    disabled={isLoading}
                />

                <div className="absolute bottom-3 right-3 left-3 flex justify-between items-center">
                    <div className="flex items-center gap-2 text-indigo-300">
                        <Sparkles className="w-4 h-4" />
                        <span className="text-xs font-medium">AI-Powered</span>
                    </div>

                    <button
                        type="submit"
                        disabled={!query.trim() || isLoading}
                        className={clsx(
                            "flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-sm",
                            query.trim() && !isLoading
                                ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-500/20 active:scale-95"
                                : "bg-slate-100 text-slate-300 cursor-not-allowed"
                        )}
                    >
                        {isLoading ? "Analyzing..." : "Ask Nyay Sathi"}
                        {!isLoading && <Send className="w-4 h-4" />}
                    </button>
                </div>
            </form>
        </div>
    );
}
