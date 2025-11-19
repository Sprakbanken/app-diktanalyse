# Diktanalyse

A Python web application that annotates end rhymes, anaphora and alliteration in poetry.

## Features

- **Flask Web Interface**: Simple and intuitive UI for submitting tasks
- **Background Processing**: Uses Python threading for asynchronous task execution
- **Real-time Updates**: Polling mechanism to check task status
- **Computational Operations**: Performs various mathematical and text analysis operations
- **No External Dependencies**: No Redis or message broker required

## Architecture

- **Web Layer**: Flask application (`app.py`)
- **Worker Layer**: ThreadPoolExecutor for background tasks (`tasks.py`)
- **Frontend**: HTML/CSS/JavaScript with responsive design

## Prerequisites

### For Docker (Recommended)

- [Docker](https://www.docker.com/get-started) and Docker Compose

### For Local Development

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

### Docker Setup (Recommended)

No installation needed! Just make sure Docker and Docker Compose are installed.

### Local Development with uv

1. **Install uv** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Sync dependencies**:

   ```bash
   uv sync
   ```

### Using pip

1. **Create a virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -e .
   ```

3. **Configure environment variables** (optional):

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Running the Application

### Docker (Recommended)

#### Quick Start

```bash
docker compose up
```

The application will be available at `http://localhost:5000`

#### Build and Run

```bash
# Build the image
docker compose build

# Run the container
docker compose up

# Run in detached mode (background)
docker compose up -d

# Stop the container
docker compose down
```

#### Using Docker directly (without compose)

```bash
# Build the image
docker build -t poetry-analysis-app .

# Run the container
docker run -p 5000:5000 poetry-analysis-app
```

### Local Development (uv)

```bash
uv run python app.py
```

### Local Development (pip/venv)

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python app.py
```

Or use the VS Code task: `Run App`

The application will be available at `http://localhost:5000`

## Usage

1. Open your browser to `http://localhost:5000`
2. Enter a number or text in the input field
3. Click "Submit Task"
4. The application will process your input in the background and display results

### Example Inputs

**Numerical Input** (e.g., `10`):

- Square, square root, factorial
- Sine and cosine values

**Text Input** (e.g., `hello world`):

- Character count, word count
- Uppercase conversion
- Reversed text
- Character frequency analysis

## Project Structure

```text
poetry-analysis-app/
├── app.py                 # Flask web application
├── tasks.py              # Background task definitions
├── config.py             # Configuration settings
├── pyproject.toml        # Project dependencies (uv/pip)
├── requirements.txt      # Legacy requirements file
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Docker Compose configuration
├── .dockerignore         # Docker build exclusions
├── templates/
│   └── index.html       # Frontend UI
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Customization

### Adding New Computational Operations

Edit `tasks.py` and modify the `process_computation` function:

```python
@celery_app.task(name='tasks.process_computation')
def process_computation(user_input, task_id):
    # Add your custom computational logic here
    result = your_custom_function(user_input)
    return result
```

### Modifying the UI

Edit `templates/index.html` to customize the frontend appearance and behavior.

### Configuration

Modify `config.py` or set environment variables in `.env` to change:

- Flask settings (SECRET_KEY, DEBUG mode)

## Production Deployment

### Docker Production Setup

1. Build the production image:

   ```bash
   docker build -t poetry-analysis-app:latest .
   ```

2. Run with production settings:

   ```bash
   docker run -d \
     -p 5000:5000 \
     -e FLASK_DEBUG=False \
     -e MAX_WORKERS=8 \
     --name poetry-app \
     poetry-analysis-app:latest
   ```

3. Or use Docker Compose with production overrides:

   ```bash
   docker compose -f docker-compose.yml up -d
   ```

### Local Deployment

For production use without Docker:

1. Set `FLASK_DEBUG=False` in `.env`
2. Use a production WSGI server (e.g., Gunicorn):

   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. Consider using a process manager (e.g., Supervisor) to keep the app running
4. Use environment variables for sensitive configuration
5. For heavy workloads, consider increasing `max_workers` in the ThreadPoolExecutor

## Fetching Poem Data from GitHub

The application includes a script (`parse_poems.py`) to fetch and parse poem data from the [norn-uio/norn-poems](https://github.com/norn-uio/norn-poems) GitHub repository.

### Usage

**Fetch poems from GitHub API:**

```bash
python parse_poems.py --github
```

**Fetch with custom file limit:**

```bash
python parse_poems.py --github --max-files=10
```

**Use embedded sample data (default):**

```bash
python parse_poems.py
```

### How it Works

The script provides the following GitHub API functions:

1. **`fetch_github_repo_contents()`** - Retrieves list of XML files from the repository
2. **`fetch_xml_file_content()`** - Downloads raw XML file content
3. **`parse_tei_xml()`** - Parses TEI XML format to extract poem metadata (author, title, year, poems)
4. **`fetch_poems_from_github()`** - Orchestrates the full fetch and parse workflow

The parsed data is saved to `static/poems.json` for use in the web application.

### TEI XML Parsing

The parser extracts:
- **Author**: From `<author>` element
- **Book Title**: From `<title type='main'>` or `<title>` element
- **Year**: From `<date>` element
- **Poems**: From `<lg type='poem'>` elements with `<head>` titles

## Troubleshooting

### Docker Issues

- **Container won't start**: Check logs with `docker compose logs` or `docker logs <container-id>`
- **Port already in use**: Change the port mapping in `docker-compose.yml` (e.g., `"8080:5000"`)
- **Permission errors**: On Linux, you may need to run with `sudo` or add your user to the docker group
- **Build fails**: Clear Docker cache with `docker builder prune` and rebuild

### General Issues

- **Tasks not processing**: Check the console output for errors in the background threads
- **Import errors**: Make sure all dependencies are installed in your virtual environment
- **Port already in use**: Change the port in `app.py` or stop the other process using port 5000

## License

MIT License
