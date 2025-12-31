export type QueryMode = 'grounded' | 'partial' | 'fallback';

export interface Section {
    act: string;
    section: string;
    text: string;
}

export interface QueryResponse {
    mode: QueryMode;
    explanation: string;
    sections: Section[];
    confidence: number;
    disclaimer: string;
}

export async function submitQuery(question: string): Promise<QueryResponse> {
    // Use mock API if no backend URL is set or explicitly requested
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;

    if (!apiUrl) {
        // Simulate network delay for realism
        await new Promise((resolve) => setTimeout(resolve, 1500));
        return mockQuery(question);
    }

    try {
        const res = await fetch(`${apiUrl}/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });

        if (!res.ok) throw new Error("Failed to fetch");
        return await res.json();
    } catch (error) {
        console.warn("API Call Failed, falling back to mock data", error);
        return mockQuery(question);
    }
}

// Mock Data Generator for Frontend Dev/Demo
function mockQuery(question: string): QueryResponse {
    const isFallback = question.toLowerCase().includes("fallback") || question.length < 5;

    if (isFallback) {
        return {
            mode: "fallback",
            confidence: 0.3,
            explanation: "Based on general legal principles, this situation involves complexities that require specific statutory analysis. The system could not find a direct high-confidence match in the database.",
            sections: [],
            disclaimer: "Nyay Sathi provides legal information for educational purposes only. It does not provide legal advice.",
        };
    }

    return {
        mode: "grounded",
        confidence: 0.88,
        explanation: "Under Indian law, specifically the Bharatiya Nyaya Sanhita, 2023, defamation is addressed as a civil and criminal wrong. If someone makes a false imputation intent on harming your reputation, you may have legal recourse.",
        sections: [
            {
                act: "Bharatiya Nyaya Sanhita, 2023",
                section: "356",
                text: "Defamation.—(1) Whoever, by words either spoken or intended to be read, or by signs or by visible representations, makes or publishes any imputation concerning any person intending to harm, or knowing or having reason to believe that such imputation will harm, the reputation of such person, is said, except in the cases hereinafter expected, to defame that person.",
            },
            {
                act: "Bharatiya Nyaya Sanhita, 2023",
                section: "356 (2)",
                text: "Explanation 1.—It may amount to defamation to impute anything to a deceased person, if the imputation would harm the reputation of that person if living, and is intended to be hurtful to the feelings of his family or other near relatives.",
            }
        ],
        disclaimer: "Nyay Sathi provides legal information for educational purposes only. It does not provide legal advice.",
    };
}
