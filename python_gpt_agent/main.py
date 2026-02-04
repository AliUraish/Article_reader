#!/usr/bin/env python3
"""
Article Summarization CLI Agent
Extracts and summarizes content from web articles using OpenAI GPT-4o-mini.
"""

import argparse
import os
import sys
import re
import webbrowser
import tempfile
from typing import Optional, Tuple

import trafilatura
import requests
from readability import Document
from bs4 import BeautifulSoup
from openai import OpenAI
import json
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def parse_arguments() -> Tuple[Optional[str], Optional[str], str, int, str, bool]:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Summarize web articles using OpenAI GPT-4o-mini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python main.py https://example.com/article --format points"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="URL of the article to summarize"
    )
    parser.add_argument(
        "--format",
        choices=["points", "para"],
        help="Summary format: 'points' for bullet points, 'para' for paragraph"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=200,
        help="Maximum words in summary (default: 200)"
    )
    parser.add_argument(
        "--output",
        choices=["console", "html", "both"],
        default="both",
        help="Output format: 'console' for terminal, 'html' for browser, 'both' for both (default: both)"
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Disable function calling tools (use basic chat completion only)"
    )
    
    args = parser.parse_args()
    return args.url, args.format, args.model, args.max_words, args.output, not args.no_tools


def get_user_input() -> Tuple[str, str]:
    """Prompt user for URL and format if not provided via CLI."""
    url = input("Enter article URL: ").strip()
    if not url:
        print("Error: URL is required", file=sys.stderr)
        sys.exit(1)
    
    format_choice = prompt_for_format(None)
    
    return url, format_choice


def prompt_for_format(existing_choice: Optional[str]) -> str:
    """Validate or prompt for summary format choice."""
    if existing_choice in ["points", "para"]:
        return existing_choice

    choice = input("Summary format? (points/para): ").strip().lower()
    while choice not in ["points", "para"]:
        print("Please enter 'points' or 'para'")
        choice = input("Summary format? (points/para): ").strip().lower()
    return choice


def clean_html(html: str) -> str:
    """
    Clean HTML content by removing NULL bytes and control characters.
    
    Args:
        html: Raw HTML content
        
    Returns:
        Cleaned HTML content
    """
    # Remove NULL bytes and control characters (except common whitespace)
    html = html.replace('\x00', '')
    # Remove other control characters except \n, \r, \t
    html = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', html)
    return html


def normalize_text(text: str) -> str:
    """Normalize whitespace in text."""
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_content(url: str) -> str:
    """
    Extract main article content from URL using trafilatura with readability fallback.
    
    Args:
        url: The URL to extract content from
        
    Returns:
        Extracted and cleaned text content
        
    Raises:
        ValueError: If content extraction fails or content is too short
        requests.RequestException: If network request fails
    """
    # Try trafilatura first
    print("Fetching article content...", file=sys.stderr)
    downloaded = trafilatura.fetch_url(url)
    
    if downloaded:
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            no_fallback=False
        )
        
        if text and len(text.strip()) >= 500:
            print("Content extracted successfully (trafilatura)", file=sys.stderr)
            return normalize_text(text)
    
    # Fallback to readability + BeautifulSoup
    print("Trying fallback extraction method...", file=sys.stderr)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch URL: {e}")
    
    # Clean HTML before processing
    cleaned_html = clean_html(response.text)
    
    # Try readability first
    try:
        doc = Document(cleaned_html)
        html_content = doc.summary()
        
        # Convert HTML to text
        soup = BeautifulSoup(html_content, 'lxml')
        text = soup.get_text(' ', strip=True)
        
        if len(text.strip()) >= 500:
            print("Content extracted successfully (readability)", file=sys.stderr)
            return normalize_text(text)
    except (ValueError, Exception) as e:
        # If readability fails, try direct BeautifulSoup extraction
        print("Readability extraction failed, trying direct HTML parsing...", file=sys.stderr)
        try:
            soup = BeautifulSoup(cleaned_html, 'lxml')
            # Remove script, style, and other non-content elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                element.decompose()
            text = soup.get_text(' ', strip=True)
            
            if len(text.strip()) >= 500:
                print("Content extracted successfully (direct parsing)", file=sys.stderr)
                return normalize_text(text)
        except Exception as e2:
            raise ValueError(
                f"Failed to extract content from the page. "
                f"The page might contain PDF content, be behind a paywall, require JavaScript, "
                f"or not contain readable article content. Error: {e2}"
            )
    
    # If we get here, extraction didn't yield enough content
    raise ValueError(
        "Could not extract sufficient content from the article. "
        "The page might be behind a paywall, require JavaScript, contain PDF content, "
        "or not contain readable article content."
    )


# Tool definitions for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extract_article_content",
            "description": "Extract the main text content from a web article URL. Use this when you need to get article content from a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the article to extract content from"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_article_metadata",
            "description": "Extract metadata (title, author, publication date, etc.) from a web article URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the article to extract metadata from"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "chunk_text",
            "description": "Split long text into smaller chunks for processing. Useful when text exceeds token limits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to split into chunks"
                    },
                    "max_chunk_size": {
                        "type": "integer",
                        "description": "Maximum characters per chunk (default: 4000)",
                        "default": 4000
                    }
                },
                "required": ["text"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict) -> str:
    """
    Execute a tool function and return the result as a JSON string.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
        
    Returns:
        JSON string containing the result or error message
    """
    try:
        if tool_name == "extract_article_content":
            url = arguments.get("url")
            if not url:
                return json.dumps({"error": "URL is required"})
            content = extract_content(url)
            return json.dumps({"content": content, "length": len(content)})
        
        elif tool_name == "get_article_metadata":
            url = arguments.get("url")
            if not url:
                return json.dumps({"error": "URL is required"})
            
            # Try to extract metadata using trafilatura
            try:
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    metadata = trafilatura.extract_metadata(downloaded)
                    if metadata:
                        result = {
                            "title": metadata.title if hasattr(metadata, 'title') else None,
                            "author": metadata.author if hasattr(metadata, 'author') else None,
                            "date": str(metadata.date) if hasattr(metadata, 'date') and metadata.date else None,
                            "site_name": metadata.sitename if hasattr(metadata, 'sitename') else None,
                        }
                        return json.dumps({k: v for k, v in result.items() if v is not None})
            except Exception:
                pass
            
            # Fallback: try to get basic info from HTML
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'lxml')
                
                title = None
                if soup.title:
                    title = soup.title.string
                elif soup.find('meta', property='og:title'):
                    title = soup.find('meta', property='og:title').get('content')
                
                result = {}
                if title:
                    result["title"] = title.strip()
                
                return json.dumps(result) if result else json.dumps({"message": "No metadata found"})
            except Exception as e:
                return json.dumps({"error": f"Failed to extract metadata: {str(e)}"})
        
        elif tool_name == "chunk_text":
            text = arguments.get("text")
            max_chunk_size = arguments.get("max_chunk_size", 4000)
            if not text:
                return json.dumps({"error": "Text is required"})
            chunks = chunk_text(text, max_chunk_size)
            return json.dumps({
                "chunks": chunks,
                "count": len(chunks),
                "total_length": len(text)
            })
        
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


def chunk_text(text: str, max_chunk_size: int = 4000) -> list[str]:
    """
    Split text into chunks for processing.
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        word_len = len(word) + 1  # +1 for space
        if current_size + word_len > max_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = word_len
        else:
            current_chunk.append(word)
            current_size += word_len
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def summarize_text(text: str, style: str, model: str, max_words: int, use_tools: bool = True) -> str:
    """
    Summarize text using OpenAI GPT with optional function calling support.
    
    Args:
        text: Text to summarize
        style: 'points' or 'para'
        model: OpenAI model name
        max_words: Maximum words in summary
        use_tools: Whether to enable function calling tools (default: True)
        
    Returns:
        Summary text
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
        Exception: If OpenAI API call fails
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it with your OpenAI API key."
        )
    
    client = OpenAI(api_key=api_key)
    
    # Determine if we need to chunk
    # Rough estimate: 1 token ≈ 4 chars, leave room for response
    needs_chunking = len(text) > 12000  # ~3000 tokens
    
    if needs_chunking:
        # Get tracer - will use the same tracer provider that agentbay initialized
        tracer = trace.get_tracer("article_summarizer")
        
        # Wrap entire chunking operation in a single span to share trace ID
        with tracer.start_as_current_span("summarize_article_chunks", kind=SpanKind.INTERNAL) as span:
            print("Article is long, processing in chunks...", file=sys.stderr)
            chunks = chunk_text(text, max_chunk_size=12000)
            
            span.set_attribute("article.chunk_count", len(chunks))
            span.set_attribute("article.total_length", len(text))
            
            # Summarize each chunk - all will share the same trace ID
            chunk_summaries = []
            for i, chunk in enumerate(chunks, 1):
                print(f"Processing chunk {i}/{len(chunks)}...", file=sys.stderr)
                try:
                    summary = _summarize_single(client, chunk, "para", model, max_words // 2)
                    if summary:
                        chunk_summaries.append(summary)
                    else:
                        print(f"Warning: Chunk {i} returned empty summary, skipping...", file=sys.stderr)
                except Exception as e:
                    print(f"Error processing chunk {i}: {e}", file=sys.stderr)
                    # Continue with other chunks instead of failing completely
                    continue
            
            if not chunk_summaries:
                raise Exception("All chunks failed to generate summaries")

            # Combine and create final summary - also shares the same trace ID
            combined = " ".join(chunk_summaries)
            print("Creating final summary...", file=sys.stderr)
            return _summarize_single(client, combined, style, model, max_words, use_tools)
    else:
        return _summarize_single(client, text, style, model, max_words, use_tools)


def _summarize_single(client: OpenAI, text: str, style: str, model: str, max_words: int, use_tools: bool = True) -> str:
    """Create a single summary using OpenAI API with optional tool calling support."""

    if style == "points":
        style_instruction = (
            "Create a bullet-point summary with 5-8 key points. "
            "Each point should be concise (1-2 lines maximum). "
            "Start each point with a bullet (•) or dash (-)."
        )
    else:  # para
        style_instruction = (
            f"Create a concise paragraph summary in 1-2 paragraphs, approximately {max_words} words. "
            "Write in clear, flowing prose."
        )

    system_prompt = (
        "You are a professional article summarizer. "
        "Your summaries are factual, concise, and capture the essential information. "
        "Do not speculate, add opinions, or include unnecessary quotes. "
        "Focus on the main ideas and key facts."
    )

    user_prompt = (
        f"{style_instruction}\n\n"
        f"Article content:\n\n{text}\n\n"
        f"Provide a {style} summary:"
    )

    try:
        # Initialize messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Maximum number of tool call iterations to prevent infinite loops
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            # GPT-5 only supports default temperature (1), so we omit it for GPT-5
            api_params = {
                "model": model,
                "messages": messages
            }

            # Add tools if enabled
            if use_tools:
                api_params["tools"] = TOOLS

            # Only include temperature for non-GPT-5 models
            if not model.startswith("gpt-5"):
                api_params["temperature"] = 0.3

            response = client.chat.completions.create(**api_params)

            # Debug: Check response structure
            if not response.choices:
                print(f"DEBUG: Full API response: {response}", file=sys.stderr)
                raise Exception("OpenAI API returned no choices in response")

            choice = response.choices[0]
            finish_reason = getattr(choice, 'finish_reason', 'unknown')

            if not choice.message:
                print(f"DEBUG: Response structure: {response}", file=sys.stderr)
                raise Exception("OpenAI API response missing message field")

            # Add assistant message to conversation
            assistant_message = {"role": "assistant", "content": choice.message.content}
            
            # Check for tool calls
            tool_calls = getattr(choice.message, 'tool_calls', None)
            if tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            
            messages.append(assistant_message)

            # If there are tool calls, execute them and continue the loop
            if tool_calls:
                print(f"Executing {len(tool_calls)} tool call(s)...", file=sys.stderr)
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    # Execute the tool
                    tool_result = execute_tool(tool_name, tool_args)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result
                    })
                
                iteration += 1
                continue  # Continue the loop to get the next response

            # No tool calls - we're done
            content = choice.message.content

            if content is None:
                # Print debug info
                print(f"DEBUG: Finish reason: {finish_reason}", file=sys.stderr)
                print(f"DEBUG: Response ID: {getattr(response, 'id', 'unknown')}", file=sys.stderr)
                print(f"DEBUG: Model used: {getattr(response, 'model', 'unknown')}", file=sys.stderr)
                print(f"DEBUG: Full choice object: {choice}", file=sys.stderr)
                raise Exception(
                    f"OpenAI API returned None content. Finish reason: {finish_reason}. "
                    f"This might indicate the model '{model}' doesn't exist or there was an API error."
                )

            summary_text = content.strip()

            # Check if summary is empty
            if not summary_text:
                print(f"DEBUG: Finish reason: {finish_reason}", file=sys.stderr)
                print(f"DEBUG: Content length: {len(content) if content else 0}", file=sys.stderr)
                raise Exception(
                    f"Received empty summary from OpenAI API. "
                    f"Finish reason: {finish_reason}. "
                    f"Model: {model}. "
                    f"Try using --model gpt-4o if the requested model is not available."
                )

            return summary_text

        # If we exit the loop, we hit max iterations
        raise Exception(f"Maximum tool call iterations ({max_iterations}) reached. The model may be stuck in a loop.")

    except Exception as e:
        raise Exception(f"OpenAI API error: {e}")


def save_summary_to_html(summary: str, url: str, format_choice: str, output_file: Optional[str] = None) -> str:
    """
    Save summary to an HTML file and return the file path.
    
    Args:
        summary: The summary text
        url: Original article URL
        format_choice: Format used ('points' or 'para')
        output_file: Optional custom output file path
        
    Returns:
        Path to the created HTML file
    """
    if output_file is None:
        # Create a temporary file with .html extension
        temp_dir = tempfile.gettempdir()
        output_file = os.path.join(temp_dir, f"article_summary_{os.getpid()}.html")
    
    # Format summary text - preserve line breaks for points
    if format_choice == "points":
        # Convert bullet points to HTML list
        summary_html = summary.replace('\n', '<br>')
        # Wrap in a styled container
        formatted_summary = f'<div style="line-height: 1.8;">{summary_html}</div>'
    else:
        # For paragraphs, preserve line breaks
        summary_html = summary.replace('\n\n', '</p><p>').replace('\n', '<br>')
        formatted_summary = f'<p>{summary_html}</p>'
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article Summary</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .meta {{
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 30px;
        }}
        .meta a {{
            color: #3498db;
            text-decoration: none;
        }}
        .meta a:hover {{
            text-decoration: underline;
        }}
        .summary {{
            font-size: 16px;
            color: #2c3e50;
            white-space: pre-wrap;
        }}
        .summary p {{
            margin: 15px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #95a5a6;
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Article Summary</h1>
        <div class="meta">
            <strong>Source:</strong> <a href="{url}" target="_blank">{url}</a><br>
            <strong>Format:</strong> {format_choice.title()}
        </div>
        <div class="summary">
            {formatted_summary}
        </div>
        <div class="footer">
            Generated by Article Summarization CLI Agent
        </div>
    </div>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file


def main():
    """Main entry point for the CLI."""
    try:
        # Parse arguments
        url, format_choice, model, max_words, output_format, use_tools = parse_arguments()
        pending_url = url
        pending_format = format_choice

        while True:
            if not pending_url:
                pending_url, pending_format = get_user_input()
            else:
                pending_format = prompt_for_format(pending_format)

            current_url = pending_url
            current_format = pending_format

            # Extract content
            text = extract_content(current_url)

            # Summarize
            tool_status = "with tools" if use_tools else "without tools"
            print(f"\nGenerating {current_format} summary using {model} ({tool_status})...\n", file=sys.stderr)
            summary = summarize_text(text, current_format, model, max_words, use_tools)

            # Output based on format preference
            if output_format in ["console", "both"]:
                print("=" * 80)
                print("SUMMARY")
                print("=" * 80)
                print(summary)
                print("=" * 80)

            if output_format in ["html", "both"]:
                html_file = save_summary_to_html(summary, current_url, current_format)
                print(f"\nSummary saved to: {html_file}", file=sys.stderr)

                # Open in browser
                try:
                    file_url = f"file://{os.path.abspath(html_file)}"
                    webbrowser.open(file_url)
                    print(f"Opening summary in browser...", file=sys.stderr)
                except Exception as e:
                    print(f"Could not open browser automatically: {e}", file=sys.stderr)
                    print(f"Please open this file manually: {html_file}", file=sys.stderr)

            continue_choice = input("\nSummarize another article? (y/n): ").strip().lower()
            if continue_choice not in ("y", "yes"):
                print("\nExiting article summarizer.", file=sys.stderr)
                break

            print("\nReady for another article!", file=sys.stderr)
            pending_url = None
            pending_format = None
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
