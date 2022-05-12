from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask import render_template,url_for,flash,redirect,request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,SubmitField,BooleanField,ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo,Regexp
from flask_login import LoginManager,UserMixin,login_user,current_user,logout_user,login_required
import cv2
import easyocr
import os
from flask_mail import Mail,Message
from itsdangerous import TimedJSONWebSignatureSerializer as serial
import glob

#-----------------------------------------IMPORT SECTION----------------------//--------------------------/-/-/-/-/--------------------///---------

from pytz import timezone
from datetime import datetime

ind_time = datetime.now(timezone("Asia/Kolkata"))

#-----------------------------------------INDIAN TIME----------------------//--------------------------/-/-/-/-/--------------------///---------


app=Flask(__name__)
app.config['SECRET_KEY']='585be82c3e6be0dfdc800d5b956af36b'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///site.db'
app.config['IMG_UPLOADS']="/Users/shyampatel/PycharmProjects/LASTYEARPROJECT/static/uploads"
app.config['IMG_UPLOADL']="/Users/shyampatel/PycharmProjects/LASTYEARPROJECT/static/uploadl"
db=SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager=LoginManager(app)
login_manager.login_view='login'
login_manager.login_message_category='info'
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'smartpark5436@gmail.com',
    MAIL_PASSWORD = 'Dramin5436',
))

mail = Mail(app)
#----------------------------------------------DATABASE SECTION STARTED ---------------------------------------------///-----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model,UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(20),nullable=False)
    email=db.Column(db.String(50), nullable=False, unique=True)
    username=db.Column(db.String(20), nullable=False, unique=True)
    image_file=db.Column(db.String(20),nullable=False, default='static/defaultuser.jpeg')
    password=db.Column(db.String(60), nullable=False)
    plate_no=db.Column(db.String(10), nullable=False, unique=True)

    def __repr__(self):
        return f"User('{self.username}','{self.username}','{self.email}','{self.image}','{self.plate_no}')"

    @staticmethod
    def get_token(self,expires_sec=18000):
        s=serial(app.config['SECRET_KEY'],expires_in=expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
    def verify_reset_token(token):
        s=serial(app.config['SECRET_KEY'])
        try:
            user_id=s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)
class Plateno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_no = db.Column(db.String(10), nullable=False)
    email_book = db.Column(db.String(20), nullable=False)
    Status = db.Column(db.String(20))
    date_created = db.Column(db.DateTime)
    def __repr__(self):
        return f"Plateno('{self.plate_no}','{self.requesttime}')"
class BOOKING(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    plate_no=db.Column(db.String(10),nullable=False)
    email_book=db.Column(db.String(20),nullable=False)
    Status=db.Column(db.String(20))
    date_created=db.Column(db.DateTime)
    def __repr__(self):
        return f"BOOKING('{self.plate_no}','{self.email_book}')"

#---------------------------------DATABSE CLASSES ENDED-------------------------------------------------------------------------------------


#-----------------------------------FORM CLASS STARTED -------------------------------------------------------------------------------------------------------
class registrationform(FlaskForm):
    name =StringField('Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(),Email()])
    plateno =StringField('PlateNo',validators=[DataRequired(),Regexp(regex='^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}',message='Enter PlateNumber properly'),Length(min=10,max=10)])
    password = PasswordField('Password',validators=[DataRequired()])
    confirmpasswd =PasswordField('Confirm Password',validators=[DataRequired(), EqualTo('password')])
    submit=SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username Already existed')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email Already exits , please choose a different one')

    def validate_plateno(self, plateno):
        user = User.query.filter_by(plate_no=plateno.data).first()
        if user:
            raise ValidationError('Number plate is already been registered please choose a new one')
class loginform(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Password',validators=[DataRequired()])
    remember= BooleanField('Remember Me')
    submit=SubmitField('Log In')

class updateform(FlaskForm):
    name =StringField('Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(),Email()])
    plateno =StringField('PlateNo',validators=[DataRequired(),Regexp(regex='^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}',message='Enter PlateNumber properly'),Length(min=10,max=10)])
    submit=SubmitField('Update')

    def validate_username(self, username):
        if username.data!= current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username Already existed')

    def validate_email(self, email):
        if email.data!= current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email Already exits , please choose a different one')

    def validate_plateno(self, plateno):
        if plateno.data != current_user.plate_no:
            user = User.query.filter_by(plate_no=plateno.data).first()
            if user:
                raise ValidationError('Number plate is already been registered please choose a new one')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(),Email()])
    submit=SubmitField('Reset Password')
    def validate_email(self, email):
            user = User.query.filter_by(email=email.data).first()
            if user is None:
                raise ValidationError('There is no account with this email please register')
class ResetPassword(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirmpasswd = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


#-----------------------------------WTFORM  END CLASSES-----------------------------------------------------------------------------------------------

#-----------ROUTES-------------------------------------------------------------------------------------------------------------------

@app.route("/")
def hello():
    return render_template('homepage.html')
@app.route("/register",methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))
    form=registrationform()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user=User(name=form.name.data,email=form.email.data,username=form.username.data,plate_no=form.plateno.data,password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account is created Thank you for being part of us!','success')
        return redirect(url_for('login'))
    return render_template("register.html",title='Register', form=form)
@app.route("/login",methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))
    form=loginform()
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page=request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('account'))
        else:
            flash('login unsucessful please check username and password','danger')
    return render_template("login.html",title='LogIn', form=form)
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('hello'))
@app.route("/account",methods=['GET','POST'])
@login_required
def account():
    form=updateform()
    if form.validate_on_submit():
        current_user.name=form.name.data
        current_user.username=form.username.data
        current_user.email=form.email.data
        current_user.plate_no=form.plateno.data
        db.session.commit()
        flash('your account has been updated!','success')
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.name.data= current_user.name
        form.username.data=current_user.username
        form.email.data=current_user.email
        form.plateno.data=current_user.plate_no
    return render_template("account.html", title='Account',form=form)

@app.route("/book",methods=['GET','POST'])
@login_required
def book():
   if current_user.id !=1:
        if request.method =='POST':
            if request.form['submitbutton']=='BOOK':
                plate = BOOKING.query.filter_by(plate_no=current_user.plate_no).first()
                if plate:
                    flash('Booking of plot for the particular car is already been done!','warning')
                else:
                    book=BOOKING(plate_no=current_user.plate_no,email_book=current_user.email,Status='BOOKED',date_created=datetime.now(timezone("Asia/Kolkata")))
                    de=Plateno(plate_no=current_user.plate_no,email_book=current_user.email,Status='BOOKED',date_created=datetime.now(timezone("Asia/Kolkata")))
                    db.session.add(de)
                    db.session.add(book)
                    db.session.commit()
                    flash('The plot for car having number plate '+current_user.plate_no+' is booked.','success')
            if request.method =="POST":
                if request.form['submitbutton']=='CANCEL':
                    plate = BOOKING.query.filter_by(plate_no=current_user.plate_no).first()
                    if plate:
                        de=Plateno(plate_no=current_user.plate_no,email_book=current_user.email,Status='CANCELLED',date_created=datetime.now(timezone("Asia/Kolkata")))
                        db.session.add(de)
                        db.session.delete(plate)
                        db.session.commit()
                        flash("Deleted the booking for number plate "+current_user.plate_no+" succesfully",'success')
                    else:
                        flash("No booking for "+current_user.plate_no+" is founded",'danger')
   else:
        flash('You are admin and cannot book','warning')
        return redirect(url_for('account'))
   return render_template("book.html",title='BOOK')
@app.route("/contact")
def contact():
    return render_template("contact.html",title="CONTACT US")

@app.route("/admin",methods=['GET','POST'])
@login_required
def admin():
    id=current_user.id
    if id==1:
        if request.method == 'POST':
            if request.form['upload'] == 'PARK':
                if request.files:
                    image=request.files["image"]
                    if image.filename == "":
                        flash("Please upload the incoming vehicle image", 'danger')
                        return redirect(url_for('admin'));
                    else:
                        image.save(os.path.join(app.config['IMG_UPLOADS'],image.filename))
                        list_of_files = glob.glob('/Users/shyampatel/PycharmProjects/LASTYEARPROJECT/static/uploads/*')
                        latest_file = max(list_of_files, key=os.path.getctime)
                        latest_file=str(latest_file)
                    # -----------IMAGE TO STRING -------------------------------------------------------------------------------------------------------------------
                        plat_detector = cv2.CascadeClassifier(
                            cv2.data.haarcascades + "haarcascade_russian_plate_number.xml")
                        img = cv2.imread(latest_file)
                        plates = plat_detector.detectMultiScale(img, scaleFactor=1.2,
                                                                minNeighbors=5, minSize=(25, 25))

                        for (x, y, w, h) in plates:
                            cv2.putText(img, text='License Plate', org=(x - 3, y - 3),
                                        fontFace=cv2.FONT_HERSHEY_COMPLEX, color=(0, 0, 255),
                                        thickness=1, fontScale=0.6)
                            carplate_img = img[y:y + h, x:x + w]
                            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        reader = easyocr.Reader(['en'], gpu=True)
                        result = reader.readtext(carplate_img)
                        text = result[-1][-2]
                        text = text.replace(" ", "")
                        text = text[-10:]
                        text = text.upper()
                        if (text[0] == '6'):
                            text = 'G' + text[0 + 1:]
                        if (text[2] == 'O'):
                            text = text[:2] + '0' + text[2 + 1:]
                        if (text[0] == 'N'):
                            text = 'M' + text[0 + 1:]

                        booker=BOOKING.query.filter_by(plate_no=text).first()
                        if booker:
                            l = booker.id
                            s=BOOKING.query.get(l)
                            if s.Status=="PARKED":
                                flash("This car is already Parked ",'danger')
                            else:
                                s.Status="PARKED"
                                s.date_created=datetime.now(timezone("Asia/Kolkata"))
                                de=Plateno(plate_no=booker.plate_no,email_book=booker.email_book,Status='PARKED',date_created=datetime.now(timezone("Asia/Kolkata")))
                                db.session.add(de)
                                db.session.commit()
                                flash("Booking for the car is available let the car inside",'success')
                        else:
                            flash("No booking done on this number plate",'danger')
                    dir = '/Users/shyampatel/PycharmProjects/LASTYEARPROJECT/static/uploads/'
                    filelist = glob.glob(os.path.join(dir, "*"))
                    for f in filelist:
                        os.remove(f)
        if request.method == "POST":
                if request.form['upload'] == 'LEAVE':
                        if request.files:
                            image = request.files["oimage"]
                            if image.filename == "":
                                flash("Please upload the incoming vehicle image", 'danger')
                                return redirect(url_for('admin'));
                            else:
                                image.save(os.path.join(app.config['IMG_UPLOADL'], image.filename))
                                list_of_files = glob.glob('/Users/shyampatel/PycharmProjects/LASTYEARPROJECT/static/uploadl/*')
                                latest_file = max(list_of_files, key=os.path.getctime)
                                latest_file = str(latest_file)
                                # -----------IMAGE TO STRING -------------------------------------------------------------------------------------------------------------------
                                plat_detector = cv2.CascadeClassifier(
                                    cv2.data.haarcascades + "haarcascade_russian_plate_number.xml")
                                img = cv2.imread(latest_file)
                                plates = plat_detector.detectMultiScale(img, scaleFactor=1.2,
                                                                        minNeighbors=5, minSize=(25, 25))

                                for (x, y, w, h) in plates:
                                    cv2.putText(img, text='License Plate', org=(x - 3, y - 3),
                                                fontFace=cv2.FONT_HERSHEY_COMPLEX, color=(0, 0, 255),
                                                thickness=1, fontScale=0.6)
                                    carplate_img = img[y:y + h, x:x + w]
                                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                            reader = easyocr.Reader(['en'], gpu=True)
                            result = reader.readtext(carplate_img)
                            text = result[-1][-2]
                            text = text.replace(" ", "")
                            text = text[-10:]
                            text = text.upper()
                            if (text[0] == '6'):
                                    text = 'G' + text[0 + 1:]
                            if (text[2] == 'O'):
                                    text = text[:2] + '0' + text[2 + 1:]
                            if (text[0] == 'N'):
                                text = 'M' + text[0 + 1:]

                            booker = BOOKING.query.filter_by(plate_no=text).first()
                            if booker:
                                    de=Plateno(plate_no=booker.plate_no,email_book=booker.email_book,Status='LEFT',date_created=datetime.now(timezone("Asia/Kolkata")))
                                    db.session.add(de)
                                    db.session.delete(booker)
                                    db.session.commit()
                                    flash("The car has left", 'success')
                            else:
                                    flash("The car has already left", 'danger')
                            dir = '/Users/shyampatel/PycharmProjects/LASTYEARPROJECT/static/uploadl/'
                            filelist = glob.glob(os.path.join(dir, "*"))
                            for f in filelist:
                                os.remove(f)
        return render_template("admin.html",title='ADMINISTRATION')
    else:
        flash("Sorry you are not the admin","danger")
        return redirect(url_for('account'))

def send_reset_email(user):
    token = user.get_token(user)
    msg = Message('Password Request',sender="shyam.180410107085@gmail.com",recipients=[user.email])
    msg.body=f'''TO reset your password please follow this link:
        {url_for('reset_token', token=token, _external=True)}
        YOUR CURRENT USERNAME IS {user.username}
        If you did not make this request then simply ignore this mail and no changes will be made
    '''
    mail.send(msg)
@app.route("/reset_password",methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('hello'))
    form=RequestResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Reset password sent successfully , if not received the mail please check the spam','success')
        return redirect(url_for('login'))
    return render_template('reset_request.html',title='ResetPassword',form=form)
@app.route("/reset_password/<token>",methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('hello'))
    user=User.verify_reset_token(token)
    if user is None:
        flash('That is  invalid or expired token','warning')
        return redirect(url_for('reset_request'))
    form=ResetPassword()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password=hashed_password
        db.session.commit()
        flash(f'Your password has been updated', 'success')
        return redirect(url_for('login'))
    return render_template("reset_token.html", title="Reset Password", form=form)
if __name__=='__main__':
    app.run(debug=True,port=3000)

##--------------------CURD--------------------------------------------------------------------------------------##
