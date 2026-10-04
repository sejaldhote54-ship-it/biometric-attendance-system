
from flask import Flask, request, redirect, session, render_template_string, url_for
import cv2
import numpy as np
import face_recognition
import base64
import pickle
import os
import sqlite3
from datetime import datetime
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
# =========================================================
# ATTENDANCE DATABASE
# =========================================================

def init_database():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_database()

# =========================================================
# LOGIN PAGE
# =========================================================

HTML = """
<!DOCTYPE html>
<html>
<head>

    <title>Biometric Access Control</title>

    <style>

        body {
            font-family: Arial;
            background: #f2f2f2;
            text-align: center;
            padding-top: 80px;
        }

        .box {
            background: white;
            width: 350px;
            margin: auto;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 0 15px #ccc;
        }

        input {
            width: 90%;
            padding: 12px;
            margin: 10px;
            box-sizing: border-box;
        }

        button {
            padding: 12px 30px;
            background: #1e3a8a;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }

    </style>

</head>

<body>

<div class="box">

    <h2>Biometric Access Control</h2>
    <h3>Admin Login</h3>

    <form method="POST">

        <input type="text"
               name="username"
               placeholder="Username"
               required>

        <br>

        <input type="password"
               name="password"
               placeholder="Password"
               required>

        <br>

        <button type="submit">Login</button>

    </form>

    {% if error %}
        <p style="color:red;">{{ error }}</p>
    {% endif %}

</div>

</body>
</html>
"""


# =========================================================
# DASHBOARD
# =========================================================

DASHBOARD = """
<!DOCTYPE html>
<html>

<head>

    <title>Biometric Dashboard</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f7fb;
        }

        .header {
            background: #1e3a8a;
            color: white;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            margin: 0;
            font-size: 25px;
        }

        .logout {
            background: #dc2626;
            color: white;
            padding: 10px 18px;
            border-radius: 6px;
            text-decoration: none;
        }

        .container {
            width: 90%;
            max-width: 1100px;
            margin: 35px auto;
        }

        .welcome {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px #ddd;
            margin-bottom: 25px;
        }

        .welcome h2 {
            margin-top: 0;
            color: #1e3a8a;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }

        .card {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px #ddd;
            text-align: center;
        }

        .card h3 {
            color: #1e3a8a;
            margin-bottom: 10px;
        }

        .card p {
            color: #666;
        }

        .btn {
            display: inline-block;
            padding: 11px 22px;
            background: #1e3a8a;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin-top: 10px;
        }

        .status {
            color: green;
            font-weight: bold;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            color: #777;
            font-size: 14px;
        }

        @media(max-width: 700px) {

            .cards {
                grid-template-columns: 1fr;
            }

            .header {
                padding: 18px;
            }

            .header h1 {
                font-size: 20px;
            }

        }

    </style>

</head>

<body>

    <div class="header">

        <h1>
            Biometric Attendance System
        </h1>

        <a href="/logout" class="logout">
            Logout
        </a>

    </div>


    <div class="container">

        <div class="welcome">

            <h2>
                Admin Dashboard
            </h2>

            <p>
                Welcome, Admin.
            </p>

            <p>
                Manage biometric access and attendance records
                from this dashboard.
            </p>

            <p class="status">
                ● System Online
            </p>

        </div>


        <div class="cards">

            <div class="card">

                <h3>
                    Face Recognition
                </h3>

                <p>
                    Register and recognize authorized faces.
                </p>

                <a href="/face" class="btn">
                    Open Face Recognition
                </a>

            </div>


            <div class="card">

                <h3>
                    Attendance Records
                </h3>

                <p>
                    View, search and manage attendance records.
                </p>

                <a href="/attendance" class="btn">
                    View Attendance
                </a>

            </div>


            <div class="card">

                <h3>
                    Access Control
                </h3>

                <p>
                    Face verification controls system access.
                </p>

                <span class="status">
                    Active
                </span>

            </div>


            <div class="card">

                <h3>
                    System Security
                </h3>

                <p>
                    Admin authentication and biometric
                    verification are enabled.
                </p>

                <span class="status">
                    Secure
                </span>

            </div>

        </div>


        <div class="footer">

            <p>
                Biometric Attendance & Access Control System
            </p>

            <p>
                MCA Major Project
            </p>

        </div>

    </div>

</body>

</html>
"""


# =========================================================
# FACE RECOGNITION PAGE
# =========================================================

FACE_PAGE = """
<!DOCTYPE html>
<html>

<head>

    <title>Face Recognition</title>

    <style>

        body {
            font-family: Arial;
            background: #f2f2f2;
            text-align: center;
            padding-top: 50px;
        }

        .box {
            background: white;
            width: 600px;
            margin: auto;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 0 15px #ccc;
        }

        video {
            width: 500px;
            height: 350px;
            border-radius: 10px;
            background: black;
            object-fit: cover;
        }

        button {
            padding: 12px 25px;
            margin: 10px;
            border: none;
            border-radius: 8px;
            background: #243b8f;
            color: white;
            cursor: pointer;
            font-size: 16px;
        }

        .back {
            display: inline-block;
            margin-top: 10px;
        }

        #result {
            font-size: 18px;
            font-weight: bold;
            margin-top: 15px;
        }

    </style>

</head>

<body>

<div class="box">

    <h1>Face Recognition</h1>

    <p>Biometric Face Authentication</p>

    <video id="video" autoplay playsinline></video>

    <br>

    <input type="text"
           id="personName"
           placeholder="Enter Name"
           style="padding:12px; width:250px; margin:10px;">

    <br>

    <button onclick="registerFace()">Register Face</button>

    <br>

    <button onclick="startCamera()">Start Camera</button>

    <button onclick="scanFace()">Scan Face</button>

    <button onclick="stopCamera()">Stop Camera</button>

    <p id="result"></p>

    <canvas id="canvas" style="display:none;"></canvas>

    <br>

    <a class="back" href="/dashboard">
        Back to Dashboard
    </a>

</div>


<script>

let stream = null;


// =========================================================
// START CAMERA
// =========================================================

function startCamera() {

    navigator.mediaDevices.getUserMedia({
        video: true
    })

    .then(function(cameraStream) {

        stream = cameraStream;

        document.getElementById("video").srcObject = stream;

        document.getElementById("result").innerText =
            "Camera Started";

    })

    .catch(function(error) {

        alert("Camera access denied or unavailable.");

        console.log(error);

    });

}


// =========================================================
// REGISTER FACE
// =========================================================

function registerFace() {

    if (!stream) {

        alert("Please start the camera first.");

        return;
    }

    const name =
        document.getElementById("personName").value.trim();

    if (!name) {

        alert("Please enter your name.");

        return;
    }

    const video =
        document.getElementById("video");

    const canvas =
        document.getElementById("canvas");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context =
        canvas.getContext("2d");

    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );

    const image =
        canvas.toDataURL("image/jpeg");


    fetch("/register_face", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            name: name,
            image: image
        })

    })

    .then(response => response.json())

    .then(data => {

        document.getElementById("result").innerText =
            data.message;

    })

    .catch(error => {

        console.log(error);

        document.getElementById("result").innerText =
            "Registration error.";

    });

}


// =========================================================
// SCAN FACE
// =========================================================

function scanFace() {

    if (!stream) {

        alert("Please start the camera first.");

        return;
    }

    const video =
        document.getElementById("video");

    const canvas =
        document.getElementById("canvas");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context =
        canvas.getContext("2d");

    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );

    const image =
        canvas.toDataURL("image/jpeg");


    fetch("/recognize", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            image: image
        })

    })

    .then(response => response.json())

    .then(data => {

        document.getElementById("result").innerText =
            data.message;

    })

    .catch(error => {

        console.log(error);

        document.getElementById("result").innerText =
            "Error occurred.";

    });

}


// =========================================================
// STOP CAMERA
// =========================================================

function stopCamera() {

    if (stream) {

        stream.getTracks().forEach(function(track) {

            track.stop();

        });

        stream = null;

        document.getElementById("video").srcObject = null;

        document.getElementById("result").innerText =
            "Camera Stopped";

    }

}

</script>

</body>

</html>
"""


# =========================================================
# LOGIN ROUTE
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["admin"] = username

            return redirect(url_for("dashboard"))

        else:

            return render_template_string(
                HTML,
                error="Invalid username or password"
            )

    return render_template_string(HTML)


# =========================================================
# DASHBOARD ROUTE
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "admin" not in session:

        return redirect(url_for("login"))

    return render_template_string(DASHBOARD)
# =========================================================
# LOGOUT ROUTE
# =========================================================

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect(url_for("login"))


# =========================================================
# FACE PAGE ROUTE
# =========================================================

@app.route("/face")
def face():

    if "admin" not in session:

        return redirect(url_for("login"))

    return render_template_string(FACE_PAGE)

# =========================================================
# REGISTER FACE
# =========================================================

@app.route("/register_face", methods=["POST"])
def register_face():

    if "admin" not in session:

        return {
            "status": "failed",
            "message": "Please login first."
        }

    try:

        data = request.json

        name = data["name"]

        image_data = data["image"]

        # Remove Base64 header
        image_data = image_data.split(",")[1]

        # Decode image
        decoded_image = base64.b64decode(image_data)

        # Convert to NumPy
        image_array = np.frombuffer(
            decoded_image,
            np.uint8
        )

        # Decode image
        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if frame is None:

            return {
                "status": "failed",
                "message": "Invalid image."
            }

        # BGR -> RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Detect faces
        face_locations = face_recognition.face_locations(
            rgb_frame
        )

        if len(face_locations) == 0:

            return {
                "status": "failed",
                "message": "No face detected. Please face the camera."
            }

        if len(face_locations) > 1:

            return {
                "status": "failed",
                "message": "Please keep only one face in camera."
            }

        # Create face encoding
        encodings = face_recognition.face_encodings(
            rgb_frame,
            face_locations
        )

        if len(encodings) == 0:

            return {
                "status": "failed",
                "message": "Could not create face encoding."
            }

        new_encoding = encodings[0]

        # Existing data
        face_data = []

        if os.path.exists("face_data.pkl"):

            try:

                with open(
                    "face_data.pkl",
                    "rb"
                ) as file:

                    face_data = pickle.load(file)

            except Exception:

                face_data = []

        # Check whether same person already exists
        for person in face_data:

            if person["name"].lower() == name.lower():

                return {
                    "status": "failed",
                    "message": "This name is already registered."
                }

        # Add new person
        face_data.append({
            "name": name,
            "encoding": new_encoding
        })

        # Save data
        with open(
            "face_data.pkl",
            "wb"
        ) as file:

            pickle.dump(
                face_data,
                file
            )

        return {
            "status": "success",
            "message": f"Face registered successfully for {name}."
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================================================
# RECOGNIZE FACE
# =========================================================

@app.route("/recognize", methods=["POST"])
def recognize():

    if "admin" not in session:
        return {
            "status": "failed",
            "message": "Please login first."
        }

    try:

        data = request.json
        image_data = data["image"]

        # Decode Base64 image
        image_data = base64.b64decode(
            image_data.split(",")[1]
        )

        image_array = np.frombuffer(
            image_data,
            np.uint8
        )

        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if frame is None:
            return {
                "status": "failed",
                "message": "Invalid image."
            }

        # BGR -> RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Detect face
        face_locations = face_recognition.face_locations(
            rgb_frame
        )

        if len(face_locations) == 0:
            return {
                "status": "failed",
                "message": "No Face Detected"
            }

        if len(face_locations) > 1:
            return {
                "status": "failed",
                "message": "Please keep only one face in camera."
            }

        # Create encoding
        face_encodings = face_recognition.face_encodings(
            rgb_frame,
            face_locations
        )

        if len(face_encodings) == 0:
            return {
                "status": "failed",
                "message": "Could not create face encoding."
            }

        unknown_encoding = face_encodings[0]

        # Check registered data
        if not os.path.exists("face_data.pkl"):
            return {
                "status": "failed",
                "message": "No registered face found."
            }

        with open("face_data.pkl", "rb") as file:
            face_data = pickle.load(file)

        # Compare face
        for person in face_data:

            registered_encoding = person["encoding"]

            match = face_recognition.compare_faces(
                [registered_encoding],
                unknown_encoding,
                tolerance=0.5
            )

            if match[0]:

                person_name = person["name"]

                now = datetime.now()

                attendance_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")

                conn = sqlite3.connect("attendance.db")
                cursor = conn.cursor()

                # Check today's attendance
                cursor.execute("""
                    SELECT id, in_time, out_time
                    FROM attendance
                    WHERE name = ?
                    AND date = ?
                    ORDER BY id DESC
                    LIMIT 1
                """, (
                    person_name,
                    attendance_date
                ))

                record = cursor.fetchone()

                # First scan = IN TIME
                if record is None:

                    cursor.execute("""
                        INSERT INTO attendance
                        (name, date, time, status, in_time, out_time, working_hours)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        person_name,
                        attendance_date,
                        current_time,
                        "Present",
                        current_time,
                        None,
                        None
                    ))

                    conn.commit()
                    conn.close()

                    return {
                        "status": "success",
                        "message":
                        f"Access Granted! Welcome {person_name}. IN Time: {current_time}"
                    }

                # Second scan = OUT TIME
                elif record[1] is not None and record[2] is None:

                    record_id = record[0]
                    in_time = record[1]

                    in_datetime = datetime.strptime(
                        in_time,
                        "%H:%M:%S"
                    )

                    out_datetime = datetime.strptime(
                        current_time,
                        "%H:%M:%S"
                    )

                    difference = out_datetime - in_datetime

                    total_seconds = int(
                        difference.total_seconds()
                    )

                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60

                    working_hours = f"{hours}h {minutes}m"

                    cursor.execute("""
                        UPDATE attendance
                        SET out_time = ?,
                            working_hours = ?
                        WHERE id = ?
                    """, (
                        current_time,
                        working_hours,
                        record_id
                    ))

                    conn.commit()
                    conn.close()

                    return {
                        "status": "success",
                        "message":
                        f"Goodbye {person_name}. OUT Time: {current_time}. Working Hours: {working_hours}"
                    }

                # Already completed
                else:

                    conn.close()

                    return {
                        "status": "success",
                        "message":
                        f"{person_name}'s attendance is already completed for today."
                    }

        return {
            "status": "failed",
            "message": "Access Denied! Face not recognized."
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }
    
# ==============================================================
# ATTENDANCE PAGE
# =========================================================
# =========================================================
# DELETE ATTENDANCE
# =========================================================

@app.route("/delete_attendance/<int:record_id>")
def delete_attendance(record_id):

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM attendance WHERE id = ?",
        (record_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("attendance"))
@app.route("/attendance")
def attendance():

    if "admin" not in session:
        return redirect(url_for("login"))
    search = request.args.get("search", "")
    date_filter = request.args.get("date", "")
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    query = """
       SELECT id, name, date, in_time, out_time, working_hours, status
FROM attendance
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND name LIKE ?"
        params.append("%" + search + "%")

    if date_filter:
        query += " AND date = ?"
        params.append(date_filter)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)

    records = cursor.fetchall()
    

    conn.close()
    attendance_html = """
    <!DOCTYPE html>
    <html>

    <head>

        <title>Attendance Records</title>

        <style>

            body {
                font-family: Arial;
                background: #f2f2f2;
                text-align: center;
                padding: 40px;
            }

            .box {
                background: white;
                width: 90%;
                max-width: 1000px;
                margin: auto;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 0 15px #ccc;
            }

            input {
                padding: 10px;
                margin: 5px;
                border: 1px solid #ccc;
                border-radius: 6px;
            }

            button {
                padding: 10px 18px;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }

            .search-btn {
                background: #1e3a8a;
            }

            .reset-btn {
                background: #666;
            }

            .delete-btn {
                background: #dc2626;
            }

            .back-btn {
                background: #1e3a8a;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 25px;
            }

            th, td {
                padding: 12px;
                border: 1px solid #ddd;
            }

            th {
                background: #1e3a8a;
                color: white;
            }

            tr:nth-child(even) {
                background: #f5f5f5;
            }

            .present {
                color: green;
                font-weight: bold;
            }

        </style>

    </head>

    <body>

    <div class="box">

        <h1>Attendance Records</h1>

        <form method="GET" action="/attendance">

            <input
                type="text"
                name="search"
                placeholder="Search Name"
                value="{{ search }}"
            >

            <input
                type="date"
                name="date"
                value="{{ date_filter }}"
            >

            <button class="search-btn" type="submit">
                Search
            </button>

            <a href="/attendance">
                <button
                    class="reset-btn"
                    type="button">
                    Reset
                </button>
            </a>

        </form>

        <table>

            <tr>
              <th>ID</th>
<th>Name</th>
<th>Date</th>
<th>In Time</th>
<th>Out Time</th>
<th>Working Hours</th>
<th>Status</th>
<th>Action</th>  
            </tr>

            {% for record in records %}
<tr>

    <td>{{ record[0] }}</td>

    <td>{{ record[1] }}</td>

    <td>{{ record[2] }}</td>

    <td>{{ record[3] or "-" }}</td>

    <td>{{ record[4] or "-" }}</td>

    <td>{{ record[5] or "-" }}</td>

    <td class="present">
        {{ record[6] }}
    </td>

    <td>
        <a href="/delete_attendance/{{ record[0] }}"
           onclick="return confirm('Delete this attendance record?');">

            <button class="delete-btn">
                Delete
            </button>

        </a>
    </td>

</tr>
           
                    

            {% endfor %}

        </table>

        <br>

        <a href="/dashboard">
            <button class="back-btn">
                Back to Dashboard
            </button>
        </a>

    </div>

    </body>

    </html>
    """

    return render_template_string(
        attendance_html,
        records=records,
        search=search,
        date_filter=date_filter
    )
    
EMPLOYEE_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Employee Attendance</title>

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            margin: 0;
            padding: 20px;
            text-align: center;
        }

        .box {
            max-width: 500px;
            margin: 30px auto;
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 3px 15px #ddd;
        }

        h1 {
            color: #1e3a8a;
        }

        video {
            width: 100%;
            max-width: 420px;
            border-radius: 12px;
            background: black;
            margin-top: 15px;
        }

        button {
            margin-top: 20px;
            padding: 14px 25px;
            border: none;
            border-radius: 8px;
            background: #1e3a8a;
            color: white;
            font-size: 17px;
            cursor: pointer;
        }

        #message {
            margin-top: 20px;
            font-weight: bold;
        }
    </style>
</head>

<body>

<div class="box">

    <h1>Employee Attendance</h1>

    <p>Face Recognition Attendance</p>

    <video id="video" autoplay playsinline></video>

    <br>

    <button onclick="captureFace()">
        Mark Attendance
    </button>

    <div id="message"></div>

</div>

<script>

const video = document.getElementById("video");

navigator.mediaDevices.getUserMedia({
    video: true
})
.then(stream => {
    video.srcObject = stream;
})
.catch(error => {
    document.getElementById("message").innerText =
        "Camera permission required.";
});

function captureFace() {

    const canvas = document.createElement("canvas");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );

    const image = canvas.toDataURL("image/jpeg");

    document.getElementById("message").innerText =
        "Checking face...";

    fetch("/employee_recognize", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            image: image
        })

    })
    .then(response => response.json())
    .then(data => {

        document.getElementById("message").innerText =
            data.message;

    })
    .catch(error => {

        document.getElementById("message").innerText =
            "Something went wrong.";

    });
}

</script>

</body>
</html>
"""
@app.route("/employee")
def employee():

    return render_template_string(EMPLOYEE_PAGE)
@app.route("/employee_recognize", methods=["POST"])
def employee_recognize():

    try:

        data = request.json
        image_data = data["image"]

        # Decode Base64 image
        image_data = base64.b64decode(
            image_data.split(",")[1]
        )

        image_array = np.frombuffer(
            image_data,
            np.uint8
        )

        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if frame is None:
            return {
                "status": "failed",
                "message": "Invalid image."
            }

        # BGR -> RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Detect face
        face_locations = face_recognition.face_locations(
            rgb_frame
        )

        if len(face_locations) == 0:
            return {
                "status": "failed",
                "message": "No Face Detected."
            }

        if len(face_locations) > 1:
            return {
                "status": "failed",
                "message": "Please keep only one face in camera."
            }

        # Create face encoding
        face_encodings = face_recognition.face_encodings(
            rgb_frame,
            face_locations
        )

        if len(face_encodings) == 0:
            return {
                "status": "failed",
                "message": "Could not create face encoding."
            }

        unknown_encoding = face_encodings[0]

        # Check registered faces
        if not os.path.exists("face_data.pkl"):
            return {
                "status": "failed",
                "message": "No registered face found."
            }

        with open("face_data.pkl", "rb") as file:
            face_data = pickle.load(file)

        # Compare face
        for person in face_data:

            registered_encoding = person["encoding"]

            match = face_recognition.compare_faces(
                [registered_encoding],
                unknown_encoding,
                tolerance=0.5
            )

            if match[0]:

                person_name = person["name"]

                now = datetime.now()

                attendance_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")

                conn = sqlite3.connect("attendance.db")
                cursor = conn.cursor()

                # Check today's attendance
                cursor.execute("""
                    SELECT id, in_time, out_time
                    FROM attendance
                    WHERE name = ?
                    AND date = ?
                    ORDER BY id DESC
                    LIMIT 1
                """, (
                    person_name,
                    attendance_date
                ))

                record = cursor.fetchone()

                # First scan = IN
                if record is None:

                    cursor.execute("""
                        INSERT INTO attendance
                        (name, date, time, status, in_time, out_time, working_hours)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        person_name,
                        attendance_date,
                        current_time,
                        "Present",
                        current_time,
                        None,
                        None
                    ))

                    conn.commit()
                    conn.close()

                    return {
                        "status": "success",
                        "message":
                        f"Welcome {person_name}! IN Time: {current_time}"
                    }

                # Second scan = OUT
                elif record[1] is not None and record[2] is None:

                    record_id = record[0]
                    in_time = record[1]

                    in_datetime = datetime.strptime(
                        in_time,
                        "%H:%M:%S"
                    )

                    out_datetime = datetime.strptime(
                        current_time,
                        "%H:%M:%S"
                    )

                    difference = out_datetime - in_datetime

                    total_seconds = int(
                        difference.total_seconds()
                    )

                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60

                    working_hours = f"{hours}h {minutes}m"

                    cursor.execute("""
                        UPDATE attendance
                        SET out_time = ?,
                            working_hours = ?
                        WHERE id = ?
                    """, (
                        current_time,
                        working_hours,
                        record_id
                    ))

                    conn.commit()
                    conn.close()

                    return {
                        "status": "success",
                        "message":
                        f"Goodbye {person_name}! OUT Time: {current_time}. Working Hours: {working_hours}"
                    }

                else:

                    conn.close()

                    return {
                        "status": "success",
                        "message":
                        f"{person_name}'s attendance is already completed for today."
                    }

        return {
            "status": "failed",
            "message": "Access Denied! Face not recognized."
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }
# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )

