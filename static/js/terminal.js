/**
 * Canlı Terminal JavaScript
 * AI Tweet Bot için canlı log görüntüleme sistemi
 */

class LiveTerminal {
    constructor() {
        this.isVisible = false;
        this.isMinimized = false;
        this.autoScroll = true;
        this.eventSource = null;
        this.logBuffer = [];
        this.maxLogLines = 1000;
        
        this.init();
    }
    
    init() {
        this.createTerminalHTML();
        this.bindEvents();
        this.addLogLine('Terminal hazır. Açmak için terminal butonuna tıklayın.', 'info');
    }
    
    createTerminalHTML() {
        // Terminal HTML'ini body'ye ekle
        const terminalHTML = `
            <!-- Terminal Toggle Button -->
            <div id="terminalToggle" class="terminal-toggle" onclick="liveTerminal.toggle()">
                <i class="fas fa-terminal"></i>
            </div>

            <!-- Floating Terminal -->
            <div id="floatingTerminal" class="floating-terminal" style="display: none;">
                <div class="terminal-container">
                    <div class="terminal-header">
                        <div class="flex items-center space-x-3">
                            <div class="flex space-x-2">
                                <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                                <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
                                <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                            </div>
                            <span class="text-white font-semibold">AI Tweet Bot Terminal</span>
                            <span id="connectionStatus" class="text-xs text-gray-400">Hazır</span>
                        </div>
                        
                        <div class="terminal-controls">
                            <button id="autoScrollBtn" class="terminal-button active" onclick="liveTerminal.toggleAutoScroll()">
                                <i class="fas fa-arrow-down"></i> Auto Scroll
                            </button>
                            <button class="terminal-button" onclick="liveTerminal.clear()">
                                <i class="fas fa-trash"></i> Temizle
                            </button>
                            <button class="terminal-button" onclick="liveTerminal.minimize()">
                                <i class="fas fa-minus"></i>
                            </button>
                            <button class="terminal-button" onclick="liveTerminal.close()">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div id="terminalContent" class="terminal-content auto-scroll">
                        <div class="terminal-line log-info">
                            <span class="text-gray-500">[SYSTEM]</span> Terminal başlatılıyor...
                        </div>
                        <div class="terminal-line">
                            <span class="cursor">█</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // CSS'i ekle
        const terminalCSS = `
            <style>
                .terminal-container {
                    background: #1a1a1a;
                    color: #00ff00;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.4;
                    border-radius: 8px;
                    overflow: hidden;
                }
                
                .terminal-header {
                    background: #333;
                    padding: 10px 15px;
                    border-bottom: 1px solid #555;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .terminal-content {
                    padding: 15px;
                    height: 500px;
                    overflow-y: auto;
                    background: #000;
                }
                
                .terminal-line {
                    margin-bottom: 2px;
                    word-wrap: break-word;
                }
                
                .log-info { color: #00ff00; }
                .log-warning { color: #ffff00; }
                .log-error { color: #ff0000; }
                .log-debug { color: #00ffff; }
                .log-success { color: #00ff88; }
                
                .terminal-controls {
                    display: flex;
                    gap: 10px;
                    align-items: center;
                }
                
                .terminal-button {
                    background: #555;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }
                
                .terminal-button:hover {
                    background: #666;
                }
                
                .terminal-button.active {
                    background: #00ff00;
                    color: #000;
                }
                
                .floating-terminal {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 800px;
                    max-width: 90vw;
                    z-index: 1000;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                    border-radius: 8px;
                    overflow: hidden;
                    transition: all 0.3s ease;
                }
                
                .floating-terminal.minimized {
                    width: 200px;
                    height: 50px;
                }
                
                .floating-terminal.minimized .terminal-content {
                    display: none;
                }
                
                .terminal-toggle {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: #1a1a1a;
                    color: #00ff00;
                    border: 2px solid #00ff00;
                    border-radius: 50%;
                    width: 60px;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    z-index: 1001;
                    font-size: 20px;
                    transition: all 0.3s ease;
                }
                
                .terminal-toggle:hover {
                    background: #00ff00;
                    color: #1a1a1a;
                }
                
                .terminal-toggle.hidden {
                    display: none;
                }
                
                @keyframes blink {
                    0%, 50% { opacity: 1; }
                    51%, 100% { opacity: 0; }
                }
                
                .cursor {
                    animation: blink 1s infinite;
                }
                
                .auto-scroll {
                    scroll-behavior: smooth;
                }
            </style>
        `;
        
        // Head'e CSS ekle
        document.head.insertAdjacentHTML('beforeend', terminalCSS);
        
        // Body'ye terminal HTML'ini ekle
        document.body.insertAdjacentHTML('beforeend', terminalHTML);
    }
    
    bindEvents() {
        // Klavye kısayolları
        document.addEventListener('keydown', (event) => {
            // Ctrl + ` (backtick) ile terminal aç/kapat
            if (event.ctrlKey && event.key === '`') {
                event.preventDefault();
                this.toggle();
            }
            
            // ESC ile terminal kapat
            if (event.key === 'Escape' && this.isVisible) {
                this.close();
            }
        });
        
        // Sayfa kapanırken bağlantıyı kapat
        window.addEventListener('beforeunload', () => {
            this.stopLogStream();
        });
    }
    
    toggle() {
        if (this.isVisible) {
            this.close();
        } else {
            this.open();
        }
    }
    
    open() {
        const terminal = document.getElementById('floatingTerminal');
        const toggle = document.getElementById('terminalToggle');
        
        terminal.style.display = 'block';
        toggle.classList.add('hidden');
        this.isVisible = true;
        
        // SSE bağlantısını başlat
        this.startLogStream();
    }
    
    close() {
        const terminal = document.getElementById('floatingTerminal');
        const toggle = document.getElementById('terminalToggle');
        
        terminal.style.display = 'none';
        toggle.classList.remove('hidden');
        this.isVisible = false;
        this.isMinimized = false;
        
        // SSE bağlantısını kapat
        this.stopLogStream();
    }
    
    minimize() {
        const terminal = document.getElementById('floatingTerminal');
        this.isMinimized = !this.isMinimized;
        
        if (this.isMinimized) {
            terminal.classList.add('minimized');
        } else {
            terminal.classList.remove('minimized');
        }
    }
    
    toggleAutoScroll() {
        const btn = document.getElementById('autoScrollBtn');
        const content = document.getElementById('terminalContent');
        
        this.autoScroll = !this.autoScroll;
        
        if (this.autoScroll) {
            btn.classList.add('active');
            content.classList.add('auto-scroll');
            this.scrollToBottom();
        } else {
            btn.classList.remove('active');
            content.classList.remove('auto-scroll');
        }
    }
    
    clear() {
        const content = document.getElementById('terminalContent');
        content.innerHTML = `
            <div class="terminal-line log-info">
                <span class="text-gray-500">[SYSTEM]</span> Terminal temizlendi
            </div>
            <div class="terminal-line">
                <span class="cursor">█</span>
            </div>
        `;
        this.logBuffer = [];
    }
    
    scrollToBottom() {
        if (this.autoScroll) {
            const content = document.getElementById('terminalContent');
            content.scrollTop = content.scrollHeight;
        }
    }
    
    addLogLine(message, level = 'info', timestamp = null) {
        if (!timestamp) {
            timestamp = new Date().toLocaleTimeString('tr-TR');
        }
        
        const logClass = `log-${level}`;
        const logLine = `
            <div class="terminal-line ${logClass}">
                <span class="text-gray-500">[${timestamp}]</span> ${this.escapeHtml(message)}
            </div>
        `;
        
        this.logBuffer.push(logLine);
        
        // Buffer limitini kontrol et
        if (this.logBuffer.length > this.maxLogLines) {
            this.logBuffer = this.logBuffer.slice(-this.maxLogLines);
        }
        
        this.updateTerminalContent();
    }
    
    updateTerminalContent() {
        const content = document.getElementById('terminalContent');
        if (!content) return;
        
        const cursorLine = '<div class="terminal-line"><span class="cursor">█</span></div>';
        
        content.innerHTML = this.logBuffer.join('') + cursorLine;
        this.scrollToBottom();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    startLogStream() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        const statusElement = document.getElementById('connectionStatus');
        statusElement.textContent = 'Bağlanıyor...';
        statusElement.className = 'text-xs text-yellow-400';
        
        this.eventSource = new EventSource('/api/logs/stream');
        
        this.eventSource.onopen = (event) => {
            statusElement.textContent = 'Bağlı';
            statusElement.className = 'text-xs text-green-400';
            this.addLogLine('Canlı log akışı başlatıldı', 'success');
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                // Heartbeat mesajlarını gösterme
                if (data.message === 'heartbeat') {
                    return;
                }
                
                this.addLogLine(data.message, data.level, data.timestamp);
            } catch (e) {
                this.addLogLine(event.data, 'info');
            }
        };
        
        this.eventSource.onerror = (event) => {
            statusElement.textContent = 'Bağlantı Hatası';
            statusElement.className = 'text-xs text-red-400';
            this.addLogLine('Log akışı bağlantısı kesildi, yeniden bağlanmaya çalışılıyor...', 'warning');
            
            // 5 saniye sonra yeniden bağlan
            setTimeout(() => {
                if (this.isVisible) {
                    this.startLogStream();
                }
            }, 5000);
        };
    }
    
    stopLogStream() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = 'Bağlantı Kesildi';
            statusElement.className = 'text-xs text-gray-400';
        }
    }
}

// Global terminal instance
let liveTerminal;

// Sayfa yüklendiğinde terminal'i başlat
document.addEventListener('DOMContentLoaded', function() {
    liveTerminal = new LiveTerminal();
}); 