import { FaRobot, FaUser, FaSpinner, FaBookmark, FaExternalLinkAlt } from "react-icons/fa";

type Message = {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  confidence?: number;
  sources?: string[];
};

type ChatMessageProps = {
  message: Message;
};

function formatPlainText(raw: string): string {
  if (!raw) return '';
  let text = raw.replace(/\r\n/g, '\n');
  // Convert markdown bullets to professional dot bullets
  text = text.replace(/^\s*[-*]\s+/gm, '• ');
  // Strip bold/italic markers
  text = text.replace(/\*\*(.*?)\*\*/g, '$1'); // **bold**
  text = text.replace(/__(.*?)__/g, '$1'); // __bold__
  text = text.replace(/\*(.*?)\*/g, '$1'); // *italic*
  text = text.replace(/_(.*?)_/g, '$1'); // _italic_
  // Remove code ticks and triple backticks
  text = text.replace(/```[\s\S]*?```/g, (m) => m.replace(/```/g, ''));
  text = text.replace(/`/g, '');
  // Remove heading hashes
  text = text.replace(/^#{1,6}\s*/gm, '');
  // Collapse excessive blank lines
  text = text.replace(/\n{3,}/g, '\n\n');
  return text.trim();
}

export default function ChatMessage({ message }: ChatMessageProps) {
  if (message.isLoading) {
    return (
      <div className="flex justify-start">
        <div className="flex items-start space-x-3 max-w-3xl">
          <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-sky-50 to-blue-100 text-blue-700 ring-1 ring-blue-200 shadow-sm">
            <FaSpinner className="w-4 h-4 animate-spin" />
          </div>
          <div className="rounded-2xl px-4 py-3 bg-white border border-slate-200/70 text-slate-900 shadow-md">
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
              <span className="text-sm text-slate-500">Analyzing lesson content with RAG…</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex items-start space-x-3 max-w-3xl ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          message.type === 'user' 
            ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow ring-1 ring-blue-300/40' 
            : 'bg-gradient-to-br from-sky-50 to-blue-100 text-blue-700 ring-1 ring-blue-200 shadow-sm'
        }`}>
          {message.type === 'user' ? <FaUser className="w-4 h-4" /> : <FaRobot className="w-4 h-4" />}
        </div>
        <div className={`rounded-3xl px-4 py-3 ${
          message.type === 'user'
            ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-md border border-white/10 backdrop-blur-sm'
            : 'bg-white border border-slate-200/70 text-slate-900 shadow-md'
        }`}>
          <p className="whitespace-pre-wrap text-[15px] leading-7">{formatPlainText(message.content)}</p>
          
          {/* Confidence removed from UI */}

          {/* Show sources if available */}
          {message.type === 'assistant' && message.sources && message.sources.length > 0 && (
            <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50/70 p-3">
              <div className="flex items-center gap-2">
                <FaExternalLinkAlt className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-xs font-semibold tracking-wide text-slate-600 uppercase">Source snippets</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">{message.sources.length}</span>
              </div>
              <div className="mt-2 grid gap-2 max-h-40 overflow-y-auto">
                {message.sources.map((source, index) => (
                  <div key={index} className="text-[12px] leading-5 text-slate-700 p-2 rounded-lg bg-white border border-slate-200 hover:border-slate-300 transition-colors">
                    {source.length > 140 ? `${source.slice(0, 140)}…` : source}
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className={`text-xs mt-2 ${
            message.type === 'user' ? 'text-blue-100/90' : 'text-slate-500'
          }`}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
      </div>
    </div>
  );
}
