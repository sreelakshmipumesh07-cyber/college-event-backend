from flask import Blueprint, request, jsonify
from db import query_db
from mysql.connector import Error

venues_bp = Blueprint("venues", __name__, url_prefix="/venues")


# ── GET /venues ───────────────────────────────────────────────
@venues_bp.get("/")
def get_all_venues():
    """Fetch all venues from the database and return them as JSON.
    Handles database errors and returns a 500 status code on failure.
    """
    try:
        rows = query_db("SELECT * FROM VENUE ORDER BY Venue_ID")
        return jsonify(rows), 200
    except Error as e:
        # Unexpected DB error – respond with a generic server error
        return jsonify({"error": str(e)}), 500


# ── GET /venues/<id> ──────────────────────────────────────────
@venues_bp.get("/<int:venue_id>")
def get_venue(venue_id):
    row = query_db(
        "SELECT * FROM VENUE WHERE Venue_ID = %s", (venue_id,), fetchone=True
    )
    if not row:
        return jsonify({"error": "Venue not found"}), 404
    return jsonify(row), 200


# ── POST /venues ──────────────────────────────────────────────
@venues_bp.post("/")
def create_venue():
    data = request.get_json()
    if not data.get("venue_name") or not data.get("location"):
        return jsonify({"error": "venue_name and location are required"}), 400

    new_id = query_db(
        "INSERT INTO VENUE (Venue_Name, Location) VALUES (%s, %s)",
        (data["venue_name"], data["location"]),
        commit=True,
    )
    return jsonify({"message": "Venue created", "Venue_ID": new_id}), 201


# ── PUT /venues/<id> ──────────────────────────────────────────
@venues_bp.put("/<int:venue_id>")
def update_venue(venue_id):
    data = request.get_json()
    fields = {"venue_name": "Venue_Name", "location": "Location"}
    updates = [(fields[k], v) for k, v in data.items() if k in fields]
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    set_clause = ", ".join(f"{col} = %s" for col, _ in updates)
    values = [v for _, v in updates] + [venue_id]

    affected = query_db(
        f"UPDATE VENUE SET {set_clause} WHERE Venue_ID = %s",
        tuple(values), commit=True,
    )
    if affected == 0:
        return jsonify({"error": "Venue not found"}), 404
    return jsonify({"message": "Venue updated"}), 200


# ── DELETE /venues/<id> ───────────────────────────────────────
@venues_bp.delete("/<int:venue_id>")
def delete_venue(venue_id):
    try:
        affected = query_db(
            "DELETE FROM VENUE WHERE Venue_ID = %s", (venue_id,), commit=True
        )
        if affected == 0:
            return jsonify({"error": "Venue not found"}), 404
        return jsonify({"message": "Venue deleted"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 409


# ── GET /venues/<id>/events ───────────────────────────────────
@venues_bp.get("/<int:venue_id>/events")
def events_at_venue(venue_id):
    rows = query_db(
        """SELECT e.Event_ID, e.Event_name, e.Date, e.Time,
                  e.Capacity, e.Remaining_Seats, e.Event_Type
           FROM EVENT e
           WHERE e.Venue_ID = %s
           ORDER BY e.Date""",
        (venue_id,),
    )
    return jsonify(rows), 200
