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
