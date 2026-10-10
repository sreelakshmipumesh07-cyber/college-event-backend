import os
import hmac

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    session,
    flash,
    render_template,
)

admin_auth_bp = Blueprint("admin_auth", __name__)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def is_admin_logged_in():
    return session.get("is_admin") is True


@admin_auth_bp.before_app_request
def protect_admin_routes():
    path = request.path.rstrip("/") or "/"
    endpoint = request.endpoint or ""

    # Authentication routes must remain accessible.
    if path in ("/admin-login", "/admin-logout"):
        return None

    # Protect URLs under /admin and endpoints whose names identify
    # them as admin routes, including admin_dashboard.
    is_admin_route = (
        path == "/admin"
        or path.startswith("/admin/")
        or path.startswith("/admin-")
        or "admin_" in endpoint.lower()
        or endpoint.lower().startswith("admin.")
    )

    if is_admin_route and not is_admin_logged_in():
        return redirect(
            url_for("admin_auth.login", next=request.url)
        )

    return None


@admin_auth_bp.route("/admin-login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next", "")

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        next_url = request.form.get("next", "")

        if not ADMIN_PASSWORD:
            flash(
                "Admin password is not configured. Set ADMIN_PASSWORD in .env.",
                "error",
            )
            return render_template(
                "admin_login.html",
                next_url=next_url,
            ), 500

        valid_username = hmac.compare_digest(
            username.encode("utf-8"),
            ADMIN_USERNAME.encode("utf-8"),
        )
        valid_password = hmac.compare_digest(
            password.encode("utf-8"),
            ADMIN_PASSWORD.encode("utf-8"),
        )

        if valid_username and valid_password:
            session["is_admin"] = True
            session.permanent = True
            flash("Admin login successful.", "success")

            # Only allow local relative paths to prevent open redirects.
            if (
                next_url.startswith("/")
                and not next_url.startswith("//")
                and "\\" not in next_url
            ):
                return redirect(next_url)

            return redirect("/admin")

        flash("Incorrect username or password.", "error")

    return render_template("admin_login.html", next_url=next_url)


@admin_auth_bp.route("/admin-logout", methods=["POST"])
def logout():
    session.pop("is_admin", None)
    flash("You have been logged out of the admin panel.", "success")
    return redirect("/")