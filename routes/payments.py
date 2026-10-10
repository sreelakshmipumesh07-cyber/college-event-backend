
from flask import Blueprint, render_template, request, redirect, url_for
from db import get_connection
from decimal import Decimal

payments_bp = Blueprint("payments", __name__)

ALLOWED_METHODS = {"Cash", "UPI", "Card", "Net Banking"}


@payments_bp.route("/payment/<int:registration_id>", methods=["GET", "POST"])
def payment_page(registration_id):
    conn = get_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)
    details = None

    try:
        # Get registration and event details
        cursor.execute(
            """
            SELECT r.Registration_ID, r.Status,
                   s.Name, s.Email,
                   e.Event_name, e.Registration_fee
            FROM registration r
            JOIN student s ON s.Student_ID = r.Student_ID
            JOIN event e ON e.Event_ID = r.Event_ID
            WHERE r.Registration_ID = %s
            """,
            (registration_id,)
        )

        details = cursor.fetchone()

        if not details:
            return "Registration not found.", 404

        if details["Status"] == "Confirmed":
            return redirect(
                url_for(
                    "payments.registration_success",
                    registration_id=registration_id
                )
            )

        if details["Status"] != "Pending":
            return "This registration cannot be paid for.", 400

        amount = Decimal(str(details["Registration_fee"]))

        if amount <= 0:
            return "This event does not require payment.", 400

        # Display payment page
        if request.method == "GET":
            details["Amount"] = amount
            return render_template(
                "payment.html",
                details=details
            )

        # Validate payment method
        method = request.form.get("payment_method", "").strip()

        if method not in ALLOWED_METHODS:
            details["Amount"] = amount

            return render_template(
                "payment.html",
                details=details,
                error="Please select a valid payment method."
            ), 400

        # Clear the transaction from the initial SELECT.
        # Start a fresh transaction for the payment operation.
        conn.rollback()
        conn.start_transaction()

        # Lock registration to prevent duplicate confirmation
        cursor.execute(
            """
            SELECT Status
            FROM registration
            WHERE Registration_ID = %s
            FOR UPDATE
            """,
            (registration_id,)
        )

        current = cursor.fetchone()

        if not current:
            conn.rollback()
            return "Registration not found.", 404

        if current["Status"] == "Confirmed":
            conn.rollback()

            return redirect(
                url_for(
                    "payments.registration_success",
                    registration_id=registration_id
                )
            )

        if current["Status"] != "Pending":
            conn.rollback()
            return "This registration cannot be paid for.", 400

        # Record the simulated payment
        cursor.execute(
            """
            INSERT INTO payment
                (Amount, Payment_Method, Registration_ID)
            VALUES (%s, %s, %s)
            """,
            (amount, method, registration_id)
        )

        # Confirm registration
        cursor.execute(
            """
            UPDATE registration
            SET Status = 'Confirmed'
            WHERE Registration_ID = %s
            """,
            (registration_id,)
        )

        # Save payment and confirmation together
        conn.commit()

        return redirect(
            url_for(
                "payments.registration_success",
                registration_id=registration_id
            )
        )

    except Exception as e:
        conn.rollback()
        print("Demo payment error:", e)

        if details:
            details["Amount"] = Decimal(
                str(details["Registration_fee"])
            )

        return render_template(
            "payment.html",
            details=details,
            error="Could not complete the demo payment: " + str(e)
        ), 500

    finally:
        cursor.close()
        conn.close()


@payments_bp.route("/registration-success/<int:registration_id>")
def registration_success(registration_id):
    conn = get_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT r.Registration_ID,
                   r.Registration_Date,
                   r.Status,
                   s.Name,
                   s.Email,
                   e.Event_name,
                   e.Date,
                   e.Time,
                   e.Registration_fee,
                   p.Payment_Method,
                   p.Payment_Date
            FROM registration r
            JOIN student s
                ON s.Student_ID = r.Student_ID
            JOIN event e
                ON e.Event_ID = r.Event_ID
            LEFT JOIN payment p
                ON p.Registration_ID = r.Registration_ID
            WHERE r.Registration_ID = %s
            """,
            (registration_id,)
        )

        details = cursor.fetchone()

        if not details:
            return "Registration not found.", 404

        if details["Status"] != "Confirmed":
            return "This registration is not yet confirmed.", 403

        return render_template(
            "registration_success.html",
            details=details
        )

    finally:
        cursor.close()
        conn.close()
