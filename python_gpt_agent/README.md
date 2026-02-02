# Article Summarization CLI Agent

A single-file Python CLI tool that fetches web articles, extracts the main content (removing ads, navigation, etc.), and produces concise summaries using OpenAI GPT-5.

## Features

- **Robust Content Extraction**: Uses `trafilatura` with `readability-lxml` fallback to extract clean article text
- **Flexible Summarization**: Choose between bullet points or paragraph format
- **Smart Chunking**: Automatically handles long articles with map-reduce summarization
- **Interactive & Scriptable**: Works both interactively and with command-line arguments
- **OpenAI Powered**: Uses GPT-5 by default

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

### Interactive Mode

Simply run the script and follow the prompts:

```bash
python main.py
```

You'll be asked for:
- The article URL
- Summary format (points or para)

### Command-Line Mode

Provide all arguments upfront:

```bash
# Paragraph summary
python main.py https://example.com/article --format para

# Bullet points summary
python main.py https://example.com/article --format points

# Custom model and word limit
python main.py https://example.com/article --format para --model gpt-4o --max-words 300
```

### Options

- `url`: Article URL (required, or will prompt)
- `--format {points,para}`: Summary format (optional, or will prompt)
- `--model MODEL`: OpenAI model to use (default: `gpt-5`)
- `--max-words N`: Maximum words in summary (default: 200)

## Examples

```bash
# Summarize a news article in bullet points
python main.py https://www.bbc.com/news/article --format points

# Get a paragraph summary with custom word limit
python main.py https://blog.example.com/post --format para --max-words 150
```

## How It Works

1. **Fetch**: Downloads the webpage content
2. **Extract**: Removes boilerplate (ads, navigation, etc.) using:
   - Primary: `trafilatura` for high-quality extraction
   - Fallback: `readability-lxml` + `BeautifulSoup` for difficult pages
3. **Summarize**: Uses OpenAI GPT to generate a concise summary:
   - For long articles: chunks content and uses map-reduce strategy
   - Respects your chosen format (points or paragraphs)
4. **Output**: Prints the formatted summary to stdout

## Limitations

- Does not handle JavaScript-rendered pages (requires server-side HTML)
- Does not work with PDFs or non-web content
- May fail with heavily paywalled content
- Expects direct article URLs (not search engine results)

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Error Handling

The tool provides clear error messages for:
- Network failures
- Invalid URLs
- Extraction failures (paywall, JavaScript-only content)
- OpenAI API errors
- Missing API key

## License

Open source - use as you wish.

