import { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  MessageSquare,
  Users, 
  Globe, 
  BookOpen, 
  Shield,
  Search, 
  RefreshCw, 
  X, 
  Trash2, 
  Award, 
  Sparkles, 
  AlertCircle, 
  FileText, 
  FileSpreadsheet,
  Calendar,
  CheckCircle,
  Clock,
  Mail,
  ClipboardList,
  Star,
  Settings
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip 
} from 'recharts';

const API_BASE = "http://127.0.0.1:8000";

interface Candidate {
  full_name: string;
  email: string;
  phone: string;
  working_role: string;
  one_liner: string;
  technologies: string[];
  total_experience_years: number;
  industry_domain: string;
  technical_evaluation: string;
  summary: string;
  elevator_pitch: string;
  tag: string;
  is_duplicate: string;
  resume_score: number;
  source_file: string;
  raw_text: string;
  match_score?: number;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  candidates?: Candidate[];
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'intake' | 'chat' | 'talent' | 'sourcing' | 'logs' | 'bulk' | 'status' | 'interview' | 'settings'>('talent');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedContext, setSelectedContext] = useState<string>("Complete Hub");
  const [sysStatus, setSysStatus] = useState<any>({ all_clear: false, server: { status: "Offline", message: "Loading..." }, model: { status: "Offline", message: "Loading..." } });
  
  // Sourcing State
  const [sourcingResults, setSourcingResults] = useState<any[]>([]);
  const [sourcingMode, setSourcingMode] = useState<'ai' | 'manual'>('ai');
  const [sourcingJd, setSourcingJd] = useState("");
  const [sourcingLimit, setSourcingLimit] = useState(10);
  const [sourcingLang, setSourcingLang] = useState("Python");
  const [sourcingLoc, setSourcingLoc] = useState("");
  const [sourcingKeywords, setSourcingKeywords] = useState("");
  const [sourcingPlatform, setSourcingPlatform] = useState<'github' | 'linkedin'>('linkedin');
  const [outreachDrafts, setOutreachDrafts] = useState<Record<string, string>>({});
  
  // Talent Hub State
  const [searchQuery, setSearchQuery] = useState("");
  const [activeSearchFilter, setActiveSearchFilter] = useState<any>(null);
  const [selectedTag, setSelectedTag] = useState("All");
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([]);
  const [deepDiveCand, setDeepDiveCand] = useState<Candidate | null>(null);
  const [deepDiveTab, setDeepDiveTab] = useState<'overview' | 'pitch' | 'prep' | 'fit'>('overview');
  const [customPitch, setCustomPitch] = useState("");
  const [customGuide, setCustomGuide] = useState("");
  const [customOutreach, setCustomOutreach] = useState("");
  const [fitJd, setFitJd] = useState("");
  const [fitAnalysis, setFitAnalysis] = useState<any>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  // Chat/Assistant State
  const [chatHistory, setChatHistory] = useState<Message[]>(() => {
    const saved = localStorage.getItem("hriq_chat_history");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error("Failed to parse saved chat history", e);
      }
    }
    return [
      { role: 'assistant', content: "Hello! I am 'HRIQ Brain', your elite AI recruitment copilot. How can I help you find and screen talent today?" }
    ];
  });
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // Intake State
  const [uploadTag, setUploadTag] = useState("Global");
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [folderTag, setFolderTag] = useState("Global");
  const [folderPath, setFolderPath] = useState("");
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [parsingLogs, setParsingLogs] = useState<any[]>([]);

  // Bulk Actions State
  const [bulkTab, setBulkTab] = useState<'outreach' | 'comparison' | 'boolean' | 'pipeline' | 'radar'>('outreach');
  const [bulkJd, setBulkJd] = useState("");
  const [bulkOutreachEmails, setBulkOutreachEmails] = useState<Record<string, string>>({});
  const [bulkComparison, setBulkComparison] = useState("");
  const [booleanSourcing, setBooleanSourcing] = useState("");
  const [pipelineStages, setPipelineStages] = useState<Record<string, string[]>>(() => {
    const saved = localStorage.getItem("hriq_pipeline");
    if (saved) { try { return JSON.parse(saved); } catch { /* ignore */ } }
    return { 'Sourced': [], 'Screening': [], 'Interview': [], 'Offer': [], 'Hired': [] };
  });
  const [draggedCandidate, setDraggedCandidate] = useState<string | null>(null);

  // Interview Hub State
  const [interviews, setInterviews] = useState<any[]>([]);
  const [interviewTab, setInterviewTab] = useState<'pipeline' | 'schedule' | 'results' | 'scorecard'>('pipeline');
  const [selectedInterviewCand, setSelectedInterviewCand] = useState<Candidate | null>(null);
  const [interviewInvite, setInterviewInvite] = useState("");
  const [scheduleForm, setScheduleForm] = useState({ date: '', time: '', platform: 'Google Meet', interviewer: '', role: '' });
  const [resultForm, setResultForm] = useState({ candidate_name: '', role: '', result: 'Passed', score: '', notes: '' });
  const [scorecard, setScorecard] = useState("");
  const [scorecardRole, setScorecardRole] = useState("");
  const [sourcingError, setSourcingError] = useState("");
  
  // Settings / Recruiter Profile State
  const [settings, setSettings] = useState<any>({
    full_name: "Dhanush",
    email: "dhanush@example.com",
    phone: "+91 99999 99999",
    role: "Lead Talent Acquisition Partner",
    company: "HRIQ Inc",
    smtp_server: "smtp.gmail.com",
    smtp_port: 587,
    smtp_username: "dhanush@example.com",
    smtp_password: ""
  });
  
  const [googleStatus, setGoogleStatus] = useState<any>({ connected: false });
  
  // Email sending UI state
  const [emailCc, setEmailCc] = useState("");
  const [emailSubject, setEmailSubject] = useState("Interview Invitation");
  const [emailStatusMsg, setEmailStatusMsg] = useState("");

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Helper to open Deep Dive reset states
  const openDeepDive = (cand: Candidate) => {
    setDeepDiveCand(cand);
    setDeepDiveTab('overview');
    setCustomPitch("");
    setCustomGuide("");
    setCustomOutreach("");
    setFitAnalysis(null);
  };

  // Sync Chat History to Local Storage
  useEffect(() => {
    localStorage.setItem("hriq_chat_history", JSON.stringify(chatHistory));
  }, [chatHistory]);

  // Sync Pipeline to LocalStorage
  useEffect(() => {
    localStorage.setItem("hriq_pipeline", JSON.stringify(pipelineStages));
  }, [pipelineStages]);

  // Load interviews on mount
  useEffect(() => {
    fetchInterviews();
  }, []);

  const fetchInterviews = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/interview/list`);
      const data = await res.json();
      setInterviews(data.interviews || []);
    } catch (e) { console.error(e); }
  };

  const fetchGoogleStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/google/status`);
      const data = await res.json();
      setGoogleStatus(data);
    } catch (e) {
      console.error("Error loading Google status", e);
    }
  };

  // Fetch initial data
  useEffect(() => {
    fetchStatus();
    fetchTalent();
    fetchSettings();
    fetchGoogleStatus();
  }, []);

  // Handle Google OAuth callback redirect
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    if (code) {
      window.history.replaceState({}, document.title, window.location.pathname);
      
      const exchangeCode = async () => {
        setUploadProgress(10);
        setUploadStatus("Connecting Google Workspace...");
        try {
          const actualRedirectUri = window.location.origin + window.location.pathname;
          
          const res = await fetch(`${API_BASE}/api/google/callback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, redirect_uri: actualRedirectUri })
          });
          const data = await res.json();
          if (res.ok && data.success) {
            alert(`🎉 Google Workspace connected successfully as ${data.email}!`);
            fetchGoogleStatus();
            setActiveTab('settings');
          } else {
            alert(`❌ Connection failed: ${data.detail || "Unknown error"}`);
          }
        } catch (e: any) {
          alert(`❌ Connection error: ${e.message}`);
        } finally {
          setUploadProgress(null);
          setUploadStatus("");
        }
      };
      exchangeCode();
    }
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, chatLoading]);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`);
      const data = await res.json();
      setSysStatus(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchTalent = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/talent`);
      const data = await res.json();
      setCandidates(data.candidates || []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/settings`);
      const data = await res.json();
      if (data) setSettings(data);
    } catch (e) { console.error("Error loading settings", e); }
  };

  const saveSettings = async (updatedSettings: any) => {
    setLoadingAction("save_settings");
    try {
      const res = await fetch(`${API_BASE}/api/settings/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedSettings)
      });
      const data = await res.json();
      if (data.success) {
        setSettings(data.settings);
        alert("Settings saved successfully!");
      }
    } catch (e) { console.error("Error saving settings", e); }
    finally { setLoadingAction(null); }
  };

  const sendInviteEmail = async () => {
    if (!selectedInterviewCand || !interviewInvite) return;
    setLoadingAction("send_email");
    setEmailStatusMsg("");
    try {
      const ccList = emailCc.split(",").map(c => c.trim()).filter(c => c);
      const res = await fetch(`${API_BASE}/api/interview/send-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to_email: selectedInterviewCand.email,
          subject: emailSubject,
          body: interviewInvite,
          cc_emails: ccList
        })
      });
      const data = await res.json();
      if (data.success) {
        setEmailStatusMsg(`✅ ${data.message}`);
      } else {
        setEmailStatusMsg(`❌ Failed: ${data.detail || "Unknown error"}`);
      }
    } catch (e: any) {
      setEmailStatusMsg(`❌ Failed: ${e.message}`);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleSearchSubmit = async (e: any) => {
    e.preventDefault();
    if (!searchQuery) {
      setActiveSearchFilter(null);
      return;
    }
    setLoadingAction("searching");
    try {
      const formData = new FormData();
      formData.append("query", searchQuery);
      formData.append("context", selectedContext);
      const res = await fetch(`${API_BASE}/api/talent/search`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      setActiveSearchFilter(data.criteria);
      setCandidates(data.matches || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleSearchReset = () => {
    setSearchQuery("");
    setActiveSearchFilter(null);
    fetchTalent();
  };

  const handleUploadFiles = async (e: any) => {
    e.preventDefault();
    if (uploadFiles.length === 0) return;
    
    setUploadProgress(10);
    setUploadStatus("Uploading files...");
    
    const formData = new FormData();
    formData.append("tag", uploadTag);
    uploadFiles.forEach(file => {
      formData.append("files", file);
    });

    try {
      const res = await fetch(`${API_BASE}/api/intake/upload`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        setUploadStatus("Successfully ingested candidates!");
        setCandidates(data.candidates);
        setUploadFiles([]);
        
        // Log results
        const newLogs = data.errors.map((err: any) => ({
          timestamp: new Date().toLocaleTimeString(),
          file: err.file,
          status: "Failed",
          details: err.error
        })).concat(
          Array.from({ length: data.processed_count }).map((_, i) => ({
            timestamp: new Date().toLocaleTimeString(),
            file: `Resume Success #${i+1}`,
            status: "Success",
            details: "Integrated to Hub"
          }))
        );
        setParsingLogs(prev => [...newLogs, ...prev]);
      } else {
        setUploadStatus("Error ingesting candidates.");
      }
    } catch (e: any) {
      setUploadStatus(`Connection error: ${e.message}`);
    } finally {
      setUploadProgress(100);
      setTimeout(() => {
        setUploadProgress(null);
        setUploadStatus("");
      }, 3000);
    }
  };

  const handleFolderScan = async () => {
    if (!folderPath.trim()) return;
    
    setUploadProgress(10);
    setUploadStatus("Scanning folder...");
    
    try {
      const res = await fetch(`${API_BASE}/api/intake/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folderPath, tag: folderTag })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setUploadStatus("Successfully ingested candidates from folder!");
        setCandidates(data.candidates);
        setFolderPath("");
        
        // Log results
        const newLogs = data.errors.map((err: any) => ({
          timestamp: new Date().toLocaleTimeString(),
          file: err.file,
          status: "Failed",
          details: err.error
        })).concat(
          Array.from({ length: data.processed_count }).map((_, i) => ({
            timestamp: new Date().toLocaleTimeString(),
            file: `Folder Success #${i+1}`,
            status: "Success",
            details: "Integrated to Hub"
          }))
        );
        setParsingLogs(prev => [...newLogs, ...prev]);
      } else {
        setUploadStatus(data.detail || "Error scanning folder.");
      }
    } catch (e: any) {
      setUploadStatus(`Connection error: ${e.message}`);
    } finally {
      setUploadProgress(100);
      setTimeout(() => {
        setUploadProgress(null);
        setUploadStatus("");
      }, 3000);
    }
  };

  const handleSendChat = async (text: string) => {
    if (!text.trim()) return;
    setChatHistory(prev => [...prev, { role: 'user', content: text }]);
    setChatInput("");
    setChatLoading(true);

    try {
      const formData = new FormData();
      formData.append("query", text);
      formData.append("context", selectedContext);
      
      const res = await fetch(`${API_BASE}/api/talent/search`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: data.response, 
        candidates: data.matches && data.matches.length > 0 ? data.matches : undefined
      }]);
    } catch (e: any) {
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: `Error communicating with HRIQ Copilot: ${e.message}` 
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const generateReport = async (cand: Candidate, type: 'pitch' | 'guide') => {
    setLoadingAction(type);
    try {
      const res = await fetch(`${API_BASE}/api/talent/${type}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cand)
      });
      const data = await res.json();
      if (type === 'pitch') {
        setCustomPitch(data.pitch);
      } else {
        setCustomGuide(data.guide);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(null);
    }
  };

  const generateOutreach = async (cand: Candidate) => {
    setLoadingAction("outreach");
    try {
      const res = await fetch(`${API_BASE}/api/talent/outreach`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate: cand, jd_text: fitJd || "A top-tier role at our premium client" })
      });
      const data = await res.json();
      setCustomOutreach(data.email);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(null);
    }
  };

  const runGapAnalysis = async (cand: Candidate) => {
    if (!fitJd.trim()) return;
    setLoadingAction("gap");
    try {
      const res = await fetch(`${API_BASE}/api/talent/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate: cand, jd_text: fitJd })
      });
      const data = await res.json();
      setFitAnalysis(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(null);
    }
  };

  const runSourcing = async () => {
    setLoadingAction("sourcing");
    setSourcingResults([]);
    setSourcingError("");
    try {
      let language = sourcingLang;
      let location = sourcingLoc;
      let keywords = sourcingKeywords.split(",").map(k => k.trim()).filter(k => k);
      const platform = sourcingPlatform;
      
      if (sourcingMode === 'ai' && sourcingJd) {
        try {
          const criteriaRes = await fetch(`${API_BASE}/api/sourcing/extract-criteria`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ jd_text: sourcingJd })
          });
          const criteria = await criteriaRes.json();
          language = criteria.primary_language || language;
          location = criteria.suggested_location || location;
          keywords = criteria.keywords?.length ? criteria.keywords : keywords;
        } catch {
          // LLM unavailable — use raw keywords from JD text
          const jdLower = sourcingJd.toLowerCase();
          const langMap: Record<string,string> = {python:'Python',javascript:'JavaScript',typescript:'TypeScript',java:'Java',go:'Go',rust:'Rust','c++':'C++','c#':'C#',ruby:'Ruby',php:'PHP'};
          for (const [k,v] of Object.entries(langMap)) {
            if (jdLower.includes(k)) { language = v; break; }
          }
          const locWords = ['hyderabad','bangalore','chennai','mumbai','delhi','pune','remote','london'];
          for (const loc of locWords) { if (jdLower.includes(loc)) { location = loc.charAt(0).toUpperCase() + loc.slice(1); break; } }
        }
      }

      if (!language && !location && keywords.length === 0) {
        setSourcingError("Please provide at least a programming language, location, or keywords to search.");
        return;
      }
      
      const res = await fetch(`${API_BASE}/api/sourcing/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language, location, keywords, limit: sourcingLimit, platform })
      });
      const data = await res.json();
      const results = data.results || [];
      setSourcingResults(results);
      if (results.length === 0) {
        setSourcingError(`No GitHub profiles found for: ${[language, location, ...keywords].filter(Boolean).join(', ')}. Try different criteria.`);
      }
    } catch (e: any) {
      setSourcingError(`Search failed: ${e.message}`);
    } finally {
      setLoadingAction(null);
    }
  };

  const draftOutreach = async (cand: any) => {
    setLoadingAction(`outreach_${cand.username}`);
    try {
      const res = await fetch(`${API_BASE}/api/sourcing/outreach`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate: cand, jd_text: sourcingJd })
      });
      const data = await res.json();
      setOutreachDrafts(prev => ({ ...prev, [cand.username]: data.email }));
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(null);
    }
  };

  const importToTalentHub = async (cand: any) => {
    const newCandidate: Candidate = {
      full_name: cand.full_name,
      email: cand.email,
      phone: "N/A",
      working_role: `${sourcingLang} Specialist`,
      one_liner: cand.bio ? cand.bio.substring(0, 100) : "Sourced GitHub profile",
      technologies: [sourcingLang],
      total_experience_years: 0,
      industry_domain: "IT & Software",
      technical_evaluation: `Sourced profile. Bio: ${cand.bio}. Repos: ${cand.public_repos}. Followers: {cand.followers}`,
      summary: cand.bio || "",
      elevator_pitch: `GitHub developer with ${cand.followers} followers and ${cand.public_repos} repos.`,
      tag: "Sourced Candidates",
      is_duplicate: "No",
      resume_score: Math.min(100, Math.max(20, 20 + Math.floor(cand.followers/10) + cand.public_repos)),
      source_file: cand.profile_url,
      raw_text: `Sourced from GitHub profile ${cand.profile_url}. Bio: ${cand.bio}`
    };

    try {
      const updated = [...candidates, newCandidate];
      const res = await fetch(`${API_BASE}/api/talent/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated)
      });
      const data = await res.json();
      if (data.success) {
        setCandidates(updated);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const runBulkActions = async () => {
    const selectedData = candidates.filter(c => selectedCandidates.includes(c.full_name));
    if (selectedData.length === 0) return;

    setLoadingAction("bulk");
    try {
      if (bulkTab === 'outreach' && bulkJd) {
        const drafts: Record<string, string> = {};
        for (const cand of selectedData) {
          const res = await fetch(`${API_BASE}/api/talent/outreach`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ candidate: cand, jd_text: bulkJd })
          });
          const data = await res.json();
          drafts[cand.full_name] = data.email;
        }
        setBulkOutreachEmails(drafts);
      } else if (bulkTab === 'comparison') {
        const res = await fetch(`${API_BASE}/api/talent/compare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(selectedData)
        });
        const data = await res.json();
        setBulkComparison(data.battlecard);
      } else if (bulkTab === 'boolean' && bulkJd) {
        const res = await fetch(`${API_BASE}/api/talent/boolean`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ jd_text: bulkJd })
        });
        const data = await res.json();
        setBooleanSourcing(data.boolean);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(null);
    }
  };

  const deleteCandidate = async (name: string) => {
    const filtered = candidates.filter(c => c.full_name !== name);
    try {
      const res = await fetch(`${API_BASE}/api/talent/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filtered)
      });
      const data = await res.json();
      if (data.success) {
        setCandidates(filtered);
        if (deepDiveCand && deepDiveCand.full_name === name) {
          setDeepDiveCand(null);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const clearTag = async (tag: string) => {
    if (tag === "All") return;
    const filtered = candidates.filter(c => c.tag !== tag);
    try {
      const res = await fetch(`${API_BASE}/api/talent/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filtered)
      });
      const data = await res.json();
      if (data.success) {
        setCandidates(filtered);
        setSelectedTag("All");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const downloadExcel = () => {
    alert("Excel Report has been generated successfully and is ready for download.");
  };

  // ─── Interview Hub API Functions ───────────────────────────────────
  const generateInvite = async (cand: Candidate | any, role: string) => {
    setLoadingAction("invite");
    try {
      const res = await fetch(`${API_BASE}/api/interview/invite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate: cand, role, company: settings.company || "Our Client", jd_text: sourcingJd || fitJd })
      });
      const data = await res.json();
      let emailBody = data.invite_email || "";
      
      // Inject personalized signature if settings exists
      if (settings.full_name) {
        const signature = `\n\nBest regards,\n${settings.full_name}\n${settings.role || ""}\n${settings.company || ""}\nEmail: ${settings.email || ""}\nPhone: ${settings.phone || ""}`;
        emailBody = emailBody.replace(/Best regards,[\s\S]*/, signature);
      }
      
      // Replace dynamic placeholders with form values
      if (scheduleForm.date) {
        emailBody = emailBody.replace(/\[DATE\]/g, scheduleForm.date);
      }
      if (scheduleForm.time) {
        emailBody = emailBody.replace(/\[TIME\]/g, scheduleForm.time);
      }
      if (scheduleForm.platform) {
        emailBody = emailBody.replace(/\[PLATFORM\]/g, scheduleForm.platform);
      }
      const interviewer = scheduleForm.interviewer || settings.full_name || "HR Team";
      emailBody = emailBody.replace(/\[INTERVIEWER_NAME\]/g, interviewer);
      
      setInterviewInvite(emailBody);
      setEmailSubject(`Interview Invitation — ${role} at ${settings.company || "Our Client"}`);
    } catch (e: any) {
      setInterviewInvite(`Error generating invite: ${e.message}`);
    } finally { setLoadingAction(null); }
  };

  const doScheduleInterview = async () => {
    if (!selectedInterviewCand || !scheduleForm.date) return;
    setLoadingAction("schedule");
    try {
      const res = await fetch(`${API_BASE}/api/interview/schedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: selectedInterviewCand.full_name || (selectedInterviewCand as any).username,
          candidate_email: selectedInterviewCand.email || "",
          ...scheduleForm,
          interviewer: scheduleForm.interviewer || settings.full_name
        })
      });
      const data = await res.json();
      if (data.success) {
        setInterviews(data.interviews || []);
        alert("🎉 Interview scheduled successfully!");
        setScheduleForm({ date: '', time: '', platform: 'Google Meet', interviewer: '', role: '' });
        setSelectedInterviewCand(null);
        setInterviewTab('pipeline');
      }
    } catch (e) { console.error(e); } finally { setLoadingAction(null); }
  };

  const doSaveResult = async () => {
    if (!resultForm.candidate_name) return;
    setLoadingAction("result");
    try {
      const res = await fetch(`${API_BASE}/api/interview/result`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...resultForm, score: resultForm.score ? parseFloat(resultForm.score) : null })
      });
      const data = await res.json();
      if (data.success) {
        setInterviews(data.interviews || []);
        alert("🎉 Post-interview results saved successfully!");
        setResultForm({ candidate_name: '', role: '', result: 'Passed', score: '', notes: '' });
        setInterviewTab('pipeline');
      }
    } catch (e) { console.error(e); } finally { setLoadingAction(null); }
  };

  const doCancelInterview = async (candidateName: string, role: string) => {
    if (!window.confirm(`Are you sure you want to cancel the scheduled interview for ${candidateName}? This will notify the candidate and remove the Google Calendar event.`)) return;
    setLoadingAction("cancel_interview");
    try {
      const res = await fetch(`${API_BASE}/api/interview/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_name: candidateName, role })
      });
      const data = await res.json();
      if (data.success) {
        setInterviews(data.interviews || []);
        alert("🎉 Interview cancelled and candidate has been notified!");
      } else {
        alert(`❌ Failed to cancel: ${data.detail || "Unknown error"}`);
      }
    } catch (e: any) {
      console.error(e);
      alert(`❌ Error cancelling interview: ${e.message}`);
    } finally {
      setLoadingAction(null);
    }
  };

  const generateScorecardFn = async (cand: Candidate | any, role: string) => {
    setLoadingAction("scorecard");
    try {
      const res = await fetch(`${API_BASE}/api/interview/scorecard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate: cand, role, jd_text: sourcingJd || fitJd })
      });
      const data = await res.json();
      setScorecard(data.scorecard || "");
    } catch (e: any) {
      setScorecard(`Error: ${e.message}`);
    } finally { setLoadingAction(null); }
  };

  // Helper to render markdown format in UI
  const renderMarkdown = (text: string) => {
    if (!text) return null;
    const lines = text.split("\n");
    return lines.map((line, idx) => {
      let content = line;
      if (content.startsWith("### ")) {
        return <h4 key={idx} className="text-md font-bold text-slate-800 mt-3 mb-1">{content.replace("### ", "")}</h4>;
      }
      if (content.startsWith("## ")) {
        return <h3 key={idx} className="text-lg font-bold text-slate-900 mt-4 mb-2">{content.replace("## ", "")}</h3>;
      }
      if (content.startsWith("# ")) {
        return <h2 key={idx} className="text-xl font-bold text-slate-900 mt-5 mb-3">{content.replace("# ", "")}</h2>;
      }
      if (content.trim().startsWith("- ")) {
        return (
          <li key={idx} className="ml-4 list-disc text-slate-700 text-sm py-0.5">
            {parseInlineMarkdown(content.trim().replace("- ", ""))}
          </li>
        );
      }
      if (content.trim() === "") return <div key={idx} className="h-2" />;
      return <p key={idx} className="text-sm text-slate-700 leading-relaxed mb-2">{parseInlineMarkdown(content)}</p>;
    });
  };

  const parseInlineMarkdown = (text: string) => {
    const boldRegex = /\*\*(.*?)\*\*/g;
    const parts = [];
    let lastIndex = 0;
    let match;
    
    while ((match = boldRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      const boldText = match[1];
      const matchCand = candidates.find(c => c.full_name.toLowerCase() === boldText.toLowerCase());
      if (matchCand) {
        parts.push(
          <button 
            key={match.index} 
            onClick={() => {
              openDeepDive(matchCand);
            }}
            className="font-bold text-indigo-600 hover:text-indigo-800 hover:underline cursor-pointer bg-transparent border-0 p-0 align-baseline font-sans text-sm inline-block"
          >
            {boldText}
          </button>
        );
      } else {
        parts.push(<strong key={match.index} className="font-semibold text-slate-900">{boldText}</strong>);
      }
      lastIndex = boldRegex.lastIndex;
    }
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }
    
    return parts.length > 0 ? parts : text;
  };

  // Filtering candidates for Hub Grid
  const getFilteredCandidates = () => {
    let list = candidates;
    if (selectedTag !== "All") {
      list = list.filter(c => c.tag === selectedTag);
    }
    return list;
  };

  // Recharts Data Parsing
  const getDomainChartData = () => {
    const counts: Record<string, number> = {};
    candidates.forEach(c => {
      const d = c.industry_domain || "Other";
      counts[d] = (counts[d] || 0) + 1;
    });
    return Object.keys(counts).map(key => ({ name: key, value: counts[key] }));
  };

  const getExperienceChartData = () => {
    const categories = { "Junior (0-2y)": 0, "Mid-level (3-5y)": 0, "Senior (6y+)": 0 };
    candidates.forEach(c => {
      const y = c.total_experience_years || 0;
      if (y <= 2) categories["Junior (0-2y)"]++;
      else if (y <= 5) categories["Mid-level (3-5y)"]++;
      else categories["Senior (6y+)"]++;
    });
    return Object.keys(categories).map(key => ({ name: key, count: (categories as any)[key] }));
  };

  const COLORS = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#EC4899', '#8B5CF6'];

  const allTags = Array.from(new Set(candidates.map(c => c.tag || "Global")));

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 ambient-bg font-sans">
      
      {/* SIDEBAR NAVIGATION */}
      <aside className="w-64 flex flex-col bg-white border-r border-slate-200">
        {/* Header Logo */}
        <div className="p-6 flex flex-col items-center border-b border-slate-100">
          <img src="/logo.png" alt="HRIQ" className="h-16 object-contain" />
          <span className="text-xs font-semibold text-slate-400 mt-2 uppercase tracking-widest">Talent Intelligence</span>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          <button 
            onClick={() => setActiveTab('intake')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all ${activeTab === 'intake' ? 'bg-indigo-50 text-indigo-600 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
          >
            <Upload className="h-5 w-5 mr-3" />
            Intake Hub
          </button>
          <button 
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all ${activeTab === 'chat' ? 'bg-indigo-50 text-indigo-600 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
          >
            <MessageSquare className="h-5 w-5 mr-3" />
            AI Assistant
          </button>
          <button 
            onClick={() => setActiveTab('talent')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all ${activeTab === 'talent' ? 'bg-indigo-50 text-indigo-600 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
          >
            <Users className="h-5 w-5 mr-3" />
            Talent Hub
          </button>
          <button 
            onClick={() => setActiveTab('sourcing')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all ${activeTab === 'sourcing' ? 'bg-indigo-50 text-indigo-600 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
          >
            <Globe className="h-5 w-5 mr-3" />
            Web Sourcing
          </button>
          <button 
            onClick={() => setActiveTab('interview')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all ${activeTab === 'interview' ? 'bg-indigo-50 text-indigo-600 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
          >
            <Calendar className="h-5 w-5 mr-3" />
            Interview Hub
          </button>
          <button 
            onClick={() => setActiveTab('bulk')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all ${activeTab === 'bulk' ? 'bg-indigo-50 text-indigo-600 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
          >
            <BookOpen className="h-5 w-5 mr-3" />
            Bulk Actions
          </button>
          <button 
            onClick={() => setActiveTab('logs')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all ${activeTab === 'logs' ? 'bg-indigo-50 text-indigo-600 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
          >
            <FileText className="h-5 w-5 mr-3" />
            Parsing Logs
          </button>
          <button 
            onClick={() => setActiveTab('status')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all ${activeTab === 'status' ? 'bg-indigo-50 text-indigo-600 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
          >
            <Shield className="h-5 w-5 mr-3" />
            Diagnostics
          </button>
          <button 
            onClick={() => setActiveTab('settings')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all ${activeTab === 'settings' ? 'bg-indigo-50 text-indigo-600 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}
          >
            <Settings className="h-5 w-5 mr-3" />
            Settings
          </button>
        </nav>

        {/* Global Connection Badge */}
        <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-400 font-medium">Model Status:</span>
          {sysStatus.all_clear ? (
            <span className="flex items-center text-emerald-600 font-semibold">
              <span className="h-2 w-2 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
              🟢 AI Connected
            </span>
          ) : (
            <span className="flex items-center text-rose-600 font-semibold">
              <span className="h-2 w-2 rounded-full bg-rose-500 mr-1.5" />
              🔴 AI Offline
            </span>
          )}
        </div>
      </aside>

      {/* MAIN SCREEN PANEL */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center space-y-1">
            <h1 className="text-lg font-bold text-slate-800 tracking-tight">HRIQ Talent Copilot</h1>
          </div>
          {/* Assistant Context Filter */}
          <div className="flex items-center space-x-3 text-sm">
            <span className="text-slate-500 font-medium">Search Context:</span>
            <select 
              value={selectedContext}
              onChange={(e) => setSelectedContext(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-slate-700 text-sm font-medium outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            >
              <option value="Complete Hub">Complete Hub</option>
              {allTags.map(tag => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
            </select>
          </div>
        </header>

        <div className="flex-1 p-8 overflow-y-auto space-y-6">
          
          {/* TAB: INTAKE HUB */}
          <div className={activeTab === 'intake' ? 'space-y-6 max-w-4xl' : 'hidden'}>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Intake Hub</h2>
                <p className="text-slate-500 text-sm mt-0.5">Ingest and process candidate resumes in parallel.</p>
              </div>

              {/* Batch Upload Component */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <h3 className="text-lg font-bold text-slate-800 flex items-center">
                  <Upload className="h-5 w-5 text-indigo-500 mr-2" />
                  Resource Integration (File Uploader)
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1.5">Batch Reference (Tag)</label>
                    <input 
                      type="text" 
                      value={uploadTag} 
                      onChange={(e) => setUploadTag(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1.5">Select Files (PDF/DOCX)</label>
                    <input 
                      type="file" 
                      multiple 
                      onChange={(e) => {
                        if (e.target.files) {
                          setUploadFiles(Array.from(e.target.files));
                        }
                      }}
                      className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
                    />
                  </div>
                </div>

                {uploadFiles.length > 0 && (
                  <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-xs text-slate-500 space-y-1">
                    <p className="font-semibold text-slate-700">Selected Files:</p>
                    {uploadFiles.map((f, i) => <p key={i}>📄 {f.name} ({(f.size/1024).toFixed(1)} KB)</p>)}
                  </div>
                )}

                <button 
                  onClick={handleUploadFiles}
                  disabled={uploadFiles.length === 0}
                  className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 disabled:text-slate-400 text-white font-semibold text-sm rounded-lg py-2.5 transition-colors flex items-center justify-center"
                >
                  🚀 Execute Parallel Ingestion
                </button>

                {uploadProgress !== null && (
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs font-semibold text-slate-500">
                      <span>{uploadStatus}</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-indigo-600 h-full rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                    </div>
                  </div>
                )}
              </div>

              {/* Folder Scan Component */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <h3 className="text-lg font-bold text-slate-800 flex items-center">
                  <Globe className="h-5 w-5 text-indigo-500 mr-2" />
                  Recursive Folder Intelligence
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1.5">Collection Reference (Tag)</label>
                    <input 
                      type="text" 
                      value={folderTag} 
                      onChange={(e) => setFolderTag(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1.5">Absolute Directory Path</label>
                    <input 
                      type="text" 
                      placeholder="e.g. C:\Users\Name\Resumes"
                      value={folderPath} 
                      onChange={(e) => setFolderPath(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>
                <button 
                  onClick={handleFolderScan}
                  disabled={!folderPath.trim()}
                  className="w-full bg-white hover:bg-slate-50 disabled:bg-slate-100 disabled:text-slate-400 text-slate-800 border border-slate-200 font-semibold text-sm rounded-lg py-2.5 transition-colors"
                >
                  ⚡ Deep Scan (Turbo Folder Scan)
                </button>
              </div>
          </div>

          {/* TAB: AI ASSISTANT CHAT */}
          <div className={activeTab === 'chat' ? 'flex flex-col h-[calc(100vh-12rem)] border border-slate-200 bg-white rounded-xl overflow-hidden shadow-sm' : 'hidden'}>
              {/* Chat Stream Header */}
              <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Sparkles className="h-5 w-5 text-indigo-500" />
                  <span className="font-bold text-slate-800 text-sm">HRIQ Brain Dialog Screen</span>
                </div>
                <button 
                  onClick={() => {
                    const cleared = [{ role: 'assistant' as const, content: "Chat timeline cleared. How can HRIQ assist you now?" }];
                    setChatHistory(cleared);
                    localStorage.setItem("hriq_chat_history", JSON.stringify(cleared));
                  }}
                  className="text-xs text-slate-400 hover:text-slate-600 font-medium"
                >
                  Clear Timeline
                </button>
              </div>

              {/* Chat Timeline list */}
              <div className="flex-1 p-6 overflow-y-auto space-y-6">
                {chatHistory.map((msg, msgIdx) => (
                  <div key={msgIdx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`flex space-x-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
                      <div className={`h-8 w-8 rounded-full shrink-0 flex items-center justify-center font-bold text-xs ${msg.role === 'user' ? 'bg-slate-900 text-white' : 'bg-indigo-600 text-white'}`}>
                        {msg.role === 'user' ? 'UR' : 'IQ'}
                      </div>
                      <div className="space-y-4">
                        <div className={`rounded-xl p-4 shadow-sm text-sm border ${msg.role === 'user' ? 'bg-slate-900 text-white border-slate-800 rounded-tr-none' : 'bg-white text-slate-800 border-slate-200 rounded-tl-none'}`}>
                          {msg.role === 'assistant' ? <div className="space-y-1">{renderMarkdown(msg.content)}</div> : msg.content}
                        </div>

                        {/* Rendering candidate attachments dynamically */}
                        {msg.candidates && (
                          <div className="space-y-3 mt-4">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Matched Talent Profiles:</span>
                            {msg.candidates.map((cand, idx) => (
                              <div key={idx} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <h4 className="font-bold text-slate-900 text-base">{cand.full_name}</h4>
                                    <p className="text-xs text-slate-400 font-medium">{cand.working_role} | 📍 {cand.phone !== "N/A" ? cand.phone : "Global"}</p>
                                  </div>
                                  <div className="flex items-center bg-indigo-50 text-indigo-700 text-xs font-extrabold px-2.5 py-1 rounded-full border border-indigo-100">
                                    <Award className="h-3.5 w-3.5 mr-1" />
                                    Score: {cand.resume_score}
                                  </div>
                                </div>
                                
                                <div className="text-xs text-slate-500 leading-relaxed border-t border-slate-100 pt-3">
                                  <p><strong className="text-slate-700 font-semibold">Pitch One-Liner:</strong> {cand.one_liner}</p>
                                  <p className="mt-1"><strong className="text-slate-700 font-semibold">Key Technologies:</strong> {cand.technologies.join(", ")}</p>
                                </div>

                                {/* Custom nested workflow widgets inside chat */}
                                <div className="border-t border-slate-100 pt-3 flex flex-wrap gap-2 text-xs">
                                  <button 
                                    onClick={() => handleSendChat(`generate pitch for ${cand.full_name}`)}
                                    className="bg-slate-50 hover:bg-slate-100 border border-slate-200 font-semibold text-slate-700 px-3 py-1.5 rounded-lg flex items-center transition-colors"
                                  >
                                    💼 Pitch
                                  </button>
                                  <button 
                                    onClick={() => handleSendChat(`generate interview prep questions for ${cand.full_name}`)}
                                    className="bg-slate-50 hover:bg-slate-100 border border-slate-200 font-semibold text-slate-700 px-3 py-1.5 rounded-lg flex items-center transition-colors"
                                  >
                                    🎤 Questions
                                  </button>
                                  <button 
                                    onClick={() => {
                                      const firstName = cand.full_name.split(" ")[0];
                                      const draftText = `Hi ${firstName},\n\nWe are glad to invite you for attending interview. Your profile is a good fit for us.\n\nBest regards,\n${settings.full_name || "HR Team"}`;
                                      setInterviewInvite(draftText);
                                      setSelectedInterviewCand(cand);
                                      setScheduleForm(f => ({ ...f, role: cand.working_role || "" }));
                                      setEmailSubject(`Interview Invitation — ${cand.working_role || "Position"} at ${settings.company || "Our Client"}`);
                                      setInterviewTab('schedule');
                                      setActiveTab('interview');
                                    }}
                                    className="bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 font-semibold text-indigo-700 px-3 py-1.5 rounded-lg flex items-center transition-colors"
                                  >
                                    📧 Email
                                  </button>
                                  <button 
                                    onClick={() => {
                                      if (!selectedCandidates.includes(cand.full_name)) {
                                        setSelectedCandidates(prev => [...prev, cand.full_name]);
                                      } else {
                                        setSelectedCandidates(prev => prev.filter(c => c !== cand.full_name));
                                      }
                                    }}
                                    className={`px-3 py-1.5 rounded-lg font-semibold border transition-all ${selectedCandidates.includes(cand.full_name) ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-indigo-50 border-indigo-200 text-indigo-700'}`}
                                  >
                                    {selectedCandidates.includes(cand.full_name) ? '✅ Selected' : '➕ Select Profile'}
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="flex space-x-3 items-center">
                      <div className="h-8 w-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs animate-bounce">
                        IQ
                      </div>
                      <span className="text-xs text-slate-400 font-medium">HRIQ Brain is typing...</span>
                    </div>
                  </div>
                )}
                
                <div ref={chatEndRef} />
              </div>

              {/* Chat Input form wrapper */}
              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendChat(chatInput);
                }}
                className="p-4 border-t border-slate-200 bg-white flex space-x-3 items-center shrink-0"
              >
                <input 
                  type="text" 
                  value={chatInput} 
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask HRIQ Copilot something (e.g. 'Who knows Python and React?')"
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm outline-none focus:bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                />
                <button 
                  type="submit" 
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm px-6 py-3 rounded-xl transition-colors shrink-0 shadow-sm shadow-indigo-100"
                >
                  Send Query
                </button>
              </form>
          </div>

          {/* TAB: TALENT HUB DATABASE */}
          <div className={activeTab === 'talent' ? 'space-y-6' : 'hidden'}>
              
              {/* Analytics Graphs row */}
              <div className="grid grid-cols-3 gap-6">
                
                {/* Metric overview */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Ecosystem Metrics</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-0.5">
                      <span className="text-3xl font-extrabold text-slate-900">{candidates.length}</span>
                      <p className="text-xs font-medium text-slate-400">Total Talent Profiles</p>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-3xl font-extrabold text-emerald-600">
                        {(candidates.reduce((sum, c) => sum + c.resume_score, 0) / (candidates.length || 1)).toFixed(1)}
                      </span>
                      <p className="text-xs font-medium text-slate-400">Average Fit Score</p>
                    </div>
                  </div>
                </div>

                {/* Domain Ecosystem Graph */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col h-48">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Domain Ecosystem</h3>
                  <div className="flex-1 min-h-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={getDomainChartData()}
                          innerRadius={30}
                          outerRadius={50}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {getDomainChartData().map((_, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Seniority Distribution Graph */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col h-48">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Seniority Profile</h3>
                  <div className="flex-1 min-h-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getExperienceChartData()}>
                        <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                        <YAxis tick={{ fontSize: 10 }} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#4F46E5" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Data search inputs bar */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">🔍 Search Filters</h3>
                <form onSubmit={handleSearchSubmit} className="flex items-center space-x-3">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-3.5 h-4 w-4 text-slate-400" />
                    <input 
                      type="text" 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search database (e.g. 'Senior dev with React experience')"
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-2.5 text-sm outline-none focus:bg-white focus:border-indigo-500 transition-all"
                    />
                  </div>
                  <button 
                    type="submit"
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm px-5 py-2.5 rounded-lg transition-colors flex items-center"
                  >
                    {loadingAction === 'searching' && <RefreshCw className="animate-spin h-4 w-4 mr-2" />}
                    Search
                  </button>
                  <button 
                    type="button"
                    onClick={handleSearchReset}
                    className="bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 font-bold text-sm px-5 py-2.5 rounded-lg transition-colors"
                  >
                    Reset
                  </button>
                </form>

                {activeSearchFilter && (
                  <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3 text-xs text-indigo-700 flex items-center justify-between">
                    <span>Active Filters extracted: <strong>Keyword:</strong> {activeSearchFilter.role_keyword || "N/A"} | <strong>Skills:</strong> {activeSearchFilter.skills?.join(", ") || "None"} | <strong>Min Exp:</strong> {activeSearchFilter.min_experience || 0}y</span>
                    <button onClick={handleSearchReset} className="font-bold text-indigo-900 hover:underline">Clear Filter</button>
                  </div>
                )}

                {/* Tag Select Filter row */}
                <div className="border-t border-slate-100 pt-4 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-slate-500">🎯 Filter by Collection Tag:</span>
                    <select 
                      value={selectedTag}
                      onChange={(e) => setSelectedTag(e.target.value)}
                      className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs font-semibold text-slate-600 outline-none"
                    >
                      <option value="All">All Tags</option>
                      {allTags.map(tag => (
                        <option key={tag} value={tag}>{tag}</option>
                      ))}
                    </select>
                  </div>

                  {selectedTag !== "All" && (
                    <button 
                      onClick={() => clearTag(selectedTag)}
                      className="text-xs text-rose-600 hover:text-rose-700 font-bold flex items-center"
                    >
                      <Trash2 className="h-3.5 w-3.5 mr-1" />
                      Clear all candidates in '{selectedTag}'
                    </button>
                  )}
                </div>
              </div>

              {/* Candidates Data Table */}
              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <h3 className="font-bold text-slate-800 text-sm">🧬 Candidate Database Matrix</h3>
                  <button 
                    onClick={downloadExcel}
                    className="bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-bold flex items-center transition-all"
                  >
                    <FileSpreadsheet className="h-4 w-4 text-emerald-600 mr-1.5" />
                    Download Excel Report
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-xs font-semibold text-slate-400 bg-slate-50/50 uppercase tracking-wider">
                        <th className="py-3 px-6 w-12">Select</th>
                        <th className="py-3 px-6">Name</th>
                        <th className="py-3 px-6">Role</th>
                        <th className="py-3 px-6">Domain</th>
                        <th className="py-3 px-6">Experience</th>
                        <th className="py-3 px-6">Score</th>
                        <th className="py-3 px-6">Duplicate</th>
                        <th className="py-3 px-6">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                      {getFilteredCandidates().map((cand, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                          <td className="py-3.5 px-6">
                            <input 
                              type="checkbox" 
                              checked={selectedCandidates.includes(cand.full_name)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedCandidates(prev => [...prev, cand.full_name]);
                                } else {
                                  setSelectedCandidates(prev => prev.filter(c => c !== cand.full_name));
                                }
                              }}
                              className="h-4 w-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
                            />
                          </td>
                          <td className="py-3.5 px-6 font-bold text-slate-900">{cand.full_name}</td>
                          <td className="py-3.5 px-6 font-medium text-indigo-600">{cand.working_role}</td>
                          <td className="py-3.5 px-6">{cand.industry_domain}</td>
                          <td className="py-3.5 px-6 font-semibold">{cand.total_experience_years} Years</td>
                          <td className="py-3.5 px-6">
                            <span className="font-extrabold bg-indigo-50 text-indigo-700 text-xs px-2.5 py-1 rounded-full border border-indigo-100">
                              {cand.resume_score}
                            </span>
                          </td>
                          <td className="py-3.5 px-6">
                            {cand.is_duplicate === "Yes" ? (
                              <span className="bg-rose-50 text-rose-700 text-xs font-semibold px-2 py-0.5 rounded border border-rose-100">Duplicate</span>
                            ) : (
                              <span className="text-slate-400 text-xs font-medium">Unique</span>
                            )}
                          </td>
                          <td className="py-3.5 px-6 space-x-2.5">
                            <button 
                              onClick={() => openDeepDive(cand)}
                              className="text-indigo-600 hover:text-indigo-800 font-bold hover:underline"
                            >
                              Deep Dive
                            </button>
                            <button 
                              onClick={() => deleteCandidate(cand.full_name)}
                              className="text-rose-600 hover:text-rose-800 font-bold hover:underline"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

          </div>

          {/* TAB: WEB SOURCING */}
          <div className={activeTab === 'sourcing' ? 'space-y-6' : 'hidden'}>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Web Sourcing Engine</h2>
                <p className="text-slate-500 text-sm mt-0.5">Find active software developers directly from the web using live API indexes.</p>
              </div>

              {/* Stateful Sourcing Switcher */}
              <div className="flex border-b border-slate-200 justify-between items-center pr-2">
                <div className="flex gap-6">
                  <button
                    onClick={() => setSourcingMode('ai')}
                    className={`pb-3 text-sm font-semibold border-b-2 transition-all ${sourcingMode === 'ai' ? 'border-indigo-600 text-indigo-600 font-bold' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
                  >
                    ⚡ AI Semantic Sourcing
                  </button>
                  <button
                    onClick={() => setSourcingMode('manual')}
                    className={`pb-3 text-sm font-semibold border-b-2 transition-all ${sourcingMode === 'manual' ? 'border-indigo-600 text-indigo-600 font-bold' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
                  >
                    🔍 Manual Sourcing
                  </button>
                </div>
                
                {/* Platform Selector Selection */}
                <div className="flex items-center space-x-2 bg-slate-100 p-1 rounded-lg border border-slate-200 mb-2">
                  <button
                    onClick={() => setSourcingPlatform('linkedin')}
                    className={`text-xs font-bold px-3 py-1.5 rounded transition-all ${sourcingPlatform === 'linkedin' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
                  >
                    💼 LinkedIn Sourcing (SerpAPI)
                  </button>
                </div>
              </div>

              {/* Sourcing parameters card */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                {sourcingMode === 'ai' ? (
                  <div className="space-y-3">
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest">Paste Job Description for Criteria Parsing:</label>
                    <textarea 
                      rows={4}
                      value={sourcingJd}
                      onChange={(e) => setSourcingJd(e.target.value)}
                      placeholder="Paste target JD to extract keywords, skills, and suggested locations..."
                      className="w-full border border-slate-200 rounded-lg p-3 text-sm outline-none focus:border-indigo-500"
                    />
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Primary Language</label>
                      <select 
                        value={sourcingLang}
                        onChange={(e) => setSourcingLang(e.target.value)}
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none"
                      >
                        {["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#", "PHP", "HTML"].map(l => (
                          <option key={l} value={l}>{l}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Target Location</label>
                      <input 
                        type="text" 
                        value={sourcingLoc} 
                        onChange={(e) => setSourcingLoc(e.target.value)}
                        placeholder="e.g. San Francisco"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Keywords</label>
                      <input 
                        type="text" 
                        value={sourcingKeywords} 
                        onChange={(e) => setSourcingKeywords(e.target.value)}
                        placeholder="e.g. React, FastAPI"
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-slate-500">Max Results Limit:</span>
                    <input 
                      type="number" 
                      min={5} 
                      max={30} 
                      value={sourcingLimit} 
                      onChange={(e) => setSourcingLimit(parseInt(e.target.value))}
                      className="w-16 border border-slate-200 rounded px-2 py-1 text-xs outline-none font-bold"
                    />
                  </div>
                  
              <button
                  onClick={runSourcing}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-6 py-2.5 rounded-lg transition-colors flex items-center"
                >
                  {loadingAction === 'sourcing' && <RefreshCw className="animate-spin h-3.5 w-3.5 mr-1.5" />}
                  🚀 {sourcingMode === 'ai' ? 'AI Extract & Source Live Profiles' : `Search ${sourcingPlatform === 'linkedin' ? 'LinkedIn' : 'GitHub'} Profiles`}
                </button>
              </div>
            </div>

              {/* Sourcing Profiles list */}
              {sourcingResults.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Profiles Sourced:</h3>
                  {sourcingResults.map((cand, idx) => (
                    <div key={idx} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                      <div className="flex justify-between items-start">
                        <div className="flex space-x-4">
                          {cand.avatar_url && <img src={cand.avatar_url} alt="" className="h-14 w-14 rounded-full border border-slate-100" />}
                          <div>
                            <h4 className="font-bold text-slate-900 text-lg flex items-center">
                              <a href={cand.profile_url} target="_blank" className="hover:underline">{cand.full_name}</a>
                              <span className="text-slate-400 text-xs font-medium ml-2">@{cand.username}</span>
                            </h4>
                            <p className="text-xs text-slate-400 font-semibold">📍 {cand.location} | 🏢 {cand.company} | ✉️ {cand.email}</p>
                            <p className="text-sm text-slate-600 font-medium mt-1">{cand.bio}</p>
                          </div>
                        </div>
                        <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs text-slate-500 space-y-0.5 text-right shrink-0">
                          {sourcingPlatform === 'github' ? (
                            <>
                              <p>⭐ Repositories: <strong>{cand.public_repos}</strong></p>
                              <p>👥 Followers: <strong>{cand.followers}</strong></p>
                            </>
                          ) : (
                            <>
                              <p>⚡ Experience: <strong>{cand.experience_years || 'N/A'}</strong></p>
                              <p>🎓 Domain: <strong>{cand.domain || 'N/A'}</strong></p>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Outreach Draft & Action keys */}
                      <div className="border-t border-slate-100 pt-3 flex items-center justify-between">
                        <div className="space-x-3">
                          <button 
                            onClick={() => draftOutreach(cand)}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors flex items-center"
                          >
                            {loadingAction === `outreach_${cand.username}` && <RefreshCw className="animate-spin h-3.5 w-3.5 mr-1.5" />}
                            ✨ Draft Personalized Pitch Campaign
                          </button>
                          
                          {candidates.some(c => c.email === cand.email && cand.email !== "N/A") ? (
                            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-3 py-2 rounded-lg">
                              ✅ Sourced & Registered
                            </span>
                          ) : (
                            <button 
                              onClick={() => importToTalentHub(cand)}
                              className="bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 font-bold text-xs px-4 py-2 rounded-lg transition-colors"
                            >
                              📥 Import candidate Profile
                            </button>
                          )}
                        </div>
                      </div>

                      {outreachDrafts[cand.username] && (
                        <div className="bg-slate-50 border border-slate-100 rounded-lg p-4 space-y-2">
                          <span className="text-xs font-bold text-slate-500">Draft outreach Campaign:</span>
                          <textarea 
                            rows={6}
                            readOnly
                            value={outreachDrafts[cand.username]}
                            className="w-full border-0 bg-transparent text-sm text-slate-700 outline-none resize-none font-mono"
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Sourcing Error State */}
              {sourcingError && sourcingResults.length === 0 && (
                <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-start space-x-3">
                  <AlertCircle className="h-5 w-5 text-rose-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-rose-800">{sourcingError}</p>
                    <p className="text-xs text-rose-600 mt-1">Make sure the backend is running and GitHub API is accessible. Try switching to Manual Sourcing mode.</p>
                  </div>
                </div>
              )}

              {/* Loading skeleton */}
              {loadingAction === 'sourcing' && (
                <div className="space-y-3">
                  {[1,2,3].map(i => (
                    <div key={i} className="bg-white border border-slate-200 rounded-xl p-5 animate-pulse">
                      <div className="flex space-x-4">
                        <div className="h-14 w-14 rounded-full bg-slate-200" />
                        <div className="flex-1 space-y-2">
                          <div className="h-4 bg-slate-200 rounded w-1/3" />
                          <div className="h-3 bg-slate-100 rounded w-1/2" />
                          <div className="h-3 bg-slate-100 rounded w-2/3" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
          </div>

          {/* TAB: INTERVIEW HUB */}
          <div className={activeTab === 'interview' ? 'space-y-6' : 'hidden'}>
            <div>
              <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Interview Hub</h2>
              <p className="text-slate-500 text-sm mt-0.5">End-to-end recruitment pipeline — invite, schedule, evaluate, and decide.</p>
            </div>

            {/* Sub-tabs */}
            <div className="flex border-b border-slate-200 gap-6">
              {(['pipeline', 'schedule', 'results', 'scorecard'] as const).map(t => {
                const labels: Record<string,string> = { pipeline: '🔄 Pipeline Board', schedule: '📅 Schedule Interview', results: '📊 Post-Interview Results', scorecard: '📋 Scorecard Generator' };
                return (
                  <button key={t} onClick={() => setInterviewTab(t)}
                    className={`pb-3 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${interviewTab === t ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
                  >{labels[t]}</button>
                );
              })}
            </div>

            {/* PIPELINE BOARD */}
            {interviewTab === 'pipeline' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-slate-800">Full Recruitment Pipeline</h3>
                    <p className="text-xs text-slate-400">Track every candidate from Sourced to Hired. Click a card to open their profile.</p>
                  </div>
                  <button onClick={fetchInterviews} className="flex items-center text-xs font-semibold text-slate-500 hover:text-slate-800">
                    <RefreshCw className="h-3.5 w-3.5 mr-1" /> Refresh
                  </button>
                </div>

                {/* Kanban Columns */}
                <div className="grid grid-cols-5 gap-3">
                  {(['Sourced', 'Screening', 'Interview', 'Offer', 'Hired'] as const).map(stage => {
                    const bgMap: Record<string,string> = { Sourced:'bg-slate-50 border-slate-300', Screening:'bg-blue-50 border-blue-300', Interview:'bg-amber-50 border-amber-300', Offer:'bg-purple-50 border-purple-300', Hired:'bg-emerald-50 border-emerald-300' };
                    const hdrMap: Record<string,string> = { Sourced:'bg-slate-200 text-slate-700', Screening:'bg-blue-200 text-blue-800', Interview:'bg-amber-200 text-amber-800', Offer:'bg-purple-200 text-purple-800', Hired:'bg-emerald-200 text-emerald-800' };
                    const stageItems = interviews.filter(i => {
                      if (stage === 'Sourced') return !i.status || i.status === 'Sourced';
                      if (stage === 'Screening') return i.status === 'Scheduled';
                      if (stage === 'Interview') return i.status === 'Completed' && !i.result;
                      if (stage === 'Offer') return i.result === 'Passed';
                      if (stage === 'Hired') return i.result === 'Offer Extended';
                      return false;
                    });
                    return (
                      <div key={stage} className={`rounded-xl border-2 border-dashed ${bgMap[stage]} min-h-[260px] flex flex-col`}>
                        <div className={`px-3 py-2.5 rounded-t-lg ${hdrMap[stage]} flex items-center justify-between`}>
                          <span className="text-xs font-extrabold uppercase tracking-wider">{stage}</span>
                          <span className="text-xs font-bold opacity-70">{stageItems.length}</span>
                        </div>
                        <div className="flex-1 p-2 space-y-2 overflow-y-auto">
                          {stageItems.map((item, i) => {
                            const cand = candidates.find(c => c.full_name === item.candidate_name);
                            const resultColor = item.result === 'Passed' ? 'text-emerald-600' : item.result === 'Failed' ? 'text-rose-600' : 'text-amber-600';
                            return (
                              <div key={i} className="bg-white border border-slate-200 rounded-lg p-2.5 shadow-sm hover:shadow-md transition-shadow cursor-pointer relative group"
                                onClick={() => { if (cand) { setSelectedInterviewCand(cand); setInterviewTab('schedule'); } }}
                              >
                                <button 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    doCancelInterview(item.candidate_name, item.role);
                                  }}
                                  className="absolute top-2 right-2 text-slate-300 hover:text-rose-600 font-extrabold text-xs opacity-0 group-hover:opacity-100 transition-opacity bg-slate-50 hover:bg-rose-50 rounded h-5 w-5 flex items-center justify-center border border-slate-100"
                                  title="Cancel Interview"
                                >
                                  ✕
                                </button>
                                <p className="font-bold text-slate-900 text-xs pr-4">{item.candidate_name}</p>
                                <p className="text-xs text-slate-400 truncate">{item.role}</p>
                                {item.date && <p className="text-xs text-slate-400 mt-1"><Clock className="inline h-3 w-3 mr-1" />{item.date} {item.time}</p>}
                                {item.result && <p className={`text-xs font-bold mt-1 ${resultColor}`}>{item.result}</p>}
                                {item.score && <p className="text-xs text-slate-400">Score: {item.score}/5</p>}
                              </div>
                            );
                          })}
                          {stageItems.length === 0 && <div className="text-xs text-slate-300 text-center py-6">No candidates</div>}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* All Interviews Table */}
                {interviews.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                    <div className="px-5 py-3 border-b border-slate-200 bg-slate-50">
                      <h4 className="font-bold text-slate-800 text-sm">All Interview Records</h4>
                    </div>
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          <th className="py-3 px-5">Candidate</th>
                          <th className="py-3 px-5">Role</th>
                          <th className="py-3 px-5">Date / Time</th>
                          <th className="py-3 px-5">Platform</th>
                          <th className="py-3 px-5">Status</th>
                          <th className="py-3 px-5">Result</th>
                          <th className="py-3 px-5">Score</th>
                          <th className="py-3 px-5">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-sm">
                        {interviews.map((item, idx) => {
                          const resultBg: Record<string,string> = { Passed: 'bg-emerald-50 text-emerald-700 border-emerald-100', Failed: 'bg-rose-50 text-rose-700 border-rose-100', Hold: 'bg-amber-50 text-amber-700 border-amber-100', 'Offer Extended': 'bg-purple-50 text-purple-700 border-purple-100' };
                          return (
                            <tr key={idx} className="hover:bg-slate-50 transition-colors">
                              <td className="py-3 px-5 font-bold text-slate-900">
                                <button onClick={() => { const c = candidates.find(c2 => c2.full_name === item.candidate_name); if (c) openDeepDive(c); }} className="hover:text-indigo-600 hover:underline text-left">{item.candidate_name}</button>
                              </td>
                              <td className="py-3 px-5 text-slate-600">{item.role}</td>
                              <td className="py-3 px-5 text-slate-500 text-xs">{item.date && `${item.date} ${item.time}`}</td>
                              <td className="py-3 px-5 text-slate-500 text-xs">{item.platform}</td>
                              <td className="py-3 px-5">
                                <span className={`text-xs font-bold px-2 py-1 rounded-full ${item.status === 'Completed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-blue-50 text-blue-700 border border-blue-100'}`}>{item.status || 'Pending'}</span>
                              </td>
                              <td className="py-3 px-5">
                                {item.result && <span className={`text-xs font-bold border px-2 py-1 rounded-full ${resultBg[item.result] || 'bg-slate-50 text-slate-600'}`}>{item.result}</span>}
                              </td>
                              <td className="py-3 px-5 font-bold text-slate-700">{item.score ? `${item.score}/5` : '—'}</td>
                              <td className="py-3 px-5 flex items-center space-x-3">
                                <button
                                  onClick={() => { setResultForm({ candidate_name: item.candidate_name, role: item.role, result: 'Passed', score: '', notes: '' }); setInterviewTab('results'); }}
                                  className="text-xs text-indigo-600 hover:underline font-semibold"
                                >Update Result</button>
                                <button
                                  onClick={() => doCancelInterview(item.candidate_name, item.role)}
                                  className="text-xs text-rose-650 hover:text-rose-800 hover:underline font-semibold"
                                >Cancel</button>
                                {item.calendar_link && (
                                  <a 
                                    href={item.calendar_link} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-xs text-emerald-600 hover:underline font-semibold flex items-center"
                                  >
                                    📅 Add to Cal
                                  </a>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* SCHEDULE INTERVIEW */}
            {interviewTab === 'schedule' && (
              <div className="grid grid-cols-2 gap-6">
                {/* Candidate Selector */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                  <h3 className="font-bold text-slate-800 flex items-center">
                    <Users className="h-4 w-4 mr-2 text-indigo-500" />
                    1. Select Candidate
                  </h3>
                  <div className="max-h-64 overflow-y-auto space-y-2">
                    {candidates.map(cand => (
                      <div key={cand.full_name}
                        onClick={() => { setSelectedInterviewCand(cand); setScheduleForm(f => ({...f, role: cand.working_role})); }}
                        className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all border ${
                          selectedInterviewCand?.full_name === cand.full_name
                            ? 'border-indigo-300 bg-indigo-50'
                            : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        <div className="h-8 w-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0">{cand.full_name[0]}</div>
                        <div className="min-w-0">
                          <p className="font-bold text-slate-900 text-sm truncate">{cand.full_name}</p>
                          <p className="text-xs text-slate-400 truncate">{cand.working_role} · {cand.total_experience_years}y</p>
                        </div>
                        <span className="shrink-0 ml-auto bg-indigo-50 text-indigo-700 text-xs font-bold px-2 py-0.5 rounded-full">{cand.resume_score}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Schedule Form */}
                <div className="space-y-4">
                  <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                    <h3 className="font-bold text-slate-800 flex items-center">
                      <Calendar className="h-4 w-4 mr-2 text-indigo-500" />
                      2. Set Interview Details
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Date</label>
                        <input type="date" value={scheduleForm.date} onChange={e => setScheduleForm(f => ({...f, date: e.target.value}))}
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Time</label>
                        <input type="time" value={scheduleForm.time} onChange={e => setScheduleForm(f => ({...f, time: e.target.value}))}
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Platform</label>
                        <select value={scheduleForm.platform} onChange={e => setScheduleForm(f => ({...f, platform: e.target.value}))}
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none">
                          {['Google Meet', 'Zoom', 'Microsoft Teams', 'In-Person', 'Phone Call'].map(p => <option key={p}>{p}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Interviewer Name</label>
                        <input type="text" placeholder="Interviewer name" value={scheduleForm.interviewer} onChange={e => setScheduleForm(f => ({...f, interviewer: e.target.value}))}
                          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Role</label>
                      <input type="text" value={scheduleForm.role} onChange={e => setScheduleForm(f => ({...f, role: e.target.value}))}
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" />
                    </div>
                    <button onClick={doScheduleInterview} disabled={!selectedInterviewCand || !scheduleForm.date}
                      className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold text-sm py-2.5 rounded-lg transition-colors flex items-center justify-center">
                      {loadingAction === 'schedule' && <RefreshCw className="animate-spin h-4 w-4 mr-2" />}
                      <Calendar className="h-4 w-4 mr-2" /> Schedule Interview
                    </button>
                  </div>

                  {/* Generate Invitation Email */}
                  {selectedInterviewCand && (
                    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                      <h3 className="font-bold text-slate-800 flex items-center">
                        <Mail className="h-4 w-4 mr-2 text-indigo-500" />
                        3. Generate Invitation Email
                      </h3>
                      <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3 flex items-center space-x-2">
                        <div className="h-8 w-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs">{selectedInterviewCand.full_name[0]}</div>
                        <div>
                          <p className="font-bold text-indigo-900 text-sm">{selectedInterviewCand.full_name}</p>
                          <p className="text-xs text-indigo-500">{selectedInterviewCand.email}</p>
                        </div>
                      </div>
                      <button onClick={() => generateInvite(selectedInterviewCand, scheduleForm.role || selectedInterviewCand.working_role)}
                        className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm py-2.5 rounded-lg transition-colors flex items-center justify-center">
                        {loadingAction === 'invite' && <RefreshCw className="animate-spin h-4 w-4 mr-2" />}
                        <Mail className="h-4 w-4 mr-2" /> Generate Invite Email
                      </button>
                      {interviewInvite && (
                        <div className="space-y-4 pt-3 border-t border-slate-100">
                          <div>
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Email Subject</label>
                            <input 
                              type="text" 
                              value={emailSubject} 
                              onChange={e => setEmailSubject(e.target.value)}
                              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" 
                            />
                          </div>

                          <div>
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Interviewer CC (comma separated emails)</label>
                            <input 
                              type="text" 
                              placeholder="e.g. lead@hriq.com, manager@hriq.com" 
                              value={emailCc} 
                              onChange={e => setEmailCc(e.target.value)}
                              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" 
                            />
                          </div>

                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-500 uppercase">Invitation Email Draft</span>
                              <button onClick={() => navigator.clipboard?.writeText(interviewInvite)} className="text-xs text-indigo-600 font-semibold border border-indigo-200 px-2 py-1 rounded hover:bg-indigo-50">📋 Copy</button>
                            </div>
                            <textarea 
                              rows={8}
                              value={interviewInvite}
                              onChange={e => setInterviewInvite(e.target.value)}
                              className="w-full border border-slate-200 rounded-lg p-3 text-xs text-slate-700 font-mono whitespace-pre-wrap leading-relaxed outline-none focus:border-indigo-500"
                            />
                          </div>

                          {emailStatusMsg && (
                            <p className="text-xs font-bold p-2.5 rounded bg-slate-100 border border-slate-200">{emailStatusMsg}</p>
                          )}

                          <button 
                            onClick={sendInviteEmail}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm py-2.5 rounded-lg transition-colors flex items-center justify-center"
                          >
                            {loadingAction === 'send_email' && <RefreshCw className="animate-spin h-4 w-4 mr-2" />}
                            🚀 Push & Send Interview Invite
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* RESULTS TAB */}
            {interviewTab === 'results' && (
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                  <h3 className="font-bold text-slate-800 flex items-center">
                    <CheckCircle className="h-4 w-4 mr-2 text-emerald-500" />
                    Post-Interview Result Entry
                  </h3>
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Candidate Name</label>
                    <select value={resultForm.candidate_name} onChange={e => setResultForm(f => ({...f, candidate_name: e.target.value}))}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none">
                      <option value="">Select Candidate...</option>
                      {interviews.map(i => <option key={i.candidate_name+i.role} value={i.candidate_name}>{i.candidate_name}</option>)}
                      {candidates.map(c => <option key={c.full_name} value={c.full_name}>{c.full_name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Role Applied For</label>
                    <input type="text" value={resultForm.role} onChange={e => setResultForm(f => ({...f, role: e.target.value}))}
                      placeholder="e.g. Senior Python Developer"
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Outcome Decision</label>
                    <div className="grid grid-cols-2 gap-2">
                      {(['Passed', 'Failed', 'Hold', 'Offer Extended'] as const).map(r => (
                        <button key={r} onClick={() => setResultForm(f => ({...f, result: r}))}
                          className={`py-2.5 rounded-lg text-sm font-bold border transition-all ${
                            resultForm.result === r
                              ? r === 'Passed' || r === 'Offer Extended' ? 'bg-emerald-600 text-white border-emerald-600'
                              : r === 'Failed' ? 'bg-rose-600 text-white border-rose-600'
                              : 'bg-amber-500 text-white border-amber-500'
                              : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                          }`}>{r}</button>
                      ))}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Score (out of 5)</label>
                      <input type="number" min={1} max={5} step={0.1} value={resultForm.score} onChange={e => setResultForm(f => ({...f, score: e.target.value}))}
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Notes</label>
                      <input type="text" value={resultForm.notes} onChange={e => setResultForm(f => ({...f, notes: e.target.value}))}
                        placeholder="Brief notes..."
                        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none" />
                    </div>
                  </div>
                  <button onClick={doSaveResult} disabled={!resultForm.candidate_name}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white font-bold text-sm py-2.5 rounded-lg transition-colors flex items-center justify-center">
                    {loadingAction === 'result' && <RefreshCw className="animate-spin h-4 w-4 mr-2" />}
                    Save Result
                  </button>
                </div>

                {/* Results Summary */}
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'Total Scheduled', value: interviews.filter(i => i.status === 'Scheduled').length, color: 'bg-blue-50 text-blue-700 border-blue-100' },
                      { label: 'Completed', value: interviews.filter(i => i.status === 'Completed').length, color: 'bg-slate-50 text-slate-700 border-slate-200' },
                      { label: 'Passed / Offers', value: interviews.filter(i => i.result === 'Passed' || i.result === 'Offer Extended').length, color: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
                      { label: 'Failed / Declined', value: interviews.filter(i => i.result === 'Failed').length, color: 'bg-rose-50 text-rose-700 border-rose-100' },
                    ].map(stat => (
                      <div key={stat.label} className={`border ${stat.color} rounded-xl p-4 text-center`}>
                        <p className="text-3xl font-extrabold">{stat.value}</p>
                        <p className="text-xs font-semibold mt-1">{stat.label}</p>
                      </div>
                    ))}
                  </div>
                  <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2">
                    <h4 className="font-bold text-slate-700 text-sm">Recent Results</h4>
                    {interviews.filter(i => i.result).slice(0, 8).map((item, idx) => {
                      const rColor: Record<string,string> = { Passed: 'text-emerald-600', Failed: 'text-rose-600', Hold: 'text-amber-600', 'Offer Extended': 'text-purple-600' };
                      return (
                        <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                          <div>
                            <p className="font-semibold text-slate-800 text-sm">{item.candidate_name}</p>
                            <p className="text-xs text-slate-400">{item.role}</p>
                          </div>
                          <div className="text-right">
                            <p className={`text-sm font-bold ${rColor[item.result] || 'text-slate-500'}`}>{item.result}</p>
                            {item.score && <p className="text-xs text-slate-400">{item.score}/5</p>}
                          </div>
                        </div>
                      );
                    })}
                    {interviews.filter(i => i.result).length === 0 && <p className="text-xs text-slate-400 text-center py-4">No results recorded yet.</p>}
                  </div>
                </div>
              </div>
            )}

            {/* SCORECARD GENERATOR */}
            {interviewTab === 'scorecard' && (
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
                  <h3 className="font-bold text-slate-800 flex items-center">
                    <ClipboardList className="h-4 w-4 mr-2 text-indigo-500" />
                    AI Scorecard Generator
                  </h3>
                  <p className="text-xs text-slate-400">Generates a structured 6-dimension scorecard tailored to the candidate and role.</p>

                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Select Candidate</label>
                    <div className="max-h-48 overflow-y-auto space-y-1.5">
                      {candidates.map(cand => (
                        <div key={cand.full_name}
                          onClick={() => setSelectedInterviewCand(cand)}
                          className={`flex items-center space-x-2 p-2.5 rounded-lg cursor-pointer border transition-all ${
                            selectedInterviewCand?.full_name === cand.full_name ? 'border-indigo-300 bg-indigo-50' : 'border-transparent hover:border-slate-200 hover:bg-slate-50'
                          }`}
                        >
                          <div className="h-7 w-7 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0">{cand.full_name[0]}</div>
                          <div className="min-w-0">
                            <p className="font-bold text-slate-900 text-xs truncate">{cand.full_name}</p>
                            <p className="text-xs text-slate-400 truncate">{cand.working_role}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Target Role</label>
                    <input type="text" value={scorecardRole} onChange={e => setScorecardRole(e.target.value)}
                      placeholder={selectedInterviewCand?.working_role || 'e.g. Senior Python Developer'}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" />
                  </div>
                  <button
                    onClick={() => { if (selectedInterviewCand) generateScorecardFn(selectedInterviewCand, scorecardRole || selectedInterviewCand.working_role); }}
                    disabled={!selectedInterviewCand}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white font-bold text-sm py-2.5 rounded-lg transition-colors flex items-center justify-center">
                    {loadingAction === 'scorecard' && <RefreshCw className="animate-spin h-4 w-4 mr-2" />}
                    <Star className="h-4 w-4 mr-2" /> Generate AI Scorecard
                  </button>
                </div>

                {/* Scorecard Output */}
                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                  <div className="px-5 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                    <h4 className="font-bold text-slate-800 text-sm">Interview Scorecard</h4>
                    {scorecard && (
                      <button onClick={() => navigator.clipboard?.writeText(scorecard)} className="text-xs text-indigo-600 border border-indigo-200 px-2 py-1 rounded hover:bg-indigo-50 font-semibold">📋 Copy</button>
                    )}
                  </div>
                  {scorecard ? (
                    <pre className="p-5 text-xs text-slate-700 font-mono whitespace-pre-wrap leading-relaxed overflow-y-auto max-h-[500px]">{scorecard}</pre>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-slate-300">
                      <ClipboardList className="h-12 w-12 mb-3" />
                      <p className="text-sm font-semibold text-slate-400">Select a candidate and generate scorecard</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* TAB: BULK ACTIONS */}
          <div className={activeTab === 'bulk' ? 'space-y-6' : 'hidden'}>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Bulk Action Hub</h2>
                <p className="text-slate-500 text-sm mt-0.5">Automate reports and pitches for selected candidates.</p>
              </div>

              {selectedCandidates.length === 0 ? (
                <div className="h-64 border border-dashed border-slate-200 rounded-xl bg-white flex flex-col items-center justify-center text-slate-400 space-y-2">
                  <AlertCircle className="h-8 w-8 text-slate-300" />
                  <p className="text-sm font-semibold text-slate-700">No candidates selected for bulk actions.</p>
                  <p className="text-xs">Go to the <strong>Talent Hub</strong> and check profiles from the matrix table first.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 text-sm text-indigo-700 flex items-center justify-between">
                    <span>Selected Profile Cohort: <strong>{selectedCandidates.length} profiles</strong> checkmarked.</span>
                    <button onClick={() => setSelectedCandidates([])} className="font-bold text-indigo-900 hover:underline">Clear Selection</button>
                  </div>

                   {/* Bulk Tabs */}
                  <div className="flex border-b border-slate-200 gap-6 overflow-x-auto">
                    <button
                      onClick={() => setBulkTab('outreach')}
                      className={`pb-3 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${bulkTab === 'outreach' ? 'border-indigo-600 text-indigo-600 font-bold' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
                    >
                      📧 Bulk Outreach
                    </button>
                    <button
                      onClick={() => setBulkTab('comparison')}
                      className={`pb-3 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${bulkTab === 'comparison' ? 'border-indigo-600 text-indigo-600 font-bold' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
                    >
                      ⚔️ Battlecard Compare
                    </button>
                    <button
                      onClick={() => setBulkTab('pipeline')}
                      className={`pb-3 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${bulkTab === 'pipeline' ? 'border-indigo-600 text-indigo-600 font-bold' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
                    >
                      🗂️ Pipeline Kanban
                    </button>
                    <button
                      onClick={() => setBulkTab('radar')}
                      className={`pb-3 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${bulkTab === 'radar' ? 'border-indigo-600 text-indigo-600 font-bold' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
                    >
                      🎯 Talent Radar
                    </button>
                    <button
                      onClick={() => setBulkTab('boolean')}
                      className={`pb-3 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${bulkTab === 'boolean' ? 'border-indigo-600 text-indigo-600 font-bold' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
                    >
                      🔍 Boolean Builder
                    </button>
                  </div>

                  {/* Bulk action view panel */}
                  <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                    {bulkTab === 'outreach' && (
                      <div className="space-y-4">
                        <div>
                          <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Job Description context:</label>
                          <textarea 
                            rows={4}
                            value={bulkJd}
                            onChange={(e) => setBulkJd(e.target.value)}
                            placeholder="Paste JD context to draft pitches..."
                            className="w-full border border-slate-200 rounded-lg p-3 text-sm outline-none focus:border-indigo-500"
                          />
                        </div>
                        <button 
                          onClick={runBulkActions}
                          disabled={!bulkJd.trim()}
                          className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-100 disabled:text-slate-400 text-white font-bold text-xs px-5 py-2.5 rounded-lg transition-colors flex items-center"
                        >
                          {loadingAction === 'bulk' && <RefreshCw className="animate-spin h-3.5 w-3.5 mr-1.5" />}
                          ⚡ Draft email outreach templates for selection
                        </button>
                        {Object.keys(bulkOutreachEmails).length > 0 && (
                          <div className="space-y-3 border-t border-slate-100 pt-4">
                            {Object.keys(bulkOutreachEmails).map(name => {
                              const cand = candidates.find(c => c.full_name === name);
                              return (
                                <div key={name} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                                  <div className="flex items-center justify-between px-4 py-3 bg-indigo-50 border-b border-indigo-100">
                                    <div className="flex items-center space-x-2">
                                      <div className="h-7 w-7 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs">{name[0]}</div>
                                      <div>
                                        <span className="font-bold text-indigo-900 text-sm">{name}</span>
                                        {cand && <span className="text-indigo-500 text-xs ml-2">{cand.working_role}</span>}
                                      </div>
                                    </div>
                                    <button
                                      onClick={() => navigator.clipboard?.writeText(bulkOutreachEmails[name])}
                                      className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold border border-indigo-200 px-2 py-1 rounded"
                                    >
                                      📋 Copy
                                    </button>
                                  </div>
                                  <pre className="p-4 text-xs text-slate-700 font-mono whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto bg-slate-50">{bulkOutreachEmails[name]}</pre>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}

                    {bulkTab === 'comparison' && (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-400">Side-by-side structured battlecard analysis for {selectedCandidates.length} selected candidates.</span>
                          <button 
                            onClick={runBulkActions}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-5 py-2.5 rounded-lg transition-colors flex items-center"
                          >
                            {loadingAction === 'bulk' && <RefreshCw className="animate-spin h-3.5 w-3.5 mr-1.5" />}
                            ⚔️ Generate Battlecard Analysis
                          </button>
                        </div>

                        {/* Visual per-candidate structured cards */}
                        <div className="grid grid-cols-1 gap-4">
                          {candidates
                            .filter(c => selectedCandidates.includes(c.full_name))
                            .map((cand, idx) => {
                              const scoreColor = cand.resume_score >= 80 ? 'emerald' : cand.resume_score >= 60 ? 'amber' : 'rose';
                              const expTier = cand.total_experience_years >= 6 ? 'Senior' : cand.total_experience_years >= 3 ? 'Mid' : 'Junior';
                              return (
                                <div key={idx} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                                  <div className="flex items-center justify-between px-5 py-3 bg-gradient-to-r from-slate-50 to-indigo-50 border-b border-slate-200">
                                    <div className="flex items-center space-x-3">
                                      <div className="h-10 w-10 rounded-full bg-indigo-600 text-white flex items-center justify-center font-extrabold text-sm">{cand.full_name[0]}</div>
                                      <div>
                                        <h4 className="font-extrabold text-slate-900">{cand.full_name}</h4>
                                        <p className="text-xs text-slate-400 font-medium">{cand.working_role} · {expTier} · {cand.industry_domain}</p>
                                      </div>
                                    </div>
                                    <div className="flex items-center space-x-3">
                                      <span className={`bg-${scoreColor}-50 text-${scoreColor}-700 border border-${scoreColor}-200 text-sm font-extrabold px-3 py-1.5 rounded-full`}>
                                        Score: {cand.resume_score}/100
                                      </span>
                                      <span className="bg-slate-100 text-slate-700 text-xs font-bold px-2.5 py-1.5 rounded-full">
                                        {cand.total_experience_years}y Exp
                                      </span>
                                      <button onClick={() => openDeepDive(cand)} className="text-indigo-600 text-xs font-bold hover:underline">View Profile →</button>
                                    </div>
                                  </div>
                                  <div className="p-5 grid grid-cols-3 gap-4">
                                    <div>
                                      <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">Key Skills</span>
                                      <div className="flex flex-wrap gap-1">
                                        {cand.technologies.slice(0, 8).map(t => (
                                          <span key={t} className="bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold px-2 py-0.5 rounded-full">{t}</span>
                                        ))}
                                        {cand.technologies.length > 8 && <span className="text-xs text-slate-400">+{cand.technologies.length - 8} more</span>}
                                      </div>
                                    </div>
                                    <div>
                                      <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">AI Elevator Pitch</span>
                                      <p className="text-xs text-slate-600 leading-relaxed">{cand.elevator_pitch?.substring(0, 160)}...</p>
                                    </div>
                                    <div>
                                      <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">Contact & Tag</span>
                                      <p className="text-xs text-slate-600">📧 {cand.email}</p>
                                      <p className="text-xs text-slate-600">📞 {cand.phone}</p>
                                      <span className="mt-1 inline-block bg-slate-100 text-slate-600 text-xs font-semibold px-2 py-0.5 rounded">{cand.tag}</span>
                                    </div>
                                  </div>
                                  {bulkComparison && (
                                    <div className="border-t border-slate-100 px-5 pb-4 pt-3 bg-slate-50">
                                      <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-2">AI Battlecard Verdict</span>
                                      <div className="text-xs text-slate-700 leading-relaxed">{renderMarkdown(bulkComparison)}</div>
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    )}

                    {bulkTab === 'pipeline' && (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-bold text-slate-800 text-sm">🗂️ Recruitment Pipeline — Drag & Drop Kanban</h3>
                            <p className="text-xs text-slate-400 mt-0.5">Drag candidates between stages. Auto-saved to browser storage.</p>
                          </div>
                          <button
                            onClick={() => {
                              const added: Record<string, string[]> = { ...pipelineStages };
                              selectedCandidates.forEach(name => {
                                const alreadyIn = Object.values(added).flat().includes(name);
                                if (!alreadyIn) added['Sourced'] = [...(added['Sourced'] || []), name];
                              });
                              setPipelineStages(added);
                            }}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors"
                          >
                            ➕ Add Selected to Pipeline
                          </button>
                        </div>
                        <div className="grid grid-cols-5 gap-3">
                          {['Sourced', 'Screening', 'Interview', 'Offer', 'Hired'].map(stage => {
                            const stageColors: Record<string, string> = {
                              'Sourced': 'bg-slate-50 border-slate-200',
                              'Screening': 'bg-blue-50 border-blue-200',
                              'Interview': 'bg-amber-50 border-amber-200',
                              'Offer': 'bg-purple-50 border-purple-200',
                              'Hired': 'bg-emerald-50 border-emerald-200',
                            };
                            const headerColors: Record<string, string> = {
                              'Sourced': 'bg-slate-200 text-slate-700',
                              'Screening': 'bg-blue-200 text-blue-800',
                              'Interview': 'bg-amber-200 text-amber-800',
                              'Offer': 'bg-purple-200 text-purple-800',
                              'Hired': 'bg-emerald-200 text-emerald-800',
                            };
                            return (
                              <div
                                key={stage}
                                className={`rounded-xl border-2 border-dashed ${stageColors[stage]} min-h-[280px] flex flex-col`}
                                onDragOver={(e) => e.preventDefault()}
                                onDrop={() => {
                                  if (!draggedCandidate) return;
                                  const updated = { ...pipelineStages };
                                  Object.keys(updated).forEach(s => {
                                    updated[s] = updated[s].filter(n => n !== draggedCandidate);
                                  });
                                  updated[stage] = [...(updated[stage] || []), draggedCandidate];
                                  setPipelineStages(updated);
                                  setDraggedCandidate(null);
                                }}
                              >
                                <div className={`px-3 py-2 rounded-t-lg ${headerColors[stage]} flex items-center justify-between`}>
                                  <span className="text-xs font-extrabold uppercase tracking-wider">{stage}</span>
                                  <span className="text-xs font-bold opacity-70">{(pipelineStages[stage] || []).length}</span>
                                </div>
                                <div className="flex-1 p-2 space-y-2 overflow-y-auto">
                                  {(pipelineStages[stage] || []).map(name => {
                                    const cand = candidates.find(c => c.full_name === name);
                                    return (
                                      <div
                                        key={name}
                                        draggable
                                        onDragStart={() => setDraggedCandidate(name)}
                                        className="bg-white border border-slate-200 rounded-lg p-2.5 shadow-sm cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
                                      >
                                        <p className="font-bold text-slate-900 text-xs">{name}</p>
                                        {cand && <p className="text-xs text-slate-400 truncate">{cand.working_role}</p>}
                                        {cand && (
                                          <div className="flex items-center justify-between mt-1.5">
                                            <span className="bg-indigo-50 text-indigo-700 text-xs font-bold px-1.5 py-0.5 rounded">{cand.resume_score}</span>
                                            <button onClick={() => openDeepDive(cand!)} className="text-indigo-500 text-xs hover:underline">View</button>
                                          </div>
                                        )}
                                      </div>
                                    );
                                  })}
                                  {(pipelineStages[stage] || []).length === 0 && (
                                    <div className="flex-1 flex items-center justify-center text-xs text-slate-300 py-8 text-center">Drop candidates here</div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {bulkTab === 'radar' && (
                      <div className="space-y-4">
                        <div>
                          <h3 className="font-bold text-slate-800 text-sm">🎯 Talent Radar — Skill Gap Heatmap</h3>
                          <p className="text-xs text-slate-400 mt-0.5">Visualizes each candidate's skill coverage across critical tech domains.</p>
                        </div>
                        {(() => {
                          const selected = candidates.filter(c => selectedCandidates.includes(c.full_name));
                          const allSkills = Array.from(new Set(selected.flatMap(c => c.technologies))).slice(0, 15);
                          if (selected.length === 0) return <div className="text-sm text-slate-400 text-center py-8">Select candidates in Talent Hub first.</div>;
                          return (
                            <div className="overflow-x-auto">
                              <table className="w-full text-left border-collapse">
                                <thead>
                                  <tr className="border-b border-slate-200">
                                    <th className="py-2 px-3 text-xs font-bold text-slate-400 uppercase tracking-wider min-w-[140px]">Candidate</th>
                                    <th className="py-2 px-3 text-xs font-bold text-slate-400 uppercase tracking-wider">Score</th>
                                    {allSkills.map(skill => (
                                      <th key={skill} className="py-2 px-2 text-xs font-bold text-slate-400 uppercase tracking-wider text-center whitespace-nowrap">{skill}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                  {selected.map((cand, idx) => (
                                    <tr key={idx} className="hover:bg-slate-50">
                                      <td className="py-2.5 px-3">
                                        <button onClick={() => openDeepDive(cand)} className="font-bold text-slate-900 text-xs hover:text-indigo-600 hover:underline text-left">{cand.full_name}</button>
                                        <p className="text-xs text-slate-400">{cand.working_role}</p>
                                      </td>
                                      <td className="py-2.5 px-3">
                                        <span className="bg-indigo-50 text-indigo-700 text-xs font-extrabold px-2 py-1 rounded-full">{cand.resume_score}</span>
                                      </td>
                                      {allSkills.map(skill => {
                                        const has = cand.technologies.some(t => t.toLowerCase().includes(skill.toLowerCase()) || skill.toLowerCase().includes(t.toLowerCase()));
                                        return (
                                          <td key={skill} className="py-2.5 px-2 text-center">
                                            <div className={`mx-auto h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold ${
                                              has ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-50 text-rose-300'
                                            }`}>
                                              {has ? '✓' : '×'}
                                            </div>
                                          </td>
                                        );
                                      })}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          );
                        })()}
                      </div>
                    )}

                    {bulkTab === 'boolean' && (
                      <div className="space-y-4">
                        <div>
                          <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Paste Job Description:</label>
                          <textarea 
                            rows={4}
                            value={bulkJd}
                            onChange={(e) => setBulkJd(e.target.value)}
                            placeholder="Paste JD requirements to build optimized Boolean queries..."
                            className="w-full border border-slate-200 rounded-lg p-3 text-sm outline-none focus:border-indigo-500"
                          />
                        </div>
                        <button 
                          onClick={runBulkActions}
                          disabled={!bulkJd.trim()}
                          className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-100 disabled:text-slate-400 text-white font-bold text-xs px-5 py-2.5 rounded-lg transition-colors flex items-center"
                        >
                          {loadingAction === 'bulk' && <RefreshCw className="animate-spin h-3.5 w-3.5 mr-1.5" />}
                          ⚡ Compile Boolean sourcing blueprints
                        </button>
                        {booleanSourcing && (
                          <div className="bg-indigo-950 text-indigo-100 rounded-xl p-5 font-mono text-sm leading-relaxed whitespace-pre-wrap border border-indigo-800">
                            {booleanSourcing}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
          </div>

          {/* TAB: LOGS */}
          <div className={activeTab === 'logs' ? 'space-y-6 max-w-4xl' : 'hidden'}>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Real-time Parsing Tracker</h2>
                <p className="text-slate-500 text-sm mt-0.5">Diagnostic audit trace of files parsed in the current lifecycle.</p>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-xs font-semibold text-slate-400 bg-slate-50/50 uppercase tracking-wider">
                      <th className="py-3 px-6">Timestamp</th>
                      <th className="py-3 px-6">File Name</th>
                      <th className="py-3 px-6">Status</th>
                      <th className="py-3 px-6">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                    {parsingLogs.length > 0 ? (
                      parsingLogs.map((log, idx) => (
                        <tr key={idx}>
                          <td className="py-3 px-6 font-mono text-xs">{log.timestamp}</td>
                          <td className="py-3 px-6 font-semibold">{log.file}</td>
                          <td className="py-3 px-6">
                            {log.status === "Success" ? (
                              <span className="bg-emerald-50 text-emerald-700 text-xs font-semibold px-2 py-0.5 rounded border border-emerald-100">Success</span>
                            ) : (
                              <span className="bg-rose-50 text-rose-700 text-xs font-semibold px-2 py-0.5 rounded border border-rose-100">Failed</span>
                            )}
                          </td>
                          <td className="py-3 px-6 text-xs text-slate-500">{log.details}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="py-8 text-center text-slate-400 font-medium">No files scanned in the current session.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
          </div>

          {/* TAB: DIAGNOSTICS */}
          <div className={activeTab === 'status' ? 'space-y-6 max-w-4xl' : 'hidden'}>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">System diagnostics Check</h2>
                <p className="text-slate-500 text-sm mt-0.5">Audit connection schemas and AI server response layers.</p>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                  <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2">AI Server Interface</h3>
                  <div className="text-sm">
                    <span className="text-xs text-slate-400 font-bold block">Status Response:</span>
                    <span className="font-semibold block mt-0.5">{sysStatus.server?.status || "Loading..."}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-xs text-slate-400 font-bold block">Connectivity Logs:</span>
                    <p className="bg-slate-50 border border-slate-100 rounded p-2 text-xs text-slate-600 mt-1 leading-relaxed">{sysStatus.server?.message}</p>
                  </div>
                </div>

                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                  <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2">AI Inference Model</h3>
                  <div className="text-sm">
                    <span className="text-xs text-slate-400 font-bold block">Status Response:</span>
                    <span className="font-semibold block mt-0.5">{sysStatus.model?.status || "Loading..."}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-xs text-slate-400 font-bold block">Model Logs:</span>
                    <p className="bg-slate-50 border border-slate-100 rounded p-2 text-xs text-slate-600 mt-1 leading-relaxed">{sysStatus.model?.message}</p>
                  </div>
                </div>
              </div>
          </div>

          {/* TAB: SETTINGS */}
          <div className={activeTab === 'settings' ? 'space-y-6 max-w-2xl' : 'hidden'}>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Recruiter Profile & settings</h2>
                <p className="text-slate-500 text-sm mt-0.5">Customize your personal details, email signature, and SMTP integration.</p>
              </div>

              {/* Google Workspace Integration */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-800 flex items-center">
                  <Star className="h-5 w-5 mr-2 text-indigo-500" />
                  Google Workspace Automation (Gmail, Calendar, Tasks)
                </h3>
                
                {googleStatus.connected ? (
                  <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-emerald-800">✅ Google Workspace Connected!</p>
                      <p className="text-xs text-emerald-600 mt-0.5">Linked Account: <strong>{googleStatus.email}</strong></p>
                      <p className="text-xs text-slate-500 mt-2 font-medium">HRIQ will now schedule interviews to Google Calendar, set tasks in Google Tasks, and send invite emails via Gmail API automatically.</p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-slate-700">Google Automation is currently offline</p>
                      <p className="text-xs text-slate-400 mt-0.5">Connect your Google account to automate Calendar scheduling, Gmail invites, and Google Tasks reminders.</p>
                    </div>
                    <button
                      onClick={async () => {
                        try {
                          const redirectUri = window.location.origin + "/google-callback";
                          const res = await fetch(`${API_BASE}/api/google/auth-url?redirect_uri=${encodeURIComponent(redirectUri)}`);
                          const data = await res.json();
                          if (data.auth_url) {
                            window.location.href = data.auth_url;
                          }
                        } catch (e: any) {
                          alert("Failed to get Google login URL: " + e.message);
                        }
                      }}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors shrink-0 shadow-sm"
                    >
                      Connect Google Workspace
                    </button>
                  </div>
                )}
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Full Name</label>
                    <input 
                      type="text" 
                      value={settings.full_name || ""} 
                      onChange={e => setSettings({...settings, full_name: e.target.value})}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" 
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Email Address</label>
                    <input 
                      type="email" 
                      value={settings.email || ""} 
                      onChange={e => setSettings({...settings, email: e.target.value})}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" 
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Phone Number</label>
                    <input 
                      type="text" 
                      value={settings.phone || ""} 
                      onChange={e => setSettings({...settings, phone: e.target.value})}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" 
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Title / Working Role</label>
                    <input 
                      type="text" 
                      value={settings.role || ""} 
                      onChange={e => setSettings({...settings, role: e.target.value})}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" 
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Company Name</label>
                  <input 
                    type="text" 
                    value={settings.company || ""} 
                    onChange={e => setSettings({...settings, company: e.target.value})}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500" 
                  />
                </div>

                <div className="border-t border-slate-100 pt-4 mt-2">
                  <h3 className="text-sm font-bold text-slate-800 mb-3">SMTP Mail Server Integration</h3>
                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div className="col-span-2">
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">SMTP Server Address</label>
                      <input 
                        type="text" 
                        value={settings.smtp_server || ""} 
                        onChange={e => setSettings({...settings, smtp_server: e.target.value})}
                        className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-indigo-500" 
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">SMTP Port</label>
                      <input 
                        type="number" 
                        value={settings.smtp_port || 587} 
                        onChange={e => setSettings({...settings, smtp_port: parseInt(e.target.value)})}
                        className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-indigo-500" 
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">SMTP Username</label>
                      <input 
                        type="text" 
                        value={settings.smtp_username || ""} 
                        onChange={e => setSettings({...settings, smtp_username: e.target.value})}
                        className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-indigo-500" 
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">SMTP Password</label>
                      <input 
                        type="password" 
                        placeholder="••••••••••••"
                        value={settings.smtp_password || ""} 
                        onChange={e => setSettings({...settings, smtp_password: e.target.value})}
                        className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-xs outline-none focus:border-indigo-500" 
                      />
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => saveSettings(settings)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-5 py-2.5 rounded-lg transition-colors flex items-center justify-center"
                >
                  {loadingAction === 'save_settings' && <RefreshCw className="animate-spin h-3.5 w-3.5 mr-1.5" />}
                  💾 Save settings & signature
                </button>
              </div>
          </div>

        </div>
      </main>

      {/* GLOBAL CANDIDATE PROFILE OVERLAY MODAL */}
      {deepDiveCand && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-fade-in"
          onClick={(e) => { if (e.target === e.currentTarget) setDeepDiveCand(null); }}
        >
          <div className="bg-white border border-slate-200 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col animate-slide-up">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-100 p-6 bg-slate-50">
              <div>
                <h3 className="text-2xl font-extrabold text-slate-900 flex items-center">
                  👤 Profile Deep Dive: {deepDiveCand.full_name}
                </h3>
                <p className="text-xs font-semibold text-slate-400 mt-1 flex items-center gap-3">
                  <span>📧 {deepDiveCand.email}</span>
                  <span>|</span>
                  <span>📞 {deepDiveCand.phone}</span>
                  <span>|</span>
                  <span>Tag: <code className="bg-slate-200 text-slate-800 px-1.5 py-0.5 rounded font-mono">{deepDiveCand.tag}</code></span>
                </p>
              </div>
              <button 
                onClick={() => setDeepDiveCand(null)}
                className="text-slate-400 hover:text-slate-600 bg-white border border-slate-200 rounded-lg p-2 shadow-sm transition-all"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Navigation Tabs */}
            <div className="flex border-b border-slate-200 px-6 gap-6 bg-slate-50/50">
              {(['overview', 'pitch', 'prep', 'fit'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setDeepDiveTab(tab)}
                  className={`pb-3 pt-3 text-sm font-semibold border-b-2 transition-all capitalize ${deepDiveTab === tab ? 'border-indigo-600 text-indigo-600 font-bold' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
                >
                  {tab === 'fit' ? 'Job Fit Analyzer' : tab === 'prep' ? 'Interview Prep' : tab === 'pitch' ? 'Client Pitch & Email' : tab}
                </button>
              ))}
            </div>

            {/* Modal Content Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              
              {deepDiveTab === 'overview' && (
                <div className="space-y-4 text-sm text-slate-700">
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-1">Technologies & Tools:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {deepDiveCand.technologies.map(t => (
                        <span key={t} className="bg-slate-100 border border-slate-200 text-slate-800 text-xs font-semibold px-2.5 py-1 rounded-full">{t}</span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-1">Professional Summary:</span>
                    <p className="bg-slate-50 border border-slate-100 rounded-lg p-3 leading-relaxed text-slate-700 whitespace-pre-wrap">{deepDiveCand.summary}</p>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-1">AI Elevator Pitch:</span>
                    <div className="bg-indigo-50/50 border border-indigo-100 text-indigo-900 rounded-lg p-3 font-medium leading-relaxed whitespace-pre-wrap">{deepDiveCand.elevator_pitch}</div>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-1">Technical Assessment Evaluation:</span>
                    <div className="bg-emerald-50/50 border border-emerald-100 text-emerald-950 rounded-lg p-3 font-medium leading-relaxed whitespace-pre-wrap">{deepDiveCand.technical_evaluation}</div>
                  </div>
                </div>
              )}

              {deepDiveTab === 'pitch' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Target Job Description (Optional context for Outreach):</label>
                    <textarea 
                      rows={3}
                      value={fitJd}
                      onChange={(e) => setFitJd(e.target.value)}
                      placeholder="Paste JD requirements to optimize outreach draft..."
                      className="w-full border border-slate-200 rounded-lg p-3 text-sm outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    {/* Client Pitch Section */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Client Pitch</span>
                        <button 
                          onClick={() => generateReport(deepDiveCand, 'pitch')}
                          className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-3 py-1.5 rounded-lg transition-colors flex items-center"
                        >
                          {loadingAction === 'pitch' && <RefreshCw className="animate-spin h-3 w-3 mr-1.5" />}
                          ✨ Generate Pitch
                        </button>
                      </div>
                      
                      {customPitch ? (
                        <div className="bg-slate-50 border border-slate-150 rounded-lg p-4 max-h-[300px] overflow-y-auto">
                          {renderMarkdown(customPitch)}
                        </div>
                      ) : (
                        <div className="h-[200px] border border-dashed border-slate-200 rounded-lg flex items-center justify-center text-slate-400 text-xs text-center p-4">
                          Click button above to compile client-facing executive pitch...
                        </div>
                      )}
                    </div>

                    {/* Outreach Email Section */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Outreach Email Draft</span>
                        <button 
                          onClick={() => generateOutreach(deepDiveCand)}
                          className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-3 py-1.5 rounded-lg transition-colors flex items-center"
                        >
                          {loadingAction === 'outreach' && <RefreshCw className="animate-spin h-3 w-3 mr-1.5" />}
                          ✨ Generate Email
                        </button>
                      </div>
                      
                      {customOutreach ? (
                        <div className="bg-slate-50 border border-slate-150 rounded-lg p-4 max-h-[300px] overflow-y-auto whitespace-pre-wrap font-mono text-xs text-slate-700">
                          {customOutreach}
                        </div>
                      ) : (
                        <div className="h-[200px] border border-dashed border-slate-200 rounded-lg flex items-center justify-center text-slate-400 text-xs text-center p-4">
                          Click button above to draft client-ready email outreach campaign...
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {deepDiveTab === 'prep' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-400">Tailors 5 core technical questions and answer blueprints.</span>
                    <button 
                      onClick={() => generateReport(deepDiveCand, 'guide')}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors flex items-center"
                    >
                      {loadingAction === 'guide' && <RefreshCw className="animate-spin h-3.5 w-3.5 mr-1.5" />}
                      ✨ Generate Interview Prep Guide
                    </button>
                  </div>
                  {customGuide ? (
                    <div className="bg-slate-50 border border-slate-150 rounded-lg p-5">
                      {renderMarkdown(customGuide)}
                    </div>
                  ) : (
                    <div className="h-32 border border-dashed border-slate-200 rounded-lg flex items-center justify-center text-slate-400 text-sm">
                      Click button above to compile interview questions...
                    </div>
                  )}
                </div>
              )}

              {deepDiveTab === 'fit' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Paste Target Job Description:</label>
                    <textarea 
                      rows={4}
                      value={fitJd}
                      onChange={(e) => setFitJd(e.target.value)}
                      placeholder="Paste JD requirements to calculate gap fit score..."
                      className="w-full border border-slate-200 rounded-lg p-3 text-sm outline-none focus:border-indigo-500"
                    />
                  </div>
                  <button 
                    onClick={() => runGapAnalysis(deepDiveCand)}
                    disabled={!fitJd.trim()}
                    className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-100 disabled:text-slate-400 text-white font-bold text-xs px-5 py-2.5 rounded-lg transition-colors flex items-center"
                  >
                    {loadingAction === 'gap' && <RefreshCw className="animate-spin h-3.5 w-3.5 mr-1.5" />}
                    ⚡ Execute Gap Analysis comparison
                  </button>

                  {fitAnalysis && (
                    <div className="border-t border-slate-100 pt-4 space-y-4">
                      <div className="flex items-center space-x-6 bg-slate-50 border border-slate-100 p-4 rounded-lg">
                        {/* Score Gauge Circle */}
                        <div className="h-16 w-16 shrink-0 relative flex items-center justify-center rounded-full bg-emerald-50 text-emerald-700 font-extrabold border border-emerald-200 text-lg">
                          {fitAnalysis.match_score}%
                        </div>
                        <div className="space-y-1">
                          <span className="text-sm font-bold text-slate-800">Job Fit Score</span>
                          <p className="text-xs text-slate-500 leading-relaxed">{fitAnalysis.explanation}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-6 text-sm">
                        <div>
                          <h4 className="font-bold text-emerald-600 text-xs uppercase mb-1.5">✅ Strengths / Matching Skills</h4>
                          <div className="flex flex-wrap gap-1">
                            {fitAnalysis.matching_skills?.map((s: string) => (
                              <span key={s} className="bg-emerald-50 border border-emerald-100 text-emerald-700 text-xs font-semibold px-2 py-0.5 rounded">{s}</span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <h4 className="font-bold text-rose-600 text-xs uppercase mb-1.5">⚠️ Missing Skills / Gaps</h4>
                          <div className="flex flex-wrap gap-1">
                            {fitAnalysis.missing_skills?.map((s: string) => (
                              <span key={s} className="bg-rose-50 border border-rose-100 text-rose-700 text-xs font-semibold px-2 py-0.5 rounded">{s}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
