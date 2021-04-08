from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json
import dbcreds
import mariadb
import uuid
import random
import datetime

app = Flask(__name__)
CORS(app)

def connection():
    return mariadb.connect(
        user = dbcreds.user,
        password = dbcreds.password,
        host = dbcreds.host,
        port = dbcreds.port,
        database = dbcreds.database   
    )
def resolve_login_token(loginToken):
    conn = None
    cursor = None
    userId = None
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id from user_session WHERE loginToken=?", [loginToken])
    userId = cursor.fetchone()[0]
    print("inside the loginToken function", userId)
    return userId

def resolve_username(userId):
    conn = None
    cursor = None
    username = None
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_name from user WHERE id=?", [userId])
    username = cursor.fetchone()[0]
    print("inside the username function", username)
    return username

@app.route('/api/user', methods=["GET", "POST", "DELETE"])
def user():
    #   GET A USER(S)
    if request.method == 'GET':
        conn = None
        cursor = None
        result = None
        userId = request.args.get("userId")
        print(userId)
        if userId != "":
            try:
                conn = connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id, user_name, email FROM user WHERE id=?", [userId])
                result = cursor.fetchone()
                print("line 58:", result)
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)
            finally: 
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close() 
                    return Response(
                        json.dumps(result, default=str),
                        mimetype = "application/json",
                        status=200
                    )
        else:
            try:
                conn = connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM user")
                result = cursor.fetchone()
                print("line 67:", result)
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)
            finally: 
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close() 
                    return Response(
                        json.dumps(result, default=str),
                        mimetype = "application/json",
                        status=200
                    )
                else: 
                    return Response(
                        "There was a problem finding that user.",
                        mimetype="text/html",
                        status=500
                    )

#   CREATE A NEW USER
    elif request.method == 'POST':
        conn = None
        cursor = None
        result = None
        userId = None
        parameters = request.get_json()
        email = parameters["email"]
        print(email)
        username = parameters["user_name"]
        print(username)
        password = parameters["password"]
        print(password)
        if username and password != "":
            try:
                print("inside the try")
                conn = connection()
                cursor = conn.cursor()
                cursor.execute("SELECT userId FROM user WHERE user_name=? AND password=?", [username, password])
                count = cursor.rowcount()
                if count == 1:
                    cursor.execute("INSERT INTO user(email, user_name, password) VALUES(?, ?, ?)", [email, username, password])
                    conn.commit()
                    result = cursor.rowcount
                    userId = cursor.lastrowid
                if len(result) == 1:
                    loginToken = str(uuid.uuid4())
                    try:
                        print(userId, loginToken)
                        cursor.execute("INSERT INTO user_session(id, loginToken) VALUES(?, ?)", [userId, loginToken])
                        conn.commit()
                    except Exception as ex:
                        return Response("The action was unsuccessful.", ex)
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)
            finally:
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                if(result == 1):
                    user = {
                        "userId": userId,
                        "email": email,
                        "username": username,
                        "loginToken": loginToken
                        }
                    return Response(
                        json.dumps(user, default=str),
                        mimetype = "application/json",
                        status=200
                    ) 
                else: 
                    return Response(
                        "There was a problem creating a new user account.",
                        mimetype="text/html",
                        status=500
                    )
        else: 
            return Response(
                "There was a problem creating a new user account.",
                    mimetype="text/html",
                    status=500
            )

#   DELETE A USER
    elif request.method == 'DELETE':
        conn = None
        cursor = None
        result = None
        parameters = request.get_json()
        password = parameters["password"]
        loginToken = parameters["loginToken"]
        userId = parameters["userId"]
        secureId = resolve_login_token(loginToken)
        print(userId)
        print(loginToken)
        print(secureId)
        if userId == secureId:
            try:
                conn = connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user WHERE id=?", [userId])
                result = cursor.rowcount
                conn.commit()
                print(result)
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)
            finally:
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                    return Response(
                        "Your account has been deleted",
                        mimetype = "html/text",
                        status=200
                    )
                else: 
                    return Response(
                        "There was a problem deleting that user.",
                        mimetype="text/html",
                        status=500
                    )
        else:
            return Response(
                        "You do not have permission to delete that user.",
                        mimetype="text/html",
                        status=500
                    )
                
@app.route('/api/login', methods=["POST", "DELETE"])
def login():
#   LOGIN
    if request.method == 'POST':
        conn = None
        cursor = None
        parameters = request.get_json()
        username = parameters["user_name"]
        print(username)
        password = parameters["password"]
        print(password)
        data = None
        if username !="" and password !="":
            try:
                conn = connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, email FROM user WHERE user_name=? AND password=?", [username, password])
                userdata = cursor.fetchone()
                userId = userdata[0]
                email = userdata[1]
                print("userdata is: ", userdata)
                print(userId)
                print(email)
                if userId !=0:
                    cursor.execute("SELECT * FROM user_session WHERE id=?", [userId])
                    result = cursor.fetchone()
                    count = cursor.rowcount
                    print("count:", count)
                    if count == 0:
                        loginToken = str(uuid.uuid4())
                        cursor.execute("INSERT INTO user_session(loginToken, Id) VALUES(?, ?)", [loginToken, userId])
                        count = cursor.rowcount
                        conn.commit()
                        data = {
                        "userId": userdata[0],
                        "email": userdata[1],
                        "username": username,
                        "loginToken": result[1]
                        }
                        print("data is: ", data)
                    else:
                        print("inside response")
                        data = {
                        "userId": userdata[0],
                        "email": userdata[1],
                        "username": username,
                        "loginToken": result[1]
                        }
                        return Response(
                        json.dumps(data, default=str),
                        mimetype="application/json",
                        status=200
                    )
                else:
                    return Response(
                    "That is not a valid username and password. Please try again.",
                    mimetype="text/html",
                    status=500
                    )        
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)
            except Exception as ex:
                return Response("error", ex)
            finally: 
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                    return Response(
                        json.dumps(data, default=str),
                        mimetype="application/json",
                        status=200
                    )
        else:
            return Response(
            "That is not a valid username and password. Please try again.",
            mimetype="text/html",
            status=500
            )    


#   LOGOUT
    elif request.method == 'DELETE':
        conn = None
        cursor = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        print(loginToken)
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_session WHERE loginToken=?", [loginToken])
            result = cursor.rowcount
            conn.commit()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                  "You are logged out",
                  mimetype = "html/text",
                  status=200
                 )
            else: 
                return Response(
                    "There was a problem logging out.",
                    mimetype="text/html",
                    status=500
                )
@app.route('/api/events', methods=["GET","POST", "DELETE", "PATCH"])
def events():
    # GET AN EVENT
    if request.method == 'GET':
        conn = None
        cursor = None
        results = None
        userId = request.args.get("userId")
        print("userid =", userId)

        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            if (userId != None):
                cursor.execute("SELECT * FROM event")
                cursor.fetchall()
                rows = cursor.rowcount
                print("rows", rows)
                i = 0
                while i < rows:
                    cursor.execute("SELECT e.*, c.name, c.quadrant, cat.name FROM event as e JOIN event_communities as ec ON ec.eventId=e.id JOIN communities as c ON ec.communityId=c.id JOIN event_categories as ecat ON ecat.eventId=e.id JOIN categories as cat ON ecat.categoryId=cat.id WHERE e.userId=?", [userId])
                    event = cursor.fetchone()
                    results = []
                    results.append(event)
                    print("line: 351", results)
                    i += 1

            else:
                cursor.execute("SELECT * FROM event")
                cursor.fetchall()
                rows = cursor.rowcount
                print("rows", rows)
                i = 0
                while i < rows:
                    cursor.execute("SELECT e.*, c.name, c.quadrant, cat.name FROM event as e JOIN event_communities as ec ON ec.eventId=e.id JOIN communities as c ON ec.communityId=c.id JOIN event_categories as ecat ON ecat.eventId=e.id JOIN categories as cat ON ecat.categoryId=cat.id")
                    event = cursor.fetchone()
                    results = []
                    results.append(event)
                    print("line: 365", results)
                    i += 1
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    json.dumps(results, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )

    #POST A EVENT
    elif request.method == 'POST':
        conn = None
        cursor = None
        eventId = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        userId = resolve_login_token(loginToken)
        username = resolve_username(userId) 
        eventname = parameters["event_name"]
        content = parameters["content"]
        createdAt = datetime.datetime.now()
        eventStart = parameters["event_start_date"]
        eventEnd = parameters["event_end_date"]
        expiry = parameters["event_expiry_date"]
        contact = parameters["contact_info"]
        communityIds = parameters["communityIds"]
        categoryIds = parameters["categoryIds"]
        # print(communityIds)
        # print(categoryIds)
        # print("inside the post an event")
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO event (userId, event_name, content, created_at, event_start_date, event_end_date, event_expiry_date, contact_info) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", [userId, eventname, content, createdAt, eventStart, eventEnd, expiry, contact])
            conn.commit()
            eventId = cursor.lastrowid
            for communityId in communityIds:
                # print(communityId)
                # print("inside the communityIds for loop")
                # print("line 300", eventId, communityId)
                try:
                    cursor.execute("INSERT INTO event_communities (eventId, communityId) VALUES(?, ?)", [eventId, communityId])
                    conn.commit()
                    rowcount = cursor.rowcount
                    # print(rowcount)
                    # print("inserting into event_communities")
                except Exception as ex:
                    print('EXCEPTION', ex)
            for categoryId in categoryIds:
                # print("inside the categoryIds for loop")
                try:
                    cursor.execute("INSERT INTO event_categories (eventId, categoryId) VALUES(?, ?)", [eventId, categoryId])
                    conn.commit()
                    rowcount = cursor.rowcount
                    # print("inserting into event_categories")
                except Exception as ex:
                    print('EXCEPTION', ex)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                if eventId != None:
                    eventdetails = {
                        "eventId": eventId,
                        "userId": userId,
                        "username": username,
                        "content": content,
                        "createdAt": createdAt,
                        "event_start_date": eventStart,
                        "event_end_date": eventEnd,
                        "event_expiry_date": expiry,
                        "communityIds": communityIds,
                        "categoryIds": categoryIds
                    }
                    return Response(
                        json.dumps(eventdetails, default=str),
                        mimetype = "application/json",
                        status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
    #DELETE AN EVENT
    elif request.method == 'DELETE':
        conn = None
        cursor = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        print(loginToken)
        userId = parameters["userId"]
        print(userId)
        secureId = resolve_login_token(loginToken)
        print(secureId)
        eventId = parameters["eventId"]
        print(eventId)

        if userId == secureId:
            try:
                conn = connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM event WHERE id = ?", [eventId, userId])
                result = cursor.rowcount
                conn.commit()
                print("result1", result)
                cursor.execute("DELETE FROM event_communities WHERE eventId=?", [eventId])
                result2 = cursor.rowcount
                conn.commit()
                print("result2", result2)
                cursor.execute("DELETE FROM event_categories WHERE eventid=?", [eventId])
                result3 = cursor.rowcount
                conn.commit()
                print("result3", result3)
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)  
            finally: 
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                    return Response(
                    "Your event has been deleted.",
                    mimetype = "text/html",
                    status=200
                    )
        else:
            return Response(
                "You do not have permission to delete this record.",
                mimetype="text/html",
                status=500
        )

    #PATCH EVENT DETAILS
    elif request.method == 'PATCH':
        conn = None
        cursor = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        userId = parameters["userId"]
        eventId = parameters["eventId"]
        user_name = resolve_username(userId) 
        event_name = parameters["event_name"]
        created_at = parameters["created_at"]
        content = parameters["content"]
        event_start_date = parameters["event_start_date"]
        event_end_date = parameters["event_end_date"]
        event_expiry_date = parameters["event_expiry_date"]
        contact_info = parameters["contact_info"]
        community = parameters["community"]
        category = parameters["name"]
        secureId = resolve_login_token(loginToken)
        print(userId)
        print(secureId)
        print("expiry date:", event_expiry_date)
        if userId == secureId:
            try:
                conn = connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE event SET event_name=?, content=?, created_at=?, event_start_date=?, event_end_date=?, event_expiry_date=?, contact_info=? WHERE id=?", [event_name, content, created_at, event_start_date, event_end_date, event_expiry_date, contact_info, eventId])
                conn.commit()
                result = cursor.rowcount  
                print(result)
                cursor.execute("SELECT id FROM communities WHERE name=?", [community])
                communityId = cursor.fetchone()
                cursor.execute("UPDATE event_communities SET communityId=? WHERE eventId=?", [communityId, eventId])
                conn.commit()
                rows = cursor.rowcount
                print("rows updated:", rows)
                cursor.execute("SELECT id FROM categories WHERE name=?", [name])
                categoryId = cursor.fetchone()
                cursor.execute("UPDATE event_categories SET categoryId=? WHERE eventiId=?", [categoryId, eventId])
                conn.commit()
                rows = cursor.rowcount
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)
            except Exception as ex:
                return Response("error", ex)
            finally: 
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                    if eventId != None:
                        eventdetails = {
                            "eventId": eventId,
                            "userId": userId,
                            "user_name": user_name,
                            "content": content,
                            "created_at": created_at,
                            "event_start_date": event_start_date,
                            "event_end_date": event_end_date,
                            "event_expiry_date": event_expiry_date,
                            "community": name,
                            "name": name
                        }
                        return Response(
                            json.dumps(eventdetails, default=str),
                            mimetype = "application/json",
                            status=200
                    )
                else: 
                    return Response(
                        "There was a problem completing the request.",
                        mimetype="text/html",
                        status=500
                    )
        else:
            return Response(
                "You do not have permission to edit this record.",
                mimetype="text/html",
                status=500
            )

@app.route('/api/communities', methods=["GET"])
def options():
    # GET COMMUNITIES
    if request.method == 'GET':
        conn = None
        cursor = None
        communities = None

        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name FROM communities")
            communities = cursor.fetchall()
            print("line 612 communities:", communities)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    json.dumps(communities, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
@app.route('/api/categories', methods=["GET"])
def categories():
    # GET CATEGORIES
    if request.method == 'GET':
        conn = None
        cursor = None
        categories = None
        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name FROM categories")
            categories = cursor.fetchall()
            print("line 646 categories:", categories)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    json.dumps(categories, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )