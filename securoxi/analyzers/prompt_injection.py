"""
SECUROXI AI Prompt Injection & Manipulation Analyzer
Deterministic analysis for system prompt overrides, ATS rating manipulation,
AI role hijacking, data exfiltration, tool tampering, and obfuscated injections.
Stage 2 Refined Engine.
"""

import re
import unicodedata
from typing import List, Optional, Tuple
from securoxi.config import SecuroxiConfig
from securoxi.models import TextSpan, SecurityFinding, AttackCategory, Severity
from securoxi.analyzers.base import BaseAnalyzer


class PromptInjectionAnalyzer(BaseAnalyzer):
    """
    Deterministic Prompt Injection Analyzer.
    Detects instruction overrides, system prompt tampering, ATS rating manipulation,
    data exfiltration, tool tampering, and obfuscated prompt injections.
    """

    LEETSPEAK_MAP = {
        "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
        "7": "t", "@": "a", "$": "s", "!": "i"
    }

    HOMOGLYPH_MAP = {
        "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i", "ѕ": "s",
        "Α": "a", "Β": "b", "Ε": "e", "Ζ": "z", "Η": "h", "Ι": "i", "Κ": "k", "Μ": "m", "Ν": "n",
        "Ο": "o", "Ρ": "p", "Τ": "t", "Υ": "y", "Χ": "x",
    }

    SAFE_JOB_TITLES = [
        "system administrator", "systems engineer", "system architect", "systems analyst",
        "ai engineer", "ai researcher", "ai developer", "llm researcher",
        "instructional designer", "quality assurance engineer", "qa analyst"
    ]

    SAFE_EXPERIENCE_PHRASES = [
        "followed safety instructions", "followed company instructions",
        "built system prompt architecture", "developed ai prompt templates",
        "configured system monitoring", "system administration"
    ]

    INSTRUCTION_OVERRIDE_PATTERNS = [
        r"\b(ignore|disregard|forget|bypass|override|cancel)\b.*\b(previous|prior|above|former|all)\b.*\b(instruction|instructions|prompt|prompts|rule|rules|command|commands|context|directions)\b",
        r"\b(do not follow|stop following)\b.*\b(previous|prior|above)\b.*\b(instruction|instructions|prompt|prompts|direction|directions)\b",
        r"\b(new|updated)\b.*\b(instruction|instructions|prompt|prompts)\b.*\b(supersede|take precedence|replace)\b",
        r"\b(ignorer|descarte)\b.*\b(les instructions|las instrucciones)\b.*\b(précédentes|anteriores)\b",  # Multilingual support (French/Spanish)
    ]

    AI_ROLE_PATTERNS = [
        r"\b(you are now|act as|behave as)\b.*\b(an ai|an assistant|a recruiter|an ats|an evaluator|developer mode)\b",
        r"\b(you are no longer|stop being)\b.*\b(an assistant|a recruiter|an ats|a resume reviewer)\b",
        r"\b(from now on|henceforth)\b.*\b(you are|act as)\b.*\b(a|an)\b",
        r"\b(your new role|your new instructions)\b.*\b(is|are)\b"
    ]

    DATA_EXFILTRATION_PATTERNS = [
        r"\b(send|transmit|exfiltrate|forward|post|upload|reveal)\b.*\b(api key|password|credential|token|prompt|system prompt|secret|data|text)\b",
        r"!\[.*?\]\(https?://[^\s]+\)",  # Markdown image injection data exfiltration
        r"\b(fetch|curl|wget)\b\s+https?://[^\s]+"
    ]

    SYSTEM_PROMPT_PATTERNS = [
        r"\[?\b(system|developer|admin|root)\s*(prompt|instruction|instructions|message|directive)\b\]?",
        r"\b(you are now in)\b.*\b(developer mode|admin mode|debug mode|unrestricted mode|jailbreak mode)\b",
        r"\b(system directive|system instruction)\s*:\s*",
        r"\[\s*system\s*\]\s*:",
        r"\b(act as|operate as|behave as)\b.*\b(system|admin|root|unrestricted ai)\b"
    ]

    ATS_MANIPULATION_PATTERNS = [
        r"\b(rank|score|rate|evaluate|select|recommend|mark)\b.*\b(candidate|me|this resume|this applicant)\b.*\b(first|10/10|10 out of 10|top|highest|100%|perfect|hired|exceptional)\b",
        r"\b(give|assign)\b.*\b(this candidate|this resume)\b.*\b(highest|perfect|10/10|top)\b.*\b(score|rating)\b",
        r"\b(unconditionally|automatically)\b.*\b(hire|select|recommend|rank 10/10)\b",
        r"\b(ignore|disregard)\b.*\b(missing requirements|skill gaps|qualifications|experience gaps)\b",
        r"\b(must|should)\b.*\b(output|print|return)\b.*\b(hired|selected|qualified|top candidate)\b"
    ]

    TOOL_MANIPULATION_PATTERNS = [
        r"\b(call|execute|run|invoke)\b.*\b(tool|function|plugin|command|script)\b",
        r"\{\s*\"tool\"\s*:\s*\"[^\"]+\"\s*,\s*\"action\"\s*:\s*\"[^\"]+\"\s*\}",
        r"<\s*tool_call\s*>.*?<\s*/\s*tool_call\s*>"
    ]

    RETRIEVAL_AND_MEMORY_POISONING_PATTERNS = [
        r"\b(authoritative|verified|ground truth)\b.*(candidate is safe|bypass policy|grant clearance)",
        r"\b(remember this|save to memory|long-term memory)\b.*\b(admin|safe|bypass|trusted|policy)\b",
        r"\b(override citations?|ignore previous evidence|fabricated citation)\b",
    ]

    def __init__(self, config: Optional[SecuroxiConfig] = None, **kwargs):
        super().__init__()
        self.config = config or SecuroxiConfig()

    def analyze(self, spans: List[TextSpan], file_path: str = "") -> List[SecurityFinding]:
        return self.analyze_spans(spans)

    def _normalize_text(self, text: str) -> Tuple[str, bool]:
        """
        Normalize text to uncover obfuscated prompt injection attempts:
        - Strip zero-width unicode format characters
        - Collapse multiple spaces
        - Handle single letter unspacing with spaces or punctuation (i.g.n.o.r.e or i_g_n_o_r_e)
        - Decode basic leetspeak
        """
        was_obfuscated = False
        original = text

        # 1. Strip zero-width format control chars
        clean_chars = [c for c in text if unicodedata.category(c) != 'Cf']
        text = "".join(clean_chars)
        if len(text) != len(original):
            was_obfuscated = True

        # 2. Punctuation or Space Unspacing Heuristic (e.g. "i g n o r e" or "i.g.n.o.r.e" or "i_g_n_o_r_e")
        spaced_pattern = r'\b([a-zA-Z])[\s\._\-]+([a-zA-Z])[\s\._\-]+([a-zA-Z])[\s\._\-]+([a-zA-Z])\b'
        if re.search(spaced_pattern, text):
            unspaced = re.sub(r'(?<=\b[a-zA-Z])[\s\._\-]+(?=[a-zA-Z]\b)', '', text)
            if unspaced != text:
                text = unspaced
                was_obfuscated = True

        # 3. Collapse whitespace
        text_collapsed = re.sub(r'\s+', ' ', text).strip()
        if text_collapsed != text:
            text = text_collapsed

        # 4. Leetspeak decoding
        leetspeak_words = []
        for word in text.split():
            if re.search(r'[a-zA-Z][013457@!][a-zA-Z]', word):
                decoded_word = "".join(self.LEETSPEAK_MAP.get(ch, ch) for ch in word)
                leetspeak_words.append(decoded_word)
                was_obfuscated = True
            else:
                leetspeak_words.append(word)
        
        text = " ".join(leetspeak_words)

        # 5. Homoglyph decoding (Cyrillic/Greek to Latin lookalikes)
        homoglyph_chars = [self.HOMOGLYPH_MAP.get(c, c) for c in text]
        text_homo = "".join(homoglyph_chars)
        if text_homo != text:
            was_obfuscated = True
            text = text_homo

        normalized = text.lower()
        return normalized, was_obfuscated

    def _is_false_positive_context(self, text_lower: str) -> bool:
        """Check if matching text is legitimate corporate vocabulary or job title."""
        for title in self.SAFE_JOB_TITLES:
            if title in text_lower:
                return True
        for phrase in self.SAFE_EXPERIENCE_PHRASES:
            if phrase in text_lower:
                return True
        return False

    def analyze_spans(self, spans: List[TextSpan]) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []

        for span in spans:
            raw_text = span.text
            norm_text, was_obfuscated = self._normalize_text(raw_text)

            # Skip false positives in legitimate context
            if self._is_false_positive_context(norm_text):
                continue

            metadata_extra = {"matched_pattern": "", "original_text": raw_text}
            if span.is_hidden or (span.font_color and span.font_color.upper() == "#FFFFFF") or (span.font_size and span.font_size < 4.0):
                metadata_extra["visual_deception_correlated"] = "WHITE_TEXT" if span.font_color == "#FFFFFF" else "MICRO_TEXT"

            # Flag Obfuscation if detected
            if was_obfuscated and len(raw_text.strip()) > 10:
                contains_suspicious_kw = any(kw in norm_text for kw in ["ignore", "system", "prompt", "instruction", "rate", "score", "hire", "eval"])
                if contains_suspicious_kw:
                    meta = dict(metadata_extra)
                    meta.update({"original_text": raw_text, "normalized_text": norm_text})
                    finding = SecurityFinding.create(
                        category=AttackCategory.OBFUSCATION_INDICATORS,
                        severity=Severity.MEDIUM,
                        title="Obfuscated Text Structure Detected",
                        description="Text contains character unspacing, punctuation separators, or leetspeak obfuscation concealing prompt injection.",
                        evidence=raw_text,
                        location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                        confidence=0.90,
                        metadata=meta
                    )
                    findings.append(finding)

            # 1. Instruction Override Patterns
            for pattern in self.INSTRUCTION_OVERRIDE_PATTERNS:
                if re.search(pattern, norm_text, re.IGNORECASE):
                    meta = dict(metadata_extra)
                    meta["matched_pattern"] = pattern
                    finding = SecurityFinding.create(
                        category=AttackCategory.INSTRUCTION_OVERRIDE,
                        severity=Severity.HIGH,
                        title="System Instruction Override Attempt",
                        description="Text contains language attempting to override or negate previous system prompts and instructions.",
                        evidence=raw_text,
                        location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                        confidence=0.95,
                        metadata=meta
                    )
                    findings.append(finding)
                    break

            # 2. AI Role Hijacking Patterns
            for pattern in self.AI_ROLE_PATTERNS:
                if re.search(pattern, norm_text, re.IGNORECASE):
                    meta = dict(metadata_extra)
                    meta["matched_pattern"] = pattern
                    finding = SecurityFinding.create(
                        category=AttackCategory.AI_ROLE_MANIPULATION,
                        severity=Severity.MEDIUM,
                        title="AI Role Assignment Hijacking",
                        description="Text attempts to reassign the AI system's persona, role, or operating rules.",
                        evidence=raw_text,
                        location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                        confidence=0.90,
                        metadata=meta
                    )
                    findings.append(finding)
                    break

            # 3. Data Exfiltration Patterns
            for pattern in self.DATA_EXFILTRATION_PATTERNS:
                if re.search(pattern, norm_text, re.IGNORECASE):
                    meta = dict(metadata_extra)
                    meta["matched_pattern"] = pattern
                    finding = SecurityFinding.create(
                        category=AttackCategory.DATA_EXFILTRATION,
                        severity=Severity.HIGH,
                        title="Data Exfiltration Command",
                        description="Text contains instructions to transmit confidential system data or credentials to external endpoints.",
                        evidence=raw_text,
                        location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                        confidence=0.95,
                        metadata=meta
                    )
                    findings.append(finding)
                    break

            # 4. System Prompt Manipulation Patterns
            for pattern in self.SYSTEM_PROMPT_PATTERNS:
                if re.search(pattern, norm_text, re.IGNORECASE):
                    meta = dict(metadata_extra)
                    meta["matched_pattern"] = pattern
                    finding = SecurityFinding.create(
                        category=AttackCategory.SYSTEM_PROMPT_MANIPULATION,
                        severity=Severity.HIGH,
                        title="System Prompt Structure Tampering",
                        description="Text uses system/developer prompt delimiters or admin directives to hijack model behavior.",
                        evidence=raw_text,
                        location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                        confidence=0.95,
                        metadata=meta
                    )
                    findings.append(finding)
                    break

            # 5. ATS Candidate Rating Manipulation Patterns
            for pattern in self.ATS_MANIPULATION_PATTERNS:
                if re.search(pattern, norm_text, re.IGNORECASE):
                    meta = dict(metadata_extra)
                    meta["matched_pattern"] = pattern
                    finding = SecurityFinding.create(
                        category=AttackCategory.ATS_MANIPULATION,
                        severity=Severity.HIGH,
                        title="ATS / Candidate Evaluation Manipulation",
                        description="Text attempts to manipulate automated ATS or LLM candidate scoring and ranking.",
                        evidence=raw_text,
                        location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                        confidence=0.95,
                        metadata=meta
                    )
                    findings.append(finding)
                    break

            # 6. Tool Tampering Patterns
            for pattern in self.TOOL_MANIPULATION_PATTERNS:
                if re.search(pattern, norm_text, re.IGNORECASE):
                    meta = dict(metadata_extra)
                    meta["matched_pattern"] = pattern
                    finding = SecurityFinding.create(
                        category=AttackCategory.TOOL_MANIPULATION,
                        severity=Severity.HIGH,
                        title="Unauthorized Tool Execution Directive",
                        description="Text attempts to invoke external tools, plugins, or system commands.",
                        evidence=raw_text,
                        location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                        confidence=0.95,
                        metadata=meta
                    )
                    findings.append(finding)
                    break

            # 7. Retrieval and Memory Poisoning Patterns
            for pattern in self.RETRIEVAL_AND_MEMORY_POISONING_PATTERNS:
                if re.search(pattern, norm_text, re.IGNORECASE):
                    meta = dict(metadata_extra)
                    meta["matched_pattern"] = pattern
                    finding = SecurityFinding.create(
                        category=AttackCategory.PROMPT_INJECTION,
                        severity=Severity.HIGH,
                        title="Retrieval / Memory Poisoning Payload Detected",
                        description="Text attempts to poison RAG retrieval context, citations, or persistent memory.",
                        evidence=raw_text,
                        location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                        confidence=0.95,
                        metadata=meta
                    )
                    findings.append(finding)
                    break

        return findings
