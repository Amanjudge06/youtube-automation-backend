# 🎬 Snip-Z - Web Interface

A modern, responsive web dashboard for managing your YouTube Shorts automation system.

## ✨ Features

### 📊 **Dashboard**
- Real-time automation status monitoring
- System performance metrics
- Recent video gallery
- Quick action controls
- API health monitoring

### 📺 **Video Library** 
- Browse all generated videos
- Download videos locally
- View detailed metadata
- Direct YouTube links
- Performance analytics

### 📈 **Trending Topics**
- Live trending topic detection
- Virality score analysis
- Topic breakdown and insights
- One-click video generation
- Regional trend monitoring

### ⚙️ **Settings**
- API key management
- Automation configuration
- Video quality settings
- Upload preferences
- Regional settings

### 📋 **Logs**
- Real-time system logs
- Filterable by log level
- Export functionality
- Auto-refresh option
- Error highlighting

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ installed
- Python 3.8+ with the automation backend
- All API keys configured

### Installation

1. **Run the setup script:**
   ```bash
   ./setup-frontend.sh
   ```

2. **Or manual setup:**
   ```bash
   # Install dependencies
   cd frontend
   npm install
   
   # Build for production
   npm run build
   
   # Start the backend
   cd ..
   python app.py
   ```

3. **Access the interface:**
   - Production: http://localhost:8000
   - Development: http://localhost:3000

## 🛠️ Development

### Start Development Mode
```bash
./start-dev.sh
```
This starts both the backend API and frontend development server with live reload.

### Build for Production
```bash
cd frontend
npm run build
```

### API Endpoints

The frontend communicates with these backend endpoints:

- `GET /api/status` - Automation status
- `POST /api/automation/trigger` - Start automation
- `GET /api/videos` - Video library
- `GET /api/trends` - Trending topics
- `GET /api/logs` - System logs
- `POST /api/config/update` - Update settings

## 📱 Interface Overview

### Dashboard
![Dashboard](docs/dashboard.png)
- Real-time status monitoring
- Performance metrics
- Quick controls

### Video Library
![Video Library](docs/videos.png)
- Grid view of all videos
- Detailed video information
- Download and YouTube links

### Trending Topics
![Trending](docs/trending.png)
- Live trending data
- Virality analysis
- One-click generation

## 🎨 Technology Stack

- **Frontend:** React 18, TailwindCSS, Lucide Icons
- **Backend:** FastAPI, Python
- **Build:** Create React App
- **Styling:** Tailwind CSS + Custom Components

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Dashboard.js      # Main dashboard
│   │   ├── VideoLibrary.js   # Video management
│   │   ├── TrendingTopics.js # Trending analysis
│   │   ├── Settings.js       # Configuration
│   │   └── Logs.js          # Log viewer
│   ├── App.js               # Main application
│   ├── index.js             # React entry point
│   └── index.css           # Global styles
└── package.json             # Dependencies
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the frontend directory:
```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_ENABLE_ANALYTICS=false
```

### API Configuration
Update the backend API base URL in `src/App.js` if needed:
```javascript
const API_BASE = '/api'; // For production
// const API_BASE = 'http://localhost:8000/api'; // For external API
```

## 🚀 Deployment

### Production Build
```bash
npm run build
# Serves from backend at localhost:8000
```

### External Hosting
```bash
# Build the frontend
npm run build

# Deploy the build/ directory to your hosting service
# Update API_BASE_URL to point to your backend
```

## 🐛 Troubleshooting

### Common Issues

**Port already in use:**
```bash
./stop-dev.sh  # Stop existing servers
./start-dev.sh # Restart
```

**Build errors:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

**API connection issues:**
- Check if backend is running on port 8000
- Verify CORS settings in FastAPI
- Check API key configuration

### Log Locations
- Frontend logs: Browser console
- Backend logs: Terminal output or `/api/logs`
- System logs: `logs/` directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the YouTube Automation system. See main README for license information.