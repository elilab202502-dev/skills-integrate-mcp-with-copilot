""" 
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

from .db import init_db, get_session, Activity, Participant
from .db_seed import seed_if_empty

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Initialize DB on startup
init_db()
seed_if_empty()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with get_session() as session:
        activities = session.query(Activity).all()
        result = {}
        for a in activities:
            result[a.name] = {
                "description": a.description,
                "schedule": a.schedule,
                "max_participants": a.max_participants,
                "participants": [p.user_email for p in a.participants]
            }
        return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    with get_session() as session:
        activity = session.query(Activity).filter(Activity.name == activity_name).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        # check existing
        existing = (
            session.query(Participant)
            .filter(Participant.activity_id == activity.id, Participant.user_email == email)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        # check max
        if activity.max_participants and len(activity.participants) >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        p = Participant(activity_id=activity.id, user_email=email)
        session.add(p)
        session.commit()
        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    with get_session() as session:
        activity = session.query(Activity).filter(Activity.name == activity_name).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        existing = (
            session.query(Participant)
            .filter(Participant.activity_id == activity.id, Participant.user_email == email)
            .first()
        )
        if not existing:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        session.delete(existing)
        session.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}
