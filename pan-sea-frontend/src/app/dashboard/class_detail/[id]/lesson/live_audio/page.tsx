"use client";

import { useState, useRef, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  FaArrowLeft, 
  FaMicrophone, 
  FaPlay, 
  FaPause, 
  FaStop, 
  FaCircle,
  FaCheck,
  FaTimes,
  FaSpinner,
  FaFileAlt,
  FaCopy,
  FaDownload
} from 'react-icons/fa';

// Define Speech Recognition types first
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: ((this: SpeechRecognition, ev: Event) => void) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;
  onend: ((this: SpeechRecognition, ev: Event) => void) | null;
  start(): void;
  stop(): void;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognitionResultList {
  readonly length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  readonly isFinal: boolean;
  readonly length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  readonly transcript: string;
  readonly confidence: number;
}

// Extend Window interface for Speech Recognition
declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

type RecordingState = 'idle' | 'recording' | 'paused' | 'completed';

export default function LiveAudioPage({ 
  params 
}: { 
  params: Promise<{ id: string }> 
}) {
  const { id: classId } = use(params);
  const router = useRouter();
  
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [recordingTime, setRecordingTime] = useState(0);
  const [recordingBlob, setRecordingBlob] = useState<Blob | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcriptSegments, setTranscriptSegments] = useState<Array<{
    text: string;
    timestamp: number;
    confidence?: number;
  }>>([]);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startTranscription = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.log('Speech recognition not supported');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
      setIsTranscribing(true);
    };
    
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      // let interimTranscript = '';
      let finalTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript + ' ';
          // Add to transcript segments
          setTranscriptSegments(prev => [...prev, {
            text: result[0].transcript,
            timestamp: recordingTime,
            confidence: result[0].confidence
          }]);
        } else {
          // interimTranscript += result[0].transcript;
        }
      }
      
      setTranscript(prev => prev + finalTranscript);
      
      // Auto-scroll to bottom
      if (transcriptRef.current) {
        transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
      }
    };
    
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
    };
    
    recognition.onend = () => {
      setIsTranscribing(false);
      if (recordingState === 'recording') {
        // Restart recognition if still recording
        setTimeout(() => startTranscription(), 100);
      }
    };
    
    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopTranscription = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsTranscribing(false);
    }
  };

  const copyTranscript = async () => {
    try {
      await navigator.clipboard.writeText(transcript);
      // You could add a toast notification here
      alert('Transcript copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy transcript:', err);
    }
  };

  const downloadTranscript = () => {
    const element = document.createElement('a');
    const file = new Blob([transcript], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `transcript-${title || 'recording'}-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      });
      
      streamRef.current = stream;
      chunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setRecordingBlob(blob);
        setRecordingState('completed');
        
        // Auto-generate title if empty
        if (!title.trim()) {
          const now = new Date();
          setTitle(`Live Recording - ${now.toLocaleDateString()} ${now.toLocaleTimeString()}`);
        }
      };
      
      mediaRecorder.start(100); // Collect data every 100ms
      setRecordingState('recording');
      setRecordingTime(0);
      
      // Start transcription
      startTranscription();
      
      // Start timer
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone. Please check permissions and try again.');
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && recordingState === 'recording') {
      mediaRecorderRef.current.pause();
      setRecordingState('paused');
      
      // Pause transcription
      stopTranscription();
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && recordingState === 'paused') {
      mediaRecorderRef.current.resume();
      setRecordingState('recording');
      
      // Resume transcription
      startTranscription();
      
      // Resume timer
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && (recordingState === 'recording' || recordingState === 'paused')) {
      mediaRecorderRef.current.stop();
      
      // Stop transcription
      stopTranscription();
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    }
  };

  const discardRecording = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    
    // Stop transcription
    stopTranscription();
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    setRecordingState('idle');
    setRecordingTime(0);
    setRecordingBlob(null);
    setTitle('');
    setDescription('');
    setTranscript('');
    setTranscriptSegments([]);
    chunksRef.current = [];
  };

  const saveRecording = async () => {
    if (!recordingBlob || !title.trim()) return;
    
    setIsSaving(true);
    
    try {
      // In a real application, you would upload the recording to a server here
      console.log('Saving recording:', {
        title: title.trim(),
        description: description.trim(),
        duration: recordingTime,
        size: recordingBlob.size,
        transcript: transcript,
        transcriptSegments: transcriptSegments,
        classId
      });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Navigate back to class detail page
      router.push(`/dashboard/class_detail/${classId}`);
      
    } catch (error) {
      console.error('Error saving recording:', error);
      alert('Failed to save recording. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link 
                href={`/dashboard/class_detail/${classId}`}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                <FaArrowLeft className="w-6 h-6" />
              </Link>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Live Audio Recording</h1>
                <p className="text-sm text-gray-600">Record your lesson in real-time</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                recordingState === 'recording' ? 'bg-red-500 animate-pulse' :
                recordingState === 'paused' ? 'bg-yellow-500' :
                recordingState === 'completed' ? 'bg-green-500' :
                'bg-gray-300'
              }`}></div>
              <span className="text-sm font-medium text-gray-700 capitalize">
                {recordingState === 'idle' ? 'Ready' : recordingState}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Recording Display */}
          <div className="text-center mb-8">
            <div className="mb-6">
              <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full mb-4 ${
                recordingState === 'recording' ? 'bg-red-100 text-red-600' :
                recordingState === 'paused' ? 'bg-yellow-100 text-yellow-600' :
                recordingState === 'completed' ? 'bg-green-100 text-green-600' :
                'bg-gray-100 text-gray-400'
              }`}>
                {recordingState === 'recording' ? (
                  <FaCircle className="text-4xl animate-pulse" />
                ) : recordingState === 'paused' ? (
                  <FaPause className="text-4xl" />
                ) : recordingState === 'completed' ? (
                  <FaCheck className="text-4xl" />
                ) : (
                  <FaMicrophone className="text-4xl" />
                )}
              </div>
              
              <div className="text-4xl font-mono font-bold text-gray-800 mb-2">
                {formatTime(recordingTime)}
              </div>
              
              {recordingBlob && (
                <p className="text-sm text-gray-600">
                  Size: {(recordingBlob.size / 1024 / 1024).toFixed(2)} MB
                </p>
              )}
            </div>

            {/* Recording Controls */}
            <div className="flex justify-center gap-4 mb-8">
              {recordingState === 'idle' && (
                <button
                  onClick={startRecording}
                  className="px-8 py-3 bg-red-500 text-white rounded-full hover:bg-red-600 font-medium text-lg transition-colors flex items-center gap-2"
                >
                  <FaCircle className="w-5 h-5" />
                  Start Recording
                </button>
              )}
              
              {recordingState === 'recording' && (
                <>
                  <button
                    onClick={pauseRecording}
                    className="px-6 py-3 bg-yellow-500 text-white rounded-full hover:bg-yellow-600 font-medium transition-colors flex items-center gap-2"
                  >
                    <FaPause className="w-5 h-5" />
                    Pause
                  </button>
                  <button
                    onClick={stopRecording}
                    className="px-6 py-3 bg-gray-600 text-white rounded-full hover:bg-gray-700 font-medium transition-colors flex items-center gap-2"
                  >
                    <FaStop className="w-5 h-5" />
                    Stop
                  </button>
                </>
              )}
              
              {recordingState === 'paused' && (
                <>
                  <button
                    onClick={resumeRecording}
                    className="px-6 py-3 bg-green-500 text-white rounded-full hover:bg-green-600 font-medium transition-colors flex items-center gap-2"
                  >
                    <FaPlay className="w-5 h-5" />
                    Resume
                  </button>
                  <button
                    onClick={stopRecording}
                    className="px-6 py-3 bg-gray-600 text-white rounded-full hover:bg-gray-700 font-medium transition-colors flex items-center gap-2"
                  >
                    <FaStop className="w-5 h-5" />
                    Stop
                  </button>
                </>
              )}
              
              {recordingState === 'completed' && (
                <>
                  <button
                    onClick={discardRecording}
                    className="px-6 py-3 bg-gray-300 text-gray-700 rounded-full hover:bg-gray-400 font-medium transition-colors flex items-center gap-2"
                  >
                    <FaTimes className="w-5 h-5" />
                    Discard
                  </button>
                  <button
                    onClick={startRecording}
                    className="px-6 py-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 font-medium transition-colors flex items-center gap-2"
                  >
                    <FaMicrophone className="w-5 h-5" />
                    Record Again
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Live Transcript Section */}
          {(recordingState === 'recording' || recordingState === 'paused' || recordingState === 'completed') && (
            <div className="border-t pt-8 mt-8">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <FaFileAlt className="w-5 h-5 text-gray-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Live Transcript</h3>
                  {isTranscribing && (
                    <div className="flex items-center gap-1 text-sm text-red-600">
                      <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                      Transcribing...
                    </div>
                  )}
                </div>
                
                {transcript && (
                  <div className="flex gap-2">
                    <button
                      onClick={copyTranscript}
                      className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Copy transcript"
                    >
                      <FaCopy className="w-4 h-4" />
                    </button>
                    <button
                      onClick={downloadTranscript}
                      className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Download transcript"
                    >
                      <FaDownload className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
              
              <div 
                ref={transcriptRef}
                className="bg-gray-50 border border-gray-200 rounded-lg p-4 h-64 overflow-y-auto text-sm leading-relaxed"
              >
                {transcript ? (
                  <div className="space-y-2">
                    {transcriptSegments.map((segment, index) => (
                      <div key={index} className="flex gap-3">
                        <span className="text-xs text-gray-500 mt-1 min-w-[50px]">
                          {formatTime(segment.timestamp)}
                        </span>
                        <span className="text-gray-800 flex-1">
                          {segment.text}
                        </span>
                        {segment.confidence && (
                          <span className="text-xs text-gray-400 mt-1">
                            {Math.round(segment.confidence * 100)}%
                          </span>
                        )}
                      </div>
                    ))}
                    
                    {/* Show current live transcript */}
                    {isTranscribing && recordingState === 'recording' && (
                      <div className="flex gap-3 opacity-60">
                        <span className="text-xs text-gray-500 mt-1 min-w-[50px]">
                          {formatTime(recordingTime)}
                        </span>
                        <span className="text-gray-600 flex-1 italic">
                          Listening...
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <FaFileAlt className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>Transcript will appear here as you speak</p>
                      {!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window) && (
                        <p className="text-xs text-red-500 mt-1">
                          Speech recognition not supported in this browser
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              {transcript && (
                <div className="mt-2 text-xs text-gray-500">
                  Total words: {transcript.split(' ').filter(word => word.trim()).length} | 
                  Segments: {transcriptSegments.length}
                </div>
              )}
            </div>
          )}

          {/* Lesson Details Form */}
          {recordingState === 'completed' && (
            <div className="border-t pt-8">
              <h3 className="text-lg font-semibold mb-4">Lesson Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Lesson Title *
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Enter lesson title..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    disabled={isSaving}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of the lesson content..."
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    disabled={isSaving}
                  />
                </div>

                <div className="flex gap-4 pt-4">
                  <button
                    onClick={discardRecording}
                    className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium flex items-center justify-center gap-2"
                    disabled={isSaving}
                  >
                    <FaTimes className="w-4 h-4" />
                    Cancel
                  </button>
                  <button
                    onClick={saveRecording}
                    disabled={!title.trim() || isSaving}
                    className="flex-1 px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-medium disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isSaving ? (
                      <>
                        <FaSpinner className="w-4 h-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <FaCheck className="w-4 h-4" />
                        Save Recording
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
