Image Processing - PDF Top Strip Darkener

Overview
This tool darkens the top strip of each page in a PDF, which can help reduce glare from scanned document headers or washed-out top margins.

Project Structure
- data/ — sample input/output PDFs
- src/enhancer.py — main script
- requirements.txt — Python dependencies

Prerequisites
- Python 3.13 (or 3.10+ should work)
- Windows PowerShell (commands below use PowerShell)

Setup
1. (Optional) Activate the bundled virtual environment:
   - PowerShell:
     - .\venv\Scripts\Activate.ps1
2. Install dependencies:
   - If the venv is active:
     - python -m pip install -r .\requirements.txt
   - If you prefer to run without activating the venv (uses the bundled interpreter):
     - .\venv\Scripts\python.exe -m pip install -r .\requirements.txt

Run Command
- Using the bundled interpreter (recommended):
  - .\venv\Scripts\python.exe .\src\enhancer.py --input ".\data\input.pdf" --output ".\data\output.pdf"
- If your own Python is active:
  - python .\src\enhancer.py --input ".\data\input.pdf" --output ".\data\output.pdf"

Inputs and Outputs
- Input PDF: Provide with --input. By default, a sample is at data\input.pdf.
- Output PDF: Provide with --output. Example writes to data\output.pdf.
- The script does not modify the original file; it writes a new PDF at the path you specify.

Optional Arguments
- --strip_height: Height in pixels of the top strip to darken. Default: 100
  - Example:
    - .\venv\Scripts\python.exe .\src\enhancer.py --input ".\data\input.pdf" --output ".\data\output2.pdf" --strip_height 160

Notes
- The repository path contains a space ("github pro"). The commands above use relative paths, so you can run them from the project root without quoting the directory name.
- If you encounter ModuleNotFoundError: fitz, ensure PyMuPDF is installed (provided via requirements.txt). The script imports fitz (PyMuPDF) and Pillow.

Examples
- Darken default sample input to a new file:
  - .\venv\Scripts\python.exe .\src\enhancer.py --input ".\data\input.pdf" --output ".\data\output2.pdf"
