from fastapi import APIRouter, File, Form, UploadFile

from app.models.schemas import GenerateResponse
from app.services.analyzer import analyze_pet_photo
from app.services.generator import generate_emoji_set

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_emojis(
    file: UploadFile = File(...),
    style: str = Form("2d"),
    emoji_count: int = Form(8),
):
    """Upload a pet photo and generate a personalized emoji set."""
    image_bytes = await file.read()
    content_type = file.content_type or "image/jpeg"

    # Step 1: Analyze pet features with Claude Vision
    pet_features = await analyze_pet_photo(image_bytes, content_type)

    # Step 2: Generate emoji set with GPT-4o
    emojis = await generate_emoji_set(pet_features, style, emoji_count)

    return GenerateResponse(pet_features=pet_features, emojis=emojis)
