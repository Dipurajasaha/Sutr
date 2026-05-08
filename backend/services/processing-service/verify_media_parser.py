#!/usr/bin/env python
"""Quick verification that media_parser loads without crashing"""
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info("Attempting to import media_parser module...")
    from app.services.media_parser import model, process_media
    
    if model is None:
        logger.warning("Whisper model failed to load - will gracefully handle media files")
        print("⚠️  Whisper model not available (FFmpeg may be missing)")
    else:
        logger.info("Whisper model loaded successfully")
        print("✅ Whisper model loaded successfully")
    
    # Test with non-existent file (should not crash)
    logger.info("Testing process_media with non-existent file...")
    result = process_media("/nonexistent/file.mp4")
    logger.info("process_media returned: %s", result)
    print("✅ process_media handles errors gracefully")
    
    print("\n✅ Media parser is properly configured with error handling")
    sys.exit(0)
    
except Exception as e:
    logger.exception("Failed to load media_parser: %s", str(e))
    print(f"❌ Error: {e}")
    sys.exit(1)
