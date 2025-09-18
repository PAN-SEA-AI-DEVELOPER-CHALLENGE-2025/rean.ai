import { useState } from 'react';
import { chatService } from '@/services/chat';

interface RagTestButtonProps {
  classId: string;
  onResult?: (result: unknown) => void;
}

export default function RagTestButton({ classId, onResult }: RagTestButtonProps) {
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const testRagConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const result = await chatService.getAnswer("what is this class about?", classId);
      setTestResult(`✅ RAG API working! Confidence: ${Math.round(result.confidence * 100)}%`);
      if (onResult) onResult(result);
    } catch (error) {
      setTestResult(`❌ RAG API error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('RAG test error:', error);
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="p-4 bg-slate-100 border border-slate-200 rounded-lg">
      <h4 className="font-semibold text-slate-900 mb-2">RAG API Test</h4>
      <p className="text-sm text-slate-600 mb-3">
        Test the connection to your RAG backend at: <code className="bg-slate-200 px-1 rounded">http://159.223.63.90/api/v1/rag/search/audio</code>
      </p>
      <button
        onClick={testRagConnection}
        disabled={isTesting}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isTesting ? 'Testing...' : 'Test RAG API'}
      </button>
      {testResult && (
        <div className="mt-3 p-2 bg-white border border-slate-200 rounded text-sm">
          {testResult}
        </div>
      )}
    </div>
  );
}
