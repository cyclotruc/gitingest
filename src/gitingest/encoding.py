import sys
import io
import codecs

def setup_encoding():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, 
            encoding='utf-8', 
            errors='replace'
        )
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, 
            encoding='utf-8', 
            errors='replace'
        )