# 📘 Textbook Content Generator using Ollama

This Python script automates the extraction and generation of educational content from textbook pages using the [Ollama](https://ollama.com) LLM API (such as LLaMA 3). It reads a JSON file containing scanned or OCR-processed text, cleans it, and generates summaries, quizzes, definitions, and more for the first 10 pages of the book.

---

## 🚀 Features

- Clean and preprocess raw page text (remove headers, footers, page numbers, etc.)
- Generate a wide range of educational materials:
  - ✅ Chapter Summaries
  - ✅ Important Points
  - ✅ Formula Sheets
  - ✅ Definition Banks
  - ✅ Concept Explanations
  - ✅ Solved Examples
  - ✅ Practice Questions
  - ✅ Quiz Creation
  - ✅ Fill-in-the-Blanks
  - ✅ True/False Statements
  - ✅ Higher Order Thinking Skills (HOTS)
  - ✅ Real-Life Applications
- Save generated content into categorized JSON files
- Simple and customizable for any textbook or subject

---

## 📂 Input Format

The script expects a JSON file named `pages.json` with the following structure:

```json
[
  {
    "pageNumber": 1,
    "imageText": "Raw OCR or scanned text content of page 1..."
  },
  {
    "pageNumber": 2,
    "imageText": "Page 2 content..."
  },
  ...
]
