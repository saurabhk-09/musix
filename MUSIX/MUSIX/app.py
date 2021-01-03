#from newsapi import NewsApiClient as NAC_client
from newsapi.newsapi_client import NewsApiClient as NAC_client
from flask import Flask
from flask import request
import yaml
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
import os
from flask import url_for
from flask import redirect
from werkzeug.utils import secure_filename
#from sqlalchemy.orm import relationship

is_auth=0
current_user_logged_id=-1

allowed_music_file_types=['wav','mp3','m4a','wma']
allowed_image_files_types=['jpeg','jpg','png']

default_album_image_path=''
default_artist_image_path=''

app=Flask(__name__)

uploads_path='./static/music'

#database_info=yaml.safe_load(open('/home/kumarguru/Documents/Programs/Python/MUSIX/db.yaml'))
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://root:@localhost/musicdata'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY']=os.urandom(10)
app.config['UPLOAD_FOLDER']=uploads_path
db=SQLAlchemy(app)

#User Database
#-----------------------------------------------------------------------------------------
class User(db.Model):
    __tablename__='UserInfo' 
    user_id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30),nullable=False)
    username=db.Column(db.String(30),nullable=False)
    password=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(30),nullable=False)
    phone=db.Column(db.String(15),nullable=False)
    favourites=db.Column(db.String(500),nullable=False,default='0')# holds ids of users favourite songs
    visibility=db.Column(db.Integer,default=0,nullable=False)
    profile_picture=db.Column(db.String(50),default='Unknown.jpg',nullable=False)
#--------------------------------------------------------------------------------------------

#Music Databse
#-------------------------------------------------------------------------------------------
class Music(db.Model):
    __tablename__='MusicInfo'
    song_id=db.Column(db.Integer,primary_key=True)
    song_name=db.Column(db.String(30),nullable=False)
    song_fname=db.Column(db.String(100),nullable=False)
    artist=db.relationship('Artist',backref='music',uselist=False)
    album=db.relationship('Album',backref='music',uselist=False)
#--------------------------------------------------------------------------------------------
#Artist 
#--------------------------------------------------------------------------------------------
class Artist(db.Model):
    __tablename__='ArtistInfo'
    artist_id=db.Column(db.Integer,primary_key=True)
    artist_name=db.Column(db.String(40),nullable=False,default='Unknown')
    artist_fname=db.Column(db.String(100),nullable=False,default='Unknown.jpg')
    song_id=db.Column(db.Integer,db.ForeignKey(Music.song_id))
#Album Database
#--------------------------------------------------------------------------------------------
class Album(db.Model):
    __tablename__='AlbumInfo'
    album_id=db.Column(db.Integer,primary_key=True)
    album_name=db.Column(db.String(30),nullable=False,default='Unknown')
    album_fname=db.Column(db.String(100),nullable=False,default='Unknown.jpg')
    song_id=db.Column(db.Integer,db.ForeignKey(Music.song_id))    
#--------------------------------------------------------------------------------------------
#Index Page
#-------------------------------------------------------------------------------------------
@app.route('/',methods=['POST','GET'])
def index_page():
    global is_auth,current_user_logged_id
    if request.method=='POST':
        if is_auth==0:
            print(str(current_user_logged_id))
            return redirect(url_for('user_login'))
        if 'player' in request.form:
            print('Goes to All music Here with '+str(is_auth)+" and user id is "+str(current_user_logged_id))
            return redirect(url_for('all_music'))
        if 'profile' in request.form:
            return redirect(url_for('profile',u_id=current_user_logged_id))
        if 'logout' in request.form:
            return redirect(url_for('log_out'))
    news_client=NAC_client(api_key='f8fd249bda5f49c1b1ed79d08e99440d')
    try:
        all_news=news_client.get_top_headlines(q='music')
    except:
        all_news=None
    all_users=User.query.all()
    all_songs=Music.query.all()
    all_albums=Album.query.all()
    all_artists=Artist.query.all()
    dashboard_data=dashboard_wrapper(all_users,all_songs,all_albums,all_artists)
    news_list=[]
    if all_news==None:
        news_list='No Internet Error Encountered while Fetching News'
    else:
        for news_obj in all_news['articles']:
            news_list.append(news_obj)
    return render_template("index.html",news_data=news_list,dash_data=dashboard_data,is_auth=is_auth)
    
#-------------------------------------------------------------------------------------------
#Login Functionality
#---------------------------------------------------------------------------------------------
@app.route('/login/',methods=['POST','GET'])
def user_login():
    global is_auth,current_user_logged_id    
    if request.method=='POST':
        if 'signup' in request.form:
            return redirect(url_for('sign_up'))
        data=User.query.all()
        u_n=request.form['username']
        p=request.form['password']
        #print(data)
        for i in data:
            if (i.username==u_n and check_password_hash(i.password,p)):
                print('was here')
                current_user_logged_id=i.user_id
                is_auth=1
                return redirect(url_for('index_page'))
        return render_template('login.html',data='fail')
    return render_template('login.html',data='no_attempt')
#------------------------------------------------------------------------------------------------
#Edit Profile
#------------------------------------------------------------------------------------------------
@app.route('/edit_profile/<int:u_id>/',methods=['GET','POST'])
def edit_profile(u_id):
    global is_auth,current_user_logged_id
    user_data=User.query.filter_by(user_id=current_user_logged_id).first()
    if is_auth==0 or current_user_logged_id!=u_id:
        current_user_logged_id=-1
        is_auth=0
        return redirect(url_for('user_login')) 
    if request.method=='POST':#Making Changes
        session_profile_edit=db.session
        old_data=User.query.filter_by(user_id=u_id).first()
        u_name=request.form['uname']
        print(u_name)
        name=request.form['name']
        pass_old=request.form['password']
        print(pass_old)
        print(old_data.password)
        pass_new=request.form['new_password']
        ph=request.form['phone']
        em=request.form['email']
        try:
            prof_pic=request.files['profile_pic']
        except:
            prof_pic=False
        if pass_new!="":       
            if check_password_hash(old_data.password,pass_old)==False:
                return render_template('edit_profile.html',data=user_data,error="Password Entered is Incorrect")
        if prof_pic:
            if  not file_validate(prof_pic.filename,'image'):
                return render_template('edit_profile.html',data=user_data,error="Improper File Format")
        old_data.name=name
        old_data.username=u_name
        if pass_new!="":
            old_data.password=generate_password_hash(pass_new)
        old_data.phone=ph
        old_data.email=em
        print(prof_pic)
        if prof_pic:
            if prof_pic.filename!='':
                sec_prof_picname=secure_filename(prof_pic.filename)
                prof_pic.save(os.path.join('static/img/profile',sec_prof_picname))
                old_data.profile_picture=sec_prof_picname
        else:
            old_data.profile_picture=old_data.profile_picture

        try:
            session_profile_edit.commit()
        except Exception as e:
            session_profile_edit.rollback()
            session_profile_edit.flush()
            print(e)
            return render_template('edit_profile.html',data=user_data,error='Database Error')
        print("ALL SUCCESS")
        return redirect(url_for('profile',u_id=current_user_logged_id))
        # here changes are made and redirected to the profile page
        #commit changes to DB
    return render_template('edit_profile.html',data=user_data,error=None)
#------------------------------------------------------------------------------------------------
#Profile Page
#------------------------------------------------------------------------------------------------
@app.route('/user_profile/<int:u_id>',methods=['POST','GET'])
def profile(u_id):
    global is_auth,current_user_logged_id
    if is_auth==0:
        current_user_logged_id=-1
        is_auth=0
        return redirect(url_for('user_login'))
    if request.method=='POST':
        return redirect(url_for('edit_profile',u_id=u_id))
    try:
        profile_data=User.query.filter_by(user_id=u_id).first()
        return render_template('profile.html',data=profile_data)
    except:
        return 'ERROR PROFILE NOT FOUND'
#------------------------------------------------------------------------------------------------

#Signup Page
#------------------------------------------------------------------------------------------------
@app.route('/signup/',methods=['POST','GET'])
def sign_up():
    global is_auth,current_user_logged_id
    if request.method=='POST':
        if 'login' in request.form:
            return redirect(url_for('user_login'))
        n=request.form['name']
        u_n=request.form['uname']
        p=request.form['password']
        em=request.form['email']
        ph=request.form['phone']
        rpw=request.form['rpassword']
        if rpw!=p:
            return render_template('signup.html',error="Passwords Do Not Match")
        query_all=User.query.all()
        for user in query_all:
            if u_n==user.username:
                return render_template('signup.html',error="Username Already Exists")
            if em==user.email:
                return  render_template('signup.html',error="Email Already Exists")
            if ph==user.phone:
                return render_template('signup.html',error="Phone Number Already Exists")
        session_a=db.session
        insert_data=User(name=n,username=u_n,password=generate_password_hash(p),email=em,phone=ph)
        try:
            session_a.add(insert_data)
            session_a.commit()
        except:
            session_a.rollback()
            session_a.flush()
        return redirect(url_for('user_login'))
    return render_template('signup.html',error=None)

#Edit Profile
# ---------------------------------------------------------------------------------------------
#@app.route('/edit_profile/<int:uid>',methods=['POST','GET'])
#def edit_profile(uid):
    #Edit Logic Here
#----------------------------------------------------------------------------------------------
def file_validate(fname,ftype):
    if fname=='':
        return False
    if ftype=='music':
        if '.' in fname and fname.rsplit('.',1)[1].lower() in allowed_music_file_types:
            return True
    elif ftype=='image':
        if '.' in fname and fname.rsplit('.',1)[1].lower() in allowed_image_files_types:
            
            return True
    else:
        print("I WAS HERE")
        return False
    print("OR HERE")
    return False
#Upload Music
#----------------------------------------------------------------------------------------------
@app.route('/upload_music/',methods=['POST','GET'])
def upload_song():
    global is_auth,current_user_logged_id
    if is_auth==0:
        return redirect(url_for('user_login'))
    if request.method=='POST':
        #song_path=""
        song_fname=''
        song_name=request.form['song_name']
        artist_name=request.form['artist_name']
        album_name=request.form['album_name']
        if 'song_input' not in request.files or song_name=='':
            #No file part in request
            return render_template('music_upload.html',data={'error':'No music file uploaded'})
        s_file=request.files['song_input']
        if s_file and file_validate(s_file.filename,'music'):
            song_fname=secure_filename(s_file.filename)
            s_file.save(os.path.join(app.config['UPLOAD_FOLDER'],song_fname))
            #song_path=os.path.join(app.config['UPLOAD_FOLDER'],song_fname)
        else:
            return render_template('music_upload.html',data={'error':'Incorrect format of music file uploaded'})
        album_fname=""
        artist_fname=""
        
        if "artist_image_input" not in request.files:
            artist_fname='Unknown.jpg'
        else:
            artist_img_file=request.files['artist_image_input']
            if not artist_img_file:
                artist_fname='Unknown.jpg'
            elif artist_img_file and file_validate(artist_img_file.filename,'image'):
                artist_fname=secure_filename(artist_img_file.filename)
                artist_img_file.save(os.path.join('./static/img/artist',artist_fname))
                #artist_path=os.path.join('./static/img/artist',artist_fname)
            else:
                return render_template('music_upload.html',data={'error':'Incorrect format of image file uploaded'})
        if "album_image_input" not in request.files:
            album_fname='Unknown.jpg'
        else:
            album_img_file=request.files['album_image_input']
            if not album_img_file:
                album_fname='Unknown.jpg'
            elif file_validate(album_img_file.filename,'image'):
                album_fname=secure_filename(album_img_file.filename)
                album_img_file.save(os.path.join('./static/img/album',album_fname))
                #album_path=os.path.join('./static/img/album',album_fname)
            else:
                return render_template('music_upload.html',data={'error':'Incorrect format of image file uploaded'})
        session_new_music=db.session
        new_song=Music(song_name=song_name,song_fname=song_fname)
        new_alb=Album(album_name=album_name,album_fname=album_fname,music=new_song)
        new_art=Artist(artist_name=artist_name,artist_fname=artist_fname,music=new_song)
        try:
            session_new_music.add(new_song)
            session_new_music.commit()
            session_new_music.add(new_alb)
            session_new_music.commit()
            session_new_music.add(new_art)
            session_new_music.commit()
        except Exception as e:
            session_new_music.rollback()
            session_new_music.flush()
            return render_template('music_upload.html',data={'error':str(e)})
        return redirect(url_for('all_music'))
    return render_template('music_upload.html',data={'error':'None'})
#-----------------------------------------------------------------------------------------------
#class to wrap music objects
#-----------------------------------------------------------------------------------------------
class music_wrapper:
    def __init__(self,music_data):
        self.song_name=music_data.song_name
        self.song_fname=music_data.song_fname
        self.song_id=music_data.song_id
        self.artist_name=music_data.artist.artist_name
        self.album_name=music_data.album.album_name 
        self.artist_fname=music_data.artist.artist_fname
        self.album_fname=music_data.album.album_fname

#-----------------------------------------------------------------------------------------------
#class to wrap dashboard data
#-----------------------------------------------------------------------------------------------
class dashboard_wrapper:
    def __init__(self,user_stats,song_stats,album_stats,artist_stats):
        self.user_count=len(user_stats)
        self.song_count=len(song_stats)
        album_name_list=[]
        for alb in album_stats:
            album_name_list.append(alb.album_name)
        self.album_count=len(set(album_name_list))
        artist_name_list=[]
        for art in artist_stats:
            artist_name_list.append(art.artist_name)
        self.artist_count=len(set(artist_name_list))
#-----------------------------------------------------------------------------------------------
#the main music player page
#-----------------------------------------------------------------------------------------------
@app.route('/play_music/',methods=['GET','POST'])
def all_music():  
    global is_auth,current_user_logged_id
    if is_auth==0:
        return redirect(url_for('user_login'))
    if request.method=='POST': #To add a song to favourites
        if 'upload' in request.form:
            return redirect(url_for('upload_song')) 
        if 'filter' in request.form: 
            return redirect(url_for('favourite_songs'))   
        sess=db.session
        user_pref=User.query.filter_by(user_id=current_user_logged_id).first()
        li=[]
        for i in request.form:
            li.append(i)
        print(li)
        user_pref.favourites=','.join(li)
        print(user_pref.favourites)
        try:
            sess.commit()
        except:
            sess.flush()
            sess.rollback()
            return 'DB ERROR'
        return redirect(url_for("index_page"))
    all_music_data=Music.query.all()
    music_list=[]
    user_data=User.query.filter_by(user_id=current_user_logged_id).first()
    favourites=[]
    favourites=user_data.favourites
    print(favourites)
    favourites=favourites.split(',')
    print(favourites)
    if favourites[0]=='':
        favourites=[]
    for i in range(len(favourites)):
        favourites[i]=int(favourites[i])
    print(favourites)
    for song in all_music_data:
        music_list.append(music_wrapper(song))
    return render_template('player.html',data=music_list,favourites=favourites)
#display favourites
#-----------------------------------------------------------------------------------------------
@app.route('/favourites/',methods=['POST','GET'])
def favourite_songs():
    if is_auth==0:
         return redirect(url_for('user_login'))
    user_data=User.query.filter_by(user_id=current_user_logged_id).first()
    music_list=Music.query.all()
    music_data=[]
    for song in music_list:
        music_data.append(music_wrapper(song))
    #music_data=music_wrapper(music_data)
    favourites=user_data.favourites
    favourites=favourites.split(',')
    if favourites[0]=='':
        favourites=[]
    for i in range(len(favourites)):
        favourites[i]=int(favourites[i])
    
    user_favourites=[]
    print(len(music_data))
    for m in music_data:
        print("here"+str(m.song_id))
        if m.song_id in favourites:            
            user_favourites.append(m)
    print(user_favourites)
    return render_template('favourites.html',data=user_favourites)
#-----------------------------------------------------------------------------------------------
#logout functionality
#-----------------------------------------------------------------------------------------------
@app.route('/logout/',methods=['POST','GET'])
def log_out():
    global is_auth,current_user_logged_id
    is_auth=0
    current_user_logged_id=-1
    return redirect(url_for('index_page'))
#-----------------------------------------------------------------------------------------------
#show song information
#-----------------------------------------------------------------------------------------------
@app.route('/view_music_data/<int:s_id>',methods=['POST','GET'])
def view_data(s_id):
    if is_auth==0:
        return redirect(url_for('user_login'))
    song_data=Music.query.filter_by(song_id=s_id).first()
    m_data=music_wrapper(song_data)
    return render_template('music_info.html',music_data=m_data)
    
#-----------------------------------------------------------------------------------------------
#Running The Server
#-----------------------------------------------------------------------------------------------
if __name__=='__main__':
    db.create_all()
    app.run(port=8081,debug=True)
#-----------------------------------------------------------------------------------------------
