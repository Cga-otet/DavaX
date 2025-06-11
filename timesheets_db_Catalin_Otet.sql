/*
USERS
 └──< TIMESHEETS (user_id FK)
        └──< TIME_ENTRIES (timesheet_id FK)
*/

-- create users table
CREATE TABLE USERS(
    user_id NUMBER PRIMARY KEY,
    first_name VARCHAR2(100) NOT NULL,
    last_name VARCHAR2(100) NOT NULL,
    email VARCHAR2(150) UNIQUE NOT NULL,
    job_title VARCHAR2(100),
    location VARCHAR2(100),
    country VARCHAR2(100) DEFAULT 'Romania',
    hire_date DATE
);

-- creating the timesheets table
CREATE TABLE TIMESHEETS (
    timesheet_id NUMBER PRIMARY KEY,
    user_id NUMBER NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    submitted_on DATE NOT NULL,
    status VARCHAR2(30) DEFAULT 'Draft',
    comments VARCHAR(255),
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES USERS(user_id) 
);

-- creating the time entries
CREATE TABLE TIME_ENTRIES (
    entry_id NUMBER PRIMARY KEY,
    timesheet_id NUMBER NOT NULL,
    entry_date DATE NOT NULL,
    project_code VARCHAR2(100),
    task VARCHAR2(100),
    time_type VARCHAR2(100) DEFAULT 'Regular',
    absence VARCHAR2(100) DEFAULT 'None',
    work_location VARCHAR2(100) DEFAULT 'Work from Office',
    country VARCHAR2(100) DEFAULT 'Romania',
    public_hol VARCHAR2(100),
    start_time DATE,
    end_time DATE,
    num_hours NUMBER(5,2),
    comments VARCHAR2(255),
    CONSTRAINT fk_timesheet_id FOREIGN KEY (timesheet_id) REFERENCES TIMESHEETS(timesheet_id)
);

-- Insert users
INSERT INTO USERS (user_id, first_name, last_name, email, job_title, location, country, hire_date)
VALUES (1, 'Alice', 'Popescu', 'alice.popescu@endava.com', 'Software Engineer', 'Bucharest', 'Romania', TO_DATE('2022-03-15', 'YYYY-MM-DD'));

INSERT INTO USERS (user_id, first_name, last_name, email, job_title, location, country, hire_date)
VALUES (2, 'Bogdan', 'Ionescu', 'bogdan.ionescu@endava.com', 'QA Engineer', 'Cluj-Napoca', 'Romania', TO_DATE('2021-08-01', 'YYYY-MM-DD'));

-- Insert timesheets
INSERT INTO TIMESHEETS (timesheet_id, user_id, period_start, period_end, submitted_on, status, comments)
VALUES (1001, 1, TO_DATE('2024-06-03', 'YYYY-MM-DD'), TO_DATE('2024-06-09', 'YYYY-MM-DD'), SYSDATE, 'Submitted', 'Weekly timesheet for sprint planning');

INSERT INTO TIMESHEETS (timesheet_id, user_id, period_start, period_end, submitted_on, status, comments)
VALUES (1002, 2, TO_DATE('2024-06-03', 'YYYY-MM-DD'), TO_DATE('2024-06-09', 'YYYY-MM-DD'), SYSDATE, 'Draft', NULL);

-- Insert time entries for timesheet
INSERT INTO TIME_ENTRIES (
    entry_id, timesheet_id, entry_date, project_code, task, time_type,
    absence, work_location, country, public_hol, start_time, end_time, num_hours, comments
)
VALUES (
    2001, 1001, TO_DATE('2024-06-03', 'YYYY-MM-DD'), 'PRJ001', 'Backend API Development', 'Regular',
    'None', 'Work from Office', 'Romania', NULL, 
    TO_DATE('2024-06-03 09:00', 'YYYY-MM-DD HH24:MI'),
    TO_DATE('2024-06-03 17:00', 'YYYY-MM-DD HH24:MI'), 
    8, 'Focused on authentication logic'
);

INSERT INTO TIME_ENTRIES (
    entry_id, timesheet_id, entry_date, project_code, task, time_type,
    absence, work_location, country, public_hol, start_time, end_time, num_hours, comments
)
VALUES (
    2002, 1001, TO_DATE('2024-06-04', 'YYYY-MM-DD'), 'PRJ001', 'Code Review', 'Regular',
    'None', 'Work from Office', 'Romania', NULL, 
    TO_DATE('2024-06-04 10:00', 'YYYY-MM-DD HH24:MI'),
    TO_DATE('2024-06-04 18:00', 'YYYY-MM-DD HH24:MI'), 
    8, 'Reviewed feature branch PRs'
);

-- view to retrieve all of a users timesheet entries
CREATE OR REPLACE VIEW V_USER_TIMESHEET_ENTRIES AS
SELECT
    u.user_id,
    u.first_name || ' ' || u.last_name AS full_name,
    u.email,
    t.timesheet_id,
    t.period_start,
    t.period_end,
    t.status,
    e.entry_id,
    e.entry_date,
    e.project_code,
    e.task,
    e.time_type,
    e.absence,
    e.work_location,
    e.country,
    e.num_hours,
    e.comments AS entry_comment
FROM
    USERS u
JOIN TIMESHEETS t ON u.user_id = t.user_id
JOIN TIME_ENTRIES e ON t.timesheet_id = e.timesheet_id;

SELECT * FROM V_USER_TIMESHEET_ENTRIES;

-- create a materialized view to sum total hours worked per user per week
CREATE MATERIALIZED VIEW MV_WEEKLY_SUMMARY
BUILD IMMEDIATE
REFRESH ON DEMAND
AS
SELECT
    u.user_id,
    u.first_name || ' ' || u.last_name AS full_name,
    t.period_start,
    t.period_end,
    SUM(e.num_hours) AS total_hours,
    COUNT(e.entry_id) AS total_entries
FROM
    USERS u
JOIN TIMESHEETS t ON u.user_id = t.user_id
JOIN TIME_ENTRIES e ON t.timesheet_id = e.timesheet_id
GROUP BY
    u.user_id,
    u.first_name,
    u.last_name,
    t.period_start,
    t.period_end;
    
-- EXEC DBMS_MVIEW.REFRESH('MV_WEEKLY_SUMMARY');

SELECT * FROM MV_WEEKLY_SUMMARY;

-- total hours worked per each project
SELECT
    u.user_id,
    u.first_name || ' ' || u.last_name AS full_name,
    e.project_code,
    SUM(e.num_hours) AS total_hours
FROM
    USERS u
JOIN TIMESHEETS t ON u.user_id = t.user_id
JOIN TIME_ENTRIES e ON t.timesheet_id = e.timesheet_id
GROUP BY
    u.user_id,
    u.first_name,
    u.last_name,
    e.project_code;

-- list all users with their latest timesheet info
SELECT
    u.user_id,
    u.first_name || ' ' || u.last_name AS full_name,
    t.timesheet_id,
    t.period_start,
    t.period_end,
    t.status
FROM
    USERS u
LEFT JOIN TIMESHEETS t ON u.user_id = t.user_id
ORDER BY
    u.user_id;
    
-- compare today's hours with hours from previous day for each user
SELECT
    u.user_id,
    u.first_name || ' ' || u.last_name AS full_name,
    e.entry_date,
    e.num_hours,
    LAG(e.num_hours, 1) OVER (PARTITION BY u.user_id ORDER BY e.entry_date) AS prev_day_hours,
    (e.num_hours - LAG(e.num_hours, 1) OVER (PARTITION BY u.user_id ORDER BY e.entry_date)) AS delta_hours
FROM
    USERS u
JOIN TIMESHEETS t ON u.user_id = t.user_id
JOIN TIME_ENTRIES e ON t.timesheet_id = e.timesheet_id
ORDER BY
    u.user_id,
    e.entry_date;
    
-- add a user preferences field (for example language and theme)
ALTER TABLE USERS ADD (
    preferences CLOB CHECK (preferences IS JSON)
);

-- email index for fast user search
CREATE INDEX idx_users_job_title ON USERS(job_title);

ALTER TABLE TIMESHEETS ADD (
    metadata XMLTYPE
);

-- status index for quick filtering of uncompleted timesheets
CREATE INDEX idx_timesheets_status ON TIMESHEETS(status);

-- update users table rows with data for the new column
UPDATE USERS
SET preferences = '{
    "language": "en",
    "theme": "dark",
    "notifications": true
}'
WHERE user_id = 1;

UPDATE USERS
SET preferences = '{
    "language": "ro",
    "theme": "light",
    "notifications": false
}'
WHERE user_id = 2;

-- update in timesheets with data to account for the newly added column
UPDATE TIMESHEETS
SET metadata = XMLTYPE('
    <submission>
        <device>Desktop</device>
        <ip_address>192.168.1.101</ip_address>
        <submitted_by>Alice</submitted_by>
    </submission>
')
WHERE timesheet_id = 1001;

UPDATE TIMESHEETS
SET metadata = XMLTYPE('
    <submission>
        <device>Mobile</device>
        <ip_address>192.168.1.202</ip_address>
        <submitted_by>Bogdan</submitted_by>
    </submission>
')
WHERE timesheet_id = 1002;

-- select all from users/timesheets/time_entries
SELECT * FROM USERS;
SELECT * FROM TIMESHEETS;
SELECT * FROM TIME_ENTRIES;

-- extracting the ip of device which made the timesheet
SELECT
    timesheet_id,
    XMLCast(XMLQuery('/submission/ip_address/text()' PASSING metadata RETURNING CONTENT) AS VARCHAR2(50)) AS ip_address
FROM
    TIMESHEETS;
    
-- creating some admin/user roles
CREATE ROLE user_role;
CREATE ROLE admin_role;

-- graning appropiate permissions to roles: user only add/view/update and admin full permissions
GRANT SELECT ON USERS TO user_role;
GRANT SELECT, INSERT, UPDATE ON TIMESHEETS TO user_role;
GRANT SELECT, INSERT, UPDATE ON TIME_ENTRIES TO user_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON USERS TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TIMESHEETS TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TIME_ENTRIES TO admin_role;
