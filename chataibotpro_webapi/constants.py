"""Constants and enumerations for chataibotpro_webapi."""
from __future__ import annotations
from enum import Enum

BASE_URL: str = "https://chataibot.pro"

# ── Chat models ───────────────────────────────────────────────────────────────

class ChatModel(Enum):
    """Chat model IDs observed in the HAR."""
    # OpenAI
    GPT_4_1_NANO        = "gpt-4.1-nano"
    GPT_4_1_MINI        = "gpt-4.1-mini"
    GPT_4_1             = "gpt-4.1"
    GPT_4O              = "gpt-4o"
    GPT_4O_MINI         = "gpt-4o-mini"
    GPT_5_1             = "gpt-5.1"
    GPT_5_1_HIGH        = "gpt-5.1-high"
    GPT_5_2             = "gpt-5.2"
    GPT_5_2_HIGH        = "gpt-5.2-high"
    GPT_5_4             = "gpt-5.4"
    GPT_5_4_NANO        = "gpt-5.4-nano"
    GPT_5_4_MINI        = "gpt-5.4-mini"
    GPT_5_4_HIGH        = "gpt-5.4-high"
    GPT_5_5             = "gpt-5.5"
    GPT_5_5_HIGH        = "gpt-5.5-high"
    O3                  = "o3"
    O3_PRO              = "o3-pro"
    O4_MINI             = "o4-mini"
    O4_MINI_DR          = "o4-mini-deep-research"
    GPT_4O_SEARCH       = "gpt-4o-search-preview"
    # Anthropic
    CLAUDE_HAIKU_4_5    = "claude-4.5-haiku"
    CLAUDE_SONNET_4_5   = "claude-3-sonnet"
    CLAUDE_SONNET_4_5_H = "claude-3-sonnet-high"
    CLAUDE_SONNET_4_6   = "claude-4.6-sonnet"
    CLAUDE_SONNET_4_6_H = "claude-4.6-sonnet-high"
    CLAUDE_OPUS_4_1     = "claude-3-opus"
    CLAUDE_OPUS_4_5     = "claude-4.5-opus"
    CLAUDE_OPUS_4_6     = "claude-4.6-opus"
    CLAUDE_OPUS_4_7     = "claude-4.7-opus"
    # Google
    GEMINI_2_5_PRO      = "gemini-pro"
    GEMINI_3_FLASH      = "gemini-3-flash"
    GEMINI_3_FLASH_S    = "gemini-3-flash-search"
    GEMINI_3_1_PRO      = "gemini-3.1-pro"
    # xAI
    GROK                = "grok"
    GROK_SEARCH         = "grok-search"
    # DeepSeek
    DEEPSEEK_R1         = "deepseek"
    DEEPSEEK_V3         = "deepseek-v3.2"
    # Qwen
    QWEN3               = "qwen3-thinking-2507"
    QWEN3_MAX           = "qwen3-max"
    QWEN3_5             = "qwen3.5"
    QWEN3_5_PLUS        = "qwen3.5-plus"
    # Perplexity
    PERPLEXITY          = "perplexity"
    PERPLEXITY_PRO      = "perplexity-pro"

    DEFAULT = "gpt-4.1-nano"


# ── Image models ──────────────────────────────────────────────────────────────

class ImageModel(Enum):
    """Image generation type strings used in /api/image/generate."""
    GPT_IMAGE_1         = "GPT_IMAGE"
    GPT_IMAGE_1_HIGH    = "GPT_IMAGE_HIGH"
    GPT_IMAGE_1_5       = "GPT_IMAGE_1_5"
    GPT_IMAGE_1_5_HIGH  = "GPT_IMAGE_1_5_HIGH"
    GPT_IMAGE_2         = "GPT_IMAGE_2"
    GPT_IMAGE_2_HIGH    = "GPT_IMAGE_2_HIGH"
    FLUX_SCHNELL        = "FLUX-schnell"
    FLUX_PRO            = "FLUX-pro"
    FLUX_ULTRA          = "FLUX-ultra"
    FLUX_KONTEXT_MAX    = "FLUX-kontext-max"
    MIDJOURNEY_6_1      = "MIDJOURNEY-6.1"
    MIDJOURNEY_7        = "MIDJOURNEY-7"
    IDEOGRAM            = "IDEOGRAM"
    IDEOGRAM_TURBO      = "IDEOGRAM_TURBO"
    RECRAFT_V3          = "RECRAFT-v3"
    GROK_IMAGE          = "GROK"
    GROK_IMAGE_QUALITY  = "GROK_QUALITY"
    QWEN_LORA           = "QWEN-lora"
    GOOGLE_NB           = "GOOGLE-nano-banana"
    GOOGLE_NB2          = "GOOGLE-nano-banana-2"
    GOOGLE_NB_PRO       = "GOOGLE-nano-banana-pro"
    SEEDREAM_4          = "BYTEDANCE-seedream-4"
    SEEDREAM_5_LITE     = "BYTEDANCE-seedream-5-lite"

    DEFAULT = "GPT_IMAGE_2"


# ── Video models ──────────────────────────────────────────────────────────────

class VideoModel(Enum):
    """Video model version strings for /api/video."""
    SEEDANCE_LITE       = "seedance-v1/lite"
    SEEDANCE_PRO        = "seedance-v1/pro"
    SEEDANCE_2          = "seedance-2.0"
    SEEDANCE_2_FAST     = "seedance-2.0/fast"
    KLING_1_6_STD       = "kling-v1.6/standard"
    KLING_2_MASTER      = "kling-v2/master"
    KLING_2_5_TURBO     = "kling-v2.5-turbo/pro"
    KLING_2_6_PRO       = "kling-v2.6/pro"
    KLING_3_STD         = "kling-v3/standard"
    KLING_3_PRO         = "kling-v3/pro"
    KLING_O1            = "kling-o1/standard"
    SORA_2              = "sora-2"
    SORA_2_PRO          = "sora-2/pro"
    VEO_3_1             = "veo-3.1"
    VEO_3_1_FAST        = "veo-3.1/fast"

    DEFAULT = "seedance-v1/lite"


class VideoGenerationType(Enum):
    TEXT_TO_VIDEO  = "text-to-video"
    IMAGE_TO_VIDEO = "image-to-video"


# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_CHAT_MODEL:  str = ChatModel.DEFAULT.value
DEFAULT_IMAGE_MODEL: str = ImageModel.DEFAULT.value
DEFAULT_VIDEO_MODEL: str = VideoModel.DEFAULT.value
