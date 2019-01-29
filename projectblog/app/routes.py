from datetime import datetime


from werkzeug.urls import url_parse

from app import app
from flask import render_template, flash, redirect, url_for
from app.forms import LoginForm, RegistrationForm, EditProfileForm,PostForm
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from flask import request
from app.model import User,Post


@app.route("/", methods = ['GET','POST'])
@app.route("/index",methods =['GET','POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data,author = current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post is now Live !")
        return redirect(url_for('index'))
    #user = {'username': "Miguel"}
    posts = current_user.followed_posts().all()
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page,app.config["POSTS_PER_PAGE"],False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page = posts.prev_num)\
        if posts.has_prev else None
    return render_template('index.html', title = 'HomePage', posts = posts.items, form=form, next_url=next_url,prev_url=prev_url)

@app.route("/explore")
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page,app.config["POSTS_PER_PAGE"],False)
    next_url = url_for( 'index', page=posts.next_num ) \
        if posts.has_next else None
    prev_url = url_for( 'index', page=posts.prev_num ) \
        if posts.has_prev else None
    return render_template('index.html', title ="Explore", posts = posts.items, next_url=next_url,prev_url=prev_url)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_passwordboolean(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user,remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc !=" ":
            next_page = url_for("index")
        return  redirect(next_page)
    else:
        return render_template("login.html", title = "Sign in" , form=form)


@app.route("/logout", methods = ['GET'])
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/registration', methods =['GET','POST'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if  form.validate_on_submit():
        user = User(username= form.username.data, email =form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user! ")
        return redirect(url_for("login"))
    return render_template('registration.html', title='register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts= user.posts.order_by(Post.timestamp.desc()).paginate(page,app.config["POSTS_PER_PAGE"], False)
    next_url = url_for('user', username=username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=username, page =posts.prev_num)\
        if posts.has_prev else None
    return render_template('user.html', user =user, posts=posts.items, next_url=next_url,prev_url=prev_url)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()



@app.route("/edit_profile/", methods = ["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if(form.validate_on_submit()):
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Changes have been saved.")
        return redirect(url_for("edit_profile"))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form = form , title = 'Edit_Profile')



@app.route("/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found' .format(username))
        return redirect(url_for("index"))
    if user==current_user:
        flash("one can not follow itself")
        return redirect(url_for('user',username=username))
    else:
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}' .format(username))
        return redirect(url_for('user',username=username))

@app.route("/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} not found ! " .format(username))
        return redirect(url_for("index"))
    if user == current_user:
        flash("you can not unfollow yourself")

    current_user.unfollow(user)
    db.session.commit()
    flash("you are not following {}" .format(username))
    return redirect(url_for('user', username=username))
