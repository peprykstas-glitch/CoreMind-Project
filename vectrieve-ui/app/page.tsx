'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  Send, Paperclip, Bot, User, Trash2, Menu, X, FileText, 
  Sparkles, BarChart2, MessageSquare, ThumbsUp, ThumbsDown, Settings, RefreshCw 
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { checkHealth, sendMessage, uploadFile, getFiles, deleteFile, sendFeedback, getAnalytics, Message } from '@/lib/api';

export default function Home() {
  // === STATE ===
  const [activeTab, setActiveTab] = useState<'chat' | 'analytics'>('chat');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [files, setFiles] = useState<string[]>([]);
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [temperature, setTemperature] = useState(0.3);
  const [analytics, setAnalytics] = useState<any>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // === INIT ===
  useEffect(() => {
    checkHealth();
    loadFiles();
  }, []);

  useEffect(() => {
    if (activeTab === 'chat') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    } else {
      loadAnalytics();
    }
  }, [messages, activeTab]);

  const loadFiles = () => getFiles().then(setFiles);
  
  const loadAnalytics = async () => {
    const data = await getAnalytics();
    if (data) setAnalytics(data);
  };

  // === ACTIONS ===
  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendMessage([...messages, userMsg], temperature);
      const botMsg: Message = {
        role: 'assistant',
        content: response.response_text,
        sources: response.sources,
        latency: response.latency,
        query_id: response.query_id, // Important for feedback
        last_query: input // Stored for feedback context
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Connection Error. Is backend running?' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (msg: Message, type: 'positive' | 'negative') => {
    if (!msg.query_id) return;
    await sendFeedback({
        query_id: msg.query_id,
        feedback: type,
        query: msg.last_query || "",
        response: msg.content,
        latency: msg.latency || 0
    });
    alert(`Feedback saved: ${type === 'positive' ? 'Thanks! 👍' : 'Noted. 👎'}`);
  };

  const clearHistory = () => {
      if(confirm("Clear chat history?")) setMessages([]);
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setIsLoading(true);
      await uploadFile(e.target.files[0]);
      await loadFiles();
      setIsLoading(false);
    }
  };

  const handleDelete = async (fname: string) => {
    if (confirm(`Remove ${fname}?`)) {
      await deleteFile(fname);
      await loadFiles();
    }
  };

  return (
    <div className="flex h-screen bg-[#121212] text-gray-100 font-sans overflow-hidden">
      
      {/* === SIDEBAR === */}
      <div className={`${isSidebarOpen ? 'w-[280px]' : 'w-0'} bg-[#0a0a0a] flex flex-col transition-all duration-300 border-r border-white/5 relative z-20`}>
        
        {/* Header */}
        <div className="p-5 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-lg tracking-tight bg-gradient-to-r from-green-400 to-emerald-600 bg-clip-text text-transparent">
            <Sparkles size={20} className="text-green-500" />
            VECTRIEVE
          </div>
          <button onClick={() => setSidebarOpen(false)} className="md:hidden text-gray-500"><X size={20}/></button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-3 pb-4 border-b border-white/5 space-y-1">
            <button 
                onClick={() => setActiveTab('chat')}
                className={`flex items-center gap-3 w-full p-2.5 rounded-lg text-sm font-medium transition ${activeTab === 'chat' ? 'bg-[#212121] text-white' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}`}
            >
                <MessageSquare size={18} /> Chat
            </button>
            <button 
                onClick={() => setActiveTab('analytics')}
                className={`flex items-center gap-3 w-full p-2.5 rounded-lg text-sm font-medium transition ${activeTab === 'analytics' ? 'bg-[#212121] text-white' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}`}
            >
                <BarChart2 size={18} /> Analytics
            </button>
        </div>

        {/* Active Tab Content */}
        <div className="flex-1 overflow-y-auto p-4">
            
            {/* FILE LIST */}
            <div className="mb-6">
                <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Knowledge Base</div>
                {files.length === 0 && <div className="text-xs text-gray-600 italic">Empty. Upload files.</div>}
                {files.map(f => (
                    <div key={f} className="group flex justify-between items-center py-2 px-2 rounded hover:bg-white/5 text-sm text-gray-400 transition cursor-pointer">
                    <div className="flex items-center gap-2 truncate">
                        <FileText size={14} className="text-blue-500" />
                        <span className="truncate">{f}</span>
                    </div>
                    <button onClick={() => handleDelete(f)} className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-500 transition"><Trash2 size={14} /></button>
                    </div>
                ))}
            </div>

            {/* SETTINGS SECTION */}
            <div className="mt-4 pt-4 border-t border-white/5">
                <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Settings size={12} /> Configuration
                </div>
                
                {/* Temperature Slider */}
                <div className="mb-4">
                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                        <span>Creativity (Temp)</span>
                        <span className="text-green-400">{temperature}</span>
                    </div>
                    <input 
                        type="range" min="0" max="1" step="0.1" 
                        value={temperature} 
                        onChange={(e) => setTemperature(parseFloat(e.target.value))}
                        className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500"
                    />
                </div>

                {/* Clear History */}
                <button 
                    onClick={clearHistory}
                    className="flex items-center gap-2 w-full p-2 text-xs text-red-400 hover:bg-red-900/20 rounded transition border border-red-900/30 justify-center"
                >
                    <Trash2 size={14} /> Clear History
                </button>
            </div>
        </div>

        {/* Upload Footer */}
        <div className="p-4 border-t border-white/5 bg-[#0a0a0a]">
            <label className="flex items-center justify-center gap-2 w-full p-3 bg-green-600/10 hover:bg-green-600/20 text-green-500 border border-green-600/30 rounded-lg cursor-pointer transition text-sm font-medium">
                <Paperclip size={16} />
                <span>Add Context</span>
                <input type="file" onChange={handleUpload} className="hidden" />
            </label>
        </div>
      </div>

      {/* === MAIN CONTENT === */}
      <div className="flex-1 flex flex-col relative h-full bg-[#121212]">
        
        {/* Toggle Button Mobile */}
        {!isSidebarOpen && (
            <div className="absolute top-4 left-4 z-50">
            <button onClick={() => setSidebarOpen(true)} className="p-2 bg-[#212121] text-gray-300 rounded-md border border-white/10"><Menu size={20}/></button>
            </div>
        )}

        {/* --- VIEW: CHAT --- */}
        {activeTab === 'chat' && (
            <>
                <div className="flex-1 overflow-y-auto scroll-smooth">
                    <div className="max-w-4xl mx-auto px-4 py-12 space-y-6">
                        {messages.length === 0 && (
                            <div className="flex flex-col items-center justify-center h-[50vh] text-center opacity-40">
                                <Sparkles size={64} className="text-green-500 mb-4" />
                                <h1 className="text-3xl font-bold text-white mb-2">Vectrieve AI</h1>
                                <p className="text-gray-400">Secure RAG Knowledge Assistant</p>
                            </div>
                        )}

                        {messages.map((msg, i) => (
                        <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in`}>
                            {msg.role === 'assistant' && (
                                <div className="w-8 h-8 rounded-full bg-green-900/30 border border-green-500/30 flex items-center justify-center shrink-0 mt-1">
                                    <Bot size={16} className="text-green-400" />
                                </div>
                            )}
                            
                            <div className={`relative max-w-[85%] md:max-w-[75%] ${msg.role === 'user' ? 'bg-[#212121] text-white px-5 py-3 rounded-2xl rounded-tr-sm border border-white/5' : ''}`}>
                                <div className="prose prose-invert prose-p:leading-relaxed prose-pre:bg-[#0a0a0a] max-w-none text-sm md:text-base">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>

                                {/* Sources */}
                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="mt-3 pt-2 border-t border-white/10">
                                        <details className="group">
                                            <summary className="text-xs text-gray-500 cursor-pointer flex items-center gap-2 hover:text-green-400 transition">
                                                <span>📚 {msg.sources.length} Sources</span>
                                                <span className="bg-[#0a0a0a] px-1.5 py-0.5 rounded text-[10px] font-mono border border-white/10">{msg.latency?.toFixed(2)}s</span>
                                            </summary>
                                            <div className="mt-2 space-y-2 pl-2 border-l-2 border-green-500/20">
                                                {msg.sources.map((src, idx) => (
                                                    <div key={idx} className="text-xs">
                                                        <span className="font-bold text-gray-400">{src.filename}</span>
                                                        <p className="text-gray-600 truncate">{src.content}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </details>
                                    </div>
                                )}

                                {/* Feedback Buttons */}
                                {msg.role === 'assistant' && (
                                    <div className="flex gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                        <button onClick={() => handleFeedback(msg, 'positive')} className="text-gray-600 hover:text-green-400 p-1"><ThumbsUp size={14} /></button>
                                        <button onClick={() => handleFeedback(msg, 'negative')} className="text-gray-600 hover:text-red-400 p-1"><ThumbsDown size={14} /></button>
                                    </div>
                                )}
                            </div>

                            {msg.role === 'user' && (
                                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center shrink-0 mt-1">
                                    <User size={16} className="text-gray-300" />
                                </div>
                            )}
                        </div>
                        ))}
                        
                        {isLoading && (
                            <div className="flex gap-4">
                                <div className="w-8 h-8 rounded-full bg-green-900/30 flex items-center justify-center"><Bot size={16} className="text-green-400" /></div>
                                <div className="flex gap-1 items-center h-8">
                                    <span className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"></span>
                                    <span className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-100"></span>
                                    <span className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-200"></span>
                                </div>
                            </div>
                        )}
                        <div ref={chatEndRef} className="h-4" />
                    </div>
                </div>

                {/* Input Area */}
                <div className="p-4 bg-[#121212]">
                    <div className="max-w-4xl mx-auto relative">
                        <div className="relative flex items-end gap-2 bg-[#1e1e1e] p-2 pr-3 rounded-2xl border border-white/10 shadow-2xl focus-within:border-gray-600 transition">
                            <button className="p-3 text-gray-500 hover:text-white transition"><Paperclip size={20} /></button>
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }}}
                                placeholder="Message Vectrieve..."
                                className="w-full bg-transparent border-0 focus:ring-0 text-white placeholder-gray-500 resize-none py-3 max-h-32"
                                rows={1}
                            />
                            <button onClick={handleSend} disabled={!input.trim() || isLoading} className="p-2 bg-white text-black rounded-xl hover:bg-gray-200 transition mb-1 disabled:opacity-50">
                                <Send size={18} fill="black" />
                            </button>
                        </div>
                    </div>
                </div>
            </>
        )}

        {/* --- VIEW: ANALYTICS --- */}
        {activeTab === 'analytics' && (
            <div className="flex-1 overflow-y-auto p-8">
                <div className="max-w-5xl mx-auto space-y-8">
                    <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                            <BarChart2 className="text-green-500" /> System Analytics
                        </h2>
                        <button onClick={loadAnalytics} className="p-2 bg-[#212121] rounded hover:bg-[#2a2a2a] text-gray-400 transition"><RefreshCw size={18} /></button>
                    </div>

                    {!analytics ? (
                        <div className="text-gray-500">Loading data...</div>
                    ) : (
                        <>
                            {/* KPI Cards */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="bg-[#1e1e1e] p-4 rounded-xl border border-white/5">
                                    <div className="text-gray-500 text-xs uppercase font-bold">Total Queries</div>
                                    <div className="text-3xl font-bold text-white mt-1">{analytics.total}</div>
                                </div>
                                <div className="bg-[#1e1e1e] p-4 rounded-xl border border-white/5">
                                    <div className="text-gray-500 text-xs uppercase font-bold">Avg Latency</div>
                                    <div className="text-3xl font-bold text-green-400 mt-1">{analytics.avg_latency}s</div>
                                </div>
                                <div className="bg-[#1e1e1e] p-4 rounded-xl border border-white/5">
                                    <div className="text-gray-500 text-xs uppercase font-bold">Thumbs Up</div>
                                    <div className="text-3xl font-bold text-blue-400 mt-1">{analytics.likes} 👍</div>
                                </div>
                                <div className="bg-[#1e1e1e] p-4 rounded-xl border border-white/5">
                                    <div className="text-gray-500 text-xs uppercase font-bold">Thumbs Down</div>
                                    <div className="text-3xl font-bold text-red-400 mt-1">{analytics.dislikes} 👎</div>
                                </div>
                            </div>

                            {/* Charts */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <div className="bg-[#1e1e1e] p-6 rounded-xl border border-white/5">
                                    <h3 className="text-lg font-semibold mb-6">Latency History</h3>
                                    <div className="h-64">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={analytics.history}>
                                                <XAxis dataKey="Timestamp" hide />
                                                <YAxis stroke="#555" fontSize={12} />
                                                <Tooltip contentStyle={{backgroundColor: '#333', border: 'none'}} />
                                                <Line type="monotone" dataKey="Latency" stroke="#10b981" strokeWidth={2} dot={false} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                                
                                <div className="bg-[#1e1e1e] p-6 rounded-xl border border-white/5">
                                    <h3 className="text-lg font-semibold mb-6">Model Usage</h3>
                                    <div className="h-64">
                                        {/* Simple visualization for models dict */}
                                        <div className="space-y-4">
                                            {Object.entries(analytics.models).map(([model, count]: any) => (
                                                <div key={model}>
                                                    <div className="flex justify-between text-sm mb-1">
                                                        <span>{model}</span>
                                                        <span className="text-gray-400">{count}</span>
                                                    </div>
                                                    <div className="w-full bg-gray-800 rounded-full h-2">
                                                        <div className="bg-blue-500 h-2 rounded-full" style={{width: `${(count / analytics.total) * 100}%`}}></div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>
        )}
      </div>
    </div>
  );
}