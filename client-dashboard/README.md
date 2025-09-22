# AgentAI Client Dashboard

A modern React.js client portal for managing and monitoring AI assistant interactions.

## 🚀 Features

### 📊 Client Dashboard
- **Personal Statistics**: View your call history, recordings, and transcripts
- **Recent Activity**: Quick overview of your latest AI interactions
- **Success Metrics**: Track your AI assistant performance
- **Quick Stats**: Average call duration, success rates, and active sessions

### 📞 Call Management
- **Call History**: Complete list of your voice calls with filtering and search
- **Call Details**: View detailed information including duration and status
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

### 👤 Profile Management
- **Account Information**: Update username and email
- **Password Management**: Secure password change with current password verification
- **Account Details**: View member since date and last login information
- **Security Settings**: Change password with modal interface

## 🛠️ Technical Stack

- **React 18**: Modern React with hooks and functional components
- **React Router**: Client-side routing for SPA navigation
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Lucide React**: Modern icon library
- **Axios**: HTTP client for API calls
- **React Hot Toast**: Toast notifications
- **Date-fns**: Date utility library

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ and npm
- Python Flask backend running (see main project README)

### Installation

1. **Navigate to the client dashboard directory:**
   ```bash
   cd client-dashboard
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
   Navigate to `http://localhost:4000` (or the port shown in terminal)

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
client-dashboard/
├── public/
│   ├── index.html
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── Sidebar.js          # Client navigation sidebar
│   │   ├── Header.js           # Client header with profile dropdown
│   │   └── PrivateRoute.js     # Authentication guard
│   ├── pages/
│   │   ├── Dashboard.js         # Client dashboard overview
│   │   ├── Calls.js            # Call management
│   │   ├── Recordings.js       # Recording management
│   │   ├── Transcripts.js      # Transcript management
│   │   ├── Profile.js          # Profile management
│   │   ├── Login.js            # Client login
│   │   ├── ForgotPassword.js   # Password reset request
│   │   └── ResetPassword.js    # Password reset form
│   ├── App.js                  # Main app component
│   ├── index.js                # React entry point
│   ├── index.css               # Global styles
│   └── api.js                  # API configuration
├── package.json
├── tailwind.config.js
├── postcss.config.js
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

- `GET /api/auth/me` - Check authentication status
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile
- `PUT /api/auth/change-password` - Change password
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password
- `GET /api/client/dashboard` - Client dashboard stats
- `GET /api/client/calls` - Client call history
- `GET /api/client/recordings` - Client recordings
- `GET /api/client/transcripts` - Client transcripts

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
- **Modal Dialogs**: For password changes and confirmations

## 🔒 Security Features

### Authentication
- **Protected Routes**: Client-only access with authentication guard
- **Session Management**: Secure session handling
- **Role-based Access**: Clients cannot access admin features

### Data Protection
- **HTTPS Only**: Secure cookie configuration
- **Input Validation**: Form validation and sanitization
- **Password Security**: Secure password change with current password verification

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
- **Export Features**: PDF reports and data exports
- **Mobile App**: React Native version
- **Enhanced Security**: Two-factor authentication
- **Custom Themes**: User-selectable color schemes
