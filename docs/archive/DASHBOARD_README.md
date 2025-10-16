# 🎨 Web Dashboard - Unified IPTV Platform

Interfaccia web moderna per la gestione della piattaforma IPTV unificata.

## 📋 Features

### Dashboard Principale
- **Statistics Cards**: 4 card con metriche real-time
  - Total Channels
  - Online Channels  
  - Active Users
  - Active Streams

- **Quick Actions**:
  - Trigger Scraping
  - Update EPG
  - Check Channels Status

- **System Info**:
  - Server configuration
  - AceStream engine status
  - Service health indicators

### Channels Management
- Lista completa canali con tabella interattiva
- Ricerca e filtri
- Status indicators (online/offline)
- Actions: Play, Edit, Delete

### Other Sections (Placeholder)
- Users Management
- Scraper Configuration
- EPG Management
- Settings

## 🎨 Design

### Layout
- **Responsive sidebar** con navigazione
- **Dark/Light mode** toggle
- **Bootstrap 5** styling
- **Bootstrap Icons**

### Colors
- Primary: #0d6efd (Blue)
- Success: #198754 (Green)
- Danger: #dc3545 (Red)
- Warning: #ffc107 (Yellow)

### Components
- Cards con hover effects
- Tables responsive con scroll
- Loading overlays
- Alert notifications
- Status badges

## 🔌 API Endpoints

### Dashboard Data
```
GET /api/dashboard/stats
GET /api/channels?limit=100
GET /api/health
```

### Actions
```
POST /api/scraper/trigger
POST /api/epg/update
POST /api/channels/check
```

## 📁 File Structure

```
app/
├── templates/
│   ├── layout.html          # Base layout
│   ├── dashboard.html       # Dashboard page
│   ├── channels.html        # Channels page
│   ├── users.html          # Users page (placeholder)
│   ├── scraper.html        # Scraper page (placeholder)
│   ├── epg.html            # EPG page (placeholder)
│   └── settings.html       # Settings page (placeholder)
├── static/
│   ├── css/
│   │   └── style.css       # Custom styles
│   ├── js/
│   │   └── main.js         # Utility functions
│   └── favicon/            # Favicon files
└── api/
    ├── dashboard.py        # Web routes
    └── api_endpoints.py    # API endpoints
```

## 🚀 Usage

### Access Dashboard
```
http://localhost:58055/
```

### Navigation
- Dashboard: `/`
- Channels: `/channels`
- Users: `/users`
- Scraper: `/scraper`
- EPG: `/epg`
- Settings: `/settings`

### Theme Toggle
Click the theme toggle button in the sidebar to switch between light and dark modes. Preference is saved in localStorage.

## 🔧 Customization

### Modify Colors
Edit `app/static/css/style.css`:
```css
:root {
    --primary-color: #0d6efd;
    --success-color: #198754;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
}
```

### Add New Pages
1. Create template in `app/templates/`
2. Add route in `app/api/dashboard.py`
3. Add navigation link in `layout.html`

### Add API Endpoints
Add new endpoints in `app/api/api_endpoints.py`

## 📊 JavaScript Functions

### Available Utilities
- `apiCall(endpoint, options)` - Make API calls
- `copyToClipboard(text)` - Copy to clipboard
- `showToast(message, type)` - Show notifications
- `formatBytes(bytes)` - Format byte sizes
- `formatDate(dateString)` - Format dates

### Example Usage
```javascript
// Load data
const data = await apiCall('/dashboard/stats');

// Show notification
showToast('Action completed!', 'success');

// Copy text
copyToClipboard('http://localhost:58055');
```

## 🎯 Features to Implement

- [ ] User management complete page
- [ ] Scraper configuration interface
- [ ] EPG source management
- [ ] Settings editor
- [ ] Channel editor modal
- [ ] Stream player integration
- [ ] Real-time WebSocket updates
- [ ] Export/Import functions
- [ ] Backup management
- [ ] Logs viewer

## 📝 Notes

- Interface inspired by acestream-scraper
- Bootstrap 5.3.0
- Bootstrap Icons 1.10.0
- Fully responsive design
- Auto-refresh data every 30 seconds
- Service status checked every 30 seconds

## 🐛 Troubleshooting

### Static files not loading
Check that `app/static` directory exists and is mounted correctly in `main.py`

### Template errors
Ensure Jinja2 is installed: `pip install jinja2`

### API errors
Check server logs and ensure all services are running

## 📄 License

Part of Unified IPTV AceStream Platform - v1.0.0
