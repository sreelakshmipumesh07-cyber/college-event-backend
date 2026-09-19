-- =============================================================
--  College Event Registration System — Sample Data
-- =============================================================
USE college_event_db;

-- VENUE
INSERT INTO VENUE (Venue_Name, Location) VALUES
('Main Auditorium',    'Block A, Ground Floor'),
('Seminar Hall 1',     'Block B, 2nd Floor'),
('Open Air Theatre',   'Central Campus, Near Canteen'),
('Conference Room 3',  'Admin Block, 3rd Floor'),
('Sports Complex',     'East Wing, Ground Floor');

-- ORGANIZER
INSERT INTO ORGANIZER (Name, Email, Phone, Department) VALUES
('Dr. Ramesh Kumar',   'ramesh.kumar@college.edu',   '9876543210', 'Computer Science'),
('Prof. Anita Sharma', 'anita.sharma@college.edu',   '9876543211', 'Electronics'),
('Mr. Suresh Verma',   'suresh.verma@college.edu',   '9876543212', 'Mechanical'),
('Dr. Priya Nair',     'priya.nair@college.edu',      '9876543213', 'Information Technology'),
('Prof. Ravi Pillai',  'ravi.pillai@college.edu',     '9876543214', 'Civil Engineering');

-- STUDENT
INSERT INTO STUDENT (Name, Phone, Email, Department, Year) VALUES
('Arjun Mehta',       '9000000001', 'arjun.mehta@student.edu',   'Computer Science',      3),
('Priya Patel',       '9000000002', 'priya.patel@student.edu',   'Electronics',           2),
('Rohit Singh',       '9000000003', 'rohit.singh@student.edu',   'Mechanical',            4),
('Sneha Iyer',        '9000000004', 'sneha.iyer@student.edu',    'Information Technology',1),
('Karan Joshi',       '9000000005', 'karan.joshi@student.edu',   'Computer Science',      2),
('Divya Nair',        '9000000006', 'divya.nair@student.edu',    'Civil Engineering',     3),
('Aman Gupta',        '9000000007', 'aman.gupta@student.edu',    'Computer Science',      1),
('Pooja Rao',         '9000000008', 'pooja.rao@student.edu',     'Electronics',           4),
('Nikhil Das',        '9000000009', 'nikhil.das@student.edu',    'Information Technology',2),
('Ananya Kapoor',     '9000000010', 'ananya.kapoor@student.edu', 'Computer Science',      3);

-- EVENT
-- Note: Remaining_Seats starts equal to Capacity (triggers will auto-manage after this)
INSERT INTO EVENT (Event_name, Description, Date, Time, Registration_fee, Capacity, Remaining_Seats, Event_Type, Venue_ID, Organizer_ID) VALUES
('TechFest 2026',
 'Annual technical fest with competitions, workshops and exhibitions.',
 '2026-10-15', '09:00:00', 200.00, 300, 300, 'Technical',      1, 1),

('Hackathon 24H',
 '24-hour coding marathon — build, innovate, win!',
 '2026-10-20', '08:00:00', 150.00, 100, 100, 'Technical',      2, 1),

('Cultural Night',
 'An evening of music, dance, drama and fine arts.',
 '2026-10-25', '18:00:00',   0.00, 500, 500, 'Cultural',       3, 2),

('Robotics Workshop',
 'Hands-on workshop on building and programming robots.',
 '2026-11-01', '10:00:00', 300.00,  50,  50, 'Workshop',       2, 4),

('Sports Day 2026',
 'Inter-department sports competitions.',
 '2026-11-10', '07:00:00',   0.00, 200, 200, 'Sports',         5, 5),

('Alumni Meet',
 'Annual gathering of alumni with networking dinner.',
 '2026-11-15', '17:00:00', 500.00, 150, 150, 'Networking',     4, 3),

('AI & ML Summit',
 'Talks and panels by industry leaders on AI and Machine Learning.',
 '2026-11-20', '09:30:00', 250.00,  80,  80, 'Technical',      1, 4);

-- REGISTRATION
-- Inserts trigger trg_decrement_seats automatically
INSERT INTO REGISTRATION (Registration_Date, Status, Student_ID, Event_ID) VALUES
('2026-09-01', 'Confirmed', 1, 1),
('2026-09-01', 'Confirmed', 2, 1),
('2026-09-02', 'Confirmed', 3, 1),
('2026-09-02', 'Pending',   4, 2),
('2026-09-03', 'Confirmed', 5, 2),
('2026-09-03', 'Confirmed', 6, 3),
('2026-09-04', 'Confirmed', 7, 3),
('2026-09-04', 'Confirmed', 1, 4),
('2026-09-05', 'Cancelled', 8, 4),
('2026-09-05', 'Confirmed', 9, 5),
('2026-09-06', 'Confirmed',10, 7),
('2026-09-06', 'Confirmed', 2, 7);

-- PAYMENT
-- Only for non-cancelled, fee-bearing registrations
INSERT INTO PAYMENT (Amount, Payment_Date, Payment_Method, Registration_ID) VALUES
(200.00, '2026-09-01', 'UPI',         1),
(200.00, '2026-09-01', 'Card',        2),
(200.00, '2026-09-02', 'Net Banking', 3),
(150.00, '2026-09-03', 'UPI',         5),
(300.00, '2026-09-04', 'Cash',        8),
(250.00, '2026-09-06', 'UPI',        11),
(250.00, '2026-09-06', 'Card',       12);
