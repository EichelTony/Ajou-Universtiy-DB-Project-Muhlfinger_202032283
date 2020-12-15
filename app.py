from flask import Flask, render_template, json, request, redirect, jsonify, url_for, flash, session
from flask.ext.mysql import MySQL
import datetime
import os

mysql = MySQL()
app = Flask(__name__)

# flask MySQL configurations 
# modify user & password & database name 
app.config['MYSQL_DATABASE_USER'] = 'flaskuser'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Halog3n!'
app.config['MYSQL_DATABASE_DB'] = 'movie_demo_data' 
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

RESOURCES_FOLDER = os.path.join('static', 'resources')
app.config['UPLOAD_FOLDER'] = RESOURCES_FOLDER

app.secret_key = 'dont tell anyone'
global currentUser
global currentUserName

mysql.init_app(app)

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')

# server-side method for the UI to insteract with the MySQL
@app.route('/signUp',methods=['POST','GET'])
def signUp():
    msg = ""
	# read the posted values from the UI
    _email = request.form['inputEmail']
    _customerID = request.form['inputID']
    _password = request.form['inputPassword']

    _firstName = request.form['inputfirstName']
    _lastName = request.form['inputlastName']
    _creditcardNumber = request.form['inputcreditCard']

	# validate the received values
    if _customerID and _email and _password :
            # All Good, let's call MySQL
        try:
            conn = mysql.connect()
            cursor = conn.cursor()
            query = """INSERT INTO Customers(CustomerID, LastName, FirstName, EMailAddress, Password, CreditCard) VALUES ('%s','%s','%s','%s','%s','%s')""" %(_customerID,_firstName,_lastName,_email,_password,_creditcardNumber)
            cursor.execute(query)	
            data = cursor.fetchall() 
            # do thing with the returned table
            if len(data) is 0:
                # commit the changes made to the database 
                conn.commit()
                flash("User created successfully !!!!")
                return redirect('/showSignIn')

            else:
                return json.dumps({'error':str(data[0])})
                flashmsg =  "error: " + str(data[0])
                flash(flashmsg)
                return redirect(url_for("signUp"))

        except Exception as e:
            flashmsg = "Upps, sth went wrong, guess CustomerID is already taken: " + '' + str(e)
            flash(flashmsg)
            return redirect(url_for("showSignUp"))

    cursor.close() 
    conn.close()

@app.route('/showSignIn')
def showSignin():
    return render_template('signin.html')

@app.route("/Authenticate", methods=['POST'])
def Authenticate():
    try:
        _username = request.form['input1Email']
        _password = request.form['inputPassword']
        # connect to mysql
	conn = mysql.connect()
        cursor = conn.cursor()
	query="""SELECT * FROM customers WHERE EMailAddress='%s' AND Password='%s'""" %(_username, _password)
	cursor.execute(query)
	data = cursor.fetchone()
	# test code
	print("query:", query)
	print("data:", data)
	# do something if no tuple found 
	if len(data) is 0:
	    flash('message:Username or Password is wrong')
	else:
	    # return redirect('/')
	    print("""first tuple returned: %s %s %s""" %(data[0][0], data[0][1], data[0][2])) 
        #return render_template('index_test.html')
        
        currentUser = str(data[0])
        currentUserName = str(data[8]) 
        session['loggedin'] = True
        session['id'] = currentUser
        session['username'] = currentUserName
        
        # to put up a flashmsg, which coculd be handy sometimes --> Example of use in base.html
        #flashmsg = currentUser
        #flash(str(session['username'])+ " successfully logged in")
        
        return redirect('/showSearch')
 
    except Exception as e:
        #return json.dumps({'error':str(e)})
        flashmsg = "Username or Password is wrong !: "
        flash(flashmsg)
        return redirect(url_for("showSignin"))
    finally:
	# close connection
        cursor.close() 
        conn.close()

@app.route('/showSearch')
def showSearch():
    return render_template('search.html')

@app.route("/livesearch",methods=["POST","GET"])
def livesearch():
    
    searchbox = request.form.get("textMovie")

    query1 = "SELECT MovieName FROM movies WHERE movieName LIKE '%{}%' ORDER BY Rating DESC".format(searchbox)
    
    conn = mysql.connect()
    cursor = conn.cursor()

    query = query1

    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close() 
    conn.close()
    return jsonify(result)

@app.route('/blocksearch', methods = ["POST","GET"])
def blocksearch():        
    conn = mysql.connect()
    cursor = conn.cursor()

    queueselect = request.form['querytype']
    keyword = request.form['keywordInput']
    keyword2 = request.form['secondkeywordInput']

    # Default Value for Keyword 2 to prevent displaying all entries every time when not set.
    if keyword2 == "":
        keyword2= "|||||"

    #ToDo: --> Movies available with a particular keyword or set of keywords in the movie name
    query1 = "SELECT MovieID, MovieName, MovieType FROM movies WHERE movieName LIKE '%" + keyword + "%' OR movieName LIKE '%"+ keyword2 + "%' ORDER BY Rating DESC "
    #ToDo: -->
    query2 = "SELECT movies.MovieID, movies.MovieName, actors.ActorName FROM Actors  JOIN Movies ON  actors.movie = movies.MovieID Where actors.ActorName LIKE '%" + keyword + "%' OR actors.ActorName LIKE '%" + keyword2 + "%' "
    #ToDo: --> Movies available of a particular type
    query3 = "SELECT MovieID, MovieName, MovieType FROM movies Where MovieType LIKE '%" + keyword + "%' "
    #ToDo: --> (optional) View the Best-Seller list of movies (extra credit)
    query4 = "SELECT orders.Movie, movies.movieName, count(orders.Movie) FROM orders Join Movies ON orders.movie = movies.movieID GROUP by Movie ORDER by count(Movie) desc"

    if queueselect == "movie" or queueselect == "Movie":
        query = query1
        heading = "You searched for: MOVIE"
        column = ['MovieID:','Movie names:', 'MovieType: ','MovieID:', 'Movie names:', 'Number of Rents:', 'Best-Seller List: MOVIE' ]
        cursor.execute(query)
        result = cursor.fetchall()

        cursor.execute(query4)
        dataBestSeller = cursor.fetchall()

        cursor.close() 
        conn.close()
        return render_template('searchResult.html', data = result, data_extended = dataBestSeller, heading = heading, column = column )

    if queueselect == "actor" or queueselect == "Actor":
        query = query2
        heading = "You searched for: ACTOR"
        column = ['MovieID:','Movie played in:', 'Actor: ']
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close() 
        conn.close()
        return render_template('searchResult.html', data = result, heading = heading, column = column )

    if queueselect == "genre" or queueselect == "Genre":
        query = query3
        heading = "You searched for: GENRE"
        column = ['MovieID:','Movie names:', 'Genre:: ']
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close() 
        conn.close()
        return render_template('searchResult.html', data = result, heading = heading, column = column )

    else:
        return render_template("search.html")

@app.route('/movies')
def movies():

    if 'loggedin' in session:
        conn = mysql.connect()
        cursor = conn.cursor()

        querymovieHistory = """SELECT Orders.CustomerID, Movies.MovieName, Orders.RentDate, Orders.ReturnDate FROM Orders JOIN Movies ON  orders.movie = movies.MovieID WHERE orders.customerID = '%s' """ %(session['id'])

        cursor.execute(querymovieHistory)
        movieHistory = cursor.fetchall()
        
        if len(movieHistory) is 0:
            column = [""]
        else: 
            column = ['CustomerID:', 'MovieName:', 'Order Date:', 'Return Date:']
        cursor.close() 
        conn.close()
        return render_template('movies.html', movieHistory=movieHistory, column = column)
    
    else:
        return redirect(url_for("showSignin"))

@app.route('/selectMovies', methods = ["POST","GET"])
def selectMovies():
    requestedMovie = request.form['inputselectMovie']

    now = datetime.datetime.utcnow()
    timeofOrder =str(now.strftime('%Y-%m-%d %H:%M:%S'))
    print("now: ", now)
    print("timeofOrder: ", timeofOrder)
    
    conn = mysql.connect()
    cursor = conn.cursor()

    # check if movie exists
    querycheckforMovie = """SELECT MovieID,MovieName, NumberOfCopies FROM movies WHERE MovieName ='%s' """ %(requestedMovie)
    print("querycheckforMovie: ",querycheckforMovie)
    
    try:
        cursor.execute(querycheckforMovie)
        selectedMovieData = cursor.fetchall()
        _numberOfCopies = int(selectedMovieData[0][2])

        if _numberOfCopies > 0:
            _numberOfCopies = _numberOfCopies - 1 

            queryselectedMovie = """INSERT INTO Orders(CustomerID, Accounts, Movie, RentDate) VALUES ('%s','%s','%s','%s')""" %(session['id'], 0 ,selectedMovieData[0][0],timeofOrder)
            cursor.execute(queryselectedMovie)
            data = cursor.fetchall()

            querydecreaseMovieNumber = """UPDATE movies SET NumberOfCopies = '%s' WHERE MovieID = '%s' """ %(_numberOfCopies, selectedMovieData[0][0])
            cursor.execute(querydecreaseMovieNumber)
            data2 = cursor.fetchall()

            if len(data) is 0 and len(data2) is 0:
                # commit the changes made to the database 
                conn.commit()
                flash("Movie added successfully !!!!")
                return redirect('/movies')

            else:
                return json.dumps({'error':str(data[0])})
                flashmsg =  "error: " + str(data[0])
                flash(flashmsg)
                return redirect(url_for("/movies"))
        else:
            flashmsg = "Upps, sth went wrong: No Movies left to order !!!! " 
            flash(flashmsg)
            return redirect(url_for("movies"))
    
    except Exception as e:
        #return json.dumps({'error':str(e)})
        flashmsg = "Upps, sth went wrong: Incorrect Input => " + str(e)
        flash(flashmsg)
        return redirect(url_for("movies"))
    
    finally:
    # close connection
        cursor.close() 
        conn.close()

@app.route('/playMovies', methods = ["POST","GET"])
def playMovies():

    conn = mysql.connect()
    cursor = conn.cursor()

    querycurrentMovie = """SELECT orders.OrderID, Movies.MovieName FROM Orders JOIN Movies ON  orders.movie = movies.MovieID WHERE orders.CustomerID ='%s' AND orders.returnDate is NULL ORDER BY orders.orderID LIMIT 1 """ %(session['id'])
    cursor.execute(querycurrentMovie)
    leastMovie = cursor.fetchall()

    cursor.close() 
    conn.close()

    if len(leastMovie) is 0:
        flashmsg =  " X: No Movies left to watch !!! "
        flash(flashmsg)
        return redirect(url_for("movies"))

    else: 
        moviepreviewJPG = os.path.join(app.config['UPLOAD_FOLDER'], 'moviepreview.jpg')
        playButtonJPG = os.path.join(app.config['UPLOAD_FOLDER'], 'playbutton.jpg')
        return render_template('playMovies.html', leastMovie = leastMovie, user_image = moviepreviewJPG, play_image = playButtonJPG)

@app.route('/returnMovies', methods = ["POST","GET"])
def returnMovies():
    print("in return Movies: ")
    conn = mysql.connect()
    cursor = conn.cursor()
    
    now = datetime.datetime.utcnow()
    timeofReturn =str(now.strftime('%Y-%m-%d %H:%M:%S'))

    # check if movie exists
    querycurrentMovie = """SELECT orders.OrderID, Movies.MovieName, Movies.NumberOfCopies, Movies.MovieID FROM Orders JOIN Movies ON  orders.movie = movies.MovieID WHERE orders.CustomerID ='%s' AND orders.returnDate is NULL ORDER BY orders.orderID LIMIT 1 """ %(session['id'])
    print("querycurrentMovie: ",querycurrentMovie)
    
    try:
        print("in try: ")
        cursor.execute(querycurrentMovie)
        currentMovie = cursor.fetchall()
        print("currentMovie:",currentMovie)
        print("currentMovie:",currentMovie[0][0])
        print("currentMovie:",currentMovie[0][1])
        print("currentMovie:",currentMovie[0][2])
        _numberOfCopiesLeft = int(currentMovie[0][2])
        _numberOfCopiesLeft =+1

        queryreturnMovie = """UPDATE Orders SET ReturnDate = '%s' WHERE OrderID = '%s' """ %(timeofReturn, currentMovie[0][0])
        cursor.execute(queryreturnMovie)
        data = cursor.fetchall()
        
        queryincreaseMovieNumber = """UPDATE movies SET NumberOfCopies = '%s' WHERE MovieID = '%s' """ %(_numberOfCopiesLeft, currentMovie[0][3])
        cursor.execute(queryincreaseMovieNumber)
        data2 = cursor.fetchall()

        if len(data) is 0:
            print("in if: ")
            # commit the changes made to the database 
            conn.commit()
            flash("Movie returned successfully !!!!")
            return redirect('/movies')

        else:
            print("in except: ")
            #return json.dumps({'error':str(data[0])})
            flashmsg =  "error with the SQL: " + str(data[0])
            flash(flashmsg)
            return redirect(url_for("/"))

    except Exception as e:
        print("in except: ")
        #return json.dumps({'error':str(e)})
        if str(e) == "tuple index out of range" or str(e) == "tuple index out of range":
            flashmsg = "Upps, sth went wrong: You already gave back that movie"
        else:
            flashmsg = "Upps, sth went wrong: " + str(e) 
        flash(flashmsg)
        return redirect(url_for("/showSignin"))
    
    finally:
    # close connection
        cursor.close() 
        conn.close()
        return redirect(url_for("movies"))


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for("showSignin"))

@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        conn = mysql.connect()
        cursor = conn.cursor()

        #ToDo: --> A customer's account settings (should not be seen by the User, so now actuall use)
        query = """SELECT * FROM accounts WHERE CustomerID = '%s' """ %(session['id'])
        cursor.execute(query)
        account = cursor.fetchall()

        #ToDo: -->  A customer's "account"(= CustomerInformation) settings
        query="""SELECT * FROM customers WHERE CustomerID='%s' """ %(session['id'])
        cursor.execute(query)
        customer = cursor.fetchall()
        
        cursor.close() 
        conn.close()

        # Show the profile page with account info
        return render_template('profile.html', account=account, customer = customer)
    # User is not loggedin redirect to SigIn page
    else:
        return redirect(url_for("showSignin"))

def returnloggedinUser():
    if 'loggedin' in session:
        return session['username']
    else:
        return "No User"
    
@app.context_processor
def context_processor():
    return dict(returnloggedinUser=returnloggedinUser)

# lunch the appli tio
if __name__ == "__main__":
    app.run(debug=True)