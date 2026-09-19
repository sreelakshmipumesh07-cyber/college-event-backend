from flask import Blueprint, request, jsonify
from db import query_db
from mysql.connector import Error

students_bp = Blueprint("students", __name__, url_prefix="/students")


# ── GET /students ─────────────────────────────────────────────
@students_bp.get("/")
def get_all_students():
    """Fetch all students from the database and return them as JSON.
    Handles database errors and returns a 500 status code on failure.
    """
    try:
        rows = query_db("SELECT * FROM STUDENT ORDER BY Student_ID")
        return jsonify(rows), 200
    except Error as e:
        # Unexpected DB error – respond with a generic server error
        return jsonify({"error": str(e)}), 500


# ── GET /students/<id> ────────────────────────────────────────
@students_bp.get("/<int:student_id>")
def get_student(student_id):
    row = query_db(
        "SELECT * FROM STUDENT WHERE Student_ID = %s", (student_id,), fetchone=True
    )
    if not row:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(row), 200


# ── POST /students ────────────────────────────────────────────
@students_bp.post("/")
def create_student():
    data = request.get_json()
    required = ["name", "phone", "email", "department", "year"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        new_id = query_db(
            """INSERT INTO STUDENT (Name, Phone, Email, Department, Year)
               VALUES (%s, %s, %s, %s, %s)""",
            (data["name"], data["phone"], data["email"],
             data["department"], data["year"]),
            commit=True,
        )
        return jsonify({"message": "Student created", "Student_ID": new_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 409


# ── PUT /students/<id> ────────────────────────────────────────
@students_bp.put("/<int:student_id>")
def update_student(student_id):
    data = request.get_json()
    fields = {
        "name": "Name", "phone": "Phone", "email": "Email",
        "department": "Department", "year": "Year",
    }
    updates = [(fields[k], v) for k, v in data.items() if k in fields]
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    set_clause = ", ".join(f"{col} = %s" for col, _ in updates)
    values = [v for _, v in updates] + [student_id]

    try:
        affected = query_db(
            f"UPDATE STUDENT SET {set_clause} WHERE Student_ID = %s",
            tuple(values), commit=True,
        )
        if affected == 0:
            return jsonify({"error": "Student not found"}), 404
        return jsonify({"message": "Student updated"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 409


# ── DELETE /students/<id> ─────────────────────────────────────
@students_bp.delete("/<int:student_id>")
def delete_student(student_id):
    affected = query_db(
        "DELETE FROM STUDENT WHERE Student_ID = %s", (student_id,), commit=True
    )
    if affected == 0:
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"message": "Student deleted"}), 200


# ── GET /students/<id>/registrations ─────────────────────────
@students_bp.get("/<int:student_id>/registrations")
def student_registrations(student_id):
    rows = query_db(
        """SELECT r.Registration_ID, r.Registration_Date, r.Status,
                  e.Event_name, e.Date AS Event_Date, e.Event_Type,
                  p.Amount, p.Payment_Method
           FROM REGISTRATION r
           JOIN EVENT e ON r.Event_ID = e.Event_ID
           LEFT JOIN PAYMENT p ON r.Registration_ID = p.Registration_ID
           WHERE r.Student_ID = %s
           ORDER BY r.Registration_Date DESC""",
        (student_id,),
    )
    return jsonify(rows), 200
