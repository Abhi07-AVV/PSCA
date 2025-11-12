# Proposal Twin Detector

A tool that checks uploaded PDF proposals against a collection of past proposals for similarity using semantic embeddings from the Hugging Face API with the nvidia/Llama-Embed-Nemotron-8B model.

## Features

- Extracts text from PDFs using PyPDF2
- Chunks text into ~500-word sections
- Computes cosine similarity using embeddings from the Hugging Face API with nvidia/Llama-Embed-Nemotron-8B model
- Generates a detailed report with scores and highlights
- Recommends merging if overall similarity >60%
- Scans the entire 'Sample Proposal' folder structure including subdirectories
- Web-based interface for easy use

## Requirements

- Python 3.10+
- Libraries: PyPDF2, numpy, scikit-learn, huggingface-hub, python-dotenv
- Hugging Face API token

## Setup

1. Install the required packages:
   ```bash
   pip install PyPDF2 numpy scikit-learn huggingface-hub python-dotenv
   ```

2. Ensure your past proposals are in the `Sample Poroposal/` folder (PDF format) in any subdirectory structure

3. Set your Hugging Face API token in the `.env` file:
   ```
   HF_TOKEN=your_huggingface_token_here
   ```

## Usage Options

### Command Line Version
Run the detector with:
```bash
python proposal_checker.py
```

### Web Interface Version
1. Start the server:
   ```bash
   python server.py
   ```
   Or double-click on `start_server.bat` on Windows.

2. Open your browser and go to http://localhost:8000

3. Upload your proposal PDF and click "Analyze Proposal"

## API Usage

The tool uses the Hugging Face Inference API with the `nvidia/Llama-Embed-Nemotron-8B` model for semantic embeddings. This model provides state-of-the-art performance for understanding the meaning of research proposals, not just matching keywords.

## Output

- Console report with overall similarity score
- Top matches with similarity percentages
- Merge recommendation based on 60% threshold
- HTML report saved as `report.html` with color-coded highlights

## How It Works

1. Indexes all PDFs in the `Sample Poroposal/` folder (including subdirectories) into chunks and gets their embeddings using the Hugging Face API
2. Processes the uploaded PDF: extracts text, chunks it, and gets embeddings
3. Computes cosine similarities between all query chunks and document chunks
4. Finds the best match for each query chunk
5. Calculates average maximum similarity
6. Generates a detailed report with recommendations

## Privacy Notice

While the PDF processing happens locally, the semantic analysis is performed using the Hugging Face Inference API. Only the text chunks are sent to the API for embedding, not the full documents. This approach balances privacy with the need for advanced semantic understanding.