from flask import Flask, render_template , jsonify
import mysql.connector
from flask import request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
# import joblib
# import sentiment_model

app = Flask(__name__)
app.secret_key = "TwitterLogin"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
# model = joblib.load('sentiment_model.joblib')

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Set up the database connection
def create_conn():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="YOUR USERNAME",
        password="YOUR PASSWORD",
        database="YOUR DATABASE NAME"

    )



@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = create_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM USER WHERE EMAIL = %s", (username,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()
        if result is not None and result[4] == password:
            user = User(result[0])
            login_user(user)
            return redirect(url_for('protected'))
        else:
            print("FAILED")

            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/index')
def home():
    # Connect to the database
    conn = create_conn()
    cursor = conn.cursor()

    # Execute a simple query
    cursor.execute("SELECT * FROM USER")
    results = cursor.fetchall()

    # Close the connection
    cursor.close()
    conn.close()

    # Render the HTML page with the query results
    return render_template('index.html', data=results)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('login.html')

@app.route('/protected')
@login_required
def protected():
    user_id = current_user.id

    conn = create_conn()
    cursor = conn.cursor()

    # cursor.execute("SELECT * FROM FEED WHERE USER_ID = %s", (user_id,))

    cursor.execute("SELECT FEED.FEED_ID, USER.FIRSTNAME, USER.LASTNAME, FEED.CONTENT, FEED.TIMESTAMP, COALESCE(COUNT_LIKES, 0), COALESCE(COUNT_RETWEETS, 0), COALESCE(COUNT_COMMENTS, 0)  FROM FEED JOIN USER ON FEED.USER_ID = USER.USER_ID LEFT JOIN (SELECT FEED_ID, COUNT(*) AS COUNT_LIKES FROM LIKES GROUP BY FEED_ID) AS LIKES_COUNT ON FEED.FEED_ID = LIKES_COUNT.FEED_ID LEFT JOIN (SELECT FEED_ID, COUNT(*) AS COUNT_RETWEETS FROM RETWEET GROUP BY FEED_ID) AS RETWEETS_COUNT ON FEED.FEED_ID = RETWEETS_COUNT.FEED_ID LEFT JOIN (SELECT FEED_ID, COUNT(*) AS COUNT_COMMENTS FROM COMMENTS GROUP BY FEED_ID) AS COMMENTS_COUNT ON FEED.FEED_ID = COMMENTS_COUNT.FEED_ID WHERE FEED.USER_ID= %s OR FEED.USER_ID IN (SELECT FOLLOWED_ID FROM FOLLOW WHERE FOLLOWER_ID= %s) ORDER BY FEED.TIMESTAMP DESC",(user_id,user_id))

    results = cursor.fetchall()

 
    feeds = [{'feed_id': row[0], 'user_name': row[1] + row [2], 'content': row[3], 'timestamp': row[4], 'likes':row[5],'retweets':row[6],'comments':row[7]} for row in results]

    for feed in feeds:
        cursor.execute("SELECT * FROM LIKES WHERE FEED_ID = %s AND USER_ID = %s", (feed['feed_id'], current_user.id))
        feed["liked_by_user"] = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return render_template('protected.html', feeds=feeds)

@app.route('/profile')
@login_required
def profile():
    conn = create_conn()
    cursor = conn.cursor()
    # Fetch user information, feeds count, followers count, and feeds
    # Replace the following lines with your actual database queries
    user_info = get_user_info()
    feeds_count = get_feeds_count()
    followers_count = get_followers_count()
    user_feeds = get_user_feeds()
        # Fetch whether the current user has liked each feed
    for feed in user_feeds:
        cursor.execute("SELECT * FROM LIKES WHERE FEED_ID = %s AND USER_ID = %s", (feed['feed_id'], current_user.id))
        feed["liked_by_user"] = cursor.fetchone() is not None


    return render_template('profile.html', user=user_info[0]['user_name'], user_email=user_info[0]['user_email'], feeds_count=feeds_count, followers_count=followers_count, feeds=user_feeds)

def get_user_info():
    user_id= current_user.id

    conn = create_conn()
    cursor = conn.cursor()

    # cursor.execute("SELECT * FROM FEED WHERE USER_ID = %s", (user_id,))

    cursor.execute("SELECT USER.FIRSTNAME, USER.LASTNAME, USER.EMAIL, USER.PASSWORD FROM USER WHERE USER.USER_ID= %s",(user_id,))

    results = cursor.fetchall()
    users = [{ 'user_name': row[0] + row [1], 'user_email': row[2], 'user_pwd': row[3]} for row in results]

    cursor.close()
    conn.close()
    return users

def get_feeds_count():
    user_id= current_user.id

    conn = create_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM FEED WHERE USER_ID= %s ",(user_id,))

    result = cursor.fetchone()
    count = result[0]

    cursor.close()
    conn.close()
    return count

def get_followers_count():
    user_id= current_user.id

    conn = create_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM FOLLOW WHERE FOLLOWED_ID= %s ",(user_id,))

    result = cursor.fetchone()
    count = result[0]

    cursor.close()
    conn.close()
    return count

def get_user_feeds():
    user_id= current_user.id

    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT FEED.FEED_ID, USER.FIRSTNAME, FEED.CONTENT, FEED.TIMESTAMP, COALESCE(COUNT_LIKES, 0), COALESCE(COUNT_RETWEETS, 0), COALESCE(COUNT_COMMENTS, 0)  FROM FEED JOIN USER ON FEED.USER_ID = USER.USER_ID LEFT JOIN (SELECT FEED_ID, COUNT(*) AS COUNT_LIKES FROM LIKES GROUP BY FEED_ID) AS LIKES_COUNT ON FEED.FEED_ID = LIKES_COUNT.FEED_ID LEFT JOIN (SELECT FEED_ID, COUNT(*) AS COUNT_RETWEETS FROM RETWEET GROUP BY FEED_ID) AS RETWEETS_COUNT ON FEED.FEED_ID = RETWEETS_COUNT.FEED_ID LEFT JOIN (SELECT FEED_ID, COUNT(*) AS COUNT_COMMENTS FROM COMMENTS GROUP BY FEED_ID) AS COMMENTS_COUNT ON FEED.FEED_ID = COMMENTS_COUNT.FEED_ID WHERE FEED.USER_ID= %s ORDER BY FEED.TIMESTAMP DESC",(user_id,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()
    feeds = [{'feed_id': row[0], 'user_id': row[1] , 'content': row[2], 'timestamp': row[3], 'likes': row[4], 'retweets': row[5], 'comments': row[6]} for row in results]

    return feeds


@app.route('/api/comments', methods=['GET'])
def get_comments():
    feed_id = request.args.get('feed_id')
    conn = create_conn()
    cursor = conn.cursor()

    if not feed_id:
        return jsonify({'error': 'Missing feed_id parameter'}), 400
    
    cursor.execute("SELECT comment_id , content, timestamp FROM COMMENTS WHERE feed_id = %s ORDER BY timestamp DESC", (feed_id,))
    
    comments = cursor.fetchall()
    cursor.close()
    
    result = []
    for comment in comments:
        result.append({
            'comment_id':comment[0],
            'content': comment[1],
            'timestamp': comment[2].strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify(result)


@app.route('/api/followers', methods=['GET'])
def followers():
    followers = get_followers()
    return jsonify(followers)

def get_followers():
    user_id= current_user.id
    conn = create_conn()
    cursor = conn.cursor()

    # Modify the query according to your database schema
    query = "SELECT * FROM user WHERE USER_ID IN (SELECT FOLLOWED_ID FROM follow WHERE FOLLOWER_ID=%s)"
    cursor.execute(query, (user_id,))

    followers = cursor.fetchall()
    cursor.close()

    return followers


@app.route('/api/submit-feed', methods=['POST'])
def submit_feed():
    data = request.get_json()
    user_id = current_user.id
    content = data['content']

    conn = create_conn()
    cursor = conn.cursor()

    query = "INSERT INTO FEED (user_id, content) VALUES (%s, %s)"
    cursor.execute(query, (user_id, content))

    conn.commit()
    cursor.close()
    conn.close()
    # sentiment = sentiment_model.predict_tweet(content,model)
    # print(sentiment)
    return jsonify({"status": "success", "message": "Feed submitted successfully"})



@app.route('/api/comment', methods=['POST'])
def add_comment():
    data = request.get_json()
    feed_id = data['feed_id']
    content = data['content']
    user_id = current_user.id;  # Assuming you've stored the user ID in the session
    try:
        conn = create_conn()
        cursor = conn.cursor()
        insert_comment_query = "INSERT INTO comments (FEED_ID, USER_ID, CONTENT) VALUES (%s, %s, %s)"
        cursor.execute(insert_comment_query, (feed_id, user_id, content))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify(success=False)

def handle_like_action(action, feed_id, user_id):
    conn = create_conn()
    cursor = conn.cursor()


    if action == "like":
        # Check if the user has already liked the post
        cursor.execute("SELECT * FROM LIKES WHERE FEED_ID = %s AND USER_ID = %s", (feed_id, user_id))
        if cursor.fetchone():
            return {"success": False}

        # Insert the like into the LIKES table
        cursor.execute("INSERT INTO LIKES (FEED_ID, USER_ID) VALUES (%s, %s)", (feed_id, user_id))
    else:  # action == "unlike"
        # Delete the like from the LIKES table
        cursor.execute("DELETE FROM LIKES WHERE FEED_ID = %s AND USER_ID = %s", (feed_id, user_id))

    # Commit the changes
    conn.commit()

    
    return {"success": True}

@app.route("/api/like", methods=["POST"])
def api_like():
    data = request.get_json()
    feed_id = data.get("feed_id")
    user_id = current_user.id
    result = handle_like_action("like", feed_id, user_id)
    return jsonify(result)


@app.route("/api/unlike", methods=["POST"])
def api_unlike():
    data = request.get_json()
    feed_id = data.get("feed_id")
    user_id = current_user.id

    result = handle_like_action("unlike", feed_id, user_id)
    return jsonify(result)



@app.route('/api/retweet', methods=['POST'])
def retweet():
    # Get the feed_id from the request
    conn = create_conn()
    cursor = conn.cursor()
    data = request.get_json()
    feed_id = data['feed_id']

    # Get the user_id from the session
    user_id = current_user.id
    # Insert the retweet into the RETWEET table
    cursor.execute("INSERT INTO RETWEET (FEED_ID, USER_ID) VALUES (%s, %s)", (feed_id, user_id))
    conn.commit()
    cursor.close()

    return jsonify(success=True)

@app.route('/api/delete_comment', methods=['POST'])
def delete_comment():
    # Get the comment_id and feed_id from the request
    data = request.get_json()
    comment_id = data['comment_id']
    feed_id = data['feed_id']
    print(data)
    # Get the user_id from the session
    user_id = current_user.id

    # Check if the user is the author of the comment or the feed
    conn = create_conn()
    cursor = conn.cursor()  
    cursor.execute("SELECT USER_ID FROM COMMENTS WHERE COMMENT_ID = %s", (comment_id,))
    comment_user_id = cursor.fetchone()[0]

    cursor.execute("SELECT USER_ID FROM FEED WHERE FEED_ID = %s", (feed_id,))
    feed_user_id = cursor.fetchone()[0]
    if int(user_id) == comment_user_id or int(user_id) == feed_user_id:
        # Delete the comment from the COMMENTS table
        print("hello")
        cursor.execute("DELETE FROM COMMENTS WHERE COMMENT_ID = %s", (comment_id,))
        conn.commit()
    else:
        return jsonify(success=False, message="You are not authorized to delete this comment."), 403

    cursor.close()

    return jsonify(success=True)

@app.route('/api/delete_feed', methods=['POST'])
def delete_feed():
    data = request.get_json()
    feed_id = data.get('feed_id')

    # Check if the feed_id is valid, otherwise return an error
    if not feed_id:
        return jsonify({"error": "Invalid feed id"}), 400

    # Delete the feed from the database
    # Replace this part with your actual database deletion logic
    success = delete_feed_from_database(feed_id)

    if success:
        return jsonify({"message": "Feed deleted successfully"}), 200
    else:
        return jsonify({"error": "Failed to delete feed"}), 500

def delete_feed_from_database(feed_id):
    conn = create_conn()
    cursor = conn.cursor() 
    cursor.execute("DELETE FROM FEED WHERE FEED_ID = %s", (feed_id,))
    conn.commit()
    return jsonify(success=True)


# @app.route('/sentiment')
# def analyze_sentiment():
#     tweet = "hello You"  # Assuming the text to analyze is in the 'text' field
#     # Perform sentiment analysis using the loaded model
#     print(tweet)
#     sentiment = sentiment_model.predict_tweet(tweet,model)
#     print(sentiment)
#     # Return the sentiment as the response
#     return sentiment



if __name__ == '__main__':
    app.run(debug=True)
