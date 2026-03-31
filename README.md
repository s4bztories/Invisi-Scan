# Invisi-Scan Enterprise Operations Center

Invisi-Scan is an advanced, full-stack Ethical Attack Surface Analyzer and Network Intelligence Platform. It features a modern, dynamic React frontend designed to mimic a high-end SaaS Enterprise dashboard, communicating seamlessly with a high-performance Python FastAPI backend.

---

## 🏗️ Project Architecture

The project has been refactored into a clean, modern full-stack split to optimize deployment and development:

- **`frontend/`**: The modern User Interface built with React and Vite. It serves as the "Command Center" where operators can input targets, track scans natively, and review robust analytics.
- **`backend/`**: The intelligence engine. It runs on Python's **FastAPI** framework for maximum concurrency and speed. The core scanning modules (AI threat analysis, banner grabbing, CVE lookups, network scanning) reside inside `backend/core/`.

---

## 🚀 How to Run Locally

We provide an automated launcher script that spins up both the frontend and backend sequentially.

### Prerequisites
1. **Node.js** (for running the React Frontend)
2. **Python 3.10+** (for running the FastAPI Backend)
3. Ensure you have installed the Python virtual environment and dependencies (`pip install -r requirements.txt`).

### The One-Click Launcher
Run the automated bash script from the root of the project:

```bash
./run.sh
```

This will automatically:
1. Validate port availability (`8001` for the API, `5174` for the UI).
2. Start the FastAPI backend on `http://localhost:8001`.
3. Start the Vite React frontend on `http://localhost:5174`.

To stop the services safely, simply press `Ctrl+C` in the terminal where it is running, or execute `./stop.sh`.

---

## 🔗 How the Frontend & Backend Connect

The platform uses two forms of communication between the React Frontend and the FastAPI Backend:

### 1. Standard HTTP REST API
- **Endpoint**: `http://localhost:8001/api/...`
- **Use Case**: This is primarily used for Authentication (Login, Register), fetching historical scan records, managing schedules, and fetching overall ecosystem Analytics.
- **Configuration in Frontend**: The application uses the global variable `API_BASE_URL` (defined via `.env` or defaulting to `http://localhost:8001`).

### 2. WebSocket Real-Time Connection
- **Endpoint**: `ws://localhost:8001/ws/scan`
- **Use Case**: When a scan is initiated by the Operator, the frontend opens a live WebSocket connection to the backend. As the Python scanning engine evaluates ports, grabs banners, and discovers CVEs in real time, it streams these updates back via the WebSocket. The frontend listens to this stream to provide the gorgeous live "Terminal" streaming log and dynamic UI updates without page refreshes.
- **Auto-Configuring**: The frontend dynamically constructs the WebSocket URL based on the REST `API_BASE_URL` by replacing `http/https` with `ws/wss` dynamically in `frontend/src/App.jsx`.

---

## 🌍 How to Deploy as a Live Website

### 1. Hosting the Backend (API Server)
Because this application runs deep real-time network scans, it requires a robust processing environment. Consider utilizing a strong Cloud Provider VPS such as **DigitalOcean**, **AWS EC2**, or **Linode**.

**Deployment Steps for Backend**:
1. Clone the repository onto your Cloud VPS.
2. Install Python dependencies and system-level requirements:
   ```bash
   sudo apt update
   sudo apt install -y python3-venv nmap lsof xdg-utils
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Use a process manager like `Systemd` or `PM2` to keep the FastAPI backend running continuously.
4. Deploy behind a reverse proxy like **Nginx**, and secure it with an SSL certificate via Certbot (Let's Encrypt). Map `https://api.yourdomain.com` to internal port `8001`.

### 2. Hosting the Frontend (Web Dashboard)
The React Frontend uses Vite, and can be easily built into static HTML/JS files to be deployed anywhere.

**Deployment Steps for Frontend**:
1. Change into the frontend directory: `cd frontend`
2. Create a `.env` file and set the `VITE_API_URL` to point to your live backend domain:
   ```
   VITE_API_URL=https://api.yourdomain.com
   ```
3. Build the production application:
   ```bash
   npm run build
   ```
4. This will output all static assets into a `dist/` directory.
5. Deploy the `dist/` directory to **Vercel**, **Netlify**, **Cloudflare Pages**, or host it completely free via GitHub Pages.

> **Note on Live File Changes:** If you use Antigravity to manipulate or change code files in the source locally, those changes will reflect on the live website **only after** you push the code updates to your deployment environment (e.g. running `npm run build` again and pushing the changes on Vercel, or pulling the new changes to your VPS).

---

## 🛡️ Default Environment Details
Upon launching, the system has default credentials loaded into the Database:
- **Operator Access**: `operator` / `operator123`
- **Root Admin Access**: `admin` / `admin123`

*(Please remember to adjust passwords if launching in a production environment)*
