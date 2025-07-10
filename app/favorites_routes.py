import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import os

router = APIRouter(prefix="/api", tags=["favorites"])

FAVORITES_FILE = "favorites.json"

def read_favorites() -> List[Dict[str, Any]]:
    """Reads the favorites from the JSON file."""
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def write_favorites(favorites: List[Dict[str, Any]]):
    """Writes the favorites to the JSON file."""
    try:
        with open(FAVORITES_FILE, "w") as f:
            json.dump(favorites, f, indent=4)
    except IOError:
        raise HTTPException(status_code=500, detail="Could not write to favorites file.")

@router.get("/favorites", response_model=List[Dict[str, Any]])
async def get_favorites():
    """Retrieve all favorite items."""
    return read_favorites()

@router.post("/favorites", status_code=201)
async def add_favorite(item: Dict[str, Any]):
    """Add an item to favorites."""
    favorites = read_favorites()
    item_id = item.get("item_id")

    if not item_id:
        raise HTTPException(status_code=400, detail="Item must have an 'item_id'.")

    if any(fav["item_id"] == item_id for fav in favorites):
        raise HTTPException(status_code=409, detail="Item already in favorites.")

    favorites.append(item)
    write_favorites(favorites)
    return {"message": "Item added to favorites."}

@router.delete("/favorites/{item_id}", status_code=200)
async def remove_favorite(item_id: str):
    """Remove an item from favorites by its ID."""
    favorites = read_favorites()
    
    original_count = len(favorites)
    favorites = [fav for fav in favorites if fav.get("item_id") != item_id]

    if len(favorites) == original_count:
        raise HTTPException(status_code=404, detail="Item not found in favorites.")

    write_favorites(favorites)
    return {"message": "Item removed from favorites."} 