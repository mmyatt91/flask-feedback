from flask import Flask, render_template, redirect, session
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized

from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = "postgres:///flask_feedback"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "speakup"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)

@app.route('/')
def root():
    """Homepage or Redirect for Register"""

    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """Show form to register a new user and handle submission"""

    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
    
        user = User.register(username, password, email, first_name, last_name)
    
        db.session.commit()
        session['username'] = user.username
        return redirect(f"/users/{user.username}")
    
    else:
        return render_template("users/register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Show form to login existing user and handle submission"""

    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.authenticate(username, password)

        if user:
            session['username'] = user.username
            return redirect(f"/users/{user.username}")
        
        else:
            form.username.errors = ["Invalid Username/Password."]
            return render_template("/users/login.html", form=form)
    
    return render_template("/users/login.html", form=form)

@app.route('/logout')
def logout():
    """Clear any information and redirect to root"""

    session.pop('username')
    return redirect('/login')

@app.route('/users/<username>')
def show_user(username):
    """Example page for logged-in-users."""

    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    form = DeleteForm()

    return render_template("users/show.html", user=user, form=form)

@app.route('/users/<username>/delete')
def delete_user(username):
    """Remove user and their feedback. Clear all user info in session""" 

    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")

    return redirect('/login')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    """Display new feedback form. Handle Submission. 
    Make sure the correct user accesses their feedback"""

    if "username" not in session or username != session['username']:
        raise Unauthorized()

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(
            title=title,
            content=content,
            username=username
        )

        db.session.add(feedback)
        db.session.commit()
        return redirect(f'/users/{feedback.username}')
    
    else:
        return render_template('feedback/new.html', form=form)

@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    """Display a form to update existing feedback. Handle submission."""

    feedback = Feedback.query.get_or_404(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")
    
    return render_template("/feedback/edit.html", form=form, feedback=feedback)

@app.route('/feedback/<int:feedback_id>/delete')
def delete_feedback(feedback_id):
    """Delete feedback"""

    feedback = Feedback.query.get_or_404(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()
    
    return redirect(f"/users/{feedback.username}")