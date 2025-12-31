import { AlertTriangle } from "lucide-react";

export default function Disclaimer() {
    return (
        <div className="w-full bg-amber-50 border-t border-amber-100 p-4 mt-auto">
            <div className="max-w-md mx-auto flex items-start gap-3 text-amber-800 text-xs sm:text-sm">
                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                <p>
                    <strong>Information Only:</strong> Nyay Sathi is an AI-powered educational tool.
                    It provides general legal information based on Indian laws but does <strong>not</strong> provide legal advice.
                    Consult a qualified advocate for real-world legal issues.
                </p>
            </div>
        </div>
    );
}
