from flask import Flask, render_template, request, redirect, url_for, session
import secrets
import sqlite3
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
# Sample events data
events = [
    {
        "id": 1,
        "title": "Event 1",
        "description": "Description of Event 1",
        "organiser": "org1"
    },
    {
        "id": 2,
        "title": "Event 2",
        "description": "Description of Event 2",
        "organiser": "org1"
    },
]

# Sample users data
users = [{
    "username": "org1@g.com",
    "password": "password",
    "type": "organisation"
}, {
    "username": "user1@g.com",
    "password": "password",
    "type": "user"
}, {
    "username": "admin@g.com",
    "password": "password",
    "type": "admin"
}]

conn = sqlite3.connect('users.db')
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT, type TEXT)''')

conn.commit()
conn.close()

@app.route('/')
def index():
  return render_template('index.html')
  
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_organization = request.form.get('is_organization') == 'on'
        type = 'organization' if is_organization else 'user'
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password, type) VALUES (?, ?, ?)", (username, password, type))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))

    # If the request method is GET, render the registration form
    return render_template("signup.html")

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#   if request.method == 'POST':
#     try:
#       username = request.form['username']
#       password = request.form['password']
#       user = next(
#           (user for user in users
#            if user['username'] == username and user['password'] == password),
#           None)
#       if user:
#         session['user'] = username
#         session['user_type'] = user['type']
#         return redirect(url_for('dashboard'))
#       else:
#         return render_template('login.html',
#                                error="Invalid username or password")
#     except Exception as e:
#       return render_template('login.html',
#                              error="An error occurred: {}".format(str(e)))
#   return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            conn = sqlite3.connect('users.db')
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cur.fetchone()

            if user and user[1] == password:
                session['user'] = username
                session['user_type'] = user[2]
                conn.close()  # Close the database connection
                return redirect(url_for('dashboard'))
            else:
                conn.close()  # Close the database connection
                return render_template('login.html', error="Invalid username or password")
        except Exception as e:
            return render_template('login.html', error="An error occurred: {}".format(str(e)))
    return render_template('login.html')

@app.route('/logout')
def logout():
  session.pop('user', None)
  session.pop('user_type', None)
  return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
  if 'user' in session:
    user_type = session.get('user_type', None)
    if user_type == 'organisation':
      return redirect(url_for('organization_dashboard'))
    elif user_type == 'user':
      return redirect(url_for('user_dashboard'))
    elif user_type == 'admin':
      return redirect(url_for('admin_dashboard'))
  return redirect(url_for('login'))


@app.route('/user_dashboard')
def user_dashboard():
  if 'user' in session and session.get('user_type') == 'user':
    return render_template('user_dashboard.html', user=session['user'])
  return redirect(url_for('login'))


@app.route('/organization_dashboard')
def organization_dashboard():
  if 'user' in session and session.get('user_type') == 'organisation':
    # Logic to retrieve organization-specific data (events, sign-ups, etc.)
    return render_template('organization_dashboard.html',
                           organization=session['user'],
                           events=events)
  return redirect(url_for('login'))


@app.route('/admin_dash')
def admin_dashboard():
  if 'user' in session and session.get('user_type') == 'admin':
    return render_template('admin_dashboard.html', user=session['user'])
  return redirect(url_for('login'))


@app.route('/opportunities')
def opportunities():
  if 'user' in session:
    user_type = session.get('user_type')
    if user_type == "user" or user_type == 'organisation' or user_type == 'admin':
      return render_template('opportunities.html',
                             events=events,
                             user_type=user_type)
  return redirect(url_for('login'))


@app.route('/event/<int:event_id>')
def event_details(event_id):
  # Logic to retrieve event details from database
  event = next((event for event in events if event['id'] == event_id), None)
  if event:
    return render_template('event_details.html', event=event)
  return "Event not found"


@app.route('/signup/<int:event_id>', methods=['POST'])
def sign_up_for_event(event_id):
  # Logic to sign up for event
  # This could involve adding the event to the user's list of signed-up events in the database
  return redirect(url_for('volunteered'))


@app.route('/volunteered')
def volunteered():
  # Logic to retrieve volunteered events for the user
  # This could involve querying the database for events the user has signed up for
  return render_template('volunteered.html')

@app.route('/skills', methods=["GET", "POST"])
def skills():
    if 'user' in session:
        # User is logged in, render the skills.html template
        return render_template("skills.html", username=session['user'])
    else:
        # User is not logged in, redirect to the login page
        return redirect(url_for('index'))

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
  if request.method == 'POST':
    # Process the form data to add a new event
    event_title = request.form['title']
    event_description = request.form['description']
    # Add more fields as needed
    # Example: Save the new event to the events list or database
    events.append({
        "id": len(events) + 1,
        "title": event_title,
        "description": event_description
    })
    return redirect(url_for('opportunities'))
  else:
    # Render the form to add a new event
    return render_template('add_event.html')


# Routes for admin to delete or edit events
@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
  # Check if the user is an admin (You may have a function or logic to do this)
  if 'user' in session and session.get('user_type') == 'admin':
    if request.method == 'POST':
      # Logic to update the event in the events list or database
      event = next((event for event in events if event['id'] == event_id),
                   None)
      if event:
        event['name'] = request.form['name']
        event['description'] = request.form['description']
        event['location'] = request.form['location']
        event['date'] = request.form['date']
        event['time'] = request.form['time']
        event['contact_email'] = request.form['contact_email']
        return redirect(url_for(
            'opportunities'))  # Redirect to opportunities page after editing
    else:
      # Fetch the event details for editing
      event = next((event for event in events if event['id'] == event_id),
                   None)
      if event:
        return render_template('edit_event.html', event=event)
      else:
        return "Event not found"
  else:
    return redirect(
        url_for('login'))  # Redirect to login if the user is not an admin


@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
  # Logic to delete event
  if 'user' in session:
    event = next((event for event in events if event['id'] == event_id), None)
    if event and (session['user_type'] == 'admin'
                  or event['organiser'] == session['user']):
      events.remove(event)
  return redirect(url_for('opportunities'))


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=81)
