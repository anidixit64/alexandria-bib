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

## Testing

### Quick Test Run
```bash
./run_tests.sh            # Run all tests (backend, frontend, integration)
```

### Individual Test Suites

#### Frontend Tests (React)
```bash
npm test                    # Run tests in watch mode
npm run test:coverage      # Run tests with coverage report
```

#### Backend Tests (Python)
```bash
python -m pytest test_app.py -v    # Run backend tests with verbose output
python -m pytest test_app.py --cov=app  # Run tests with coverage
```

### Test Coverage

The test suite includes:

#### Backend Tests (`test_app.py`)
- **API Endpoint Tests**: Health check, home endpoint, search endpoint
- **Wikipedia Integration Tests**: Search, content retrieval, citation extraction
- **Error Handling Tests**: Missing queries, network errors, API failures
- **Unit Tests**: Individual function testing with mocked dependencies
- **Integration Tests**: Real API calls (when backend is running)

#### Frontend Tests (`src/SearchPage.test.js`)
- **Component Rendering**: Initial render, form elements, navigation
- **Search Functionality**: Form submission, API calls, loading states
- **Results Display**: Popup rendering, citation numbering, scroll behavior
- **Error Handling**: Network errors, API errors, user feedback
- **User Interactions**: Button clicks, form validation, navigation

#### Test Placeholders
Some tests include TODO sections for you to fill in:
- **Specific Citations**: Add expected citations for "Guy Fawkes", "Philosophy", "Mathematics"
- **Edge Cases**: Test special characters, long queries, non-English pages
- **Integration Scenarios**: Real API testing with different topics

### Code Quality
```bash
npm run lint              # Run ESLint
npm run lint:fix          # Fix ESLint issues
npm run format            # Format code with Prettier
npm run format:check      # Check code formatting
npm run ci                # Run all checks (format, lint, test)
```

## CI/CD

The project uses GitHub Actions for continuous integration:

- **Triggers**: Runs on pull requests and pushes to main/develop branches
- **Frontend Checks**: 
  - Code formatting (Prettier)
  - Linting (ESLint)
  - Unit tests with coverage
- **Backend Checks**:
  - Code formatting (Black)
  - Linting (Flake8)
  - Unit tests with coverage
- **Build**: Creates production build artifacts

### Coverage Requirements
- Frontend: 80% coverage threshold
- Backend: 80% coverage threshold