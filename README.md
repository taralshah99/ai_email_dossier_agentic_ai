# Email Dossier - AI-Powered Email Analysis Application

A comprehensive React + Flask application that transforms your Gmail conversations into actionable business insights using AI-powered analysis. Generate meeting agendas, client dossiers, and comprehensive email summaries with advanced search capabilities.

## ✨ Features

### 🔐 **Secure Authentication**
- **Google OAuth 2.0 Integration** - Secure login with your Google account
- **Session Management** - 24-hour persistent sessions across browser refreshes
- **Auto-logout** - Sessions cleared on server restart for security
- **User Profile Display** - Shows email and Gmail statistics

### 🔍 **Advanced Email Search**
- **Date Range Filtering** - Flexible date selection with smart defaults
- **Keyword Search** - Required keyword filtering with intelligent matching
- **Sender Filtering** - Filter by specific email addresses
- **Advanced Query Support** - Gmail-style search operators:
  - `subject:"meeting"` - Search email subjects
  - `has:attachment` - Find emails with attachments
  - `is:important` - Important emails only
  - `from:@domain.com` - Domain-based filtering
  - `filename:pdf` - Specific file types
  - Boolean operators (`OR`, `AND`) for complex queries

### 📊 **AI-Powered Analysis**
- **Thread Processing** - Extract metadata and participants from email threads
- **Multi-thread Analysis** - Analyze multiple conversations simultaneously
- **Client Detection** - Automatically identify external clients from email domains
- **Participant Mapping** - Comprehensive contact extraction with roles

### 📋 **Intelligent Dossier Generation**
- **Meeting Flow Dossier** - Generate structured meeting agendas and action items
- **Client Dossier** - Create detailed client profiles and interaction summaries
- **Till-Date Agenda** - Comprehensive project timelines and milestones
- **Customizable Output** - Tailored reports based on email content

### 🎨 **Modern UI/UX**
- **Responsive Design** - Works seamlessly on desktop and mobile
- **Dark Theme Interface** - Professional, easy-on-eyes design
- **Real-time Updates** - Live status updates and progress indicators
- **Intuitive Navigation** - Step-by-step workflow with clear guidance
- **Error Handling** - User-friendly error messages and recovery options

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **Google Cloud Project** with Gmail API enabled
- **GROQ API Key** for AI analysis

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd ai_email_dossier_agentic_ai
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create environment file
echo "FLASK_SECRET_KEY=your-secret-key-here" > .env
echo "OAUTH_REDIRECT_URI=http://localhost:5000/api/auth/callback" >> .env
echo "GROQ_API_KEY=your-groq-api-key" >> .env
```

### 3. Google OAuth Setup
1. **Create OAuth 2.0 Credentials** in Google Cloud Console
2. **Download credentials** as `web_credentials.json`
3. **Add authorized origins**:
   - `http://localhost:3000`
   - `http://localhost:5000`
4. **Add redirect URI**:
   - `http://localhost:5000/api/auth/callback`

### 4. Frontend Setup
```bash
# Install React dependencies
npm install
```

### 5. Start the Application
```bash
# Start Flask backend
python app.py

# In another terminal, start React frontend
npm start
```

### 6. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Login** with your Google account to begin

## 🏗️ Application Architecture

### Backend (Flask)
```
├── app.py                     # Main Flask application with API routes
├── auth.py                    # Google OAuth authentication system
├── session_manager.py         # Session lifecycle management
├── gmail_utils.py            # Gmail API integration utilities
├── crewai_agents.py          # AI agents for email analysis
└── utils.py                  # General utility functions
```

### Frontend (React)
```
├── src/
│   ├── App.js                     # Main application with authentication routing
│   ├── components/
│   │   ├── LoginScreen.js         # Google OAuth login interface
│   │   ├── UserProfile.js         # User profile display
│   │   ├── SearchResults.js       # Email thread search results
│   │   ├── AnalysisReport.js      # Email analysis display
│   │   ├── MeetingFlowReport.js   # Meeting dossier component
│   │   └── ClientDossierReport.js # Client dossier component
│   ├── contexts/
│   │   └── AuthContext.js         # Authentication state management
│   └── utils/
│       ├── authUtils.js           # Authentication utilities
│       └── parseOutput.js         # AI output parsing
```

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/login` - Initiate Google OAuth flow
- `GET /api/auth/callback` - Handle OAuth callback
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/logout` - Logout and revoke tokens
- `GET /api/auth/profile` - Get user profile

### Email Operations
- `POST /api/find_threads` - Search Gmail threads
- `POST /api/process_threads_metadata` - Extract thread metadata
- `POST /api/analyze_thread` - Analyze single thread
- `POST /api/analyze_multiple_threads` - Analyze multiple threads

### Dossier Generation
- `POST /api/generate_meeting_dossier` - Create meeting flow dossier
- `POST /api/generate_client_dossier` - Create client dossier

## 🛡️ Security Features

### Authentication Security
- **OAuth 2.0** with Google's secure authorization
- **Session-based authentication** with signed cookies
- **CSRF protection** with OAuth state parameters
- **Automatic token refresh** for expired credentials

### Session Management
- **24-hour session timeout** for security
- **Server restart cleanup** - all sessions cleared on restart
- **Secure session storage** with filesystem backend
- **Token revocation** on logout

### Data Protection
- **No email storage** - processes emails in memory only
- **Credentials encryption** in session storage
- **CORS protection** with specific origin allowlist
- **HTTPS enforcement** for production deployments

## 🌐 Production Deployment

### Google Cloud Console Updates
1. **Add production URLs** to OAuth settings:
   ```
   Authorized JavaScript Origins:
   - https://yourdomain.com
   - https://www.yourdomain.com
   
   Authorized Redirect URIs:
   - https://yourdomain.com/api/auth/callback
   ```

2. **Update OAuth Consent Screen**:
   - Add production domain
   - Publish app (may require Google review)

### Environment Variables
```env
FLASK_SECRET_KEY=production-secret-key
OAUTH_REDIRECT_URI=https://yourdomain.com/api/auth/callback
GROQ_API_KEY=your-groq-api-key
```

### Code Updates
- Update CORS origins in `app.py`
- Set production base URLs
- Use HTTPS for all OAuth redirects

## 🔍 Advanced Search Examples

### Business Use Cases
```
# Meeting-related emails
subject:meeting has:attachment

# Invoice and payment tracking
subject:invoice has:attachment filename:pdf

# Client communications
from:@clientdomain.com is:important

# Project updates
subject:roadmap OR subject:timeline OR subject:milestone

# Document sharing
has:attachment (filename:docx OR filename:pdf)

# Urgent matters
is:important (subject:urgent OR subject:asap)
```

## 📈 Usage Workflow

### 1. **Authentication**
- Click "Continue with Gmail"
- Authorize Gmail read access
- Automatic login for 24 hours

### 2. **Email Search**
- Set date range (defaults to Jan 2023 - today)
- Enter required keyword
- Optional: Add sender email filter
- Optional: Use advanced Gmail operators
- Click "Find Relevant Emails"

### 3. **Thread Selection**
- Review search results
- Select threads using checkboxes
- Click "Process Selected Threads"

### 4. **AI Analysis**
- Choose analysis type:
  - Meeting Flow Dossier
  - Client Dossier
  - Till-Date Agenda
- AI generates structured reports
- View results in organized format

## 🛠️ Development

### Tech Stack
- **Frontend**: React 18, styled-components, Axios
- **Backend**: Flask, Flask-Session, Google APIs
- **AI**: GROQ API, CrewAI framework
- **Authentication**: Google OAuth 2.0
- **Styling**: CSS-in-JS with styled-components

### Development Commands
```bash
# Backend development
python app.py

# Frontend development
npm start

# Build for production
npm run build

# Install dependencies
pip install -r requirements.txt
npm install
```

## 🐛 Troubleshooting

### Common Issues

**Authentication Errors (401)**
- Clear browser cookies for localhost
- Restart Flask server to clear sessions
- Check `.env` file has `FLASK_SECRET_KEY`

**OAuth Scope Errors**
- Clear browser data and Flask sessions
- Ensure `include_granted_scopes='false'` in auth.py

**API Connection Issues**
- Verify both servers are running
- Check CORS settings in app.py
- Confirm ports 3000 and 5000 are available

**Gmail API Errors**
- Verify `web_credentials.json` is present
- Check Google Cloud Console OAuth settings
- Ensure Gmail API is enabled in your project

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For support, please open an issue in the GitHub repository or contact the development team.

---

**Built with ❤️ using React, Flask, and Google APIs**