from flask import Flask, render_template, request, flash, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
import cv2
import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

# MongoDB connection
client = MongoClient('mongodb://localhost:27017')
db = client['your_database_name']
users_collection = db['users']

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'webp', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processImage(filename, operation):
    print(f"the operation is {operation} and filename is {filename}")
    img = cv2.imread(f"uploads/{filename}")
    match operation:
        case "cgray":
            imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            newFilename = f"static/{filename}"
            cv2.imwrite(newFilename, imgProcessed)
            return newFilename
        case "cwebp": 
            newFilename = f"static/{filename.split('.')[0]}.webp"
            cv2.imwrite(newFilename, img)
            return newFilename
        case "cjpg": 
            newFilename = f"static/{filename.split('.')[0]}.jpg"
            cv2.imwrite(newFilename, img)
            return newFilename
        case "cpng": 
            newFilename = f"static/{filename.split('.')[0]}.png"
            cv2.imwrite(newFilename, img)
            return newFilename
    pass

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/edit", methods=["GET", "POST"])
def edit():
    processed_file = None
    if request.method == "POST":
        operation = request.form.get("operation")
        
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_file = processImage(filename, operation)
            
            if new_file:
                processed_file = new_file.replace("static/", "")
                flash("Your image has been processed and is available below.")
            else:
                flash("Error processing image")

    return render_template("index.html", processed_file=processed_file)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        # Check if username exists in MongoDB
        user = users_collection.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            # Correct credentials, set up session
            session['logged_in'] = True
            session['username'] = username
            flash('Logged in successfully!')
            return redirect(url_for('edit'))  # Redirect to edit page or dashboard
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route("/logout")
def logout():
    # Clear session variables
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Logged out successfully!')
    return redirect(url_for('home'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        if users_collection.find_one({'username': username}):
            flash('Username already exists. Please choose another.')
            return redirect(url_for('signup'))
        
        # Hash the password before storing
        hashed_password = generate_password_hash(password, method='sha256')
        
        # Insert new user into MongoDB
        new_user = {
            'username': username,
            'password': hashed_password
        }
        users_collection.insert_one(new_user)
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory('static', filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
