// Audio upload service for transcription and summary generation
interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

interface UploadResponse {
  success: boolean;
  summary_id?: string;
  message?: string;
  error?: string;
}

interface AudioFile {
  file: File;
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
  summaryId?: string;
}

class UploadService {

  async uploadAudio(
    file: File,
    classId: string,
    onProgress?: (progress: UploadProgress) => void,
    options?: { lecture_title?: string; language?: string; subject?: string; materials?: File[] }
  ): Promise<UploadResponse> {
    try {
      // Validate file
      if (!this.isValidAudioFile(file)) {
        throw new Error('Invalid file type. Please upload audio files only.');
      }

      const maxSize = 50 * 1024 * 1024; // 50MB limit for better reliability
      if (file.size > maxSize) {
        throw new Error(`File too large. Maximum size is ${Math.round(maxSize / (1024 * 1024))}MB. Current file size: ${Math.round(file.size / (1024 * 1024))}MB.`);
      }

      // Create FormData
      const formData = new FormData();
      formData.append('file', file);
      formData.append('class_id', classId);
      if (options?.lecture_title) formData.append('lecture_title', options.lecture_title);
      if (options?.language) formData.append('language', options.language);
      if (options?.subject) formData.append('subject', options.subject);
      if (options?.materials && Array.isArray(options.materials)) {
        const maxMaterials = 3;
        const safeMaterials = options.materials.slice(0, maxMaterials).filter(Boolean) as File[];

        // validate materials
        const allowedExtensions = ['.pdf', '.ppt', '.pptx', '.docx', '.txt'];
        for (const m of safeMaterials) {
          const lower = m.name.toLowerCase();
          const isAllowed = allowedExtensions.some(ext => lower.endsWith(ext));
          if (!isAllowed) {
            throw new Error('Invalid material type. Allowed: PDF, PPT, PPTX, DOCX, TXT');
          }
        }
        for (const mat of safeMaterials) {
          formData.append('materials', mat);
        }
      }

      // Create XMLHttpRequest for progress tracking
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable && onProgress) {
            const progress: UploadProgress = {
              loaded: event.loaded,
              total: event.total,
              percentage: Math.round((event.loaded / event.total) * 100)
            };
            onProgress(progress);
          }
        });

        // Handle completion
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              resolve({
                success: true,
                summary_id: response.summary_id,
                message: response.message || 'Upload successful'
              });
            } catch {
              resolve({
                success: true,
                message: 'Upload completed successfully'
              });
            }
          } else {
            try {
              const errorResponse = JSON.parse(xhr.responseText || '{}');
              let derived = errorResponse.message || errorResponse.error || errorResponse.detail || '';
              if (!derived && errorResponse.raw) {
                derived = typeof errorResponse.raw === 'string' ? errorResponse.raw : JSON.stringify(errorResponse.raw);
              }
              const errorMessage = derived || `Upload failed with status ${xhr.status}`;
              
              // Provide more specific error messages
              if (xhr.status === 413) {
                reject(new Error('File too large. Please choose a smaller file (max 50MB) or compress your audio.'));
              } else if (xhr.status === 504) {
                reject(new Error('Processing timeout. Your audio file is taking too long to process. Please try with a shorter audio file or compress it further.'));
              } else if (xhr.status === 400) {
                reject(new Error(errorMessage));
              } else if (xhr.status >= 500) {
                // Surface backend-provided message to help debugging
                reject(new Error(errorMessage || 'Server error. Please try again later.'));
              } else {
                reject(new Error(errorMessage));
              }
            } catch {
              if (xhr.status === 413) {
                reject(new Error('File too large. Please choose a smaller file (max 50MB) or compress your audio.'));
              } else if (xhr.status === 504) {
                reject(new Error('Processing timeout. Your audio file is taking too long to process. Please try with a shorter audio file or compress it further.'));
              } else {
                reject(new Error(`Upload failed with status ${xhr.status}. Please try again.`));
              }
            }
          }
        });

        // Handle errors
        xhr.addEventListener('error', () => {
          reject(new Error('Network error during upload'));
        });

        xhr.addEventListener('timeout', () => {
          reject(new Error('Upload timeout after 10 minutes. The file might be too complex to process. Please try with a shorter audio file or contact support.'));
        });

        // Configure and send request to local API proxy
        const uploadUrl = `/api/execution/process-overall`;
        xhr.open('POST', uploadUrl);
        xhr.setRequestHeader('accept', 'application/json');
        try {
          const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
          if (token) {
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
          }
        } catch {}
        xhr.timeout = 600000; // 10 minutes timeout for audio processing
        xhr.send(formData);
      });

    } catch (error) {
      throw error;
    }
  }

  private isValidAudioFile(file: File): boolean {
    const validTypes = [
      'audio/mpeg',
      'audio/mp3', 
      'audio/wav',
      'audio/ogg',
      'audio/webm',
      'audio/m4a',
      'audio/aac',
      'audio/flac'
    ];
    
    const validExtensions = ['.mp3', '.wav', '.ogg', '.webm', '.m4a', '.aac', '.flac'];
    
    const hasValidType = validTypes.includes(file.type);
    const hasValidExtension = validExtensions.some(ext => 
      file.name.toLowerCase().endsWith(ext)
    );
    
    return hasValidType || hasValidExtension;
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }



  createAudioFile(file: File): AudioFile {
    return {
      file,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0
    };
  }
}

export const uploadService = new UploadService();
export type { AudioFile, UploadProgress, UploadResponse };
