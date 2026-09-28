import os
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models import User, WorkoutPlan
from app.schemas import UserInput, WorkoutRequest, FeedbackRequest
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter()


# -------------------------------------------------------------------
# Database Helpers
# -------------------------------------------------------------------
def save_user(user_id: int, name: str, age: int, weight: float, goal: str, intensity: str):
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(id=user_id).first()
        if existing:
            existing.name = name
            existing.age = age
            existing.weight = weight
            existing.goal = goal
            existing.intensity = intensity
        else:
            user = User(
                id=user_id,
                name=name,
                age=age,
                weight=weight,
                goal=goal,
                intensity=intensity,
                schedule=7,
            )
            db.add(user)
        db.commit()
    finally:
        db.close()


def save_plan(user_id: int, plan: str):
    db = SessionLocal()
    try:
        workout = WorkoutPlan(user_id=user_id, original_plan=plan)
        db.add(workout)
        db.commit()
    finally:
        db.close()


def update_plan(user_id: int, updated_text: str):
    db = SessionLocal()
    try:
        workout = db.query(WorkoutPlan).filter_by(user_id=user_id).first()
        if workout:
            workout.updated_plan = updated_text
            db.commit()
    finally:
        db.close()


def get_original_plan(user_id: int):
    db = SessionLocal()
    try:
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
        return plan.original_plan if plan else None
    finally:
        db.close()


def get_user(user_id: int):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


# -------------------------------------------------------------------
# Web Routes (HTML)
# -------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Home page displaying the user input form."""
    return templates.TemplateResponse(request, "index.html")


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: int = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
):
    """Process user input, generate workout plan + nutrition tip, save to DB."""
    try:
        save_user(user_id, username, age, weight, goal, intensity)
        plan = generate_workout_gemini({"goal": goal, "intensity": intensity})
        save_plan(user_id, plan)
        nutrition_tip = generate_nutrition_tip_with_flash(goal)

        return templates.TemplateResponse(
            request,
            "result.html",
            {
                "username": username,
                "user_id": user_id,
                "age": age,
                "weight": weight,
                "goal": goal,
                "intensity": intensity,
                "workout_plan": plan,
                "nutrition_tip": nutrition_tip,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: int = Form(...),
    feedback: str = Form(...),
):
    """Update the workout plan based on user feedback."""
    original = get_original_plan(user_id)
    if not original:
        return templates.TemplateResponse(
            request,
            "result.html",
            {
                "username": f"User {user_id}",
                "user_id": user_id,
                "age": "-",
                "weight": "-",
                "goal": "-",
                "intensity": "-",
                "workout_plan": "Original plan not found for this user.",
                "nutrition_tip": "",
                "error": "Original plan not found for this user.",
            },
        )

    updated = update_workout_plan(original, feedback)
    update_plan(user_id, updated)

    user = get_user(user_id)
    goal = user.goal if user else "general fitness"
    nutrition_tip = generate_nutrition_tip_with_flash(goal)

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "username": user.name if user else f"User {user_id}",
            "user_id": user_id,
            "age": user.age if user else "-",
            "weight": user.weight if user else "-",
            "goal": goal,
            "intensity": user.intensity if user else "-",
            "workout_plan": updated,
            "nutrition_tip": nutrition_tip,
            "message": "Your plan has been updated based on your feedback!",
        },
    )


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request):
    """Admin panel - view all users and their plans."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        user_data = []
        for user in users:
            plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user.id).first()
            user_data.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "age": user.age,
                    "weight": user.weight,
                    "goal": user.goal,
                    "intensity": user.intensity,
                    "original_plan": plan.original_plan if plan else "N/A",
                    "updated_plan": plan.updated_plan
                    if plan and plan.updated_plan
                    else "Not updated",
                }
            )
    finally:
        db.close()

    return templates.TemplateResponse(
        request, "all_users.html", {"users": user_data}
    )


# -------------------------------------------------------------------
# API Routes (JSON)
# -------------------------------------------------------------------
@router.post("/api/generate-workout/gemini")
async def generate_gemini_workout(request: WorkoutRequest):
    """API: Generate workout using Gemini Pro."""
    try:
        result = generate_workout_gemini(
            {"goal": request.goal, "intensity": request.intensity}
        )
        return {"model": "gemini-pro", "workout_plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/nutrition-tip")
def get_flash_tip(goal: str):
    """API: Generate nutrition tip using Gemini Flash."""
    tip = generate_nutrition_tip_with_flash(goal)
    return {"goal": goal, "nutrition_tip": tip}


@router.post("/api/generate-plan")
def generate_plan(user_data: UserInput):
    """API: Save user info & generate plan."""
    try:
        save_user(
            user_id=user_data.user_id,
            name=user_data.username,
            age=user_data.age,
            weight=user_data.weight,
            goal=user_data.goal,
            intensity=user_data.intensity,
        )
        plan = generate_workout_gemini(
            {"goal": user_data.goal, "intensity": user_data.intensity}
        )
        save_plan(user_data.user_id, plan)
        return {
            "message": "Workout plan generated and saved successfully!",
            "workout_plan": plan,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")


@router.post("/api/update-plan/{user_id}", response_model=dict)
def update_user_plan(user_id: int, data: FeedbackRequest):
    """API: Update workout plan based on user feedback."""
    original = get_original_plan(user_id)
    if not original:
        return {"error": "Original plan not found for this user."}
    updated = update_workout_plan(original, data.feedback)
    update_plan(user_id, updated)
    return {"updated_plan": updated}