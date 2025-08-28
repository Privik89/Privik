# Privik Frontend

The React.js frontend for the Privik Email Security Platform.

## Features

- **Modern UI**: Built with React 18, Tailwind CSS, and Heroicons
- **Real-time Dashboard**: Live threat monitoring and statistics
- **Email Analysis**: Comprehensive email threat analysis interface
- **User Risk Management**: Monitor user behavior and risk profiles
- **Threat Intelligence**: View threat indicators and intelligence feeds
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Prerequisites

- Node.js 16+ 
- npm 8+
- Backend API running on http://localhost:8000

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
# Make the script executable
chmod +x start_frontend.sh

# Start the frontend
./start_frontend.sh
```

### Option 2: Manual Setup

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The frontend will be available at http://localhost:3000

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

### Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Sidebar.js      # Navigation sidebar
│   ├── StatCard.js     # Statistics display card
│   └── AlertCard.js    # Alert notification card
├── pages/              # Main application pages
│   ├── Dashboard.js    # Main dashboard
│   ├── EmailAnalysis.js # Email threat analysis
│   ├── ThreatIntel.js  # Threat intelligence
│   ├── UserRisk.js     # User risk management
│   └── Settings.js     # Application settings
├── App.js              # Main application component
├── index.js            # Application entry point
└── index.css           # Global styles and Tailwind imports
```

### Styling

The application uses Tailwind CSS with custom Privik brand colors:

- `privik-blue-*` - Primary brand blue
- `privik-red-*` - Danger/threat colors  
- `privik-green-*` - Success/safe colors

### API Integration

The frontend connects to the backend API through:

- **Proxy**: Configured in `package.json` to proxy requests to http://localhost:8000
- **React Query**: For data fetching and caching
- **Axios**: For HTTP requests (ready for implementation)

## Building for Production

```bash
npm run build
```

This creates a `build` folder with optimized production files.

## Deployment

The frontend can be deployed to any static hosting service:

- **Netlify**: Drag and drop the `build` folder
- **Vercel**: Connect your repository
- **AWS S3**: Upload the `build` folder
- **Docker**: Use a static file server

## Contributing

1. Follow the existing code style
2. Use Tailwind CSS for styling
3. Add proper TypeScript types when possible
4. Test your changes thoroughly

## License

Same as the main Privik project.
