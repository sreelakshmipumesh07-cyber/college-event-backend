
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

    cursor = None
    event = None

    try:
        cursor = conn.cursor(dictionary=True)

        # Get event details
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

        # Display registration form
        if request.method == "GET":
            return render_template(
                "register.html",
                event=event
            )

        # Read student details
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()

        # Validate required fields
        if not all([name, phone, email, department, year]):
            print("DEBUG: Missing student details")
            print("Name:", repr(name))
            print("Phone:", repr(phone))
            print("Email:", repr(email))
            print("Department:", repr(department))
            print("Year:", repr(year))

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

        # Validate registration fee
        fee = event.get("Registration_fee")

        if fee is None:
            return render_template(
                "register.html",
                event=event,
                error="The registration fee is missing for this event."
            )

        # End the initial read transaction
        conn.rollback()

        # Lock the event row to prevent overbooking
        cursor.execute(
            """
            SELECT *
            FROM event
            WHERE Event_ID = %s
            FOR UPDATE
            """,
            (event_id,)
        )
        event = cursor.fetchone()

        if not event:
            conn.rollback()
            return render_template(
                "register.html",
                event=None,
                error="Event not found."
            )

        if (
            event["Remaining_Seats"] is None
            or event["Remaining_Seats"] <= 0
        ):
            conn.rollback()
            return render_template(
                "register.html",
                event=event,
                error="This event is full or unavailable."
            )

        # Check whether the email or phone already exists
        cursor.execute(
            """
            SELECT Student_ID, Name, Email, Phone
            FROM student
            WHERE Email = %s OR Phone = %s
            """,
            (email, phone)
        )
        student_rows = cursor.fetchall()

        # Email and phone must belong to the same student
        if len(student_rows) > 1:
            conn.rollback()
            return render_template(
                "register.html",
                event=event,
                error=(
                    "That email and phone belong to different "
                    "student records. Please check your details."
                )
            )

        if student_rows:
            student = student_rows[0]

            if (
                student["Email"] != email
                or student["Phone"] != phone
            ):
                conn.rollback()
                return render_template(
                    "register.html",
                    event=event,
                    error=(
                        "The email or phone already belongs to "
                        "another student record. Please check "
                        "your details."
                    )
                )

            student_id = student["Student_ID"]

        else:
            # Create a new student record
            cursor.execute(
                """
                INSERT INTO student
                    (Name, Phone, Email, Department, Year)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, phone, email, department, year)
            )
            student_id = cursor.lastrowid

        # Prevent duplicate registration for the same event
        cursor.execute(
            """
            SELECT Registration_ID
            FROM registration
            WHERE Student_ID = %s AND Event_ID = %s
            """,
            (student_id, event_id)
        )
        existing_registration = cursor.fetchone()

        if existing_registration:
            conn.rollback()
            return render_template(
                "register.html",
                event=event,
                error="This student is already registered for this event."
            )

        # Determine registration status
        fee = event["Registration_fee"]

        if float(fee) == 0:
            status = "Confirmed"
        else:
            status = "Pending"

        # Save the registration
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
              AND Remaining_Seats > 0
            """,
            (event_id,)
        )

        if cursor.rowcount != 1:
            conn.rollback()
            return render_template(
                "register.html",
                event=event,
                error="No seats are available for this event."
            )

        # Commit registration before redirecting
        conn.commit()

        print("Registration saved successfully.")
        print("Registration ID:", registration_id)
        print("Event ID:", event_id)
        print("Registration fee:", fee)

        # Free events go directly to the success page
        if float(fee) == 0:
            print("DEBUG: Free event. Redirecting to success page.")

            return redirect(
                url_for(
                    "payments.registration_success",
                    registration_id=registration_id
                )
            )

        # Paid events go to the payment page
        print("DEBUG: Reached payment redirect")
        print("DEBUG: Registration ID:", registration_id)
        print("DEBUG: Fee:", fee)

        return redirect(
            url_for(
                "payments.payment_page",
                registration_id=registration_id
            )
        )

    except Exception as e:
        if conn:
            conn.rollback()

        print("Registration error:", repr(e))

        return render_template(
            "register.html",
            event=event,
            error="Registration failed. Please check the terminal for details."
        ), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
