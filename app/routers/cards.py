from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.card import Card
from app.schemas.card import CardCreate, CardResponse
from app.dependencies import get_current_active_user

router = APIRouter()

@router.post("/", response_model=dict)
async def add_card(
    card_in: CardCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Optional: check if card already exists for user
    query = await db.execute(
        select(Card).where(Card.user_id == current_user.id, Card.card_number == card_in.card_number)
    )
    if query.scalars().first():
        raise HTTPException(status_code=400, detail="Card is already linked to your account")

    new_card = Card(
        user_id=current_user.id,
        card_number=card_in.card_number,
        card_holder_name=card_in.card_holder_name,
        expiry_date=card_in.expiry_date,
        cvv=card_in.cvv
    )
    
    db.add(new_card)
    await db.commit()
    await db.refresh(new_card)
    
    return {
        "success": True,
        "message": "Card added successfully",
        "data": {
            "id": str(new_card.id),
            "masked_card_number": f"**** **** **** {new_card.card_number[-4:]}" if len(new_card.card_number) >= 4 else new_card.card_number
        }
    }

@router.get("/", response_model=dict)
async def list_cards(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = await db.execute(select(Card).where(Card.user_id == current_user.id))
    cards = query.scalars().all()
    
    data = []
    for card in cards:
        data.append({
            "id": str(card.id),
            "card_holder_name": card.card_holder_name,
            "expiry_date": card.expiry_date,
            "masked_card_number": f"**** **** **** {card.card_number[-4:]}" if len(card.card_number) >= 4 else card.card_number,
            "created_at": card.created_at.isoformat()
        })
        
    return {
        "success": True,
        "data": data
    }
