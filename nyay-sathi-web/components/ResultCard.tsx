import { Section, QueryMode } from "@/lib/api";
import { BookOpen, CheckCircle, AlertCircle, FileText } from "lucide-react";
import clsx from "clsx";

interface ResultCardProps {
    explanation: string;
    sections: Section[];
    confidence: number;
    mode: QueryMode;
}

export default function ResultCard({ explanation, sections, confidence, mode }: ResultCardProps) {
    const isHighConfidence = mode === 'grounded' && confidence > 0.7;

    return (
        <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* Explanation Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden mb-4">
                <div className="p-5">
                    <div className="flex items-center gap-2 mb-3">
                        {isHighConfidence ? (
                            <div className="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1">
                                <CheckCircle className="w-3 h-3" />
                                High Relevance
                            </div>
                        ) : (
                            <div className="bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" />
                                {mode === 'fallback' ? 'General Info' : 'Partial Match'}
                            </div>
                        )}
                    </div>

                    <h3 className="text-slate-900 font-semibold mb-2">Explanation</h3>
                    <p className="text-slate-600 text-sm leading-relaxed whitespace-pre-wrap">
                        {explanation}
                    </p>
                </div>
            </div>

            {/* Legal Sections */}
            {sections.length > 0 && (
                <div className="space-y-3">
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1">Relevant Laws</h4>

                    {sections.map((section, idx) => (
                        <div key={idx} className="bg-slate-50 rounded-xl border border-slate-200 p-4 transition-all hover:bg-white hover:shadow-md hover:border-slate-300">
                            <div className="flex items-start gap-3">
                                <div className="bg-indigo-100 p-2 rounded-lg text-indigo-600 flex-shrink-0">
                                    <BookOpen className="w-4 h-4" />
                                </div>
                                <div>
                                    <h5 className="font-semibold text-slate-900 text-sm">
                                        {section.act}
                                    </h5>
                                    <p className="text-indigo-600 text-xs font-medium mb-2">
                                        Section {section.section}
                                    </p>
                                    <p className="text-slate-500 text-xs leading-relaxed line-clamp-4">
                                        {section.text}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
