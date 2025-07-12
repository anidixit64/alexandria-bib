# Alexandria

A web application with React frontend and Python Flask backend.

## Project Structure

```
alexandria-bib/
├── public/          # React public files
├── src/             # React source code
├── app.py           # Flask backend
├── requirements.txt # Python dependencies
├── package.json     # Node.js dependencies
└── start.sh         # Startup script
```

## Quick Start

### Option 1: One Command (Recommended)
```bash
./start.sh
```

### Option 2: Using npm
```bash
npm run dev:install  # Install all dependencies
npm run dev          # Start both services
```

### Option 3: Manual Setup

#### Backend Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Flask backend:
   ```bash
   python app.py
   ```
   
   The backend will run on http://localhost:5000

#### Frontend Setup

1. Install Node.js dependencies:
   ```bash
   npm install
   ```

2. Run the React development server:
   ```bash
   npm start
   ```
   
   The frontend will run on http://localhost:3000

## Features

- React frontend with modern UI
- Flask backend with REST API
- CORS enabled for cross-origin requests
- Health check endpoint at `/api/health`
- One-command startup for both services

## Development

- Frontend: React with modern CSS animations
- Backend: Flask with JSON API responses
- Both services can run simultaneously for development
- Use `Ctrl+C` to stop both services when using the startup script