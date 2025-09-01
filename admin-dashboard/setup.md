# Admin Dashboard Setup Guide

This guide will help you set up and run the React.js admin dashboard for your Twilio Voice AI Assistant.

## 🚀 Quick Start

### 1. Prerequisites
- Node.js 16+ installed
- Python Flask backend running (see main project README)
- npm or yarn package manager

### 2. Install Dependencies
```bash
cd admin-dashboard
npm install
```

### 3. Start Development Server
```bash
npm start
```

### 4. Access Dashboard
Open your browser and navigate to: `http://localhost:3000`

## 🔧 Configuration

### Backend Connection
The dashboard is configured to connect to your Flask backend at `http://localhost:5000` via the proxy setting in `package.json`.

### Environment Variables
No additional environment variables are needed for the dashboard itself, but ensure your Flask backend has the required environment variables:

```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
NGROK_URL=https://your-ngrok-url.ngrok.io
HUMAN_AGENT_NUMBER=+1234567890
SECRET_KEY=your_secret_key
```

## 📊 Features Overview

### Dashboard
- **Real-time Statistics**: View call metrics, success rates, and system health
- **Interactive Charts**: Call volume trends and intent distribution
- **Recent Activity**: Latest calls with quick access to details

### Call Management
- **Call History**: Complete list with filtering and search
- **Call Details**: View transcripts, recordings, and intent analysis
- **Status Tracking**: Monitor call status and performance

### Recording Management
- **Audio Playback**: Built-in player for call recordings
- **Download Support**: Direct download of recordings
- **Search & Filter**: Find recordings by various criteria

### Transcript Management
- **Conversation View**: Full transcripts with speaker identification
- **Chat Interface**: Chat-like display of conversations
- **Export Functionality**: Download transcripts as text files

### Analytics
- **Performance Charts**: Call volume, confidence trends, hourly distribution
- **Intent Analysis**: Distribution and success rates
- **Time-based Metrics**: Filter by different time periods

### Settings
- **Twilio Configuration**: Manage credentials and phone numbers
- **AI Settings**: Configure confidence thresholds and response times
- **System Preferences**: Call forwarding, recording settings
- **Security Settings**: HTTPS, session timeouts, audit logging

## 🛠️ Development

### Project Structure
```
admin-dashboard/
├── src/
│   ├── components/
│   │   └── Sidebar.js          # Navigation
│   ├── pages/
│   │   ├── Dashboard.js         # Main dashboard
│   │   ├── Calls.js            # Call management
│   │   ├── Recordings.js       # Recording management
│   │   ├── Transcripts.js      # Transcript management
│   │   ├── Analytics.js        # Analytics and charts
│   │   └── Settings.js         # System settings
│   ├── App.js                  # Main app
│   └── index.js                # Entry point
├── public/
│   └── index.html
├── package.json
└── tailwind.config.js
```

### Available Scripts
```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Eject from Create React App
npm run eject
```

## 🔌 API Integration

The dashboard expects these API endpoints from your Flask backend:

### Dashboard Stats
- `GET /api/dashboard/stats` - Dashboard statistics

### Call Management
- `GET /api/calls` - Call history

### Recording Management
- `GET /api/recordings` - Recording list
- `GET /recordings/<filename>` - Serve recording files

### Transcript Management
- `GET /api/transcripts` - Transcript list
- `GET /transcripts/<filename>` - Serve transcript files

### Analytics
- `GET /api/analytics` - Analytics data

### Settings
- `GET /api/settings` - Get system settings
- `POST /api/settings` - Update system settings

## 🎨 Customization

### Styling
The dashboard uses Tailwind CSS. You can customize the theme in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          // Your custom colors
        }
      }
    }
  }
}
```

### Adding New Pages
1. Create a new component in `src/pages/`
2. Add the route to `App.js`
3. Add navigation item to `Sidebar.js`

### Adding New API Endpoints
1. Add the endpoint to your Flask backend
2. Update the React component to call the new endpoint
3. Handle loading states and error cases

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Deployment Options
- **Netlify**: Drag and drop the `build` folder
- **Vercel**: Connect your GitHub repository
- **AWS S3**: Upload build files to S3 bucket
- **Firebase Hosting**: Deploy to Firebase

### Environment Configuration
For production, update the proxy configuration or set up proper API endpoints.

## 🔒 Security

### Authentication Ready
The dashboard is prepared for authentication implementation:
- Protected routes structure
- Session management
- Role-based access control

### Data Protection
- HTTPS configuration
- Input validation
- CSRF protection ready

## 🐛 Troubleshooting

### Common Issues

1. **Dashboard not loading data**
   - Check if Flask backend is running on port 5000
   - Verify API endpoints are working
   - Check browser console for errors

2. **CORS errors**
   - Ensure Flask backend allows requests from localhost:3000
   - Check proxy configuration in package.json

3. **Build errors**
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility

4. **Charts not rendering**
   - Verify Recharts library is installed
   - Check data format for charts

### Debug Mode
Enable debug mode in your Flask backend:
```python
app.run(debug=True)
```

## 📞 Support

For issues and questions:
- Check browser console for JavaScript errors
- Review Flask backend logs
- Verify API connectivity
- Test with sample data

## 🔮 Next Steps

1. **Connect Real Data**: Replace mock data with actual API calls
2. **Add Authentication**: Implement user login and session management
3. **Real-time Updates**: Add WebSocket support for live data
4. **Advanced Analytics**: Implement more detailed metrics
5. **Export Features**: Add PDF reports and data exports
6. **Mobile Optimization**: Improve mobile responsiveness 