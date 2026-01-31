# Article Summarizer - Full Stack Application

## Overview
This application provides article summarization using both OpenAI GPT and Google Gemini models, with a React frontend and Python FastAPI backend.

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd python_gpt_agent
```

2. Activate the virtual environment:
```bash
source venv/bin/activate
```

3. Install dependencies (if not already installed):
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```bash
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

5. Start the backend server:
```bash
python api.py
# or
uvicorn api:app --reload
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd summarizer
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables in `.env.local`:
```bash
VITE_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

## Usage

1. Start both the backend and frontend servers
2. Open your browser to `http://localhost:5173`
3. Select your preferred AI model (GPT or Gemini)
4. Choose the summary format (Bullet Points or Paragraph)
5. Set the word budget (150, 300, or 500 words)
6. Enter an article URL and click "Run Analysis"

## Features

- **Dual Model Support**: Choose between OpenAI GPT-4o-mini and Google Gemini
- **Multiple Formats**: Get summaries as bullet points or paragraphs
- **Customizable Length**: Control summary length with word budget
- **History Tracking**: View and revisit previous summaries
- **Modern UI**: Clean, editorial-style interface

## API Endpoints

### `POST /api/extract`
Extract article content from a URL.

**Request:**
```json
{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "title": "Article Title",
  "content": "Article content..."
}
```

### `POST /api/summarize`
Summarize article content using selected model.

**Request:**
```json
{
  "title": "Article Title",
  "content": "Article content...",
  "format": "BULLET_POINTS",
  "maxWords": 250,
  "model": "gpt"
}
```

**Response:**
```json
{
  "summary": "Summary text..."
}
```

## CLI Tool (Separate)

The original CLI tool is still available in `python_gpt_agent/main.py`:

```bash
python main.py https://example.com/article --format points --max-words 200
```

## Troubleshooting

- **CORS errors**: Ensure the backend is running on port 8000
- **API key errors**: Check that both API keys are properly set in the backend `.env` file
- **Module not found**: Ensure all dependencies are installed in the virtual environment
