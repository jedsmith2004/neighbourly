# 🏘️ Neighbourly

A community-driven platform connecting neighbours for local help and support. Request assistance with errands, groceries, or other tasks, and let nearby helpers lend a hand.

**Built at HackSheffield 9** by Ben, Jack, Jonathan & Nikkhil

🌐 **Live:** [neighbourly.jacksmith.me](https://neighbourly.jacksmith.me)

## Features

- 📍 **Location-based requests** - Pin your delivery location on an interactive map
- 🛒 **Item lists** - Specify what you need with quantities
- 💬 **Real-time chat** - Communicate directly with your helper
- 🔐 **Secure auth** - Auth0 integration for safe sign-in
- 📱 **Responsive design** - Works on desktop and mobile

## Tech Stack

**Frontend:** SvelteKit 5, TailwindCSS, Google Maps API  
**Backend:** Python Flask, SQLAlchemy, PostgreSQL  
**Auth:** Auth0  
**Hosting:** Vercel (frontend), Fly.io (backend), Supabase (database)

## Local Development

### Prerequisites
- Node.js 18+
- Python 3.10+
- Google Maps API key
- Auth0 account

### Backend Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create `.env` in backend folder (see `.env.example`):
```
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
AUTH0_DOMAIN=your_domain.auth0.com
APP_SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///neighbourly.db
FRONTEND_URL=http://localhost:5173
```

Run the server:
```bash
python server.py
```

### Frontend Setup

```bash
cd frontend
npm install
```

Create `.env` in frontend folder (see `.env.example`):
```
PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_key
VITE_API_URL=http://localhost:3000
```

Run the dev server:
```bash
npm run dev
```

## Deployment

### Backend (Fly.io)

```bash
cd backend
fly launch  # First time only
fly secrets set AUTH0_CLIENT_ID=xxx AUTH0_CLIENT_SECRET=xxx AUTH0_DOMAIN=xxx APP_SECRET_KEY=xxx DATABASE_URL=xxx FRONTEND_URL=https://neighbourly.jacksmith.me
fly deploy
```

### Frontend (Vercel)

1. Connect GitHub repo to Vercel
2. Set root directory to `frontend`
3. Add environment variables:
   - `PUBLIC_GOOGLE_MAPS_API_KEY`
   - `VITE_API_URL=https://neighbourly-api.fly.dev`
4. Deploy

### Database (Supabase)

1. Create new Supabase project
2. Copy the connection string from Settings → Database
3. Set `DATABASE_URL` in Fly.io secrets

### Auth0 Configuration

Add these URLs to your Auth0 application:
- **Allowed Callback URLs:** `https://neighbourly-api.fly.dev/callback`
- **Allowed Logout URLs:** `https://neighbourly-api.fly.dev/login`
- **Allowed Web Origins:** `https://neighbourly.jacksmith.me`

## Usage

1. Sign in with Auth0
2. Create a request with your location and items
3. Wait for a neighbour to help
4. Chat with your helper and track your request
5. Mark as delivered when complete

## License

MIT

##