# GitHub Backlog Generator Frontend

React-based frontend for the GitHub Backlog Generator that provides real-time log streaming from CloudWatch Logs.

## Features

- Real-time log streaming from AWS CloudWatch
- Log filtering and search
- Auto-scrolling with pause on user interaction
- Copy logs to clipboard
- Download logs as text file
- Responsive design for mobile and desktop
- Dark/light theme support

## Development

### Prerequisites

- Node.js 16+ and npm
- Backend API running (see ../backend/README.md)

### Installation

```bash
npm install
```

### Running Locally

```bash
# Start development server on http://localhost:3000
npm run dev

# The dev server proxies API calls to http://localhost:4000
# Override with API_URL environment variable:
API_URL=https://api.example.com npm run dev
```

### Building for Production

```bash
# Create optimized build in dist/
npm run build

# Preview production build
npx serve dist
```

### Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

### Linting

```bash
# Check for linting errors
npm run lint

# Fix linting errors
npm run lint:fix
```

## Architecture

### Components

- **App.js**: Main application component that handles routing and task state
- **LogViewer.jsx**: Core log streaming component with filtering and controls
- **LogViewer.css**: Styles for the log viewer with dark/light themes

### API Integration

The frontend expects these API endpoints:

- `GET /api/status?task_id={taskId}` - Get task status and metadata
- `GET /api/logs?log_stream={stream}&next_token={token}` - Stream logs

### URL Parameters

The app expects a `taskId` parameter in the URL:
```
https://example.com/?taskId=task-12345678
```

## Deployment

### S3 + CloudFront

1. Build the production bundle:
   ```bash
   npm run build
   ```

2. Upload to S3:
   ```bash
   aws s3 sync dist/ s3://your-bucket-name/ --delete
   ```

3. Invalidate CloudFront cache:
   ```bash
   aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
   ```

### Docker

```bash
# Build image
docker build -t github-backlog-ui .

# Run container
docker run -p 80:80 github-backlog-ui
```

## Configuration

### Environment Variables

- `API_URL`: Backend API URL (default: `/api` for proxy)
- `REACT_APP_THEME`: Default theme (`dark` or `light`, default: `dark`)

### Customization

1. **Themes**: Edit `LogViewer.css` for color schemes
2. **Polling Interval**: Pass `pollInterval` prop to LogViewer (ms)
3. **Max Retries**: Pass `maxRetries` prop to LogViewer

## Component Usage

### Embedding LogViewer

```jsx
import LogViewer from './components/LogViewer';

function MyApp() {
  return (
    <LogViewer
      apiUrl="https://api.example.com"
      taskId="task-12345678"
      logStream="ecs/github-backlog/abc123"
      onComplete={(status) => console.log('Task completed:', status)}
      pollInterval={2000}
      maxRetries={3}
    />
  );
}
```

### Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| apiUrl | string | Yes | - | Base URL for API endpoints |
| taskId | string | Yes | - | ECS task ID |
| logStream | string | Yes | - | CloudWatch log stream name |
| onComplete | function | No | - | Callback when task completes |
| pollInterval | number | No | 2000 | Log polling interval (ms) |
| maxRetries | number | No | 3 | Max retries for failed requests |

## Browser Support

- Chrome/Edge 80+
- Firefox 75+
- Safari 13+
- Mobile browsers (iOS Safari, Chrome for Android)

## Security

- No sensitive data stored in browser
- API authentication handled by backend
- XSS protection via React's built-in escaping
- Content Security Policy headers recommended

## Troubleshooting

### Logs not appearing
1. Check browser console for errors
2. Verify API URL is correct
3. Ensure task ID and log stream are valid
4. Check CORS configuration on API

### Performance issues
1. Increase `pollInterval` for less frequent updates
2. Clear browser cache
3. Check network latency to API

### Build errors
1. Delete `node_modules/` and reinstall
2. Clear webpack cache: `rm -rf node_modules/.cache/`
3. Check Node.js version (16+ required)