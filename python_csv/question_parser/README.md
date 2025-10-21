# HTML Question Parser → MongoDB + S3

A Python tool that parses CBSE-style HTML question banks, uploads referenced images to AWS S3, and stores normalized question documents in MongoDB.

## Features

- **Smart Image Processing**: Extracts image references from HTML, finds local images by filename, and uploads to S3
- **MongoDB Integration**: Stores questions with proper schema including S3 image URLs
- **Flexible Configuration**: Supports environment variables, .env files, and CLI overrides
- **Excel Cross-check**: Optional validation against Excel files
- **Robust Image Resolution**: Handles various filename patterns and extensions

## Prerequisites

- Python 3.10+ (tested with 3.10, 3.11, 3.12)
- AWS S3 bucket with appropriate permissions
- MongoDB Atlas or compatible database
- Virtual environment (recommended)

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd python_csv/question_parser
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net
MONGO_DATABASE_NAME=adminjs

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=ap-south-1
AWS_BUCKET=your_bucket_name

# Question Parser Defaults
AUTHOR_USER_ID=your_author_id_here
QUESTION_LANGUAGE=English
QUESTION_SUBJECT=Mathematics
QUESTION_TOPIC=Generic
QUESTION_SUBTOPIC=Generic
QUESTION_AGE=IX
```

### 3. Prepare Your Files

```
project/
├── question_parser/
│   ├── parser.py
│   └── images/          # Place your images here
│       ├── image1.png
│       ├── image2.jpg
│       └── ...
├── question-bank.html   # Your HTML file
└── .env                 # Your configuration
```

### 4. Run the Parser

```bash
python parser.py "path/to/question-bank.html" --images-root "path/to/images"
```

## Usage

### Basic Usage

```bash
python parser.py "question-bank.html" --images-root "images/"
```

### With Excel Cross-check

```bash
python parser.py "question-bank.html" --images-root "images/" --excel "validation.xlsx"
```

### AWS Credentials Override

```bash
python parser.py "question-bank.html" --images-root "images/" \
  --aws-access-key-id "AKIA..." \
  --aws-secret-access-key "secret..." \
  --aws-region "us-east-1"
```

### Skip S3 Uploads (Offline Mode)

```bash
python parser.py "question-bank.html" --images-root "images/" --skip-s3
```

### Validate AWS Credentials

```bash
python parser.py "question-bank.html" --images-root "images/" --aws-validate
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection string | Required |
| `MONGO_DATABASE_NAME` | Target database name | `adminjs` |
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `ap-south-1` |
| `AWS_BUCKET` | S3 bucket name | `textbookpdf` |
| `AUTHOR_USER_ID` | Default author ID | Required |
| `QUESTION_LANGUAGE` | Default language | `English` |
| `QUESTION_SUBJECT` | Default subject | `Mathematics` |

### CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `html_file` | Path to HTML question bank | Required |
| `--images-root` | Directory containing images | `extracted_images` |
| `--excel` | Excel file for validation | None |
| `--aws-region` | AWS region override | From env |
| `--aws-access-key-id` | AWS access key override | From env |
| `--aws-secret-access-key` | AWS secret key override | From env |
| `--aws-profile` | AWS profile name | From env |
| `--aws-validate` | Validate credentials at startup | False |
| `--skip-s3` | Skip S3 uploads | False |
| `--env-file` | Custom .env file path | `.env` |

## Output Schema

### Questions Collection (`genericquestions`)

Each question document includes:

```json
{
  "_id": "ObjectId",
  "author_user_id": "ObjectId",
  "questionType": "MCQ",
  "questionNumber": 1,
  "questionText": "HTML with S3 image URLs",
  "options": [
    {
      "optionText": "HTML with S3 URLs",
      "imageDetails": [{"path": "s3_url", "width": 0, "height": 0}]
    }
  ],
  "imageDetails": [{"path": "s3_url", "width": 0, "height": 0}],
  "Images": ["s3_url1", "s3_url2"],
  "language": "English",
  "subject": "Mathematics",
  "topic": "Generic",
  "subtopic": "Generic",
  "priority": "NORMAL",
  "chapter": "Chapter Name",
  "answer": "Option 1",
  "marks": "1.00",
  "active": true,
  "approved": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Question Papers Collection (`questionpapers`)

```json
{
  "_id": "ObjectId",
  "title": "question-bank",
  "questions": ["ObjectId1", "ObjectId2", "..."]
}
```

## Image Processing

The parser intelligently handles image references:

1. **Extracts filename** from HTML src attributes (e.g., `./folder/image.png` → `image.png`)
2. **Searches locally** in your images directory
3. **Tries multiple extensions** (.png, .jpg, .jpeg, .webp, .gif, .bmp, .svg)
4. **Handles name variations** (case-insensitive, normalized matching)
5. **Uploads to S3** with organized key structure: `question_images/filename`
6. **Replaces HTML src** with S3 URLs in the stored documents

## Troubleshooting

### Common Issues

**"Unable to locate credentials"**
- Ensure AWS credentials are set in `.env` or environment
- Run `aws configure` if using AWS CLI
- Use `--aws-validate` to test credentials

**"MONGO_URI environment variable is required"**
- Set `MONGO_URI` in your `.env` file
- Ensure MongoDB connection string is correct

**Images not found**
- Verify `--images-root` points to the correct directory
- Check that image filenames match exactly (case-sensitive)
- Ensure images have supported extensions

**S3 upload failures**
- Verify AWS credentials have S3 permissions
- Check bucket exists and is in the correct region
- Ensure bucket policy allows PutObject operations

### Debug Mode

For detailed image resolution logging, temporarily add debug prints in `resolve_image_local_path()`.

## Security Notes

- **Never commit `.env` files** - they're in `.gitignore`
- **Use IAM roles** in production instead of access keys
- **Rotate credentials** regularly
- **Limit S3 permissions** to only what's needed

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review the configuration options
- Open an issue on GitHub