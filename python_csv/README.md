# HTML Question Parser

A Python tool for parsing CBSE-style HTML question banks and storing them in MongoDB with S3-hosted images.

## Quick Start

```bash
cd question_parser
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python parser.py "path/to/question-bank.html" --images-root "path/to/images"
```

See [question_parser/README.md](question_parser/README.md) for detailed documentation.

## Features

- Parses HTML question banks into structured MongoDB documents
- Uploads images to AWS S3 and replaces local paths with S3 URLs
- Supports flexible configuration via environment variables
- Handles various image formats and naming patterns
- Optional Excel cross-validation

## Requirements

- Python 3.10+
- MongoDB database
- AWS S3 bucket
- See `question_parser/requirements.txt` for Python dependencies