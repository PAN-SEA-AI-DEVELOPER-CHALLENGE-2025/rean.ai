import { FaPaperPlane } from "react-icons/fa";

type ChatInputProps = {
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  placeholder?: string;
};

export default function ChatInput({ 
  inputValue, 
  onInputChange, 
  onSubmit, 
  isLoading, 
  placeholder = "Ask me anything about this lecture..." 
}: ChatInputProps) {
  return (
    <div className="border-t border-slate-200/70 bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/75 p-4">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={onSubmit} className="flex items-end space-x-3">
          <div className="flex-1">
            <div className="rounded-2xl border border-slate-200/70 bg-white shadow-md focus-within:ring-2 focus-within:ring-blue-500">
              <textarea
                value={inputValue}
                onChange={(e) => onInputChange(e.target.value)}
                placeholder={placeholder}
                rows={1}
                className="w-full resize-none px-4 py-3 rounded-2xl outline-none placeholder:text-slate-400 text-slate-800 leading-6 min-h-[44px] max-h-40"
                disabled={isLoading}
                onInput={(e) => {
                  const el = e.currentTarget;
                  el.style.height = 'auto';
                  el.style.height = `${Math.min(el.scrollHeight, 320)}px`;
                }}
              />
            </div>
            <p className="mt-1 text-[11px] text-slate-500">Press Enter to send • Shift+Enter for new line</p>
          </div>
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="h-[44px] aspect-square inline-flex items-center justify-center bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md"
            aria-label="Send message"
            title="Send"
          >
            <FaPaperPlane className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
