"""
SECUROXI AI Centralized Security Engine Configuration
Stage 3 Security Reasoning Layer Configuration & Risk Weights.
"""

from dataclasses import dataclass, field
from typing import Dict
from securoxi.models import AttackCategory


@dataclass
class SecuroxiConfig:
    """
    Centralized configuration for SECUROXI AI engine, analyzers, risk scoring,
    AI reasoning layer, resource limits, and security logging controls.
    """

    # Resource & DoS Protection Limits
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB limit
    max_pdf_pages: int = 50                      # 50 pages max
    max_spans_per_doc: int = 10_000               # 10,000 text spans max
    max_processing_time_seconds: float = 10.0    # 10 second timeout limit

    # Visual Deception Thresholds
    micro_font_threshold: float = 4.0            # Font size < 4.0pt
    micro_font_extreme_threshold: float = 2.0    # Font size < 2.0pt (High severity)
    white_color_threshold: float = 25.0          # RGB distance to #FFFFFF <= 25.0
    bg_match_threshold: float = 20.0             # RGB distance font to bg <= 20.0

    # Verdict Score Thresholds
    verdict_safe_max: int = 24                   # 0 - 24: SAFE
    verdict_suspicious_max: int = 59             # 25 - 59: SUSPICIOUS (60+: HIGH_RISK)

    # Privacy & Logging Controls
    log_sensitive_evidence: bool = False         # Do NOT log document text by default

    # Stage 3 AI Reasoning Layer Controls
    ai_reasoning_enabled: bool = True            # Enable AI Reasoning Layer
    ai_provider: str = "mock"                    # "mock" or "gemini"
    gemini_model: str = "gemini-2.5-flash"       # Default Gemini model

    # Baseline Category Weights
    category_weights: Dict[AttackCategory, int] = field(default_factory=lambda: {
        # Visual Indicators
        AttackCategory.MICRO_TEXT: 25,
        AttackCategory.WHITE_TEXT: 25,
        AttackCategory.BACKGROUND_MATCH: 25,
        AttackCategory.HIDDEN_TEXT: 30,
        AttackCategory.INVISIBLE_UNICODE: 25,
        AttackCategory.SUSPICIOUS_POSITION: 25,
        AttackCategory.VISUAL_DECEPTION: 25,

        # Prompt Injection & Manipulation Indicators
        AttackCategory.INSTRUCTION_OVERRIDE: 35,
        AttackCategory.SYSTEM_PROMPT_MANIPULATION: 40,
        AttackCategory.ATS_MANIPULATION: 40,
        AttackCategory.AI_ROLE_MANIPULATION: 30,
        AttackCategory.DATA_EXFILTRATION: 45,
        AttackCategory.TOOL_MANIPULATION: 45,
        AttackCategory.OBFUSCATION_INDICATORS: 25,
        AttackCategory.PROMPT_INJECTION: 35,
        AttackCategory.OBFUSCATION: 25
    })

    # Correlation Boost Scores
    correlation_boosts: Dict[str, int] = field(default_factory=lambda: {
        "span_level_overlap": 20,
        "nearby_span_overlap": 20,
        "white_hidden_plus_ats": 25,
        "white_hidden_plus_override": 20,
        "obfuscation_plus_injection": 15,
        "data_exfil_plus_hidden": 25
    })
