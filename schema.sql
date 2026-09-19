-- =============================================================
--  College Event Registration System — Database Schema
--  DBMS Project | Python + Flask + MySQL
-- =============================================================

-- Create and select database
CREATE DATABASE IF NOT EXISTS college_event_db;
USE college_event_db;

-- =============================================================
-- 1. VENUE
-- =============================================================
CREATE TABLE IF NOT EXISTS VENUE (
    Venue_ID    INT          NOT NULL AUTO_INCREMENT,
    Venue_Name  VARCHAR(100) NOT NULL,
    Location    VARCHAR(200) NOT NULL,
    CONSTRAINT pk_venue PRIMARY KEY (Venue_ID)
);

-- =============================================================
-- 2. ORGANIZER
-- =============================================================
CREATE TABLE IF NOT EXISTS ORGANIZER (
    Organizer_ID INT          NOT NULL AUTO_INCREMENT,
    Name         VARCHAR(100) NOT NULL,
    Email        VARCHAR(100) NOT NULL UNIQUE,
    Phone        VARCHAR(15)  NOT NULL,
    Department   VARCHAR(100) NOT NULL,
    CONSTRAINT pk_organizer PRIMARY KEY (Organizer_ID)
);

-- =============================================================
-- 3. STUDENT
-- =============================================================
CREATE TABLE IF NOT EXISTS STUDENT (
    Student_ID  INT          NOT NULL AUTO_INCREMENT,
    Name        VARCHAR(100) NOT NULL,
    Phone       VARCHAR(15)  NOT NULL UNIQUE,
    Email       VARCHAR(100) NOT NULL UNIQUE,
    Department  VARCHAR(100) NOT NULL,
    Year        TINYINT      NOT NULL CHECK (Year BETWEEN 1 AND 5),
    CONSTRAINT pk_student PRIMARY KEY (Student_ID)
);

-- =============================================================
-- 4. EVENT
-- =============================================================
CREATE TABLE IF NOT EXISTS EVENT (
    Event_ID         INT            NOT NULL AUTO_INCREMENT,
    Event_name       VARCHAR(150)   NOT NULL,
    Description      TEXT,
    Date             DATE           NOT NULL,
    Time             TIME           NOT NULL,
    Registration_fee DECIMAL(8, 2)  NOT NULL DEFAULT 0.00,
    Capacity         INT            NOT NULL CHECK (Capacity > 0),
    Remaining_Seats  INT            NOT NULL CHECK (Remaining_Seats >= 0),
    Event_Type       VARCHAR(50)    NOT NULL,
    Venue_ID         INT            NOT NULL,
    Organizer_ID     INT            NOT NULL,
    CONSTRAINT pk_event        PRIMARY KEY (Event_ID),
    CONSTRAINT fk_event_venue  FOREIGN KEY (Venue_ID)
        REFERENCES VENUE(Venue_ID) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_event_org    FOREIGN KEY (Organizer_ID)
        REFERENCES ORGANIZER(Organizer_ID) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_seats       CHECK (Remaining_Seats <= Capacity)
);

-- =============================================================
-- 5. REGISTRATION
-- =============================================================
CREATE TABLE IF NOT EXISTS REGISTRATION (
    Registration_ID   INT         NOT NULL AUTO_INCREMENT,
    Registration_Date DATE        NOT NULL DEFAULT (CURRENT_DATE),
    Status            ENUM('Pending', 'Confirmed', 'Cancelled') NOT NULL DEFAULT 'Pending',
    Student_ID        INT         NOT NULL,
    Event_ID          INT         NOT NULL,
    CONSTRAINT pk_registration     PRIMARY KEY (Registration_ID),
    CONSTRAINT fk_reg_student      FOREIGN KEY (Student_ID)
        REFERENCES STUDENT(Student_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reg_event        FOREIGN KEY (Event_ID)
        REFERENCES EVENT(Event_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    -- A student cannot register twice for the same event
    CONSTRAINT uq_student_event    UNIQUE (Student_ID, Event_ID)
);

-- =============================================================
-- 6. PAYMENT
-- =============================================================
CREATE TABLE IF NOT EXISTS PAYMENT (
    Payment_ID      INT            NOT NULL AUTO_INCREMENT,
    Amount          DECIMAL(8, 2)  NOT NULL CHECK (Amount >= 0),
    Payment_Date    DATE           NOT NULL DEFAULT (CURRENT_DATE),
    Payment_Method  ENUM('Cash', 'UPI', 'Card', 'Net Banking') NOT NULL,
    Registration_ID INT            NOT NULL UNIQUE,   -- 1-to-1 with REGISTRATION
    CONSTRAINT pk_payment      PRIMARY KEY (Payment_ID),
    CONSTRAINT fk_pay_reg      FOREIGN KEY (Registration_ID)
        REFERENCES REGISTRATION(Registration_ID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- =============================================================
-- TRIGGERS
-- =============================================================

DELIMITER $$

-- Trigger 1: Decrement Remaining_Seats when a new registration is inserted
--            (only when status is NOT 'Cancelled')
CREATE TRIGGER trg_decrement_seats
AFTER INSERT ON REGISTRATION
FOR EACH ROW
BEGIN
    IF NEW.Status != 'Cancelled' THEN
        UPDATE EVENT
        SET    Remaining_Seats = Remaining_Seats - 1
        WHERE  Event_ID = NEW.Event_ID;
    END IF;
END$$

-- Trigger 2: Handle status changes on REGISTRATION UPDATE
--            Cancelled → Confirmed/Pending  => decrement
--            Confirmed/Pending → Cancelled  => increment
CREATE TRIGGER trg_update_seats
AFTER UPDATE ON REGISTRATION
FOR EACH ROW
BEGIN
    -- Registration was just cancelled → free up a seat
    IF OLD.Status != 'Cancelled' AND NEW.Status = 'Cancelled' THEN
        UPDATE EVENT
        SET    Remaining_Seats = Remaining_Seats + 1
        WHERE  Event_ID = NEW.Event_ID;

    -- Registration was re-activated from Cancelled → occupy a seat
    ELSEIF OLD.Status = 'Cancelled' AND NEW.Status != 'Cancelled' THEN
        UPDATE EVENT
        SET    Remaining_Seats = Remaining_Seats - 1
        WHERE  Event_ID = NEW.Event_ID;
    END IF;
END$$

-- Trigger 3: Increment Remaining_Seats when a registration row is deleted
CREATE TRIGGER trg_delete_seats
AFTER DELETE ON REGISTRATION
FOR EACH ROW
BEGIN
    IF OLD.Status != 'Cancelled' THEN
        UPDATE EVENT
        SET    Remaining_Seats = Remaining_Seats + 1
        WHERE  Event_ID = OLD.Event_ID;
    END IF;
END$$

DELIMITER ;

-- =============================================================
-- VIEW: event_summary_view
--   Joins EVENT + ORGANIZER + VENUE + registration count
-- =============================================================
CREATE OR REPLACE VIEW event_summary_view AS
SELECT
    e.Event_ID,
    e.Event_name,
    e.Event_Type,
    e.Date,
    e.Time,
    e.Registration_fee,
    e.Capacity,
    e.Remaining_Seats,
    (e.Capacity - e.Remaining_Seats) AS Registered_Count,
    v.Venue_Name,
    v.Location,
    o.Name         AS Organizer_Name,
    o.Department   AS Organizer_Dept,
    o.Email        AS Organizer_Email
FROM EVENT e
JOIN VENUE    v ON e.Venue_ID     = v.Venue_ID
JOIN ORGANIZER o ON e.Organizer_ID = o.Organizer_ID;

-- =============================================================
-- VIEW: student_registration_view
--   Full registration details: student + event + payment
-- =============================================================
CREATE OR REPLACE VIEW student_registration_view AS
SELECT
    r.Registration_ID,
    r.Registration_Date,
    r.Status,
    s.Student_ID,
    s.Name          AS Student_Name,
    s.Email         AS Student_Email,
    s.Department    AS Student_Dept,
    s.Year,
    e.Event_ID,
    e.Event_name,
    e.Date          AS Event_Date,
    e.Event_Type,
    p.Payment_ID,
    p.Amount,
    p.Payment_Method,
    p.Payment_Date
FROM REGISTRATION r
JOIN STUDENT s ON r.Student_ID = s.Student_ID
JOIN EVENT   e ON r.Event_ID   = e.Event_ID
LEFT JOIN PAYMENT p ON r.Registration_ID = p.Registration_ID;
