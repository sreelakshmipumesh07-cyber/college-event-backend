from flask import Blueprint, request, jsonify
from db import query_db
from mysql.connector import Error

organizers_bp = Blueprint("organizers", __name__, url_prefix="/organizers")


# ── GET /organizers ───────────────────────────────────────────
@organizers_bp.get("/")
def get_all_organizers():
    """Fetch all organizers from the database and return them as JSON.
    Handles database errors and returns a 500 status code on failure.
    """
    try:
        rows = query_db("SELECT * FROM ORGANIZER ORDER BY Organizer_ID")
        return jsonify(rows), 200
    except Error as e:
        # Unexpected DB error – respond with a generic server error
        return jsonify({"error": str(e)}), 500


# ── GET /organizers/<id> ──────────────────────────────────────
@organizers_bp.get("/<int:organizer_id>")
def get_organizer(organizer_id):
    row = query_db(
        "SELECT * FROM ORGANIZER WHERE Organizer_ID = %s",
        (organizer_id,), fetchone=True,
    )
    if not row:
        return jsonify({"error": "Organizer not found"}), 404
    return jsonify(row), 200


# ── POST /organizers ──────────────────────────────────────────
@organizers_bp.post("/")
def create_organizer():
    data = request.get_json()
    required = ["name", "email", "phone", "department"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        new_id = query_db(
            """INSERT INTO ORGANIZER (Name, Email, Phone, Department)
               VALUES (%s, %s, %s, %s)""",
            (data["name"], data["email"], data["phone"], data["department"]),
            commit=True,
        )
        return jsonify({"message": "Organizer created", "Organizer_ID": new_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 409


# ── PUT /organizers/<id> ──────────────────────────────────────
@organizers_bp.put("/<int:organizer_id>")
def update_organizer(organizer_id):
    data = request.get_json()
    fields = {
        "name": "Name", "email": "Email",
        "phone": "Phone", "department": "Department",
    }
    updates = [(fields[k], v) for k, v in data.items() if k in fields]
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    set_clause = ", ".join(f"{col} = %s" for col, _ in updates)
    values = [v for _, v in updates] + [organizer_id]

    try:
        affected = query_db(
            f"UPDATE ORGANIZER SET {set_clause} WHERE Organizer_ID = %s",
            tuple(values), commit=True,
        )
        if affected == 0:
            return jsonify({"error": "Organizer not found"}), 404
        return jsonify({"message": "Organizer updated"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 409


# ── DELETE /organizers/<id> ───────────────────────────────────
@organizers_bp.delete("/<int:organizer_id>")
def delete_organizer(organizer_id):
    try:
        affected = query_db(
            "DELETE FROM ORGANIZER WHERE Organizer_ID = %s",
            (organizer_id,), commit=True,
        )
        if affected == 0:
            return jsonify({"error": "Organizer not found"}), 404
        return jsonify({"message": "Organizer deleted"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 409


# ── GET /organizers/<id>/events ───────────────────────────────
@organizers_bp.get("/<int:organizer_id>/events")
def organizer_events(organizer_id):
    rows = query_db(
        """SELECT e.Event_ID, e.Event_name, e.Date, e.Time,
                  e.Capacity, e.Remaining_Seats, e.Event_Type,
                  v.Venue_Name
           FROM EVENT e
           JOIN VENUE v ON e.Venue_ID = v.Venue_ID
           WHERE e.Organizer_ID = %s
           ORDER BY e.Date""",
        (organizer_id,),
    )
    return jsonify(rows), 200
