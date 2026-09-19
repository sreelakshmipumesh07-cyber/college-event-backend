from flask import Blueprint, request, jsonify
from db import query_db
from mysql.connector import Error

events_bp = Blueprint("events", __name__, url_prefix="/events")


# ── GET /events ───────────────────────────────────────────────
@events_bp.get("/")
def get_all_events():
    """Return all events joined with venue and organizer info.
    Convert MySQL TIME values to string for JSON serialization.
    """
    rows = query_db(
        """SELECT e.*, v.Venue_Name, v.Location,
                  o.Name AS Organizer_Name, o.Department AS Organizer_Dept
               FROM EVENT e
               JOIN VENUE     v ON e.Venue_ID     = v.Venue_ID
               JOIN ORGANIZER o ON e.Organizer_ID = o.Organizer_ID
               ORDER BY e.Date"""
    )
    # Convert any TIME or timedelta objects to plain strings so jsonify works
    import datetime
    for row in rows:
        if "Time" in row and isinstance(row["Time"], (datetime.time, datetime.timedelta)):
            row["Time"] = str(row["Time"])
    return jsonify(rows), 200


# ── GET /events/summary ───────────────────────────────────────
@events_bp.get("/summary")
def events_summary():
    """Return event_summary_view (includes registration count)."""
    rows = query_db("SELECT * FROM event_summary_view ORDER BY Date")
    return jsonify(rows), 200


# ── GET /events/<id> ──────────────────────────────────────────
@events_bp.get("/<int:event_id>")
def get_event(event_id):
    row = query_db(
        """SELECT e.*, v.Venue_Name, v.Location,
                  o.Name AS Organizer_Name, o.Email AS Organizer_Email,
                  o.Department AS Organizer_Dept
           FROM EVENT e
           JOIN VENUE     v ON e.Venue_ID     = v.Venue_ID
           JOIN ORGANIZER o ON e.Organizer_ID = o.Organizer_ID
           WHERE e.Event_ID = %s""",
        (event_id,), fetchone=True,
    )
    if not row:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(row), 200


# ── POST /events ──────────────────────────────────────────────
@events_bp.post("/")
def create_event():
    data = request.get_json()
    required = ["event_name", "date", "time", "capacity",
                "event_type", "venue_id", "organizer_id"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    capacity = int(data["capacity"])
    try:
        new_id = query_db(
            """INSERT INTO EVENT
                (Event_name, Description, Date, Time, Registration_fee,
                 Capacity, Remaining_Seats, Event_Type, Venue_ID, Organizer_ID)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                data["event_name"],
                data.get("description", ""),
                data["date"],
                data["time"],
                float(data.get("registration_fee", 0.0)),
                capacity,
                capacity,                          # Remaining_Seats == Capacity at start
                data["event_type"],
                int(data["venue_id"]),
                int(data["organizer_id"]),
            ),
            commit=True,
        )
        return jsonify({"message": "Event created", "Event_ID": new_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 409


# ── PUT /events/<id> ──────────────────────────────────────────
@events_bp.put("/<int:event_id>")
def update_event(event_id):
    data = request.get_json()
    field_map = {
        "event_name":       "Event_name",
        "description":      "Description",
        "date":             "Date",
        "time":             "Time",
        "registration_fee": "Registration_fee",
        "capacity":         "Capacity",
        "event_type":       "Event_Type",
        "venue_id":         "Venue_ID",
        "organizer_id":     "Organizer_ID",
    }
    updates = [(field_map[k], v) for k, v in data.items() if k in field_map]
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    set_clause = ", ".join(f"{col} = %s" for col, _ in updates)
    values = [v for _, v in updates] + [event_id]

    try:
        affected = query_db(
            f"UPDATE EVENT SET {set_clause} WHERE Event_ID = %s",
            tuple(values), commit=True,
        )
        if affected == 0:
            return jsonify({"error": "Event not found"}), 404
        return jsonify({"message": "Event updated"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 409


# ── DELETE /events/<id> ───────────────────────────────────────
@events_bp.delete("/<int:event_id>")
def delete_event(event_id):
    try:
        affected = query_db(
            "DELETE FROM EVENT WHERE Event_ID = %s", (event_id,), commit=True
        )
        if affected == 0:
            return jsonify({"error": "Event not found"}), 404
        return jsonify({"message": "Event deleted"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 409


# ── GET /events/<id>/students ─────────────────────────────────
@events_bp.get("/<int:event_id>/students")
def event_students(event_id):
    """All students registered for a specific event."""
    rows = query_db(
        """SELECT s.Student_ID, s.Name, s.Email, s.Department, s.Year,
                  r.Registration_ID, r.Status, r.Registration_Date
           FROM REGISTRATION r
           JOIN STUDENT s ON r.Student_ID = s.Student_ID
           WHERE r.Event_ID = %s
           ORDER BY r.Registration_Date""",
        (event_id,),
    )
    return jsonify(rows), 200


# ── GET /events/type/<type> ───────────────────────────────────
@events_bp.get("/type/<string:event_type>")
def events_by_type(event_type):
    rows = query_db(
        """SELECT e.*, v.Venue_Name, o.Name AS Organizer_Name
           FROM EVENT e
           JOIN VENUE     v ON e.Venue_ID     = v.Venue_ID
           JOIN ORGANIZER o ON e.Organizer_ID = o.Organizer_ID
           WHERE e.Event_Type = %s
           ORDER BY e.Date""",
        (event_type,),
    )
    return jsonify(rows), 200
