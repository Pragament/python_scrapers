import PyPDF2
import json
import os
from datetime import datetime
import ollama
import re

# Function to clean extracted text (remove noise like page numbers, headers, etc.)
def clean_text(text):
    text = re.sub(r'Page \d+|\d+/\d+', '', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'Chapter \d+.*?\d+', '', text)
    return text

# Function to extract meaningful text from all pages of the PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text_by_page = {}
        for page_num in range(len(reader.pages)):  # Process all pages
            page = reader.pages[page_num]
            raw_text = page.extract_text()
            cleaned_text = clean_text(raw_text)
            if cleaned_text:
                text_by_page[page_num + 1] = cleaned_text
    return text_by_page

# Function to interact with Ollama and generate content
def generate_content_with_ollama(text, prompt_type):
    prompts = {
        "Chapter Summaries": f"Summarize the following text in 150-200 words, suitable for a class 9 student: {text[:1500]}",
        "Important Points": f"Extract 5-7 key points or formulas from the following text in bullet points: {text[:1500]}",
        "Definition Bank": f"Identify and define 3-5 key terms from the following text in simple words: {text[:1500]}",
        "Formula Sheet": f"List all formulas from the following text with a one-sentence explanation for each: {text[:1500]}",
        "Concept Explanation": f"Explain the main concept from the following text in simple language with one example: {text[:1500]}",
        "Solved Examples": f"Generate 2 solved examples based on the following text, showing detailed steps: {text[:1500]}",
        "Practice Questions": f"Create 5 practice questions (mix of MCQs, short answer, and long answer) from the following text: {text[:1500]}",
        "Quiz Creation": f"Create a 5-question multiple-choice quiz based on the following text, with answers and explanations: {text[:1500]}",
        "Fill in the Blanks": f"Create 3 fill-in-the-blank questions from the following text: {text[:1500]}",
        "True/False": f"Create 3 true/false statements from the following text with correct answers: {text[:1500]}",
        "Higher Order Thinking (HOTS)": f"Create 2 higher-order thinking questions (HOTS) from the following text that encourage analysis and application: {text[:1500]}",
        "Real Life": f"Describe 2 real-life applications of concepts from the following text: {text[:1500]}"
    }
    prompt = prompts.get(prompt_type, "")
    if not prompt:
        return None
    try:
        print(f"Generating {prompt_type} with Ollama...")
        response = ollama.generate(model='llama3', prompt=prompt)
        return response['response']
    except Exception as e:
        print(f"Error generating {prompt_type}: {e}")
        return None

# Function to generate educational content for each page
def generate_educational_content(pdf_path, output_dir="textbook_content"):
    # Ensure the output directory exists with error handling
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
    except PermissionError as e:
        print(f"Error: Permission denied creating directory '{output_dir}': {e}")
        return None
    except Exception as e:
        print(f"Error creating directory '{output_dir}': {e}")
        return None

    pages_text = extract_text_from_pdf(pdf_path)
    if not pages_text:
        print("No meaningful content extracted from the PDF.")
        return None
    content_types = [
        "Chapter Summaries", "Important Points", "Definition Bank", "Formula Sheet",
        "Concept Explanation", "Solved Examples", "Practice Questions", "Quiz Creation",
        "Fill in the Blanks", "True/False", "Higher Order Thinking (HOTS)", "Real Life"
    ]
    # Structure to hold content for each type
    textbook_data = {
        "textbook_name": os.path.basename(pdf_path),
        "generated_at": datetime.now().isoformat(),
        "pages": {}
    }
    for page_num, text in pages_text.items():
        print(f"Processing page {page_num}...")
        page_data = {
            "page_number": page_num,
            "raw_text": text[:500],
            "generated_content": {}
        }
        for content_type in content_types:
            generated_content = generate_content_with_ollama(text, content_type)
            if generated_content:
                page_data["generated_content"][content_type] = generated_content
        textbook_data["pages"][f"page_{page_num}"] = page_data

    # Save each content type to a separate JSON file
    output_paths = []
    for content_type in content_types:
        content_type_cleaned = content_type.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")  # Fix for "True/False"
        content_data = {
            "textbook_name": textbook_data["textbook_name"],
            "generated_at": textbook_data["generated_at"],
            "content_type": content_type,
            "pages": {}
        }
        # Add the content for this type for all pages
        for page_key, page_data in textbook_data["pages"].items():
            content_data["pages"][page_key] = {
                "page_number": page_data["page_number"],
                "raw_text": page_data["raw_text"],
                "generated_content": {content_type: page_data["generated_content"].get(content_type, None)}
            }
        output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(pdf_path))[0]}_{content_type_cleaned}.json")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=4, ensure_ascii=False)
            output_paths.append(output_path)
            print(f"Generated content saved to {output_path}")
        except Exception as e:
            print(f"Error saving {output_path}: {e}")
            return None
    return output_paths

if __name__ == "__main__":
    import time
    start_time = time.time()
    pdf_path = "Give Your pdf path here"   # Pdf path 
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        exit(1)
    output_files = generate_educational_content(pdf_path)
    if output_files:
        for output_file in output_files:
            print(f"Generated content saved to {output_file}")
    else:
        print("Failed to generate content.")
    print(f"Total time taken: {(time.time() - start_time)/60:.2f} minutes")