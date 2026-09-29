import { lazy, Suspense, useMemo, useState, useEffect, useRef } from 'react';
import { Terminal, Shield, AlertTriangle, CheckCircle, Activity, Lock, Unlock, Server, Download, KeyRound, LogOut, History, Crosshair, Globe, Target, Sparkles, Bot } from 'lucide-react';

const TopologyGraph = lazy(() => import('./TopologyGraph'));
const DiffModal = lazy(() => import('./DiffModal'));
const AnalyticsDashboard = lazy(() => import('./AnalyticsDashboard'));
const Autopilot = lazy(() => import('./Autopilot'));
const AdminPanel = lazy(() => import('./AdminPanel'));
const AiChatbot = lazy(() => import('./AiChatbot'));

const ParticleNetwork3D = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    
    let particles = [];
    const mouse = { x: null, y: null };
    
    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      init();
    };
    
    const handleMouseMove = (e) => {
      mouse.x = e.x;
      mouse.y = e.y;
    };
    
    const handleMouseLeave = () => {
      mouse.x = null;
      mouse.y = null;
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseout', handleMouseLeave);

    function Particle() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.size = Math.random() * 2 + 0.5;
      this.speedX = Math.random() * 0.5 - 0.25;
      this.speedY = Math.random() * 0.5 - 0.25;

      this.update = function() {
        this.x += this.speedX;
        this.y += this.speedY;
        if (this.x < 0 || this.x > width) this.speedX *= -1;
        if (this.y < 0 || this.y > height) this.speedY *= -1;
      };

      this.draw = function() {
        ctx.fillStyle = 'rgba(129, 140, 248, 0.4)';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      };
    }

    const init = () => {
      particles = [];
      const particleCount = Math.min(Math.floor((width * height) / 18000), 80);
      for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
      }
    };
    init();

    let animationFrameId;
    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();
        
        for (let j = i; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < 120) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(129, 140, 248, ${0.15 - distance/800})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
        
        if (mouse.x != null) {
          const dx = particles[i].x - mouse.x;
          const dy = particles[i].y - mouse.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < 180) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(168, 85, 247, ${0.3 - distance/600})`;
            ctx.lineWidth = 1;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.stroke();
          }
        }
      }
      animationFrameId = requestAnimationFrame(animate);
    };
    animate();
    
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseout', handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden bg-[#0A0A0B]">
      {/* 3D Geometric Floor Graphic */}
      <div className="absolute inset-0 flex justify-center opacity-30 mix-blend-screen" style={{ perspective: '1000px' }}>
        <div className="w-[300vw] h-[200vh] absolute bottom-[-75vh] origin-top animated-grid"
             style={{ 
               transform: 'rotateX(75deg) translateZ(-200px)',
               background: 'linear-gradient(transparent 10%, #0A0A0B 75%), linear-gradient(rgba(99, 102, 241, 0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(99, 102, 241, 0.4) 1px, transparent 1px)',
               backgroundSize: '100% 100%, 80px 80px, 80px 80px',
               animation: 'gridForward 15s linear infinite'
             }}>
        </div>
      </div>
      
      {/* Vercel Ambient Orbs */}
      <div className="absolute top-[-20%] left-[-10%] w-[50vw] h-[50vh] rounded-full bg-blue-500/10 blur-[130px]"></div>
      <div className="absolute top-[20%] right-[-10%] w-[40vw] h-[40vh] rounded-full bg-purple-500/10 blur-[130px]"></div>

      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full opacity-70" />
    </div>
  );
};

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

function SectionLoader({ text = 'Loading...' }) {
  return <div className="text-center py-10 text-slate-400 animate-pulse">{text}</div>;
}

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const googleButtonRef = useRef(null);
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  useEffect(() => {
    if (isRegistering || !googleClientId) return undefined;

    const initGoogle = () => {
      if (!window.google?.accounts?.id || !googleButtonRef.current) return;
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response) => {
          if (!response?.credential) {
            setError('Google sign-in did not return a valid credential.');
            return;
          }

          const controller = new AbortController();
          const timeoutId = window.setTimeout(() => controller.abort(), 6000);

          setGoogleLoading(true);
          setError('');
          try {
            const res = await fetch(`${API_BASE_URL}/api/auth/google`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              signal: controller.signal,
              body: JSON.stringify({ id_token: response.credential }),
            });
            const data = await res.json();
            if (data.ok && data.token) {
              onLogin(data);
            } else {
              setError(data.error || 'Google sign-in failed');
            }
          } catch (err) {
            console.error(err);
            setError(err.name === 'AbortError' ? 'Google sign-in took too long. Please try again.' : 'Google sign-in failed');
          } finally {
            window.clearTimeout(timeoutId);
            setGoogleLoading(false);
          }
        }
      });

      googleButtonRef.current.innerHTML = '';
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        type: 'standard',
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        shape: 'pill',
        width: 360
      });
    };

    const existingScript = document.getElementById('google-identity-script');
    if (existingScript) {
      initGoogle();
      return undefined;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.id = 'google-identity-script';
    script.onload = initGoogle;
    script.onerror = () => setError('Failed to load Google sign-in. Please refresh and try again.');
    document.head.appendChild(script);
    return undefined;
  }, [googleClientId, isRegistering, onLogin]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isRegistering ? `${API_BASE_URL}/api/register` : `${API_BASE_URL}/api/login`;
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      
      if (data.ok) {
        if (isRegistering) {
            setError('Account secured & created! You may now login.');
            setIsRegistering(false);
            setPassword('');
        } else {
            if (data.otp_required) {
              setError('OTP-enabled accounts require OTP verification flow in UI.');
            } else {
              onLogin(data);
            }
        }
      } else {
        setError(data.error || 'Request failed');
      }
    } catch (err) {
      console.error(err);
      setError('Could not connect to SOC API backend');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative bg-[#0A0A0B] overflow-hidden">
      {/* 3D Background Engine */}
      <ParticleNetwork3D />
      
      {/* Floating Center Panel */}
      <div className="glass-panel max-w-md w-[95%] sm:w-full p-6 sm:p-10 mx-auto relative z-10 border border-white/10 shadow-[0_0_50px_rgba(99,102,241,0.1)] hover:shadow-[0_0_80px_rgba(99,102,241,0.2)] transition-shadow duration-700">
        <div className="flex flex-col items-center mb-10 relative">
          <div className="absolute inset-0 bg-indigo-500/20 blur-3xl rounded-full"></div>
          <Shield className="w-14 h-14 text-indigo-400 mb-5 relative z-10 drop-shadow-[0_0_15px_rgba(129,140,248,0.5)]" />
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">InvisiScan</h1>
          <p className="text-indigo-300 font-medium text-sm tracking-wide">Enterprise Operations Center</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-4 rounded-xl text-center font-medium shadow-inner">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs text-slate-400 mb-2 font-semibold tracking-wide">Workstation ID</label>
            <div className="relative">
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-field pl-12 shadow-inner"
                placeholder="Enter credentials..."
                required
              />
              <Terminal className="w-5 h-5 text-slate-500 absolute left-4 top-3.5" />
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-2 font-semibold tracking-wide">Authentication Token</label>
            <div className="relative">
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field pl-12 shadow-inner"
                placeholder="Enter secure token..."
                required
              />
              <KeyRound className="w-5 h-5 text-slate-500 absolute left-4 top-3.5" />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading || googleLoading}
            className="btn-primary w-full mt-8 py-4 text-base"
          >
            {loading ? <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin"></div> : <Unlock className="w-5 h-5" />}
            {isRegistering ? 'Create Account' : 'Login'}
          </button>

          {!isRegistering && (
            <>
              <div className="text-center text-[11px] uppercase tracking-widest text-slate-500">or</div>
              {googleClientId ? (
                <div className="flex justify-center">
                  <div className="flex flex-col items-center gap-3">
                    <div ref={googleButtonRef} className={googleLoading ? 'pointer-events-none opacity-60' : ''} />
                    {googleLoading && (
                      <div className="text-xs text-slate-400">Google sign-in in progress...</div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center text-xs text-amber-300/80 bg-amber-500/10 border border-amber-500/20 rounded-xl p-3">
                  Add `VITE_GOOGLE_CLIENT_ID` in frontend env to enable Google Sign-In.
                </div>
              )}
            </>
          )}
          
          <div className="text-center mt-6">
             <button 
                type="button" 
                onClick={() => { setIsRegistering(!isRegistering); setError(''); }} 
                className="text-sm font-medium text-slate-400 hover:text-indigo-400 transition-colors"
             >
                {isRegistering ? 'Already have an account? Login' : 'Need an account? Create Account'}
             </button>
          </div>
        </form>
      </div>
    </div>
  );
}
function Dashboard({ authData, onLogout }) {
  const [activeTab, setActiveTab] = useState('analytics');
  const [target, setTarget] = useState('');
  const [portsMode, setPortsMode] = useState('fast');
  const [isScanning, setIsScanning] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('soc_theme') || 'default');

  useEffect(() => {
    if (theme === 'default') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', theme);
    }
    localStorage.setItem('soc_theme', theme);
  }, [theme]);
  
  // Real-time states
  const [logs, setLogs] = useState([]);
  const [openPorts, setOpenPorts] = useState([]);
  const [banners, setBanners] = useState({});
  const [cves, setCves] = useState({});
  const [explanations, setExplanations] = useState({});
  const [subdomains, setSubdomains] = useState([]);
  const [geoInfo, setGeoInfo] = useState(null);
  const [webRecon, setWebRecon] = useState({});
  const [reportData, setReportData] = useState(null);
  const [diffData, setDiffData] = useState(null);

  // History state
  const [historyList, setHistoryList] = useState([]);

  const wsRef = useRef(null);
  const logsEndRef = useRef(null);
  const previousLogsCountRef = useRef(0);

  const { username, role } = authData;
  const previousByTarget = useMemo(() => {
    const map = new Map();
    for (const item of historyList) {
      const existing = map.get(item.target);
      if (!existing) {
        map.set(item.target, []);
      }
      map.get(item.target).push(item);
    }
    return map;
  }, [historyList]);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  useEffect(() => {
    const hasNewLogs = logs.length > previousLogsCountRef.current;
    previousLogsCountRef.current = logs.length;

    if (activeTab === 'scanner' && isScanning && hasNewLogs && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [logs, activeTab, isScanning]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/history`, {
        headers: {
          'Authorization': `Bearer ${authData?.token}`
        }
      });
      if (res.status === 401) {
        localStorage.removeItem('soc_session');
        window.location.reload();
        return;
      }
      const data = await res.json();
      if (data.ok) {
        setHistoryList(data.history);
        setActiveTab('history'); // Switch to history tab after fetching
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  };

  const loadPastReport = (report) => {
    setTarget(report.target);
    setOpenPorts(report.report_json.open_ports || []);
    setBanners(report.report_json.banners || {});
    setCves(report.report_json.cves || {});
    setExplanations(report.report_json.explanations || {});
    setSubdomains(report.report_json.subdomains || []);
    setGeoInfo(report.report_json.geolocation || null);
    setWebRecon(report.report_json.web_recon || {});
    setReportData(report.report_json);
    setLogs([{ time: new Date().toLocaleTimeString(), msg: `Loaded historical report from ${new Date(report.timestamp).toLocaleString()}`, type: 'info' }]);
    setActiveTab('scanner');
  };

  const addLog = (msg, type = 'info') => {
    setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), msg, type }]);
  };

  const startScan = () => {
    if (!target) return;
    
    setLogs([]);
    setOpenPorts([]);
    setBanners({});
    setCves({});
    setExplanations({});
    setSubdomains([]);
    setGeoInfo(null);
    setWebRecon({});
    setReportData(null);
    setIsScanning(true);

    addLog('Connecting to SOC Scanning Engine...', 'info');

    const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/ws/scan';
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({
        target,
        token: authData.token,
        ports: portsMode
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'info':
          addLog(data.message, 'info');
          break;
        case 'error':
          addLog(data.message, 'error');
          setIsScanning(false);
          ws.close();
          if (data.message.toLowerCase().includes('expired') || data.message.toLowerCase().includes('invalid')) {
            setTimeout(() => {
              localStorage.removeItem('soc_session');
              window.location.reload();
            }, 2500);
          }
          break;
        case 'port_found':
          setOpenPorts(prev => {
            if (!prev.includes(data.port)) return [...prev, data.port].sort((a,b)=>a-b);
            return prev;
          });
          addLog(`Port ${data.port} is OPEN`, 'port');
          break;
        case 'banners':
          setBanners(data.data);
          addLog('Banners retrieved.', 'success');
          break;
        case 'cves':
          setCves(data.data);
          addLog('CVE database lookup complete.', 'success');
          break;
        case 'explanations':
          setExplanations(data.data);
          addLog('AI Risk Assessment complete.', 'success');
          break;
        case 'geolocation':
          setGeoInfo(data.data);
          break;
        case 'web_recon':
          setWebRecon(data.data);
          break;
        case 'subdomains':
          setSubdomains(data.data);
          break;
        case 'complete':
          setReportData(data.report);
          addLog('Scan sequence complete and stored in database.', 'success');
          setIsScanning(false);
          break;
        default:
          break;
      }
    };

    ws.onerror = () => {
      addLog('WebSocket connection error. Is the API backend running?', 'error');
      setIsScanning(false);
    };

    ws.onclose = () => {
      setIsScanning(false);
    };
  };

  // const stopScan = () => {
  //   if (wsRef.current) wsRef.current.close();
  //   addLog('Scan aborted by user.', 'error');
  //   setIsScanning(false);
  // };

  // const handleExportJson = () => {
  //   const blob = new Blob([JSON.stringify(reportData, null, 2)], {type: 'application/json'});
  //   const url = URL.createObjectURL(blob);
  //   const a = document.createElement('a');
  //   a.href = url;
  //   a.download = `scan_report_${target}.json`;
  //   a.click();
  // };

  const handleExportPdf = async () => {
    if (!reportData) return;
    const [{ default: jsPDF }, autoTableModule] = await Promise.all([
      import('jspdf'),
      import('jspdf-autotable'),
    ]);
    const autoTable = autoTableModule.default || autoTableModule.autoTable;

    const doc = new jsPDF();
    doc.setFont("helvetica", "bold");
    doc.setFontSize(20);
    doc.text(`InvisiScan Enterprise Report`, 14, 20);
    doc.setFontSize(12);
    doc.setFont("helvetica", "normal");
    doc.text(`Target: ${target}`, 14, 30);
    doc.text(`Timestamp: ${new Date().toLocaleString()}`, 14, 38);
    
    const portsData = openPorts.map(p => [
        p,
        banners[p] ? banners[p].substring(0, 30) : "N/A",
        cves[p] ? cves[p].length.toString() : "0"
    ]);
    
    autoTable(doc, {
        startY: 45,
        head: [['Port', 'Banner/Service', 'CVEs']],
        body: portsData,
        theme: 'grid',
        headStyles: { fillColor: [99, 102, 241] }
    });
    
    let currentY = doc.lastAutoTable.finalY + 15;
    Object.keys(cves).forEach(port => {
        if(cves[port] && cves[port].length > 0) {
            if (currentY > 270) { doc.addPage(); currentY = 20; }
            doc.setFont("helvetica", "bold");
            doc.text(`Port ${port} Critical Vulnerabilities:`, 14, currentY);
            currentY += 8;
            doc.setFont("helvetica", "normal");
            
            cves[port].forEach(cve => {
                if (currentY > 280) { doc.addPage(); currentY = 20; }
                doc.setFont("helvetica", "bold");
                doc.text(`${cve.id}:`, 14, currentY);
                doc.setFont("helvetica", "normal");
                const splitText = doc.splitTextToSize(cve.summary || "", 180);
                doc.text(splitText, 14, currentY + 6);
                currentY += (splitText.length * 6) + 10;
            });
            currentY += 5;
        }
    });

    const pdfBlob = doc.output('blob');
    const file = new File([pdfBlob], `InvisiScan_Report_${target}.pdf`, { type: 'application/pdf' });
    
    if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
       try {
         await navigator.share({
           files: [file],
           title: 'Invisi-Scan Report',
           text: `Security assessment report for ${target}`
         });
         return;
       } catch (err) {
         console.warn('Share sheet failed or cancelled', err);
       }
    }
    
    doc.save(`InvisiScan_Report_${target}.pdf`);
  };

  const handleExportCsv = async () => {
    if (!reportData) return;
    const rows = [ ["Port", "Banner", "CVE Count"] ];
    openPorts.forEach(p => {
       rows.push([
           p, 
           banners[p] ? `"${banners[p].replace(/"/g, '""')}"` : "N/A",
           cves[p] ? cves[p].length : 0
       ]);
    });
    const csvContent = rows.map(e => e.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const file = new File([blob], `InvisiScan_Report_${target}.csv`, { type: 'text/csv' });

    if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
       try {
         await navigator.share({
           files: [file],
           title: 'Invisi-Scan CSV Report',
           text: `Raw data export for ${target}`
         });
         return;
       } catch (err) {
         console.warn('Share sheet failed or cancelled', err);
       }
    }

    const encodedUri = "data:text/csv;charset=utf-8," + encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `InvisiScan_Report_${target}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="min-h-screen relative overflow-hidden pb-20 bg-[#0A0A0B]">
      {/* 3D Global Dashboard Background */}
      <ParticleNetwork3D />

      <div className="max-w-7xl mx-auto px-6 pt-8 relative z-10 w-full">
        {/* Modern Clean Header */}
        <header className="glass-nav rounded-2xl md:rounded-[2rem] px-4 md:px-8 py-4 md:py-5 flex flex-col md:flex-row items-center justify-between mb-12">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">InvisiScan</h1>
              <p className="text-slate-400 text-xs font-medium tracking-wide">Enterprise Intelligence</p>
            </div>
          </div>
          
          <div className="flex flex-col md:flex-row items-center gap-4 md:gap-8 mt-4 md:mt-0 w-full md:w-auto">
            <div className="hidden md:flex flex-wrap justify-center sm:flex-nowrap bg-[#1A1A1D] rounded-xl p-1 shadow-inner w-full sm:w-auto overflow-x-auto gap-1 sm:gap-0">
              <button 
                onClick={() => setActiveTab('analytics')} 
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2 ${activeTab === 'analytics' ? 'bg-white text-black shadow-sm' : 'text-slate-400 hover:text-white'}`}
              >
                <Activity className="w-4 h-4" /> Command Center
              </button>
              <button 
                onClick={() => setActiveTab('scanner')} 
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${activeTab === 'scanner' ? 'bg-white text-black shadow-sm' : 'text-slate-400 hover:text-white'}`}
              >
                Scanner
              </button>
              <button 
                onClick={fetchHistory} 
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2 ${activeTab === 'history' ? 'bg-white text-black shadow-sm' : 'text-slate-400 hover:text-white'}`}
              >
                <History className="w-4 h-4" /> History
              </button>
              <button 
                onClick={() => setActiveTab('autopilot')} 
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2 ${activeTab === 'autopilot' ? 'bg-white text-black shadow-sm' : 'text-slate-400 hover:text-white'}`}
              >
                Autopilot
              </button>
              <button 
                onClick={() => setActiveTab('ai-assistant')} 
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2 ${activeTab === 'ai-assistant' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm' : 'text-slate-400 hover:text-white'}`}
              >
                <Sparkles className="w-4 h-4 text-cyan-400" /> AI Assistant
              </button>
              {role === 'admin' && (
                <button 
                  onClick={() => setActiveTab('admin')} 
                  className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center gap-2 ${activeTab === 'admin' ? 'bg-white text-black shadow-sm' : 'text-slate-400 hover:text-white'}`}
                >
                  <Shield className="w-4 h-4" /> Root
                </button>
              )}
            </div>
            
            <div className="flex items-center justify-center gap-4 pt-4 md:pt-0 md:pl-8 border-t md:border-t-0 md:border-l border-white/10 w-full md:w-auto mt-2 md:mt-0">
              <select onChange={(e) => setTheme(e.target.value)} value={theme} className="hidden lg:block bg-[#1A1A1D] border border-white/10 rounded-xl px-2 py-1.5 text-xs text-slate-400 outline-none hover:bg-white/5 font-semibold cursor-pointer appearance-none text-center">
                 <option value="default">Midnight</option>
                 <option value="matrix">Matrix</option>
                 <option value="neon">Neon</option>
                 <option value="ghost">Ghost</option>
              </select>
              <div className="text-right">
                <p className="text-sm text-slate-200 font-semibold">{(username || 'GUEST')}</p>
                <p className="text-xs text-indigo-400 font-medium tracking-wide">{(role || 'OPERATOR').toUpperCase()}</p>
              </div>
              <button onClick={onLogout} className="p-2.5 bg-white/5 hover:bg-red-500/10 text-slate-400 hover:text-red-400 rounded-xl transition-all">
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>
        
        {activeTab === 'analytics' ? (
           <Suspense fallback={<SectionLoader text="Loading command center..." />}>
             <AnalyticsDashboard authData={authData} />
           </Suspense>
        ) : activeTab === 'autopilot' ? (
           <Suspense fallback={<SectionLoader text="Loading autopilot..." />}>
             <Autopilot authData={authData} />
           </Suspense>
        ) : activeTab === 'admin' ? (
           <Suspense fallback={<SectionLoader text="Loading admin panel..." />}>
             <AdminPanel authData={authData} />
           </Suspense>
        ) : activeTab === 'scanner' ? (
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
            {/* Left Column Controls */}
            <div className="xl:col-span-4 space-y-6">
              
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-[2rem] blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
                <div className="glass-panel p-8 relative ring-1 ring-white/5">
                  <h2 className="text-sm font-semibold text-slate-200 mb-6 flex items-center gap-3 tracking-wider uppercase">
                    <Target className="w-4 h-4 text-indigo-400" /> Assessment Parameters
                  </h2>
                  
                  <div className="space-y-6">
                    <div>
                      <div className="relative">
                        <input 
                          type="text" 
                          value={target}
                          onChange={(e) => setTarget(e.target.value)}
                          disabled={isScanning}
                          className="w-full bg-[#131316] border border-white/[0.05] focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/10 rounded-2xl pl-12 pr-5 py-4 text-slate-200 text-sm font-mono outline-none transition-all placeholder:text-slate-600 shadow-inner"
                          placeholder="target.hostname.com"
                        />
                        <Globe className="w-5 h-5 text-slate-500 absolute left-4 top-4" />
                      </div>
                    </div>

                    <div className="flex bg-[#131316] p-1.5 rounded-2xl border border-white/[0.02]">
                      <button 
                        onClick={() => setPortsMode('fast')}
                        disabled={isScanning}
                        className={`flex-1 py-3 text-xs font-semibold uppercase tracking-widest rounded-xl transition-all ${portsMode === 'fast' ? 'bg-white/10 text-white shadow-lg shadow-black/20' : 'text-slate-500 hover:text-slate-300'}`}
                      >
                        Top 100
                      </button>
                      <button 
                        onClick={() => setPortsMode('all')}
                        disabled={isScanning}
                        className={`flex-1 py-3 text-xs font-semibold uppercase tracking-widest rounded-xl transition-all ${portsMode === 'all' ? 'bg-white/10 text-white shadow-lg shadow-black/20' : 'text-slate-500 hover:text-slate-300'}`}
                      >
                        Deep Scan
                      </button>
                    </div>

                    <button 
                      onClick={startScan} 
                      disabled={isScanning || !target}
                      className={`relative w-full py-4 rounded-2xl font-bold tracking-widest text-sm uppercase transition-all duration-300 overflow-hidden group ${
                        isScanning 
                          ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 shadow-[0_0_30px_rgba(99,102,241,0.2)]'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_40px_rgba(99,102,241,0.5)] border border-indigo-500/50'
                      }`}
                    >
                      {isScanning ? (
                        <span className="flex items-center justify-center gap-3">
                          <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
                          Uplink Active...
                        </span>
                      ) : (
                        <span className="flex items-center justify-center gap-3 relative z-10">
                          <Crosshair className="w-4 h-4" /> Initialize Sequence
                        </span>
                      )}
                      {!isScanning && <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]"></div>}
                    </button>
                  </div>
                </div>
              </div>

              {/* Advanced Execution Terminal */}
              <div className="glass-panel p-0 flex flex-col h-[380px] relative overflow-hidden group border border-white/5">
                 <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-indigo-500 via-purple-500 to-transparent opacity-50"></div>
                 <div className="bg-black/40 backdrop-blur-md border-b border-white/[0.05] p-4 flex items-center justify-between z-10">
                    <div className="flex items-center gap-3">
                      <Terminal className="w-4 h-4 text-indigo-400" />
                      <span className="text-xs font-semibold text-slate-300 tracking-widest uppercase">Live Telemetry</span>
                    </div>
                    <span className={`flex items-center gap-2 text-[10px] font-bold tracking-widest uppercase ${isScanning ? 'text-indigo-400' : 'text-slate-600'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${isScanning ? 'bg-indigo-400 animate-pulse shadow-[0_0_10px_rgba(129,140,248,1)]' : 'bg-slate-600'}`}></span>
                      {isScanning ? 'Streaming' : 'Standby'}
                    </span>
                 </div>
                 <div className="flex-1 overflow-y-auto p-5 custom-scrollbar font-mono text-[11px] md:text-xs tracking-wide bg-[#0A0A0C]/90 z-0">
                  {logs.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-slate-700 space-y-3 opacity-50">
                      <Shield className="w-8 h-8" />
                      <span>Awaiting target lock...</span>
                    </div>
                  )}
                  {logs.map((log, i) => (
                    <div key={i} className="mb-2.5 leading-relaxed flex items-start gap-3 hover:bg-white/[0.02] p-1 rounded transition-colors">
                      <span className="text-slate-600 shrink-0 select-none">[{log.time}]</span>
                      <span className={`${
                        log.type === 'error' ? 'text-rose-400 font-medium' : 
                        log.type === 'success' ? 'text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)]' : 
                        log.type === 'port' ? 'text-cyan-300 font-medium' : 'text-indigo-200/80'
                      } break-all`}>
                        {log.msg}
                      </span>
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              </div>
            </div>

            {/* Right Column Canvas */}
            <div className="xl:col-span-8 flex flex-col min-h-[600px]">
              
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 px-2 gap-4">
                <h2 className="text-2xl font-bold text-white flex items-center gap-3 tracking-tight">
                  <Activity className="w-7 h-7 text-indigo-400 drop-shadow-[0_0_15px_rgba(129,140,248,0.5)]" /> 
                  Advanced Scanner
                </h2>
                
                {reportData && (
                   <div className="flex gap-3">
                     <button 
                       onClick={handleExportPdf}
                       className="group flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-indigo-100 bg-indigo-500/20 hover:bg-indigo-500 border border-indigo-500/30 px-5 py-2.5 rounded-xl transition-all duration-300 shadow-[0_0_20px_rgba(99,102,241,0.15)] hover:shadow-[0_0_30px_rgba(99,102,241,0.4)]"
                     >
                       <Download className="w-4 h-4 group-hover:-translate-y-0.5 transition-transform" /> Export PDF
                     </button>
                     <button 
                       onClick={handleExportCsv}
                       className="group flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-300 bg-white/5 hover:bg-white/10 border border-white/10 px-5 py-2.5 rounded-xl transition-all duration-300"
                     >
                       <Download className="w-4 h-4 group-hover:-translate-y-0.5 transition-transform" /> CSV
                     </button>
                   </div>
                )}
              </div>

              {reportData && (
                <div className="mb-8 relative group">
                   <div className="absolute -inset-1 bg-gradient-to-b from-indigo-500/10 to-transparent blur-xl opacity-50 pointer-events-none rounded-[3rem]"></div>
                   <div className="relative z-10">
                     <Suspense fallback={<SectionLoader text="Loading topology graph..." />}>
                       <TopologyGraph data={reportData} />
                     </Suspense>
                   </div>
                </div>
              )}

              {subdomains && subdomains.length > 0 && (
                <div className="mb-8 glass-panel p-8 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 blur-[100px] rounded-full pointer-events-none -translate-y-1/2 translate-x-1/2"></div>
                  <h3 className="text-xs font-bold tracking-widest uppercase text-blue-400 mb-6 flex items-center gap-3">
                    <Server className="w-4 h-4" /> Discovered Network Surface ({subdomains.length})
                  </h3>
                  <div className="flex flex-wrap gap-2.5 relative z-10">
                    {subdomains.map(sub => (
                      <span key={sub} className="text-[11px] font-mono tracking-wide bg-[#0A0A0C] text-blue-200/90 border border-blue-500/20 px-3.5 py-1.5 rounded-lg shadow-sm hover:border-blue-500/50 transition-colors cursor-default">{sub}</span>
                    ))}
                  </div>
                </div>
              )}

              {geoInfo && (
                <div className="mb-8 glass-panel p-8 relative overflow-hidden">
                  <div className="absolute top-1/2 right-10 -translate-y-1/2 opacity-[0.02] pointer-events-none">
                    <Globe className="w-48 h-48" />
                  </div>
                  
                  <h3 className="text-xs font-bold tracking-widest uppercase text-emerald-400 mb-6 flex items-center gap-3">
                    <Crosshair className="w-4 h-4" /> Geolocation Routing Trace
                  </h3>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-sm relative z-10">
                    <div className="space-y-1.5">
                      <span className="block text-slate-500 text-[10px] uppercase font-bold tracking-widest">Public IP Address</span>
                      <span className="font-mono text-slate-200 text-sm">{geoInfo.ip}</span>
                    </div>
                    <div className="space-y-1.5">
                      <span className="block text-slate-500 text-[10px] uppercase font-bold tracking-widest">Physical Region</span>
                      <span className="text-slate-200 font-medium text-sm">{geoInfo.city}, {geoInfo.country}</span>
                    </div>
                    <div className="md:col-span-2 space-y-1.5">
                      <span className="block text-slate-500 text-[10px] uppercase font-bold tracking-widest">Network Provider AS</span>
                      <span className="text-slate-200 font-medium text-sm">{geoInfo.isp} <span className="text-slate-500 ml-2 font-mono text-xs">({geoInfo.asn})</span></span>
                    </div>
                  </div>
                </div>
              )}

              {isScanning && openPorts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-32 flex-1 relative">
                  {/* Premium Scanner Orb */}
                  <div className="relative flex justify-center items-center w-40 h-40 mb-12">
                    <div className="absolute inset-0 bg-indigo-500/20 rounded-full blur-2xl animate-pulse"></div>
                    <div className="absolute inset-4 border-2 border-indigo-500/30 border-dashed rounded-full animate-[spin_12s_linear_infinite]"></div>
                    <div className="absolute inset-8 border border-purple-500/20 rounded-full animate-[spin_8s_linear_infinite_reverse]"></div>
                    <div className="absolute inset-12 bg-gradient-to-br from-[#111113] to-[#1A1A1D] border border-white/10 rounded-full shadow-[inset_0_0_20px_rgba(0,0,0,0.8)] flex items-center justify-center z-10">
                       <Activity className="w-8 h-8 text-indigo-400 drop-shadow-[0_0_10px_rgba(129,140,248,0.8)] animate-pulse" />
                    </div>
                  </div>
                  
                  <h3 className="text-xl font-bold text-white tracking-tight mb-3">Synthesizing Threat Vectors</h3>
                  <p className="text-sm font-medium tracking-wide text-slate-400">Executing autonomous handshake protocols...</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-6 pb-20">
                  {openPorts.map(port => {
                    const hasCves = cves[port]?.length > 0;
                    return (
                      <div key={port} className="relative group">
                        {/* Dynamic Side Glow */}
                        <div className={`absolute -inset-[1px] rounded-3xl opacity-50 group-hover:opacity-100 transition-opacity duration-500 blur-[2px] ${hasCves ? 'bg-gradient-to-r from-red-500/50 to-transparent' : 'bg-gradient-to-r from-emerald-500/20 to-transparent'}`}></div>
                        
                        <div className="relative glass-panel bg-[#0F0F11]/95 px-8 py-7 border border-white/[0.05] group-hover:border-white/[0.1] transition-colors rounded-3xl z-10 transform-gpu group-hover:-translate-y-1 duration-500">
                          
                          <div className="flex flex-wrap md:flex-nowrap justify-between items-start gap-6 mb-6">
                            <div className="flex items-center gap-5">
                              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 shadow-inner ${hasCves ? 'bg-red-500/10 border border-red-500/20' : 'bg-emerald-500/10 border border-emerald-500/20'}`}>
                                <Server className={`w-6 h-6 ${hasCves ? 'text-red-400' : 'text-emerald-400'}`} />
                              </div>
                              <div className="flex flex-col gap-1.5">
                                <span className="font-bold text-2xl tracking-tight text-white flex items-center gap-2">
                                  {port} <span className="text-sm font-medium text-slate-500 tracking-widest uppercase">/ TCP</span>
                                </span>
                                {banners[port] && <span className="text-xs text-slate-400 font-mono bg-[#0A0A0C] px-3 py-1.5 rounded-lg border border-white/5 inline-block max-w-[280px] sm:max-w-[400px] truncate">{banners[port]}</span>}
                              </div>
                            </div>
                            
                            {hasCves ? (
                              <div className="flex flex-col items-end gap-2">
                                <div className="flex items-center gap-2.5 bg-red-500/10 text-red-400 px-4 py-2 rounded-xl border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]">
                                  <AlertTriangle className="w-4 h-4" />
                                  <span className="font-bold text-xs uppercase tracking-widest">{cves[port].length} Exploits</span>
                                </div>
                              </div>
                            ) : (
                              <div className="flex items-center gap-2 bg-emerald-500/10 text-emerald-400 px-4 py-2 rounded-xl border border-emerald-500/20">
                                <CheckCircle className="w-4 h-4" />
                                <span className="font-bold text-xs uppercase tracking-widest">Fortified</span>
                              </div>
                            )}
                          </div>

                          {webRecon[port] && (
                            <div className="mb-6 pt-5 border-t border-white/5">
                               <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">Discovered Web Surface</p>
                               <div className="flex flex-wrap gap-2">
                                  {webRecon[port].directories?.map(dir => (
                                    <span key={dir} className="text-xs bg-[#151518] hover:bg-[#1A1A1D] border border-white/10 text-slate-300 px-3 py-1.5 rounded-lg font-mono transition-colors cursor-default shadow-inner">{dir}</span>
                                  ))}
                                  {webRecon[port].waf && webRecon[port].waf !== "No WAF Detected" && (
                                    <span className="text-xs bg-amber-500/10 border border-amber-500/20 text-amber-400 px-3 py-1.5 rounded-lg font-mono flex items-center gap-2">
                                      <Shield className="w-3 h-3" /> WAF: {webRecon[port].waf}
                                    </span>
                                  )}
                               </div>
                            </div>
                          )}
                          
                          {hasCves && (
                            <div className="mb-6 space-y-2.5">
                              {cves[port].map(cve => (
                                <div key={cve.id} className="bg-[#151518] border border-red-500/10 hover:border-red-500/30 p-4 rounded-xl flex items-start gap-4 transition-colors">
                                  <span className="bg-red-500/10 text-red-400 font-bold font-mono text-xs px-2.5 py-1 rounded inline-block whitespace-nowrap">{cve.id}</span>
                                  <span className="text-slate-300 text-sm leading-relaxed">{cve.summary}</span>
                                </div>
                              ))}
                            </div>
                          )}
                          
                          <div className="mt-2 pt-6 border-t border-white/5 relative">
                            {explanations[port] ? (
                              <div className="relative overflow-hidden rounded-2xl border border-indigo-500/20 group/ai">
                                <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500/50"></div>
                                <div className="bg-gradient-to-r from-indigo-500/[0.03] to-transparent p-6">
                                  <p className="text-[10px] uppercase font-bold tracking-widest text-indigo-400 flex items-center gap-2 mb-4">
                                    <Activity className="w-3.5 h-3.5" /> AI Risk Synthesis
                                  </p>
                                  <div className="prose prose-invert prose-sm max-w-none text-slate-300/90 leading-relaxed text-[13px] font-medium">
                                      {explanations[port]}
                                  </div>
                                </div>
                              </div>
                            ) : (
                              explanations && Object.keys(explanations).length > 0 ? null : (
                                <div className="flex items-center gap-4 bg-white/[0.02] p-5 rounded-2xl border border-white/[0.05]">
                                  <div className="relative w-5 h-5">
                                    <div className="absolute inset-0 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
                                  </div>
                                  <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Synthesizing threat context via LLM...</p>
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
      ) : (
        /* History Tab */
        <div className="glass-panel p-8 min-h-[500px]">
          <div className="flex justify-between items-center mb-8 pb-6 border-b border-white/5">
            <h2 className="text-xl font-bold text-white flex items-center gap-3">
              <History className="w-6 h-6 text-indigo-400" />
              Historical Scan Database
            </h2>
            <button onClick={fetchHistory} className="text-sm font-medium text-slate-400 hover:text-white transition-colors bg-white/5 px-4 py-2 rounded-xl">
              Refresh Data
            </button>
          </div>

          {historyList.length === 0 ? (
            <div className="text-center py-20 text-slate-500 font-medium">
              No previous assessments found in the database.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300 border-separate border-spacing-y-3">
                <thead className="text-xs text-slate-500 font-semibold tracking-wide uppercase">
                  <tr>
                    <th className="px-6 py-4 font-normal">Reference ID</th>
                    <th className="px-6 py-4 font-normal">Timestamp</th>
                    <th className="px-6 py-4 font-normal">Target</th>
                    <th className="px-6 py-4 font-normal">Operator</th>
                    <th className="px-6 py-4 font-normal">Risk Profile</th>
                    <th className="px-6 py-4 font-normal text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="space-y-4">
                  {historyList.map(item => (
                    <tr key={item.id} className="bg-white/[0.02] hover:bg-white/[0.04] transition-colors shadow-sm">
                      <td className="px-6 py-5 rounded-l-2xl font-mono text-slate-500">#{item.id}</td>
                      <td className="px-6 py-5">{new Date(item.timestamp).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}</td>
                      <td className="px-6 py-5 text-indigo-300 font-mono">{item.target}</td>
                      <td className="px-6 py-5 font-medium">{(item.operator || 'Guest')}</td>
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-3">
                          <span className="bg-[#1A1A1D] px-3 py-1.5 rounded-lg text-xs font-semibold">{item.open_ports_count} Open</span>
                          <span className={`text-xs px-3 py-1.5 rounded-lg font-bold ${
                            item.risk_level === 'High' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                            item.risk_level === 'Medium' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                            'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          }`}>
                            {item.risk_level} Risk
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-5 rounded-r-2xl text-right border-l border-white/5 whitespace-nowrap space-x-2">
                        <button 
                          onClick={() => loadPastReport(item)}
                          className="text-sm bg-white hover:bg-slate-200 text-black font-semibold px-4 py-2 rounded-xl transition-all shadow-sm inline-block"
                        >
                          Review Data
                        </button>
                        {(previousByTarget.get(item.target) || []).some(h => new Date(h.timestamp) < new Date(item.timestamp)) && (
                          <button 
                            onClick={() => {
                               const sortedHistory = (previousByTarget.get(item.target) || [])
                                 .filter(h => new Date(h.timestamp) < new Date(item.timestamp))
                                 .sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp));
                               if (sortedHistory.length > 0) {
                                  setDiffData({ older: sortedHistory[0], newer: item });
                               }
                            }}
                            className="text-sm bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/30 border border-indigo-500/30 font-semibold px-4 py-2 rounded-xl transition-all shadow-sm inline-block"
                          >
                            Compare
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'ai-assistant' && (
        <Suspense fallback={<SectionLoader text="Loading InvisiBot AI Assistant..." />}>
          <AiChatbot activeReport={reportData} token={authData?.token} apiBaseUrl={API_BASE_URL} />
        </Suspense>
      )}

      {diffData && (
        <Suspense fallback={<SectionLoader text="Loading comparison..." />}>
          <DiffModal data={diffData} onClose={() => setDiffData(null)} />
        </Suspense>
      )}
      </div>
      
      {/* Mobile Bottom Navigation Bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#111113]/90 backdrop-blur-2xl border-t border-white/[0.05] pb-6 pt-2 px-2 shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
        <div className="flex justify-around items-center max-w-md mx-auto">
          <button onClick={() => setActiveTab('analytics')} className={`flex flex-col items-center gap-1.5 p-2 rounded-xl flex-1 transition-all ${activeTab === 'analytics' ? 'text-indigo-400 font-bold scale-110 drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]' : 'text-slate-500 font-medium'}`}>
            <Activity className="w-5 h-5" />
            <span className="text-[10px]">Command</span>
          </button>
          <button onClick={() => setActiveTab('scanner')} className={`flex flex-col items-center gap-1.5 p-2 rounded-xl flex-1 transition-all ${activeTab === 'scanner' ? 'text-indigo-400 font-bold scale-110 drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]' : 'text-slate-500 font-medium'}`}>
            <Target className="w-5 h-5" />
            <span className="text-[10px]">Scanner</span>
          </button>
          <button onClick={fetchHistory} className={`flex flex-col items-center gap-1.5 p-2 rounded-xl flex-1 transition-all ${activeTab === 'history' ? 'text-indigo-400 font-bold scale-110 drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]' : 'text-slate-500 font-medium'}`}>
            <History className="w-5 h-5" />
            <span className="text-[10px]">History</span>
          </button>
          <button onClick={() => setActiveTab('autopilot')} className={`flex flex-col items-center gap-1.5 p-2 rounded-xl flex-1 transition-all ${activeTab === 'autopilot' ? 'text-indigo-400 font-bold scale-110 drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]' : 'text-slate-500 font-medium'}`}>
            <Shield className="w-5 h-5" />
            <span className="text-[10px]">Autopilot</span>
          </button>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [authData, setAuthData] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem('soc_session');
    if (saved) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setAuthData(JSON.parse(saved));
    }
  }, []);

  const subscribePush = async (token) => {
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
      const perm = await Notification.requestPermission();
      if (perm !== 'granted') return;
      
      const reg = await navigator.serviceWorker.ready;
      if (!reg) return;

      const res = await fetch(`${API_BASE_URL}/api/vapid-public-key`);
      if (!res.ok) return;
      const { publicKey } = await res.json();
      
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: publicKey
      });
      
      await fetch(`${API_BASE_URL}/api/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ subscription: sub })
      });
    } catch(e) {
      console.warn("Push subscription failed", e);
    }
  };

  const handleLogin = (data) => {
    setAuthData(data);
    localStorage.setItem('soc_session', JSON.stringify(data));
    if (data.token) {
      subscribePush(data.token);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authData.token}`
        }
      });
    } catch(e) {
      console.error("Logout error", e);
    }
    localStorage.removeItem('soc_session');
    setAuthData(null);
    window.location.reload();
  };

  return authData ? (
    <Dashboard authData={authData} onLogout={handleLogout} />
  ) : (
    <Login onLogin={handleLogin} />
  );
}

export default App;
