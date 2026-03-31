from pydantic import BaseModel


class PetFeatures(BaseModel):
    animal_type: str  # dog, cat, etc.
    breed: str
    fur_color: str
    fur_pattern: str
    ear_shape: str
    eye_color: str
    eye_shape: str
    nose_shape: str
    body_shape: str
    distinctive_features: list[str]  # e.g. spots, stripes, scars
    current_expression: str
    overall_vibe: str  # e.g. cute, majestic, goofy


class EmojiRequest(BaseModel):
    style: str = "2d"  # "2d" or "3d"
    emoji_count: int = 8


class EmojiResult(BaseModel):
    emotion: str
    image_url: str  # base64 data URL or file URL


class ConvertedEmoji(BaseModel):
    emotion: str
    image_url: str
    format: str  # kakao, imessage, sticker, gif, wallpaper
    width: int
    height: int


class GenerateResponse(BaseModel):
    pet_features: PetFeatures
    emojis: list[EmojiResult]


class ConvertResponse(BaseModel):
    format: str
    emojis: list[ConvertedEmoji]


# ─── Wizard (Phase 1) ─────────────────────────


class WizardStartResponse(BaseModel):
    session_id: str
    session_token: str
    pet_features: PetFeatures
    tier_config: dict


class WizardStepRequest(BaseModel):
    session_id: str
    step: str  # style, proportion, detail, reference
    selection: dict  # step별 선택값


class WizardBackRequest(BaseModel):
    session_id: str
    target_step: str


class WizardBackResponse(BaseModel):
    current_step: str
    previews: dict[str, str]  # step -> preview image URL


class WizardGenerateRequest(BaseModel):
    session_id: str
    emoji_count: int = 8
