# Educational Content Generator from PDF using LLaMA3

This project provides a Python script to extract text from a PDF file (limited to the first page) and generate educational content using the LLaMA3 model via the Ollama framework. The script creates separate JSON files for 12 different content types (e.g., Chapter Summaries, Practice Questions, Quizzes) based on the extracted text.

## Features
- Extracts text from the first page of a PDF file.
- Generates 12 types of educational content using LLaMA3:
  - Chapter Summaries
  - Important Points
  - Definition Bank
  - Formula Sheet
  - Concept Explanation
  - Solved Examples
  - Practice Questions
  - Quiz Creation
  - Fill in the Blanks
  - True/False
  - Higher Order Thinking (HOTS)
  - Real Life Applications
- Saves each content type in a separate JSON file in the `textbook_content` directory.
- Includes error handling for file operations and Ollama interactions.
- Provides progress updates during execution.

## Prerequisites
- **Python 3.12** or later.
- **Ollama** installed to run the LLaMA3 model locally.
- Required Python libraries: `PyPDF2`, `ollama`.

## Installation

### 1. Install Ollama
- Download and install Ollama from [https://ollama.com/](https://ollama.com/).
- Pull the LLaMA3 model by running the following command in a Command Prompt: