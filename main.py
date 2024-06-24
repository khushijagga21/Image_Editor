from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
import cv2
import os
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'webp', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# In-memory user storage for demonstration purposes
users = {}

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processImage(filename, operation):
    print(f"The operation is {operation} and filename is {filename}")
    img = cv2.imread(os.path.join(UPLOAD_FOLDER, filename))
    
    if img is None:
        print(f"Could not read image: {filename}")
        return None
    
    newFilename = os.path.join("static", filename)
    if operation == "cgray":
        imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif operation == "cwebp":
        newFilename = os.path.join("static", f"{filename.split('.')[0]}.webp")
        imgProcessed = img
    elif operation == "cjpg":
        newFilename = os.path.join("static", f"{filename.split('.')[0]}.jpg")
        imgProcessed = img
    elif operation == "cpng":
        newFilename = os.path.join("static", f"{filename.split('.')[0]}.png")
        imgProcessed = img
    else:
        return None
    
    cv2.imwrite(newFilename, imgProcessed)
    return newFilename

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
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
                flash(f"Your image has been processed and is available <a href='/{new_file}' target='_blank'>here</a>")
            else:
                flash("Error processing image")

            return redirect(url_for('home'))

    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user_id = len(users) + 1
        new_user = User(user_id, username, hashed_password)
        users[user_id] = new_user

        flash("Registration successful! Please login.")
        return redirect(url_for('login'))
    
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        for user in users.values():
            if user.username == username and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash("Logged in successfully!")
                return redirect(url_for('home'))
        
        flash("Invalid username or password")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!")
    return redirect(url_for('home'))

if __name__ == "__main__":
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True, port=5001)
