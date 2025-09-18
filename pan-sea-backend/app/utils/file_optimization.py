"""
File upload and processing optimization utilities.
"""
import os
import tempfile
import asyncio
import aiofiles
from typing import AsyncGenerator, Optional
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)


class FileOptimizer:
    """Utilities for optimized file handling"""
    
    @staticmethod
    async def stream_upload_to_temp(
        file: UploadFile, 
        chunk_size: int = 8192
    ) -> str:
        """Stream upload file to temporary location with memory optimization"""
        try:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(
                suffix=os.path.splitext(file.filename)[-1] if file.filename else '.tmp'
            )
            
            # Close the file descriptor immediately
            os.close(temp_fd)
            
            # Stream upload in chunks to avoid memory issues
            async with aiofiles.open(temp_path, 'wb') as temp_file:
                while chunk := await file.read(chunk_size):
                    await temp_file.write(chunk)
            
            logger.info(f"File streamed to temporary location: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error streaming file upload: {str(e)}")
            raise
    
    @staticmethod
    async def get_file_info(file_path: str) -> dict:
        """Get file information without loading entire file into memory"""
        try:
            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_file": os.path.isfile(file_path),
                "extension": os.path.splitext(file_path)[-1].lower()
            }
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {}
    
    @staticmethod
    async def validate_file_size(
        file_path: str, 
        max_size: int = 10 * 1024 * 1024  # 10MB default
    ) -> bool:
        """Validate file size without loading into memory"""
        try:
            file_info = await FileOptimizer.get_file_info(file_path)
            return file_info.get("size", 0) <= max_size
        except Exception as e:
            logger.error(f"Error validating file size: {str(e)}")
            return False
    
    @staticmethod
    async def cleanup_temp_file(file_path: str) -> bool:
        """Safely cleanup temporary file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
                return True
            return True
        except Exception as e:
            logger.warning(f"Could not cleanup temp file {file_path}: {str(e)}")
            return False
    
    @staticmethod
    async def stream_file_chunks(
        file_path: str, 
        chunk_size: int = 8192
    ) -> AsyncGenerator[bytes, None]:
        """Stream file in chunks for processing"""
        try:
            async with aiofiles.open(file_path, 'rb') as file:
                while chunk := await file.read(chunk_size):
                    yield chunk
        except Exception as e:
            logger.error(f"Error streaming file chunks: {str(e)}")
            raise


class AudioOptimizer:
    """Audio-specific optimization utilities"""
    
    @staticmethod
    async def optimize_audio_for_processing(file_path: str) -> str:
        """Optimize audio file for processing (convert to WAV if needed)"""
        try:
            from pydub import AudioSegment
            
            # Check if already WAV
            if file_path.lower().endswith('.wav'):
                return file_path
            
            # Convert to WAV for better processing
            audio = AudioSegment.from_file(file_path)
            
            # Create optimized WAV file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            
            # Export as WAV with optimized settings
            audio.export(
                temp_path,
                format="wav",
                parameters=["-ac", "1", "-ar", "16000"]  # Mono, 16kHz for better processing
            )
            
            logger.info(f"Audio optimized for processing: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error optimizing audio: {str(e)}")
            return file_path
    
    @staticmethod
    async def get_audio_duration(file_path: str) -> float:
        """Get audio duration without loading entire file"""
        try:
            from pydub import AudioSegment
            
            # Load only metadata
            audio = AudioSegment.from_file(file_path)
            duration = len(audio) / 1000.0  # Convert to seconds
            
            logger.info(f"Audio duration: {duration} seconds")
            return duration
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return 0.0
    
    @staticmethod
    async def split_audio_async(
        file_path: str, 
        chunk_duration: int = 30
    ) -> list[str]:
        """Split audio into chunks asynchronously"""
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(file_path)
            duration = len(audio) / 1000.0
            
            if duration <= chunk_duration:
                return [file_path]
            
            chunks = []
            chunk_length = chunk_duration * 1000  # Convert to milliseconds
            
            for i in range(0, len(audio), chunk_length):
                chunk = audio[i:i + chunk_length]
                
                # Create temporary file for chunk
                temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
                os.close(temp_fd)
                
                chunk.export(temp_path, format="wav")
                chunks.append(temp_path)
            
            logger.info(f"Audio split into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting audio: {str(e)}")
            return [file_path]


class MemoryOptimizer:
    """Memory usage optimization utilities"""
    
    @staticmethod
    def get_memory_usage() -> dict:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "percent": process.memory_percent(),
                "available": psutil.virtual_memory().available
            }
        except ImportError:
            logger.warning("psutil not available for memory monitoring")
            return {}
        except Exception as e:
            logger.error(f"Error getting memory usage: {str(e)}")
            return {}
    
    @staticmethod
    async def cleanup_memory():
        """Force garbage collection to free memory"""
        try:
            import gc
            gc.collect()
            logger.info("Memory cleanup completed")
        except Exception as e:
            logger.error(f"Error during memory cleanup: {str(e)}")


# Global instances
file_optimizer = FileOptimizer()
audio_optimizer = AudioOptimizer()
memory_optimizer = MemoryOptimizer()
