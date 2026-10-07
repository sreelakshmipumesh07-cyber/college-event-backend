from flask import Blueprint, render_template, request, redirect
from db import get_connection

registrations_bp = Blueprint(
    "registrations",
    __name__
)


@registrations_bp.route("/register", methods=["GET", "POST"])
def register():

    event = None

    event_id = request.args.get("event_id")

    if not event_id:
        return redirect("/events-page")

    conn = get_connection()

    if conn is None:
        return "Database connection failed"

    cursor = conn.cursor(dictionary=True)

    try:

        print("===================================")
        print("REGISTER PAGE")
        print("Event ID received:", event_id)
        print("===================================")

        # Get event
        cursor.execute(
            """
            SELECT *
            FROM event
            WHERE Event_ID = %s
            """,
            (event_id,)
        )

        event = cursor.fetchone()

        print("Event found:", event)

        if not event:

            return render_template(
                "register.html",
                event=None,
                error="Event ID does not exist in the database."
            )

        # -----------------------------------------
        # POST
        # -----------------------------------------

        if request.method == "POST":

            student_id = request.form.get("student_id")
            name = request.form.get("name")
            email = request.form.get("email")
            phone = request.form.get("phone")
            class_id = request.form.get("class_id")
            department = request.form.get("department")

            # Validation

            if not student_id:
                return render_template(
                    "register.html",
                    event=event,
                    error="Student ID is required."
                )

            if not name:
                return render_template(
                    "register.html",
                    event=event,
                    error="Student name is required."
                )

            if not email:
                return render_template(
                    "register.html",
                    event=event,
                    error="Email is required."
                )

            if not phone:
                return render_template(
                    "register.html",
                    event=event,
                    error="Phone number is required."
                )

            if not class_id:
                return render_template(
                    "register.html",
                    event=event,
                    error="Class ID is required."
                )

            if not department:
                return render_template(
                    "register.html",
                    event=event,
                    error="Department is required."
                )

            # -----------------------------------------
            # CHECK STUDENT
            # -----------------------------------------

            cursor.execute(
                """
                SELECT Student_ID
                FROM student
                WHERE Student_ID = %s
                """,
                (student_id,)
            )

            existing_student = cursor.fetchone()

            # -----------------------------------------
            # INSERT STUDENT
            # -----------------------------------------

            if not existing_student:

                cursor.execute(
                    """
                    INSERT INTO student
                    (
                        Student_ID,
                        Name,
                        Email,
                        Phone,
                        Class_ID,
                        Department
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        student_id,
                        name,
                        email,
                        phone,
                        class_id,
                        department
                    )
                )

            # -----------------------------------------
            # CHECK DUPLICATE REGISTRATION
            # -----------------------------------------

            cursor.execute(
                """
                SELECT *
                FROM registration
                WHERE Student_ID = %s
                AND Event_ID = %s
                """,
                (
                    student_id,
                    event_id
                )
            )

            existing_registration = cursor.fetchone()

            if existing_registration:

                conn.rollback()

                return render_template(
                    "register.html",
                    event=event,
                    error="You are already registered for this event."
                )

            # -----------------------------------------
            # CHECK SEATS
            # -----------------------------------------

            if "Remaining_Seats" in event:

                if event["Remaining_Seats"] is not None:

                    if int(event["Remaining_Seats"]) <= 0:

                        conn.rollback()

                        return render_template(
                            "register.html",
                            event=event,
                            error="Sorry, this event is full."
                        )

            # -----------------------------------------
            # INSERT REGISTRATION
            # -----------------------------------------

            cursor.execute(
                """
                INSERT INTO registration
                (
                    Student_ID,
                    Event_ID
                )
                VALUES
                (
                    %s,
                    %s
                )
                """,
                (
                    student_id,
                    event_id
                )
            )

            # -----------------------------------------
            # UPDATE SEATS
            # -----------------------------------------

            if "Remaining_Seats" in event:

                cursor.execute(
                    """
                    UPDATE event
                    SET Remaining_Seats = Remaining_Seats - 1
                    WHERE Event_ID = %s
                    AND Remaining_Seats > 0
                    """,
                    (event_id,)
                )

            # Save

            conn.commit()

            return redirect("/registrations-page")

        # -----------------------------------------
        # GET
        # -----------------------------------------

        return render_template(
            "register.html",
            event=event
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print("===================================")
        print("REGISTRATION DATABASE ERROR")
        print(e)
        print("===================================")

        return render_template(
            "register.html",
            event=event,
            error=str(e)
        )

    finally:

        cursor.close()
        conn.close()