#!/usr/bin/env python3
"""
Query preprocessing module for search enhancement.
Handles spell checking, normalization, and query cleaning.
"""

from spellchecker import SpellChecker
import re
from typing import Tuple


class QueryProcessor:
    """
    Process user queries to improve search quality.
    Performs normalization, spell checking, and cleaning.
    """
    
    def __init__(self):
        """Initialize query processor with spell checker."""
        self.spell = SpellChecker()
    
    def normalize(self, query: str) -> str:
        """
        Normalize query string.
        
        Args:
            query: Raw query string
        
        Returns:
            Normalized query
        """
        # Strip leading/trailing whitespace
        query = query.strip()
        
        # Convert to lowercase
        query = query.lower()
        
        # Remove extra whitespace (multiple spaces become single space)
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    def spell_check(self, query: str) -> Tuple[str, bool]:
        """
        Fix common spelling errors in query.
        
        Args:
            query: Query string to check
        
        Returns:
            Tuple of (corrected_query, was_corrected)
        """
        words = query.split()
        corrected_words = []
        was_corrected = False
        
        for word in words:
            # Skip very short words or words with numbers
            if len(word) <= 2 or any(c.isdigit() for c in word):
                corrected_words.append(word)
                continue
            
            # Get correction
            corrected_word = self.spell.correction(word)
            
            # Use correction if available and different
            if corrected_word and corrected_word != word:
                corrected_words.append(corrected_word)
                was_corrected = True
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), was_corrected
    
    def remove_special_chars(self, query: str, keep_chars: str = "-'") -> str:
        """
        Remove special characters from query, keeping useful ones.
        
        Args:
            query: Query string
            keep_chars: Characters to keep (default: hyphens and apostrophes)
        
        Returns:
            Cleaned query
        """
        # Build pattern: keep alphanumeric, spaces, and specified chars
        pattern = f"[^a-zA-Z0-9\\s{re.escape(keep_chars)}]"
        query = re.sub(pattern, '', query)
        
        # Remove extra spaces that might have been created
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def process(self, query: str, apply_spell_check: bool = True) -> Tuple[str, bool]:
        """
        Process query with all preprocessing steps.
        
        Args:
            query: Raw query string
            apply_spell_check: Whether to apply spell checking (default True)
        
        Returns:
            Tuple of (processed_query, was_corrected)
        """
        if not query or not query.strip():
            return query, False
        
        original = query
        
        # Step 1: Normalize
        query = self.normalize(query)
        
        # Step 2: Remove special characters (but keep hyphens and apostrophes)
        query = self.remove_special_chars(query)
        
        # Step 3: Spell check (if enabled)
        was_corrected = False
        if apply_spell_check:
            query, was_corrected = self.spell_check(query)
        
        return query, was_corrected

