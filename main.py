from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import asyncpg
import os
from contextlib import asynccontextmanager

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db:5432/recipedb")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

# Database Models
class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    ingredients = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    prep_time = Column(Integer)  # in minutes
    cook_time = Column(Integer)  # in minutes
    servings = Column(Integer)
    difficulty = Column(String(50))
    cuisine = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


SEED_RECIPES = [
    {
        "title": "Spaghetti Carbonara",
        "description": "Classic Roman pasta with eggs, cheese, and pancetta.",
        "ingredients": "spaghetti, pancetta, eggs, parmesan, black pepper, salt",
        "instructions": "Boil the spaghetti until al dente. Cook pancetta until crisp. Whisk eggs with parmesan and pepper. Toss pasta with pancetta and egg mixture off the heat. Serve immediately.",
        "prep_time": 15,
        "cook_time": 20,
        "servings": 2,
        "difficulty": "Medium",
        "cuisine": "Italian",
    },
    {
        "title": "Chicken Tikka Masala",
        "description": "Creamy and aromatic Indian-inspired chicken curry.",
        "ingredients": "chicken breast, yogurt, garlic, ginger, tomato, cream, curry powder, onion",
        "instructions": "Marinate chicken in yogurt and spices. Sear until lightly browned. Simmer onion, garlic, ginger, tomato, and spices. Add chicken and cream, cook until tender.",
        "prep_time": 25,
        "cook_time": 30,
        "servings": 4,
        "difficulty": "Hard",
        "cuisine": "Indian",
    },
    {
        "title": "Avocado Toast",
        "description": "A quick and nutritious breakfast favorite.",
        "ingredients": "bread, avocado, lemon juice, chili flakes, salt, olive oil",
        "instructions": "Toast the bread. Mash avocado with lemon juice, salt, and chili flakes. Spread over toast and finish with olive oil.",
        "prep_time": 10,
        "cook_time": 5,
        "servings": 2,
        "difficulty": "Easy",
        "cuisine": "American",
    },
    {
        "title": "Beef Burrito Bowl",
        "description": "Protein-packed bowl with rice, beans, and beef.",
        "ingredients": "ground beef, rice, black beans, corn, tomato, lettuce, salsa, cheese",
        "instructions": "Cook beef with taco seasoning. Warm rice and beans. Assemble bowls with greens, corn, salsa, and cheese.",
        "prep_time": 20,
        "cook_time": 20,
        "servings": 4,
        "difficulty": "Medium",
        "cuisine": "Mexican",
    },
    {
        "title": "Vegetable Stir-Fry",
        "description": "Colorful and crunchy weeknight stir-fry.",
        "ingredients": "broccoli, bell pepper, carrot, snap peas, soy sauce, garlic, ginger, sesame oil",
        "instructions": "Sauté garlic and ginger, then add vegetables. Stir-fry until crisp-tender. Finish with soy sauce and sesame oil.",
        "prep_time": 15,
        "cook_time": 12,
        "servings": 3,
        "difficulty": "Easy",
        "cuisine": "Chinese",
    },
    {
        "title": "Greek Salad",
        "description": "Fresh salad with cool cucumber and feta.",
        "ingredients": "cucumber, tomato, red onion, olives, feta, oregano, olive oil, lemon",
        "instructions": "Chop the vegetables and olives. Toss with feta and dressing made from olive oil, lemon, and oregano. Serve chilled.",
        "prep_time": 15,
        "cook_time": 0,
        "servings": 2,
        "difficulty": "Easy",
        "cuisine": "Greek",
    },
    {
        "title": "Lemon Herb Salmon",
        "description": "Oven-baked salmon with bright citrus flavor.",
        "ingredients": "salmon fillets, lemon, dill, garlic, olive oil, salt, pepper",
        "instructions": "Season salmon with lemon, dill, garlic, oil, salt, and pepper. Bake at 200C until the fish flakes easily. Serve warm.",
        "prep_time": 10,
        "cook_time": 18,
        "servings": 2,
        "difficulty": "Medium",
        "cuisine": "Mediterranean",
    },
    {
        "title": "Mushroom Risotto",
        "description": "Creamy rice dish with earthy mushrooms.",
        "ingredients": "arborio rice, mushrooms, onion, garlic, vegetable stock, parmesan, butter",
        "instructions": "Cook onion and garlic, then toast rice. Add stock gradually while stirring until creamy. Stir in mushrooms, butter, and parmesan.",
        "prep_time": 20,
        "cook_time": 35,
        "servings": 3,
        "difficulty": "Hard",
        "cuisine": "Italian",
    },
    {
        "title": "Pesto Pasta",
        "description": "Fast pasta with basil and nutty pesto sauce.",
        "ingredients": "pasta, basil, pine nuts, garlic, olive oil, parmesan, salt",
        "instructions": "Cook pasta according to package instructions. Blend basil, pine nuts, garlic, olive oil, and parmesan into pesto. Toss with warm pasta and serve.",
        "prep_time": 10,
        "cook_time": 12,
        "servings": 2,
        "difficulty": "Easy",
        "cuisine": "Italian",
    },
    {
        "title": "Chicken Caesar Wrap",
        "description": "A crisp lunch wrap with grilled chicken and Caesar dressing.",
        "ingredients": "chicken breast, tortillas, lettuce, romaine, parmesan, caesar dressing, croutons",
        "instructions": "Grill or pan-sear chicken until cooked through. Fill tortillas with lettuce, chicken, parmesan, and dressing. Add croutons and roll up.",
        "prep_time": 15,
        "cook_time": 15,
        "servings": 2,
        "difficulty": "Easy",
        "cuisine": "American",
    },
]


async def seed_database() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Recipe).limit(1))
        if existing.scalar_one_or_none() is not None:
            return

        session.add_all([Recipe(**recipe) for recipe in SEED_RECIPES])
        await session.commit()

# Pydantic Models
class RecipeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Recipe title")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients: str = Field(..., min_length=1, description="List of ingredients")
    instructions: str = Field(..., min_length=1, description="Cooking instructions")
    prep_time: Optional[int] = Field(None, ge=0, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(None, ge=0, description="Cooking time in minutes")
    servings: Optional[int] = Field(None, ge=1, description="Number of servings")
    difficulty: Optional[str] = Field(None, description="Difficulty level (Easy, Medium, Hard)")
    cuisine: Optional[str] = Field(None, description="Cuisine type")

# RecipeCreate removed - using RecipeBase directly

class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    ingredients: Optional[str] = Field(None, min_length=1)
    instructions: Optional[str] = Field(None, min_length=1)
    prep_time: Optional[int] = Field(None, ge=0)
    cook_time: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1)
    difficulty: Optional[str] = None
    cuisine: Optional[str] = None

class RecipeResponse(RecipeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RecipeListResponse(BaseModel):
    recipes: List[RecipeResponse]
    total: int
    page: int
    per_page: int

# Database dependency
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_database()
    yield
    # Shutdown
    await engine.dispose()

# FastAPI app
app = FastAPI(
    title="Recipe API",
    description="A comprehensive API for managing cooking recipes with full CRUD operations",
    version="1.0.0",
    contact={
        "name": "Recipe API Support",
        "email": "support@recipeapi.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that returns API information
    
    Returns basic information about the Recipe API including version and available endpoints.
    """
    return {
        "message": "Welcome to Recipe API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.post("/recipes/", response_model=RecipeResponse, status_code=201, tags=["Recipes"])
async def create_recipe(
    recipe: RecipeBase,  # Changed from RecipeCreate
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new recipe
    
    Creates a new recipe with the provided information including title, ingredients,
    instructions, and optional metadata like prep time, servings, and difficulty level.
    
    - **title**: Required recipe name (1-200 characters)
    - **description**: Optional recipe description
    - **ingredients**: Required list of ingredients
    - **instructions**: Required cooking instructions
    - **prep_time**: Optional preparation time in minutes
    - **cook_time**: Optional cooking time in minutes
    - **servings**: Optional number of servings
    - **difficulty**: Optional difficulty level
    - **cuisine**: Optional cuisine type
    """
    db_recipe = Recipe(**recipe.dict())
    db.add(db_recipe)
    await db.commit()
    await db.refresh(db_recipe)
    return db_recipe

@app.get("/recipes/", response_model=RecipeListResponse, tags=["Recipes"])
async def get_recipes(
    skip: int = Query(0, ge=0, description="Number of recipes to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of recipes to return"),
    search: Optional[str] = Query(None, description="Search term for recipe titles"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine type"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all recipes with pagination and filtering
    
    Retrieves a paginated list of recipes with optional search and filtering capabilities.
    Supports searching by title and filtering by cuisine and difficulty level.
    
    - **skip**: Number of recipes to skip (for pagination)
    - **limit**: Maximum number of recipes to return (1-100)
    - **search**: Search term to filter recipes by title
    - **cuisine**: Filter recipes by cuisine type
    - **difficulty**: Filter recipes by difficulty level
    """
    query = select(Recipe)
    
    # Apply filters
    if search:
        query = query.where(Recipe.title.ilike(f"%{search}%"))
    if cuisine:
        query = query.where(Recipe.cuisine.ilike(f"%{cuisine}%"))
    if difficulty:
        query = query.where(Recipe.difficulty.ilike(f"%{difficulty}%"))
    
    # Get total count
    total_query = query
    total_result = await db.execute(total_query)
    total = len(total_result.scalars().all())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    recipes = result.scalars().all()
    
    return RecipeListResponse(
        recipes=recipes,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@app.get("/recipes/{recipe_id}", response_model=RecipeResponse, tags=["Recipes"])
async def get_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific recipe by ID
    
    Retrieves detailed information about a specific recipe using its unique identifier.
    Returns 404 if the recipe is not found.
    
    - **recipe_id**: The unique identifier of the recipe to retrieve
    """
    query = select(Recipe).where(Recipe.id == recipe_id)
    result = await db.execute(query)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe

@app.put("/recipes/{recipe_id}", response_model=RecipeResponse, tags=["Recipes"])
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing recipe
    
    Updates an existing recipe with new information. Only provided fields will be updated,
    while others remain unchanged. Returns 404 if the recipe is not found.
    
    - **recipe_id**: The unique identifier of the recipe to update
    - **title**: Optional new recipe title
    - **description**: Optional new description
    - **ingredients**: Optional new ingredients list
    - **instructions**: Optional new cooking instructions
    - **prep_time**: Optional new preparation time
    - **cook_time**: Optional new cooking time
    - **servings**: Optional new serving count
    - **difficulty**: Optional new difficulty level
    - **cuisine**: Optional new cuisine type
    """
    query = select(Recipe).where(Recipe.id == recipe_id)
    result = await db.execute(query)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    update_data = recipe_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        for key, value in update_data.items():
            setattr(recipe, key, value)
        
        await db.commit()
        await db.refresh(recipe)
    
    return recipe

@app.delete("/recipes/{recipe_id}", tags=["Recipes"])
async def delete_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a recipe
    
    Permanently deletes a recipe from the database. This action cannot be undone.
    Returns 404 if the recipe is not found.
    
    - **recipe_id**: The unique identifier of the recipe to delete
    """
    query = select(Recipe).where(Recipe.id == recipe_id)
    result = await db.execute(query)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    await db.delete(recipe)
    await db.commit()
    
    return {"message": f"Recipe {recipe_id} deleted successfully"}

@app.get("/recipes/search/by-ingredient", response_model=List[RecipeResponse], tags=["Search"])
async def search_recipes_by_ingredient(
    ingredient: str = Query(..., description="Ingredient to search for"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search recipes by ingredient
    
    Finds all recipes that contain a specific ingredient in their ingredients list.
    The search is case-insensitive and matches partial ingredient names.
    
    - **ingredient**: The ingredient to search for in recipes
    """
    query = select(Recipe).where(Recipe.ingredients.ilike(f"%{ingredient}%"))
    result = await db.execute(query)
    recipes = result.scalars().all()
    
    return recipes

@app.get("/recipes/stats", tags=["Statistics"])
async def get_recipe_stats(db: AsyncSession = Depends(get_db)):
    """
    Get recipe statistics
    
    Returns various statistics about the recipes in the database including:
    total count, average preparation time, most common cuisine types, and difficulty distribution.
    """
    # Total recipes
    total_query = select(Recipe)
    total_result = await db.execute(total_query)
    total_recipes = len(total_result.scalars().all())
    
    # Get all recipes for calculations
    all_recipes = total_result.scalars().all()
    
    if not all_recipes:
        return {
            "total_recipes": 0,
            "average_prep_time": 0,
            "average_cook_time": 0,
            "cuisines": {},
            "difficulties": {}
        }
    
    # Calculate averages
    prep_times = [r.prep_time for r in all_recipes if r.prep_time is not None]
    cook_times = [r.cook_time for r in all_recipes if r.cook_time is not None]
    
    avg_prep_time = sum(prep_times) / len(prep_times) if prep_times else 0
    avg_cook_time = sum(cook_times) / len(cook_times) if cook_times else 0
    
    # Count cuisines and difficulties
    cuisines = {}
    difficulties = {}
    
    for recipe in all_recipes:
        if recipe.cuisine:
            cuisines[recipe.cuisine] = cuisines.get(recipe.cuisine, 0) + 1
        if recipe.difficulty:
            difficulties[recipe.difficulty] = difficulties.get(recipe.difficulty, 0) + 1
    
    return {
        "total_recipes": total_recipes,
        "average_prep_time": round(avg_prep_time, 2),
        "average_cook_time": round(avg_cook_time, 2),
        "cuisines": cuisines,
        "difficulties": difficulties
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)