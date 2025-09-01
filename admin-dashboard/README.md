# Twilio Voice AI - Admin Dashboard

A modern React.js admin dashboard for managing and monitoring the Twilio Voice AI Assistant system.

## 🚀 Features

### 📊 Dashboard Overview
- **Real-time Statistics**: View total calls, recordings, transcripts, and success rates
- **Interactive Charts**: Call volume trends, intent distribution, and confidence metrics
- **Recent Activity**: Latest calls with quick access to details
- **Performance Metrics**: Average call duration, success rates, and system health

### 📞 Call Management
- **Call History**: Complete list of all voice calls with filtering and search
- **Call Details**: View detailed information including transcripts and recordings
- **Status Tracking**: Monitor call status (completed, failed, in-progress)
- **Intent Analysis**: See AI confidence scores and detected intents

### 🎙️ Recording Management
- **Audio Playback**: Built-in audio player for call recordings
- **Recording Grid**: Visual cards with metadata and playback controls
- **Download Support**: Direct download of recordings
- **Search & Filter**: Find recordings by call ID, phone number, or intent

### 📝 Transcript Management
- **Conversation View**: Full conversation transcripts with speaker identification
- **Chat Interface**: Chat-like display showing customer and AI interactions
- **Export Functionality**: Download transcripts as text files
- **Search & Filter**: Find transcripts by various criteria

### 📈 Analytics & Insights
- **Performance Charts**: Call volume trends, confidence trends, hourly distribution
- **Intent Analysis**: Distribution of customer intents and success rates
- **Time-based Metrics**: Filter analytics by different time periods
- **Top Intents Table**: Performance metrics for each intent category

### ⚙️ System Settings
- **Twilio Configuration**: Manage account credentials and phone numbers
- **AI Settings**: Configure confidence thresholds and response times
- **System Preferences**: Call forwarding, recording settings, analytics
- **Security Settings**: HTTPS, session timeouts, audit logging

## 🛠️ Technical Stack

- **React 18**: Modern React with hooks and functional components
- **React Router**: Client-side routing for SPA navigation
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Recharts**: Beautiful and responsive charts
- **Lucide React**: Modern icon library
- **Axios**: HTTP client for API calls
- **React Hot Toast**: Toast notifications
- **Date-fns**: Date utility library

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ and npm
- Python Flask backend running (see main project README)

### Installation

1. **Navigate to the admin dashboard directory:**
   ```bash
   cd admin-dashboard
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

### Development

```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## 📁 Project Structure

```
admin-dashboard/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   └── Sidebar.js          # Navigation sidebar
│   ├── pages/
│   │   ├── Dashboard.js         # Main dashboard overview
│   │   ├── Calls.js            # Call management
│   │   ├── Recordings.js       # Recording management
│   │   ├── Transcripts.js      # Transcript management
│   │   ├── Analytics.js        # Analytics and charts
│   │   └── Settings.js         # System settings
│   ├── App.js                  # Main app component
│   ├── index.js                # React entry point
│   └── index.css               # Global styles
├── package.json
├── tailwind.config.js
└── README.md
```

## 🔧 Configuration

### Environment Variables
The dashboard connects to your Flask backend via proxy configuration in `package.json`:

```json
{
  "proxy": "http://localhost:5000"
}
```

### API Integration
The dashboard expects the following API endpoints from your Flask backend:

- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/calls` - Call history
- `GET /api/recordings` - Recording list
- `GET /api/transcripts` - Transcript list
- `GET /api/analytics` - Analytics data
- `GET /api/settings` - System settings
- `POST /api/settings` - Update settings

## 🎨 UI Components

### Responsive Design
- **Mobile-first**: Optimized for all screen sizes
- **Sidebar Navigation**: Collapsible on mobile devices
- **Grid Layouts**: Responsive card and table layouts
- **Touch-friendly**: Optimized for touch interactions

### Color Scheme
- **Primary**: Blue (#3B82F6) for main actions
- **Success**: Green (#10B981) for positive states
- **Warning**: Yellow (#F59E0B) for warnings
- **Danger**: Red (#EF4444) for errors
- **Neutral**: Gray scale for text and backgrounds

### Interactive Elements
- **Loading States**: Spinner animations during data fetching
- **Toast Notifications**: Success/error feedback
- **Hover Effects**: Smooth transitions on interactive elements
- **Modal Dialogs**: For detailed views and confirmations

## 📊 Data Visualization

### Charts Used
- **Line Charts**: For time-series data (call volume, confidence trends)
- **Area Charts**: For cumulative metrics
- **Bar Charts**: For categorical data (hourly distribution)
- **Pie Charts**: For distribution data (intent breakdown)
- **Progress Bars**: For performance metrics

### Real-time Updates
- **Auto-refresh**: Dashboard stats update automatically
- **Live Indicators**: System status and connection health
- **WebSocket Ready**: Prepared for real-time updates

## 🔒 Security Features

### Authentication Ready
- **Protected Routes**: Ready for authentication implementation
- **Session Management**: Prepared for user sessions
- **Role-based Access**: Structure for different user roles

### Data Protection
- **HTTPS Only**: Secure cookie configuration
- **Input Validation**: Form validation and sanitization
- **CSRF Protection**: Ready for CSRF token implementation

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Static Hosting
The build output can be deployed to:
- **Netlify**: Drag and drop the `build` folder
- **Vercel**: Connect your GitHub repository
- **AWS S3**: Upload build files to S3 bucket
- **Firebase Hosting**: Deploy to Firebase

### Environment Configuration
For production, update the proxy configuration or set up proper API endpoints.

## 🔧 Customization

### Adding New Pages
1. Create a new component in `src/pages/`
2. Add the route to `App.js`
3. Add navigation item to `Sidebar.js`

### Styling
- **Tailwind CSS**: Use utility classes for styling
- **Custom Components**: Create reusable components
- **Theme Customization**: Modify `tailwind.config.js`

### API Integration
- **Axios**: Use for HTTP requests
- **Error Handling**: Implement proper error boundaries
- **Loading States**: Add loading indicators

## 📈 Performance

### Optimization
- **Code Splitting**: React Router handles lazy loading
- **Image Optimization**: Optimized icons and assets
- **Bundle Size**: Minimal dependencies
- **Caching**: Browser caching for static assets

### Monitoring
- **Error Tracking**: Ready for error monitoring tools
- **Analytics**: Prepared for usage analytics
- **Performance Metrics**: Core Web Vitals ready

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the browser console for errors
- Verify API connectivity
- Review the Flask backend logs
- Test with sample data

## 🔮 Future Enhancements

- **Real-time Updates**: WebSocket integration for live data
- **Advanced Analytics**: More detailed performance metrics
- **User Management**: Multi-user support with roles
- **Export Features**: PDF reports and data exports
- **Mobile App**: React Native version
- **Dark Mode**: Theme switching capability 