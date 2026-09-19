from flask import Blueprint, request, jsonify
from db import query_db
from mysql.connector import Error

registrations_bp = Blueprint("registrations", __name__, url_prefix="/registrations")

VALID_STATUSES = {"Pending", "Confirmed", "Cancelled"}


# ── GET /registrations ────────────────────────────────────────
@registrations_bp.get("/")
def get_all_registrations():
    """Fetch all registrations (with related student, event, and payment info) and return them as JSON.
    Handles database errors and returns a 500 status code on failure.
    """
    try:
        rows = query_db(
            """SELECT r.Registration_ID, r.Registration_Date, r.Status,
                      s.Student_ID, s.Name AS Student_Name,
                      e.Event_ID,   e.Event_name,
                      p.Payment_ID, p.Amount, p.Payment_Method
               FROM REGISTRATION r
               JOIN STUDENT s ON r.Student_ID = s.Student_ID
               JOIN EVENT   e ON r.Event_ID   = e.Event_ID
               LEFT JOIN PAYMENT p ON r.Registration_ID = p.Registration_ID
               ORDER BY r.Registration_ID"""
        )
        return jsonify(rows), 200
    except Error as e:
        # Unexpected DB error – respond with a generic server error
        return jsonify({"error": str(e)}), 500


# ── GET /registrations/<id> ───────────────────────────────────
@registrations_bp.get("/<int:reg_id>")
def get_registration(reg_id):
    row = query_db(
        """SELECT r.*, s.Name AS Student_Name, s.Email AS Student_Email,
                  e.Event_name, e.Date AS Event_Date, e.Event_Type,
                  p.Amount, p.Payment_Method, p.Payment_Date
           FROM REGISTRATION r
           JOIN STUDENT s ON r.Student_ID = s.Student_ID
           JOIN EVENT   e ON r.Event_ID   = e.Event_ID
           LEFT JOIN PAYMENT p ON r.Registration_ID = p.Registration_ID
           WHERE r.Registration_ID = %s""",
        (reg_id,), fetchone=True,
    )
    if not row:
        return jsonify({"error": "Registration not found"}), 404
    return jsonify(row), 200


# ── POST /registrations ───────────────────────────────────────
@registrations_bp.post("/")
def create_registration():
    """Register a student for an event. Trigger handles seat decrement."""
    data = request.get_json()
    if not data.get("student_id") or not data.get("event_id"):
        return jsonify({"error": "student_id and event_id are required"}), 400

    student_id = int(data["student_id"])
    event_id   = int(data["event_id"])

    # Check student exists
    if not query_db("SELECT 1 FROM STUDENT WHERE Student_ID=%s", (student_id,), fetchone=True):
        return jsonify({"error": "Student not found"}), 404

    # Check event exists and has seats
    event = query_db(
        "SELECT Remaining_Seats FROM EVENT WHERE Event_ID=%s", (event_id,), fetchone=True
    )
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event["Remaining_Seats"] <= 0:
        return jsonify({"error": "No remaining seats for this event"}), 409

    try:
        new_id = query_db(
            """INSERT INTO REGISTRATION (Registration_Date, Status, Student_ID, Event_ID)
               VALUES (CURDATE(), %s, %s, %s)""",
            (data.get("status", "Pending"), student_id, event_id),
            commit=True,
        )
        return jsonify({"message": "Registered successfully", "Registration_ID": new_id}), 201
    except Error as e:
        if "uq_student_event" in str(e) or "Duplicate" in str(e):
            return jsonify({"error": "Student is already registered for this event"}), 409
        return jsonify({"error": str(e)}), 500


# ── PUT /registrations/<id> ───────────────────────────────────
@registrations_bp.put("/<int:reg_id>")
def update_registration(reg_id):
    """Update status (Pending/Confirmed/Cancelled). Trigger handles seats."""
    data = request.get_json()
    status = data.get("status")
    if not status or status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {VALID_STATUSES}"}), 400

    try:
        affected = query_db(
            "UPDATE REGISTRATION SET Status = %s WHERE Registration_ID = %s",
            (status, reg_id), commit=True,
        )
        if affected == 0:
            return jsonify({"error": "Registration not found"}), 404
        return jsonify({"message": f"Registration status updated to '{status}'"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ── DELETE /registrations/<id> ────────────────────────────────
@registrations_bp.delete("/<int:reg_id>")
def delete_registration(reg_id):
    """Delete a registration. Trigger handles seat restoration."""
    affected = query_db(
        "DELETE FROM REGISTRATION WHERE Registration_ID = %s", (reg_id,), commit=True
    )
    if affected == 0:
        return jsonify({"error": "Registration not found"}), 404
    return jsonify({"message": "Registration deleted and seat restored"}), 200


# ── GET /registrations/student/<student_id> ───────────────────
@registrations_bp.get("/student/<int:student_id>")
def registrations_by_student(student_id):
    rows = query_db(
        """SELECT r.Registration_ID, r.Registration_Date, r.Status,
                  e.Event_name, e.Date AS Event_Date, e.Event_Type,
                  e.Registration_fee,
                  p.Amount, p.Payment_Method
           FROM REGISTRATION r
           JOIN EVENT e ON r.Event_ID = e.Event_ID
           LEFT JOIN PAYMENT p ON r.Registration_ID = p.Registration_ID
           WHERE r.Student_ID = %s
           ORDER BY r.Registration_Date DESC""",
        (student_id,),
    )
    return jsonify(rows), 200


# ── GET /registrations/event/<event_id> ───────────────────────
@registrations_bp.get("/event/<int:event_id>")
def registrations_by_event(event_id):
    rows = query_db(
        """SELECT r.Registration_ID, r.Registration_Date, r.Status,
                  s.Student_ID, s.Name AS Student_Name,
                  s.Email, s.Department, s.Year,
                  p.Amount, p.Payment_Method
           FROM REGISTRATION r
           JOIN STUDENT s ON r.Student_ID = s.Student_ID
           LEFT JOIN PAYMENT p ON r.Registration_ID = p.Registration_ID
           WHERE r.Event_ID = %s
           ORDER BY r.Registration_Date""",
        (event_id,),
    )
    return jsonify(rows), 200
