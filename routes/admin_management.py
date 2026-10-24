
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from db import get_connection
from routes.admin_auth import is_admin_logged_in


admin_management_bp = Blueprint(
    "admin_management",
    __name__,
    url_prefix="/admin/manage"
)


# Database tables and editable fields
ENTITIES = {
    "events": {
        "title": "Events",
        "table": "event",
        "primary": "Event_ID",
        "columns": [
            "Event_ID", "Event_name", "Description", "Date", "Time",
            "Registration_fee", "Capacity", "Remaining_Seats",
            "Event_Type", "Venue_ID", "Organizer_ID"
        ],
        "fields": [
            ("Event_name", "Event Name", "text"),
            ("Description", "Description", "textarea"),
            ("Date", "Date", "date"),
            ("Time", "Time", "time"),
            ("Registration_fee", "Registration Fee", "number"),
            ("Capacity", "Capacity", "number"),
            ("Remaining_Seats", "Remaining Seats", "number"),
            ("Event_Type", "Event Type", "text"),
            ("Venue_ID", "Venue ID", "number"),
            ("Organizer_ID", "Organizer ID", "number"),
        ],
    },
    "students": {
        "title": "Students",
        "table": "student",
        "primary": "Student_ID",
        "columns": [
            "Student_ID", "Name", "Phone", "Email", "Department", "Year"
        ],
        "fields": [
            ("Name", "Student Name", "text"),
            ("Phone", "Phone", "tel"),
            ("Email", "Email", "email"),
            ("Department", "Department", "text"),
            ("Year", "Year", "number"),
        ],
    },
    "venues": {
        "title": "Venues",
        "table": "venue",
        "primary": "Venue_ID",
        "columns": ["Venue_ID", "Venue_Name", "Location"],
        "fields": [
            ("Venue_Name", "Venue Name", "text"),
            ("Location", "Location", "text"),
        ],
    },
    "organizers": {
        "title": "Organizers",
        "table": "organizer",
        "primary": "Organizer_ID",
        "columns": [
            "Organizer_ID", "Name", "Email", "Phone", "Department"
        ],
        "fields": [
            ("Name", "Organizer Name", "text"),
            ("Email", "Email", "email"),
            ("Phone", "Phone", "tel"),
            ("Department", "Department", "text"),
        ],
    },
}


# Require admin login for every management page
@admin_management_bp.before_request
def require_admin():
    if not is_admin_logged_in():
        return redirect(
            url_for("admin_auth.login", next=request.url)
        )


def get_entity(entity):
    return ENTITIES.get(entity)


def get_db_connection():
    conn = get_connection()

    if conn is None:
        raise RuntimeError("Could not connect to the database.")

    return conn


def render_form(entity, config, mode, record=None):
    return render_template(
        "admin/manage_records.html",
        entity=entity,
        config=config,
        records=[],
        mode=mode,
        record=record or {},
    )


def read_form_values(config):
    """Read and validate submitted form fields."""
    values = {}

    for column, label, field_type in config["fields"]:
        value = request.form.get(column, "").strip()

        if value == "":
            raise ValueError(f"{label} is required.")

        if field_type == "number":
            try:
                if column == "Registration_fee":
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                raise ValueError(
                    f"{label} must be a valid number."
                )

        values[column] = value

    if "Registration_fee" in values:
        if values["Registration_fee"] < 0:
            raise ValueError(
                "Registration fee cannot be negative."
            )

    if "Capacity" in values:
        capacity = values["Capacity"]
        remaining = values["Remaining_Seats"]

        if capacity < 0:
            raise ValueError(
                "Capacity cannot be negative."
            )

        if remaining < 0 or remaining > capacity:
            raise ValueError(
                "Remaining seats must be between zero and capacity."
            )

    return values


def get_cursor_connection(dictionary=False):
    """Create a database connection and cursor."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=dictionary)
    return conn, cursor


# Management home page
@admin_management_bp.route("/")
def index():
    sections = [
        {
            "name": config["title"],
            "url": url_for(
                "admin_management.list_records",
                entity=entity
            ),
        }
        for entity, config in ENTITIES.items()
    ]

    return render_template(
        "admin/manage_index.html",
        sections=sections
    )


# View all records
@admin_management_bp.route("/<entity>")
def list_records(entity):
    config = get_entity(entity)

    if config is None:
        return "Management section not found.", 404

    conn, cursor = get_cursor_connection(dictionary=True)

    try:
        cursor.execute(
            f"SELECT * FROM `{config['table']}` "
            f"ORDER BY `{config['primary']}` DESC"
        )

        records = cursor.fetchall()

        return render_template(
            "admin/manage_records.html",
            entity=entity,
            config=config,
            records=records,
            mode="list",
            record=None,
        )

    except Exception as error:
        print("ADMIN LIST ERROR:", repr(error))
        flash("Could not load records. Check the Flask terminal.", "error")
        return redirect(url_for("admin_management.index"))

    finally:
        cursor.close()
        conn.close()


# Insert a new record
@admin_management_bp.route(
    "/<entity>/insert",
    methods=["GET", "POST"]
)
def insert_record(entity):
    config = get_entity(entity)

    if config is None:
        return "Management section not found.", 404

    if request.method == "GET":
        return render_form(entity, config, "insert")

    # Validate the submitted form
    try:
        values = read_form_values(config)
    except ValueError as error:
        flash(str(error), "error")
        return render_form(
            entity, config, "insert", request.form
        )

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        columns = list(values.keys())
        column_sql = ", ".join(
            f"`{column}`" for column in columns
        )
        placeholders = ", ".join(
            ["%s"] * len(columns)
        )

        query = (
            f"INSERT INTO `{config['table']}` "
            f"({column_sql}) VALUES ({placeholders})"
        )

        cursor.execute(
            query,
            tuple(values[column] for column in columns)
        )

        conn.commit()

        print(
            f"ADMIN INSERT SUCCESS: entity={entity}, "
            f"new_id={cursor.lastrowid}"
        )

        flash(
            f"{config['title']} record added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin_management.list_records",
                entity=entity
            )
        )

    except Exception as error:
        if conn is not None:
            conn.rollback()

        # Print the real error for debugging
        print(
            f"ADMIN INSERT ERROR for '{entity}':",
            repr(error)
        )

        flash(
            f"Could not add the record: {error}",
            "error"
        )

        return render_form(
            entity, config, "insert", request.form
        )

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()


# Update an existing record
@admin_management_bp.route(
    "/<entity>/update/<int:record_id>",
    methods=["GET", "POST"]
)
def update_record(entity, record_id):
    config = get_entity(entity)

    if config is None:
        return "Management section not found.", 404

    conn = None
    cursor = None

    try:
        conn, cursor = get_cursor_connection(dictionary=True)

        cursor.execute(
            f"SELECT * FROM `{config['table']}` "
            f"WHERE `{config['primary']}` = %s",
            (record_id,)
        )

        record = cursor.fetchone()

        if record is None:
            flash("Record not found.", "error")
            return redirect(
                url_for(
                    "admin_management.list_records",
                    entity=entity
                )
            )

        if request.method == "GET":
            return render_form(
                entity, config, "update", record
            )

        try:
            values = read_form_values(config)
        except ValueError as error:
            flash(str(error), "error")
            return render_form(
                entity, config, "update", request.form
            )

        assignments = ", ".join(
            f"`{column}` = %s" for column in values
        )

        parameters = list(values.values())
        parameters.append(record_id)

        cursor.execute(
            f"UPDATE `{config['table']}` "
            f"SET {assignments} "
            f"WHERE `{config['primary']}` = %s",
            tuple(parameters)
        )

        conn.commit()

        flash(
            f"{config['title']} record updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin_management.list_records",
                entity=entity
            )
        )

    except Exception as error:
        if conn is not None:
            conn.rollback()

        print(
            f"ADMIN UPDATE ERROR for '{entity}':",
            repr(error)
        )

        flash(
            f"Could not update the record: {error}",
            "error"
        )

        return redirect(
            url_for(
                "admin_management.list_records",
                entity=entity
            )
        )

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()


# Delete a record
@admin_management_bp.route(
    "/<entity>/delete/<int:record_id>",
    methods=["POST"]
)
def delete_record(entity, record_id):
    config = get_entity(entity)

    if config is None:
        return "Management section not found.", 404

    conn = None
    cursor = None

    try:
        conn, cursor = get_cursor_connection()

        cursor.execute(
            f"DELETE FROM `{config['table']}` "
            f"WHERE `{config['primary']}` = %s",
            (record_id,)
        )

        deleted = cursor.rowcount
        conn.commit()

        if deleted:
            flash("Record deleted successfully.", "success")
        else:
            flash("Record not found.", "error")

    except Exception as error:
        if conn is not None:
            conn.rollback()

        print(
            f"ADMIN DELETE ERROR for '{entity}':",
            repr(error)
        )

        flash(
            f"Cannot delete this record: {error}",
            "error"
        )

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()

    return redirect(
        url_for(
            "admin_management.list_records",
            entity=entity
        )
    )
