# Email Dossier Creator - React Frontend

A React.js frontend for the Email Thread Analyzer and Client Dossier Creator application, designed to match the functionality of the original Streamlit interface.

## Features

- **Dark Theme UI**: Modern dark interface matching the original design
- **Step-by-Step Flow**: Follows the same workflow as the Streamlit app
- **Search Parameters**: Date range, keyword, sender email, and general query filters
- **Thread Selection**: Multi-select checkboxes for email threads
- **Analysis Results**: Structured email analysis with formatted output
- **Client Dossier**: Generate detailed client dossiers
- **Error Handling**: User-friendly error and warning messages
- **Responsive Design**: Works on desktop and mobile devices

## Application Flow

1. **Step 1**: Find relevant emails based on date range and optional filters
2. **Step 2**: Select one or more threads to analyze their content
3. **Step 3**: Generate a detailed client dossier if needed

## Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Gmail API credentials
- GROQ API key

### Quick Start (Windows)
```bash
# Double-click the start_app.bat file
# Or run from command line:
start_app.bat
```

### Manual Setup
1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install React dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   Create a `.env` file with:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Start the application**:
   ```bash
   # Option 1: Use the startup script
   python start_dev.py
   
   # Option 2: Start servers separately
   # Terminal 1 - Backend
   python app.py
   # Terminal 2 - Frontend
   npm start
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

## Project Structure

```
├── src/
│   ├── App.js                 # Main application component
│   ├── index.js               # React entry point
│   ├── index.css              # Global styles
│   ├── components/
│   │   └── SearchResults.js   # Search results component
│   └── utils/
│       └── parseOutput.js     # CrewAI output parsing utilities
├── public/
│   └── index.html             # HTML template
├── app.py                     # Flask backend with API endpoints
├── requirements.txt           # Python dependencies
├── package.json              # React dependencies
├── start_dev.py              # Development startup script
├── start_app.bat             # Windows startup script
└── README.md                 # This file
```

## API Integration

The frontend communicates with the Flask backend through these endpoints:

- `POST /api/find_threads` - Search for email threads
- `POST /api/analyze_thread` - Analyze single thread
- `POST /api/analyze_multiple_threads` - Analyze multiple threads
- `POST /api/generate_dossier` - Generate meeting and client dossiers
- `GET /api/health` - Health check

## Features Comparison with Streamlit

| Feature | Streamlit | React |
|---------|-----------|-------|
| Step-by-step flow | ✅ | ✅ |
| Date range selection | ✅ | ✅ |
| Optional search filters | ✅ | ✅ |
| Thread selection | ✅ | ✅ |
| Analysis results | ✅ | ✅ |
| Client dossier generation | ✅ | ✅ |
| Error handling | ✅ | ✅ |
| Responsive design | ❌ | ✅ |
| Dark theme | ❌ | ✅ |
| Real-time updates | ❌ | ✅ |

## Development

- **Built with**: React 18, styled-components, lucide-react
- **Backend**: Flask with CORS support
- **HTTP Client**: Axios for API calls
- **Styling**: Styled-components for CSS-in-JS

## Available Scripts

- `npm start` - Start React development server
- `npm build` - Build for production
- `npm test` - Run tests
- `python app.py` - Start Flask backend
- `python start_dev.py` - Start both servers

## Troubleshooting

1. **Port conflicts**: Make sure ports 3000 and 5000 are available
2. **API errors**: Check that your GROQ_API_KEY is set in the `.env` file
3. **Gmail access**: Ensure your Gmail API credentials are properly configured
4. **Dependencies**: Run `npm install` and `pip install -r requirements.txt` if you encounter missing modules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the application
5. Submit a pull request 