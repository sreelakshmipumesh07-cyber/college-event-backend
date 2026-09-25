"""
College Event Registration System - Flask Entry Point
"""

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from db import query_db

from routes.students import students_bp
from routes.events import events_bp
from routes.venues import venues_bp
from routes.organizers import organizers_bp
from routes.registrations import registrations_bp
from routes.payments import payments_bp


# ==================================================
# CREATE FLASK APPLICATION
# ==================================================

app = Flask(__name__)

# Enable CORS
CORS(app)


# ==================================================
# REGISTER BLUEPRINTS
# ==================================================

app.register_blueprint(students_bp)
app.register_blueprint(events_bp)
app.register_blueprint(venues_bp)
app.register_blueprint(organizers_bp)
app.register_blueprint(registrations_bp)
app.register_blueprint(payments_bp)


# ==================================================
# HOME PAGE
# ==================================================

@app.get("/")
def index():

    return render_template("index.html")


# ==================================================
# EVENTS PAGE
# ==================================================

@app.get("/events-page")
def events_page():

    events = query_db(
        """
        SELECT *
        FROM event
        ORDER BY Event_ID
        """
    )

    return render_template(
        "events.html",
        events=events
    )


# ==================================================
# REGISTRATIONS PAGE
# ==================================================

@app.get("/registrations")
def registrations():

    registrations = query_db(
        """
        SELECT
            r.Registration_ID,
            r.Registration_Date,
            r.Status,

            s.Student_ID,
            s.Name AS Student_Name,

            e.Event_ID,
            e.Event_name

        FROM registration r

        JOIN student s
            ON r.Student_ID = s.Student_ID

        JOIN event e
            ON r.Event_ID = e.Event_ID

        ORDER BY r.Registration_ID DESC
        """
    )

    return render_template(
        "registrations.html",
        registrations=registrations
    )


# ==================================================
# EVENT REGISTRATION
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    # --------------------------------------------------
    # GET REQUEST
    # Show selected event
    # --------------------------------------------------

    if request.method == "GET":

        event_id = request.args.get("event_id")


        # No event selected
        if not event_id:

            return """
            <!DOCTYPE html>

            <html>

            <head>
                <title>Select Event</title>
            </head>

            <body>

                <h1>
                    Please select an event first.
                </h1>

                <a href="/events-page">
                    Go to Events
                </a>

            </body>

            </html>
            """


        # Find event
        event = query_db(
            """
            SELECT *
            FROM event
            WHERE Event_ID = %s
            """,
            (event_id,),
            fetchone=True
        )


        # Event does not exist
        if not event:

            return """
            <!DOCTYPE html>

            <html>

            <head>
                <title>Event Not Found</title>
            </head>

            <body>

                <h1>
                    Event Not Found
                </h1>

                <a href="/events-page">
                    Back to Events
                </a>

            </body>

            </html>
            """


        # Show registration page
        return render_template(
            "register.html",
            event=event
        )


    # ==================================================
    # POST REQUEST
    # Save registration
    # ==================================================

    student_id = request.form.get("student_id")
    event_id = request.form.get("event_id")


    # --------------------------------------------------
    # CHECK STUDENT
    # --------------------------------------------------

    student = query_db(
        """
        SELECT *
        FROM student
        WHERE Student_ID = %s
        """,
        (student_id,),
        fetchone=True
    )


    # Student does not exist
    if not student:

        return """
        <!DOCTYPE html>

        <html>

        <head>
            <title>Student Not Found</title>
        </head>

        <body>

            <h1>
                Student Not Found
            </h1>

            <p>
                The Student ID you entered does not exist.
            </p>

            <a href="/events-page">
                Back to Events
            </a>

        </body>

        </html>
        """


    # --------------------------------------------------
    # CHECK EVENT
    # --------------------------------------------------

    event = query_db(
        """
        SELECT *
        FROM event
        WHERE Event_ID = %s
        """,
        (event_id,),
        fetchone=True
    )


    # Event does not exist
    if not event:

        return """
        <!DOCTYPE html>

        <html>

        <head>
            <title>Event Not Found</title>
        </head>

        <body>

            <h1>
                Event Not Found
            </h1>

            <a href="/events-page">
                Back to Events
            </a>

        </body>

        </html>
        """


    # --------------------------------------------------
    # CHECK REMAINING SEATS
    # --------------------------------------------------

    if event["Remaining_Seats"] <= 0:

        return """
        <!DOCTYPE html>

        <html>

        <head>
            <title>Event Full</title>
        </head>

        <body>

            <h1>
                Event Full
            </h1>

            <p>
                Sorry, this event has no remaining seats.
            </p>

            <a href="/events-page">
                Back to Events
            </a>

        </body>

        </html>
        """


    # --------------------------------------------------
    # CHECK DUPLICATE REGISTRATION
    # --------------------------------------------------

    existing = query_db(
        """
        SELECT *
        FROM registration
        WHERE Student_ID = %s
        AND Event_ID = %s
        """,
        (student_id, event_id),
        fetchone=True
    )


    # Student already registered
    if existing:

        return f"""
        <!DOCTYPE html>

        <html>

        <head>
            <title>Already Registered</title>
        </head>

        <body>

            <h1>
                Already Registered
            </h1>

            <p>
                Student {student_id}
                is already registered for
                {event["Event_name"]}.
            </p>

            <a href="/events-page">
                Back to Events
            </a>

        </body>

        </html>
        """


    # ==================================================
    # CREATE REGISTRATION
    # ==================================================

    try:

        registration_id = query_db(
            """
            INSERT INTO registration
                (Student_ID, Event_ID)

            VALUES
                (%s, %s)
            """,
            (student_id, event_id),
            commit=True
        )


        # --------------------------------------------------
        # REDUCE REMAINING SEATS
        # --------------------------------------------------

        query_db(
            """
            UPDATE event

            SET Remaining_Seats =
                Remaining_Seats - 1

            WHERE Event_ID = %s
            """,
            (event_id,),
            commit=True
        )


        # --------------------------------------------------
        # SUCCESS PAGE
        # --------------------------------------------------

        return f"""
        <!DOCTYPE html>

        <html>

        <head>

            <title>
                Registration Successful
            </title>

            <link rel="stylesheet"
                  href="/static/css/style.css">

        </head>


        <body>


            <nav>

                <h2>
                    College Events
                </h2>

                <div>

                    <a href="/">
                        Home
                    </a>

                    <a href="/events-page">
                        Events
                    </a>

                    <a href="/registrations">
                        Registrations
                    </a>

                    <a href="/admin">
                        Admin
                    </a>

                </div>

            </nav>


            <div class="container">


                <div class="event-card">


                    <h1>
                        Registration Successful! 🎉
                    </h1>


                    <p>
                        Your registration has been
                        successfully saved.
                    </p>


                    <br>


                    <p>

                        <strong>
                            Registration ID:
                        </strong>

                        {registration_id}

                    </p>


                    <p>

                        <strong>
                            Student ID:
                        </strong>

                        {student_id}

                    </p>


                    <p>

                        <strong>
                            Student Name:
                        </strong>

                        {student["Name"]}

                    </p>


                    <p>

                        <strong>
                            Event:
                        </strong>

                        {event["Event_name"]}

                    </p>


                    <br>


                    <a class="button"
                       href="/events-page">

                        Back to Events

                    </a>


                    <a class="button"
                       href="/registrations">

                        View Registrations

                    </a>


                </div>


            </div>


        </body>

        </html>
        """


    # ==================================================
    # REGISTRATION ERROR
    # ==================================================

    except Exception as e:

        return f"""
        <!DOCTYPE html>

        <html>

        <head>
            <title>Registration Failed</title>
        </head>

        <body>

            <h1>
                Registration Failed
            </h1>

            <p>
                {str(e)}
            </p>

            <a href="/events-page">
                Back to Events
            </a>

        </body>

        </html>
        """


# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.get("/admin")
def admin_dashboard():

    # --------------------------------------------------
    # TOTAL REGISTRATIONS
    # --------------------------------------------------

    total_registrations = query_db(
        """
        SELECT COUNT(*) AS total
        FROM registration
        """,
        fetchone=True
    )


    # --------------------------------------------------
    # TOTAL STUDENTS
    # --------------------------------------------------

    total_students = query_db(
        """
        SELECT COUNT(*) AS total
        FROM student
        """,
        fetchone=True
    )


    # --------------------------------------------------
    # TOTAL EVENTS
    # --------------------------------------------------

    total_events = query_db(
        """
        SELECT COUNT(*) AS total
        FROM event
        """,
        fetchone=True
    )


    # --------------------------------------------------
    # TOTAL ORGANIZERS
    # --------------------------------------------------

    total_organizers = query_db(
        """
        SELECT COUNT(*) AS total
        FROM organizer
        """,
        fetchone=True
    )


    # --------------------------------------------------
    # EVENT-WISE REGISTRATION SUMMARY
    # --------------------------------------------------

    event_summary = query_db(
        """
        SELECT

            e.Event_ID,

            e.Event_name,

            e.Capacity,

            e.Remaining_Seats,

            COUNT(r.Registration_ID)
                AS Registration_Count

        FROM event e

        LEFT JOIN registration r
            ON e.Event_ID = r.Event_ID

        GROUP BY

            e.Event_ID,
            e.Event_name,
            e.Capacity,
            e.Remaining_Seats

        ORDER BY
            e.Event_ID
        """
    )


    # --------------------------------------------------
    # RECENT REGISTRATIONS
    # --------------------------------------------------

    recent_registrations = query_db(
        """
        SELECT

            r.Registration_ID,

            r.Registration_Date,

            r.Status,

            s.Student_ID,

            s.Name AS Student_Name,

            e.Event_name

        FROM registration r

        JOIN student s
            ON r.Student_ID = s.Student_ID

        JOIN event e
            ON r.Event_ID = e.Event_ID

        ORDER BY
            r.Registration_ID DESC

        LIMIT 10
        """
    )


    # --------------------------------------------------
    # SHOW ADMIN PAGE
    # --------------------------------------------------

    return render_template(

        "admin.html",

        total_registrations=
            total_registrations["total"],

        total_students=
            total_students["total"],

        total_events=
            total_events["total"],

        total_organizers=
            total_organizers["total"],

        event_summary=
            event_summary,

        recent_registrations=
            recent_registrations
    )


# ==================================================
# ERROR HANDLERS
# ==================================================

@app.errorhandler(404)
def not_found(e):

    return jsonify({
        "error": "Route not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(e):

    return jsonify({
        "error": "Method not allowed"
    }), 405


@app.errorhandler(500)
def internal_error(e):

    return jsonify({
        "error": "Internal server error",
        "details": str(e)
    }), 500


# ==================================================
# RUN FLASK APPLICATION
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )