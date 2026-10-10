
from flask import Blueprint, render_template, request, redirect, url_for
from db import get_connection

registrations_bp = Blueprint("registrations", __name__)


@registrations_bp.route("/register", methods=["GET", "POST"])
def register():
    event_id = request.args.get("event_id")

    if not event_id:
        return redirect("/events-page")

    conn = get_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)
    event = None

    try:
        # Fetch event details
        cursor.execute(
            "SELECT * FROM event WHERE Event_ID = %s",
            (event_id,)
        )
        event = cursor.fetchone()

        if not event:
            return render_template(
                "register.html",
                event=None,
                error="Event not found."
            )

        if request.method == "GET":
            return render_template("register.html", event=event)

        # Get student details from the form
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()

        if not all([name, phone, email, department, year]):
            return render_template(
                "register.html",
                event=event,
                error="Please complete all student details."
            )

        # Validate study year
        try:
            year = int(year)

            if year < 1 or year > 6:
                raise ValueError

        except ValueError:
            return render_template(
                "register.html",
                event=event,
                error="Enter a valid study year."
            )

        # Clear the transaction created by the earlier SELECT.
        # Then begin a fresh transaction for registration.
        conn.rollback()
        conn.start_transaction()

        # Lock the event row to prevent overbooking
        cursor.execute(
            """
            SELECT * FROM event
            WHERE Event_ID = %s
            FOR UPDATE
            """,
            (event_id,)
        )
        event = cursor.fetchone()

        if not event or event["Remaining_Seats"] <= 0:
            conn.rollback()
            return render_template(
                "register.html",
                event=event,
                error="This event is full or unavailable."
            )

        # Find an existing student using email or phone
        cursor.execute(
            """
            SELECT Student_ID, Email, Phone
            FROM student
            WHERE Email = %s OR Phone = %s
            """,
            (email, phone)
        )
        student_rows = cursor.fetchall()

        if len(student_rows) > 1:
            conn.rollback()
            return render_template(
                "register.html",
                event=event,
                error=(
                    "That email and phone belong to "
                    "different student records."
                )
            )

        if student_rows:
            student = student_rows[0]

            # Prevent using an existing student's email with another phone,
            # or an existing phone with another email.
            if student["Email"] != email or student["Phone"] != phone:
                conn.rollback()
                return render_template(
                    "register.html",
                    event=event,
                    error=(
                        "The email or phone already belongs to "
                        "another student record. Please check your details."
                    )
                )

            student_id = student["Student_ID"]

        else:
            # Create a new student
            cursor.execute(
                """
                INSERT INTO student
                    (Name, Phone, Email, Department, Year)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, phone, email, department, year)
            )

            student_id = cursor.lastrowid

        # Prevent duplicate registration
        cursor.execute(
            """
            SELECT Registration_ID
            FROM registration
            WHERE Student_ID = %s AND Event_ID = %s
            """,
            (student_id, event_id)
        )

        if cursor.fetchone():
            conn.rollback()
            return render_template(
                "register.html",
                event=event,
                error="This student is already registered for this event."
            )

        # Create registration
        fee = event["Registration_fee"]

        status = "Confirmed" if fee == 0 else "Pending"

        cursor.execute(
            """
            INSERT INTO registration
                (Status, Student_ID, Event_ID)
            VALUES (%s, %s, %s)
            """,
            (status, student_id, event_id)
        )

        registration_id = cursor.lastrowid

        # Reduce the available seat count
        cursor.execute(
            """
            UPDATE event
            SET Remaining_Seats = Remaining_Seats - 1
            WHERE Event_ID = %s
            """,
            (event_id,)
        )

        # Save all registration changes
        conn.commit()

        # Redirect based on registration fee
        if fee == 0:
            return redirect(
                url_for(
                    "payments.registration_success",
                    registration_id=registration_id
                )
            )

        return redirect(
            url_for(
                "payments.payment_page",
                registration_id=registration_id
            )
        )

    except Exception as e:
        conn.rollback()
        print("Registration error:", e)

        return render_template(
            "register.html",
            event=event,
            error="Registration failed: " + str(e)
        ), 500

    finally:
        cursor.close()
        conn.close()
