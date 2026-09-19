"""
College Event Registration System — Flask Entry Point
"""
from flask import Flask, jsonify
from flask_cors import CORS
from routes.students      import students_bp
from routes.events        import events_bp
from routes.venues        import venues_bp
from routes.organizers    import organizers_bp
from routes.registrations import registrations_bp
from routes.payments      import payments_bp

app = Flask(__name__)
CORS(app)  # Allow requests from the HTML frontend

# ── Register all blueprints ────────────────────────────────────
app.register_blueprint(students_bp)
app.register_blueprint(events_bp)
app.register_blueprint(venues_bp)
app.register_blueprint(organizers_bp)
app.register_blueprint(registrations_bp)
app.register_blueprint(payments_bp)


# ── Health check ──────────────────────────────────────────────
@app.get("/")
def index():
    return jsonify({
        "project": "College Event Registration System",
        "version": "1.0",
        "endpoints": {
            "students":      "/students",
            "events":        "/events",
            "venues":        "/venues",
            "organizers":    "/organizers",
            "registrations": "/registrations",
            "payments":      "/payments",
        },
    }), 200


# ── Global error handlers ─────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
