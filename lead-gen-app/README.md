# Lead Gen App - Retro UI SvelteKit

A complete, production-ready **Phase-1 SvelteKit** lead generation app that uses **Google Maps JavaScript API + Places API (New)** with **Retro UI** styling. Single purpose: **Search → Map → Results list → Save lead → Export CSV**.

## Features

- 🔍 **Search businesses** using Google Maps Places API (New)
- 🗺️ **Interactive map** with markers (Google Maps JavaScript API)
- 📱 **Responsive design** - desktop split view, mobile tabs
- 💾 **Local storage** for saved leads (no auth required)
- 📊 **CSV export** with complete business data
- 🎨 **Retro UI styling** - authentic retro/brutalist aesthetic
- 🔑 **Secure API integration** - requires proper Google Maps API setup

## Tech Stack

- **SvelteKit** (latest) with TypeScript
- **Tailwind CSS** for styling
- **Google Maps JavaScript API** + **Places API (New)**
- **localStorage** for data persistence
- **Retro UI** design system components

## Quick Start

### Prerequisites

- Node.js 18+ and pnpm/npm
- Google Cloud account with enabled APIs
- Domain restriction configured for security

### 1. Clone and Install

```bash
git clone <repository-url>
cd lead-gen-app
pnpm install
```

### 2. Google Maps API Setup

#### Enable Required APIs:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable these APIs:
   - **Maps JavaScript API**
   - **Places API (New)**

#### Get API Key:

**IMPORTANT**: You need **TWO API keys** for this app:

**1. Server-side API Key** (for Places API calls):
- Go to **Credentials** → **Create Credentials** → **API Key**
- **Application restrictions**: None (or IP addresses for production)
- **API restrictions**: Select only "Places API (New)"
- Use this key in your `.env` file

**2. Client-side API Key** (for Maps JavaScript API):
- Go to **Credentials** → **Create Credentials** → **API Key**
- **Application restrictions**: HTTP referrers
- **Add your domain(s)**: `localhost:5173/*`, `yourdomain.com/*`
- **API restrictions**: Select only "Maps JavaScript API"

**Alternative (Simpler Setup)**:
- Create ONE API key with **no application restrictions**
- **API restrictions**: Select "Maps JavaScript API" AND "Places API (New)"
- ⚠️ **Less secure** but works for development

#### Set Environment Variable:
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

### 3. Run the App

```bash
# Development mode
pnpm dev

# Production build
pnpm build
pnpm preview
```

Visit `http://localhost:5173`

## Usage Guide

### Desktop Layout
- **Left side**: Interactive Google Maps with markers
- **Right side**: Tabbed interface
  - **Results tab**: Search results with business cards
  - **My Leads tab**: Saved leads table with export

### Mobile Layout
- **Top**: Full-screen map with markers
- **Bottom**: Sliding panel with tabs
- **Bottom tabs**: Switch between Results and My Leads

### Search Flow
1. Enter **business type** (e.g., "restaurants", "coffee shops")
2. Enter **location** (e.g., "New York, NY", "San Francisco")
3. Click **Search** or press Enter
4. View results on map markers and results list
5. Click markers or "View Details" for more info
6. Click **"Save Lead"** to add to your leads
7. Go to **"My Leads"** tab to manage saved leads
8. Click **"Export CSV"** to download leads data

## Data Fields Collected

The app collects these fields from Google Places API (New):

### Core Fields (Places API New)
- `displayName` - Business name
- `formattedAddress` - Full address
- `internationalPhoneNumber` - International phone number
- `websiteUri` - Website URL
- `rating` - Google rating (1-5)
- `userRatingCount` - Number of reviews

### Additional Fields (Places API New)
- `primaryType` - Business category code
- `types[]` - All applicable categories
- `businessStatus` - OPERATIONAL, CLOSED_TEMPORARILY, etc.
- `location` - Latitude and longitude coordinates

### Removed Fields (Not Available in Places API New)
- `nationalPhoneNumber` - Use internationalPhoneNumber instead
- `editorialSummary` - Not available in new API
- `primaryTypeDisplayName` - Use primaryType instead

### CSV Export Schema
```
Name, Address, Phone, Website, Rating, Reviews, Category, Business Status
```
Note: Editorial Summary field is not available in Places API (New) so it will be empty in exports.

## API Configuration

### Field Mask Optimization (Places API New)
The app uses optimized field masks to minimize API costs:

```javascript
const FIELD_MASK = [
  'places.id',
  'places.displayName',
  'places.formattedAddress',
  'places.internationalPhoneNumber',
  'places.websiteUri',
  'places.rating',
  'places.userRatingCount',
  'places.primaryType',
  'places.types',
  'places.businessStatus',
  'places.location'
].join(',');
```

### Search Types

#### Text Search (Default) - Places API (New)
```javascript
// Used for: "restaurants in New York"
POST /api/places/search
{
  "textQuery": "restaurants in New York",
  "pageSize": 20
}
```

#### Nearby Search (Alternative) - Places API (New)
```javascript
// Used for: businesses near specific coordinates
POST /api/places/nearby
{
  "locationRestriction": {
    "circle": {
      "center": {"latitude": 40.7128, "longitude": -74.0060},
      "radius": 1000.0
    }
  },
  "includedTypes": ["restaurant"],
  "pageSize": 20
}
```

## Development Requirements

### API Key Required
The app requires a valid Google Maps API key to function. Without it, you'll see an error message and the map will not load.

### Switch Search Types
Edit `/src/lib/utils/maps.ts` to change between Text Search and Nearby Search:

```javascript
// For Text Search (current default)
const response = await fetch('/api/places/search', {
  method: 'POST',
  body: JSON.stringify({
    textQuery: `${query} in ${location}`,
    maxResultCount: 20
  })
});

// For Nearby Search (uncomment to use)
// const response = await fetch('/api/places/nearby', {
//   method: 'POST',
//   body: JSON.stringify({
//     locationRestriction: {
//       circle: { center: coords, radius: 5000 }
//     },
//     includedTypes: [businessType],
//     maxResultCount: 20
//   })
// });
```

## Security Features

### API Key Protection
- ✅ **Server-side proxy**: API key never exposed to client
- ✅ **Domain restrictions**: Key only works on specified domains
- ✅ **API restrictions**: Key only works with specified Google APIs
- ✅ **Rate limiting**: Simple protection against abuse
- ✅ **Input validation**: Server validates all requests

### Best Practices Implemented
- Environment variables for sensitive data
- Field masks to minimize API costs
- Error handling and fallbacks
- Input sanitization
- CORS considerations

## Project Structure

```
src/
├── lib/
│   ├── components/
│   │   ├── ui/           # Retro UI components
│   │   │   ├── Button.svelte
│   │   │   ├── Input.svelte
│   │   │   ├── Badge.svelte
│   │   │   ├── Card.svelte
│   │   │   └── Card*.svelte
│   │   ├── MapView.svelte
│   │   ├── SearchBar.svelte
│   │   ├── PlaceCard.svelte
│   │   ├── ResultsList.svelte
│   │   ├── LeadsTable.svelte
│   │   └── MobileTabs.svelte
│   ├── stores/
│   │   ├── app.ts       # App state
│   │   └── leads.ts     # Leads management
│   ├── types/
│   │   └── index.ts     # TypeScript interfaces
│   └── utils/
│       ├── maps.ts      # Google Maps utilities
│       └── csv.ts       # CSV export utilities
├── routes/
│   ├── api/places/
│   │   ├── search/+server.ts    # Text search proxy
│   │   └── nearby/+server.ts    # Nearby search proxy
│   ├── +layout.svelte
│   └── +page.svelte
├── app.html
├── app.css
└── ...
```

## Retro UI Components

The app uses only authentic Retro UI components:

### Button
```svelte
<Button variant="default|secondary|outline|link" size="sm|md|lg|icon">
  Click Me
</Button>
```

### Input
```svelte
<Input
  placeholder="Type something..."
  bind:value={inputValue}
/>
```

### Badge
```svelte
<Badge variant="default|outline|solid|surface" size="sm|md|lg">
  Label
</Badge>
```

### Card
```svelte
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    Content goes here
  </CardContent>
</Card>
```

## Commands Reference

```bash
# Development
pnpm dev              # Start dev server
pnpm build            # Build for production
pnpm preview          # Preview production build
pnpm check            # Run type checking

# Dependencies
pnpm install          # Install dependencies
```

## Troubleshooting

### API Key Issues

#### Error: Google Maps API key not configured
```
Solution:
1. Copy .env.example to .env
2. Add your actual Google Maps API key to .env
3. Restart the development server
4. Ensure the API key has the required permissions
```

#### Error: API_KEY_HTTP_REFERRER_BLOCKED
```
Error: "Requests from referer <empty> are blocked"
Cause: API key has HTTP referrer restrictions blocking server requests
Solution:
1. Go to Google Cloud Console → Credentials
2. Edit your API key
3. Set "Application restrictions" to "None" (for development)
4. Or create separate server/client keys as described above
```

#### Error: Places API request failed (403)
```
Cause: Places API (New) not enabled or billing not set up
Solution:
1. Enable "Places API (New)" in Google Cloud Console
2. Set up billing account (required for Places API)
3. Verify API key has Places API permissions
```

### CORS Errors
```
Error: This API key is not authorized for this domain
Solution: Add your domain to API key restrictions
```

### No Search Results
```
Error: Places API request failed
Solution: Check API is enabled and key has Places API access
```

### Map Not Loading
```
Error: Google Maps failed to load
Solution: Check Maps JavaScript API is enabled
```

## Important Notes

### API Key Requirements
- **This app requires a valid Google Maps API key to function**
- **No mock mode or fallbacks are provided**
- The app will show error messages if the API key is missing or invalid
- Ensure your API key has the required permissions and restrictions

### Security Considerations
- API key is handled server-side for Places API calls
- Client-side receives API key only for Maps JavaScript API
- Implement proper domain restrictions in production
- Monitor API usage and set appropriate quotas

---

**Note**: This app is designed for **lead generation purposes**. Ensure compliance with Google's Terms of Service and applicable data privacy regulations when collecting business information.