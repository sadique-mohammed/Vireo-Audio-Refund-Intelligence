import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "outputs"
CACHE_PATH = ROOT / "cache" / "llm_cache.jsonl"
PROMPTS_DIR = ROOT / "prompts"
TAXONOMY_PATH = ROOT / "taxonomy.md"

SOURCE_RULES = {
    "legacy_fd": {"unit_divisor": 100, "rule_id": "legacy_fd_div_100"},
    "helpdesk": {"unit_divisor": 1, "rule_id": "helpdesk_no_change"},
}
SOURCE_RANK = {"helpdesk": 0, "legacy_fd": 1}
KNOWN_STATUS = {"resolved", "closed", "open", "pending"}

LABELS = [
    "PAYMENT_ISSUE",
    "NON_DELIVERY",
    "DAMAGED_IN_TRANSIT",
    "WRONG_ITEM",
    "PRODUCT_DEFECT",
    "CANCELLATION",
    "PRICE_COUPON",
    "RETURN_PICKUP_QC",
    "WARRANTY_BUYBACK",
    "REFUND_STATUS_FOLLOWUP",
    "GOODWILL",
    "OTHER_UNCLEAR",
]
UNCERTAIN = "UNCERTAIN"

CODE_MAP = {
    "DOA-REPL": "PRODUCT_DEFECT",
    "LOST-TRANSIT": "NON_DELIVERY",
    "DUP-PAYMENT": "PAYMENT_ISSUE",
    "CANCEL": "CANCELLATION",
    "PRICE-ADJ": "PRICE_COUPON",
    "RETURN-QC-OK": "RETURN_PICKUP_QC",
    "WTY-BUYBACK": "WARRANTY_BUYBACK",
}

PROMPT_VERSION = os.environ.get("VIREO_PROMPT", "reason_v1")
THINKING_LEVEL = os.environ.get("VIREO_THINKING", "low")
MAX_OUTPUT_TOKENS = 2048
WORKERS = int(os.environ.get("VIREO_WORKERS", "1"))

RETRY_DELAYS = (2, 4, 8, 16)
RETRY_MAX_JITTER = 1.5

PROVIDER = os.environ.get("VIREO_PROVIDER", "groq")
GROQ_MODEL = os.environ.get("VIREO_GROQ_MODEL", "openai/gpt-oss-120b")
