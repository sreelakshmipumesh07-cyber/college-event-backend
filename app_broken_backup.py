
"""
College Event Registration System - Flask Entry Point
import os
from dotenv import load_dotenv
load_dotenv(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ".env"
    )
)
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from db import query_db
from routes.students import students_bp
from routes.events import events_bp
from routes.venues import venues_bp
from routes.organizers import organizers_bp
from routes.registrations import registrations_bp
from routes.payments import payments_bp
from routes.admin_auth import admin_auth_bp
from routes.admin_management import admin_management_bp
# ==================================================
# CREATE FLASK APPLICATION
app = Flask(__name__)
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing from the .env file"
app.secret_key = SECRET_KEY
CORS(app)
# REGISTER BLUEPRINTS
app.register_blueprint(students_bp)
app.register_blueprint(events_bp)
app.register_blueprint(venues_bp)
app.register_blueprint(organizers_bp)
app.register_blueprint(registrations_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(admin_auth_bp)
# HOME PAGE
@app.get("/")
def index():
    return render_template("index.html")
# EVENTS PAGE
@app.get("/events-page")
def events_page():
    events = query_db(
        """
        SELECT *
        FROM event
        ORDER BY Event_ID
    if events is None:
        events = []
    print("EVENTS FROM DATABASE:", events)
    return render_template(
        "events.html",
        events=events
# EVENT DETAILS PAGE
@app.get("/event-details/<int:event_id>")
def event_details(event_id):
    event = query_db(
        WHERE Event_ID = %s
        """,
        (event_id,),
        fetchone=True
    if not event:
        return "Event not found", 404
        "event_details.html",
        event=event
# REGISTRATIONS PAGE
@app.get("/registrations")
def registrations():
    registration_list = query_db(
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
    if registration_list is None:
        registration_list = []
        "registrations.html",
        registrations=registration_list
# EVENT REGISTRATION
@app.route("/register", methods=["GET", "POST"])
def register():
    # --------------------------------------------------
    # GET REQUEST: SHOW SELECTED EVENT
    if request.method == "GET":
        event_id = request.args.get("event_id")
        if not event_id:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Select Event</title>
            </head>
            <body>
                <h1>Please select an event first.</h1>
                <a href="/events-page">Go to Events</a>
            </body>
            </html>
            """, 400
        event = query_db(
            """
            SELECT *
            FROM event
            WHERE Event_ID = %s
            """,
            (event_id,),
            fetchone=True
        )
        if not event:
                <title>Event Not Found</title>
                <h1>Event Not Found</h1>
                <a href="/events-page">Back to Events</a>
            """, 404
        return render_template(
            "register.html",
            event=event
    # POST REQUEST: SAVE REGISTRATION
    student_id = request.form.get("student_id")
    event_id = request.form.get("event_id")
    if not student_id or not event_id:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Missing Information</title>
        </head>
        <body>
            <h1>Missing Information</h1>
            <p>Please provide both Student ID and Event ID.</p>
            <a href="/events-page">Back to Events</a>
        </body>
        </html>
        """, 400
    # CHECK STUDENT
    student = query_db(
        FROM student
        WHERE Student_ID = %s
        (student_id,),
    if not student:
            <title>Student Not Found</title>
            <h1>Student Not Found</h1>
            <p>The Student ID you entered does not exist.</p>
        """, 404
    # CHECK EVENT
            <title>Event Not Found</title>
            <h1>Event Not Found</h1>
    # CHECK REMAINING SEATS
    if event["Remaining_Seats"] is None or event["Remaining_Seats"] <= 0:
            <title>Event Full</title>
            <h1>Event Full</h1>
            <p>Sorry, this event has no remaining seats.</p>
        """, 409
    # CHECK DUPLICATE REGISTRATION
    existing = query_db(
        FROM registration
          AND Event_ID = %s
        (student_id, event_id),
    if existing:
        return f"""
            <title>Already Registered</title>
            <h1>Already Registered</h1>
            <p>
                Student {student_id} is already registered
                for {event["Event_name"]}.
            </p>
    # CREATE REGISTRATION
    try:
        registration_id = query_db(
            INSERT INTO registration
                (Student_ID, Event_ID)
            VALUES
                (%s, %s)
            (student_id, event_id)
        if not registration_id:
                <title>Registration Failed</title>
                <h1>Registration Failed</h1>
                <p>The registration could not be saved.</p>
            """, 500
        # Reduce the remaining seats after a successful insert.
        update_result = query_db(
            UPDATE event
            SET Remaining_Seats = Remaining_Seats - 1
              AND Remaining_Seats > 0
            (event_id,)
        if update_result is None:
                <title>Registration Issue</title>
                <h1>Registration Saved</h1>
                <p>
                    Your registration was saved, but the seat count
                    could not be updated. Please contact the administrator.
                </p>
        # --------------------------------------------------
        # REGISTRATION SUCCESS PAGE
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Registration Successful</title>
            <link rel="stylesheet" href="/static/css/style.css">
            <nav>
                <h2>College Events</h2>
                <div>
                    <a href="/">Home</a>
                    <a href="/events-page">Events</a>
                    <a href="/registrations">Registrations</a>
                    <a href="/admin">Admin</a>
                </div>
            </nav>
            <div class="container">
                <div class="event-card">
                    <h1>Registration Successful! ðŸŽ‰</h1>
                    <p>Your registration has been successfully saved.</p>
                    <p>
                        <strong>Registration ID:</strong>
                        {registration_id}
                    </p>
                        <strong>Student ID:</strong>
                        {student_id}
                        <strong>Student Name:</strong>
                        {student["Name"]}
                        <strong>Event:</strong>
                        {event["Event_name"]}
                        <strong>Registration Fee:</strong>
                        â‚¹{event["Registration_fee"]}
                    <br>
                    <a class="button" href="/events-page">
                        Back to Events
                    </a>
                    <a class="button" href="/registrations">
                        View Registrations
            </div>
    except Exception:
        app.logger.exception("Registration failed")
            <title>Registration Failed</title>
            <h1>Registration Failed</h1>
            <p>An error occurred while processing your registration.</p>
        """, 500
# ADMIN DASHBOARD
@app.get("/admin")
def admin_dashboard():
    # TOTAL REGISTRATIONS
    total_registrations = query_db(
        SELECT COUNT(*) AS total
    # TOTAL STUDENTS
    total_students = query_db(
    # TOTAL EVENTS
    total_events = query_db(
    # TOTAL ORGANIZERS
    total_organizers = query_db(
        FROM organizer
    # EVENT-WISE REGISTRATION SUMMARY
    event_summary = query_db(
            e.Event_name,
            e.Capacity,
            e.Remaining_Seats,
            COUNT(r.Registration_ID) AS Registration_Count
        FROM event e
        LEFT JOIN registration r
            ON e.Event_ID = r.Event_ID
        GROUP BY
            e.Remaining_Seats
        ORDER BY e.Event_ID
    # RECENT REGISTRATIONS
    recent_registrations = query_db(
        LIMIT 10
    if any(
        result is None
        for result in (
            total_registrations,
            total_students,
            total_events,
            total_organizers
    ):
        return "Unable to load admin dashboard data.", 500
    if event_summary is None:
        event_summary = []
    if recent_registrations is None:
        recent_registrations = []
        "admin.html",
        total_registrations=total_registrations["total"],
        total_students=total_students["total"],
        total_events=total_events["total"],
        total_organizers=total_organizers["total"],
        event_summary=event_summary,
        recent_registrations=recent_registrations
# ERROR HANDLERS
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Route not found"
    }), 404
@app.errorhandler(405)
def method_not_allowed(error):
        "error": "Method not allowed"
    }), 405
@app.errorhandler(500)
def internal_error(error):
    app.logger.exception("Internal server error")
        "error": "Internal server error",
        "details": str(error)
    }), 500
# RUN FLASK APPLICATION
if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000

app.register_blueprint(admin_management_bp)
