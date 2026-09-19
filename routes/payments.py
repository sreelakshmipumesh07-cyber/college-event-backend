from flask import Blueprint, request, jsonify
from db import query_db
from mysql.connector import Error

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")

VALID_METHODS = {"Cash", "UPI", "Card", "Net Banking"}


# ── GET /payments ─────────────────────────────────────────────
@payments_bp.get("/")
def get_all_payments():
    """Fetch all payments (including student and event info) and return them as JSON.
    Handles database errors and returns a 500 status code on failure.
    """
    try:
        rows = query_db(
            """SELECT p.*, s.Name AS Student_Name, e.Event_name
               FROM PAYMENT p
               JOIN REGISTRATION r ON p.Registration_ID = r.Registration_ID
               JOIN STUDENT       s ON r.Student_ID      = s.Student_ID
               JOIN EVENT         e ON r.Event_ID         = e.Event_ID
               ORDER BY p.Payment_Date DESC"""
        )
        return jsonify(rows), 200
    except Error as e:
        # Unexpected DB error – respond with a generic server error
        return jsonify({"error": str(e)}), 500


# ── GET /payments/<id> ────────────────────────────────────────
@payments_bp.get("/<int:payment_id>")
def get_payment(payment_id):
    row = query_db(
        """SELECT p.*, s.Name AS Student_Name, s.Email AS Student_Email,
                  e.Event_name, e.Date AS Event_Date
           FROM PAYMENT p
           JOIN REGISTRATION r ON p.Registration_ID = r.Registration_ID
           JOIN STUDENT       s ON r.Student_ID      = s.Student_ID
           JOIN EVENT         e ON r.Event_ID         = e.Event_ID
           WHERE p.Payment_ID = %s""",
        (payment_id,), fetchone=True,
    )
    if not row:
        return jsonify({"error": "Payment not found"}), 404
    return jsonify(row), 200


# ── POST /payments ────────────────────────────────────────────
@payments_bp.post("/")
def create_payment():
    data = request.get_json()
    required = ["registration_id", "amount", "payment_method"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    if data["payment_method"] not in VALID_METHODS:
        return jsonify({"error": f"payment_method must be one of {VALID_METHODS}"}), 400

    # Confirm the registration exists
    reg = query_db(
        "SELECT Registration_ID FROM REGISTRATION WHERE Registration_ID = %s",
        (int(data["registration_id"]),), fetchone=True,
    )
    if not reg:
        return jsonify({"error": "Registration not found"}), 404

    try:
        new_id = query_db(
            """INSERT INTO PAYMENT (Amount, Payment_Date, Payment_Method, Registration_ID)
               VALUES (%s, CURDATE(), %s, %s)""",
            (float(data["amount"]), data["payment_method"], int(data["registration_id"])),
            commit=True,
        )
        return jsonify({"message": "Payment recorded", "Payment_ID": new_id}), 201
    except Error as e:
        if "Duplicate" in str(e) or "unique" in str(e).lower():
            return jsonify({"error": "Payment already exists for this registration"}), 409
        return jsonify({"error": str(e)}), 500


# ── GET /payments/registration/<reg_id> ───────────────────────
@payments_bp.get("/registration/<int:reg_id>")
def payment_by_registration(reg_id):
    row = query_db(
        "SELECT * FROM PAYMENT WHERE Registration_ID = %s", (reg_id,), fetchone=True
    )
    if not row:
        return jsonify({"error": "No payment found for this registration"}), 404
    return jsonify(row), 200


# ── GET /payments/event/<event_id>/total ──────────────────────
@payments_bp.get("/event/<int:event_id>/total")
def total_revenue_for_event(event_id):
    """Total revenue collected for a specific event."""
    row = query_db(
        """SELECT e.Event_name,
                  COUNT(p.Payment_ID)  AS Total_Payments,
                  SUM(p.Amount)        AS Total_Revenue
           FROM EVENT e
           LEFT JOIN REGISTRATION r ON e.Event_ID = r.Event_ID
           LEFT JOIN PAYMENT      p ON r.Registration_ID = p.Registration_ID
           WHERE e.Event_ID = %s
           GROUP BY e.Event_ID, e.Event_name""",
        (event_id,), fetchone=True,
    )
    if not row:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(row), 200


# ── DELETE /payments/<id> ─────────────────────────────────────
@payments_bp.delete("/<int:payment_id>")
def delete_payment(payment_id):
    affected = query_db(
        "DELETE FROM PAYMENT WHERE Payment_ID = %s", (payment_id,), commit=True
    )
    if affected == 0:
        return jsonify({"error": "Payment not found"}), 404
    return jsonify({"message": "Payment deleted"}), 200
