
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ExtractResponse {
    title: string;
    content: string;
}

export interface SummarizeRequest {
    title: string;
    content: string;
    format: 'BULLET_POINTS' | 'PARAGRAPH';
    maxWords: number;
    model: 'gpt' | 'gemini';
}

export interface SummarizeResponse {
    summary: string;
}

export const extractArticle = async (url: string): Promise<ExtractResponse> => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to extract article content');
        }

        return await response.json();
    } catch (error) {
        console.error('Extract Article Error:', error);
        if (error instanceof Error) throw error;
        throw new Error('An error occurred while extracting the article');
    }
};

export const summarizeArticle = async (
    title: string,
    content: string,
    format: 'BULLET_POINTS' | 'PARAGRAPH',
    maxWords: number,
    model: 'gpt' | 'gemini'
): Promise<string> => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/summarize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title,
                content,
                format,
                maxWords,
                model,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate summary');
        }

        const data: SummarizeResponse = await response.json();
        return data.summary;
    } catch (error) {
        console.error('Summarize Article Error:', error);
        if (error instanceof Error) throw error;
        throw new Error('An error occurred while generating the summary');
    }
};
