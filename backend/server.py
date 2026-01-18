import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from datetime import datetime

from flask import Flask, redirect, session, request, url_for, jsonify
from flask_cors import CORS, cross_origin
from flask_session import Session as FlaskSession
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from sqlalchemy.orm import Session
from models import Order, OrderItem, Account, Message, engine, DATABASE_URL

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# Trust proxy headers (Railway/cloud platforms use a reverse proxy)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Use database sessions (shared across all instances)
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY_TABLE'] = 'sessions'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True  # Required for SameSite=None

# Import Flask-SQLAlchemy and configure session to use it
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)
app.config['SESSION_SQLALCHEMY'] = db
FlaskSession(app)

FRONTEND_URL = env.get("FRONTEND_URL", "http://localhost:5173")

CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "https://neighbourly.jacksmith.me",
    FRONTEND_URL
])

oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


# Auth helpers
def get_user_email():
    if 'user' in session:
        return session.get('user').get('email')
    return None


def is_authorized():
    if 'user' not in session:
        return False
    with Session(engine) as db:
        email = get_user_email()
        user = db.query(Account).filter_by(email=email).first()
        if not user:
            db.add(Account(email=email))
            db.commit()
    return True


BACKEND_URL = env.get("BACKEND_URL", "http://localhost:3000")


# Health check route
@app.route("/")
def health_check():
    return jsonify({"status": "healthy"}), 200


# Auth routes
@app.route("/login")
def login():
    callback_url = f"{BACKEND_URL}/callback"
    print(f"DEBUG: Callback URL being used: '{callback_url}'")
    print(f"DEBUG: BACKEND_URL value: '{BACKEND_URL}'")
    return oauth.auth0.authorize_redirect(redirect_uri=callback_url)


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    # Store only userinfo to keep session cookie small
    session["user"] = token.get('userinfo')
    return redirect(f"{FRONTEND_URL}/makerequest")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"https://{env.get('AUTH0_DOMAIN')}/v2/logout?" +
        urlencode({
            "returnTo": FRONTEND_URL,
            "client_id": env.get("AUTH0_CLIENT_ID"),
        }, quote_via=quote_plus)
    )


@app.route("/check-auth")
@cross_origin(supports_credentials=True)
def check_auth():
    if is_authorized():
        user = session.get('user')
        return jsonify({
            "authenticated": True,
            "email": user.get('email'),
            "name": user.get('name', user.get('nickname', 'User')),
            "picture": user.get('picture', '')
        })
    return jsonify({"authenticated": False})


# Account routes
@app.route("/account")
@cross_origin(supports_credentials=True)
def get_account():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    user = session.get('user').get('userinfo')
    return jsonify([{
        "email": user.get('email'),
        "nickname": user.get('nickname', user.get('name', 'User')),
        "verified": user.get('email_verified', False),
        "picture": user.get('picture', '')
    }])


# Request routes
@app.route("/requests")
@cross_origin(supports_credentials=True)
def get_requests():
    if not is_authorized():
        return redirect(url_for("login"))
    
    email = get_user_email()
    today = datetime.now().strftime("%Y-%m-%d")
    
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=email).first()
        # Get unfulfilled orders that haven't expired (date >= today or no date set)
        all_unfulfilled = db.query(Order).filter_by(fulfilled=None).all()
        unfulfilled = [o for o in all_unfulfilled if not o.collectionDate or o.collectionDate >= today]
        my_fulfilling = db.query(Order).filter_by(fulfilled=user.id).all()
        all_items = db.query(OrderItem).all()

        def build_order_list(orders, include_id_as="order_id"):
            if not orders:
                return [{"error": "No orders"}]
            result = []
            for order in orders:
                items = [{"name": i.name, "quantity": i.quantity} 
                        for i in all_items if i.order_id == order.id]
                entry = {
                    include_id_as: order.id,
                    "message": order.message,
                    "account_id": order.account_id,
                    "lat": order.lat,
                    "lng": order.lng,
                    "fulfilled": order.fulfilled,
                    "items": items,
                    "time": order.collectionTime,
                    "date": order.collectionDate,
                    "address": order.address
                }
                if include_id_as == "id":
                    entry["id"] = order.id
                result.append(entry)
            return result

        my_list = build_order_list(my_fulfilling, "id")
        unfulfilled_list = build_order_list(unfulfilled, "order_id")
        
        return json.dumps([my_list, unfulfilled_list])


@app.route("/deliver-personal-order")
@cross_origin(supports_credentials=True)
def get_my_orders():
    if not is_authorized():
        return redirect(url_for("login"))
    
    email = get_user_email()
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        orders = db.query(Order).filter_by(account_id=user.id).all()
        if not orders:
            return json.dumps([{"error": "No orders"}])

        result = []
        for order in orders:
            items = db.query(OrderItem).filter_by(order_id=order.id).all()
            result.append({
                "id": order.id,
                "message": order.message,
                "account_id": order.account_id,
                "lat": order.lat,
                "lng": order.lng,
                "address": order.address,
                "collectionTime": order.collectionTime,
                "collectionDate": order.collectionDate,
                "items": [{"name": i.name, "quantity": i.quantity} for i in items],
                "fulfilled": order.fulfilled,
            })
        return json.dumps(result)


@app.route("/check-order")
@cross_origin(supports_credentials=True)
def check_order():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    email = get_user_email()
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=email).first()
        if not user:
            return jsonify({"exists": False}), 404
        has_order = db.query(Order).filter_by(account_id=user.id).first() is not None
        return jsonify({"exists": has_order})


@app.route("/create-request", methods=["POST"])
@cross_origin(supports_credentials=True)
def create_request():
    if not is_authorized():
        return redirect(url_for("login"))
    
    data = request.get_json()
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=get_user_email()).first()
        order = Order(
            message=data.get("message"),
            account_id=user.id,
            lat=data.get("lat"),
            lng=data.get("lng"),
            address=data.get("address"),
            collectionTime=data.get("collectionTime"),
            collectionDate=data.get("collectionDate"),
            fulfilled=None
        )
        db.add(order)
        db.commit()

        for item in data.get("items", []):
            db.add(OrderItem(
                order_id=order.id,
                name=item['name'],
                quantity=item['quantity']
            ))
        db.commit()

    return jsonify({"success": True})


@app.route("/fulfil-request", methods=["POST"])
@cross_origin(supports_credentials=True)
def fulfil_request():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    order_id = request.get_json().get("order_id")
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=get_user_email()).first()
        order = db.query(Order).filter_by(id=order_id).first()
        order.fulfilled = user.id
        db.commit()
    return jsonify({"success": True, "order_id": order_id})


@app.route("/my-commitments")
@cross_origin(supports_credentials=True)
def get_commitments():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    email = get_user_email()
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        orders = db.query(Order).filter_by(fulfilled=user.id).all()
        result = []
        for order in orders:
            items = db.query(OrderItem).filter_by(order_id=order.id).all()
            requester = db.query(Account).filter_by(id=order.account_id).first()
            result.append({
                "id": order.id,
                "message": order.message,
                "lat": order.lat,
                "lng": order.lng,
                "address": order.address,
                "collectionTime": order.collectionTime,
                "collectionDate": order.collectionDate,
                "items": [{"name": i.name, "quantity": i.quantity} for i in items],
                "requester_email": requester.email if requester else "Unknown"
            })
        return jsonify(result)


@app.route("/unfulfil-request", methods=["POST"])
@cross_origin(supports_credentials=True)
def unfulfil_request():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    order_id = request.get_json().get("order_id")
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=get_user_email()).first()
        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            return jsonify({"error": "Order not found"}), 404
        if order.fulfilled != user.id:
            return jsonify({"error": "Not your commitment"}), 403
        order.fulfilled = None
        db.commit()
    return jsonify({"success": True})


@app.route("/complete-commitment", methods=["POST"])
@cross_origin(supports_credentials=True)
def complete_commitment():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    order_id = request.get_json().get("order_id")
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=get_user_email()).first()
        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            return jsonify({"error": "Order not found"}), 404
        if order.fulfilled != user.id:
            return jsonify({"error": "Not your commitment"}), 403
        
        # Delete order and items
        for item in db.query(OrderItem).filter_by(order_id=order.id).all():
            db.delete(item)
        db.delete(order)
        db.commit()
    return jsonify({"success": True})


@app.route("/completed-request")
@cross_origin(supports_credentials=True)
def delete_my_request():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=get_user_email()).first()
        order = db.query(Order).filter_by(account_id=user.id).first()
        if order:
            for item in db.query(OrderItem).filter_by(order_id=order.id).all():
                db.delete(item)
            # Delete associated messages
            for msg in db.query(Message).filter_by(order_id=order.id).all():
                db.delete(msg)
            db.delete(order)
            db.commit()
            return jsonify({"success": True})
        return jsonify({"error": "Order not found"}), 404


# Chat routes
@app.route("/messages/<int:order_id>")
@cross_origin(supports_credentials=True)
def get_messages(order_id):
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    email = get_user_email()
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Only requester or helper can access
        if order.account_id != user.id and order.fulfilled != user.id:
            return jsonify({"error": "Access denied"}), 403

        messages = db.query(Message).filter_by(order_id=order_id).order_by(Message.timestamp).all()
        messages_list = [{
            "id": m.id,
            "sender_email": m.sender_email,
            "content": m.content,
            "timestamp": m.timestamp,
            "is_mine": m.sender_email == email
        } for m in messages]

        # Get other user info
        other_user = None
        if order.account_id == user.id and order.fulfilled:
            helper = db.query(Account).filter_by(id=order.fulfilled).first()
            if helper:
                other_user = {"name": helper.email.split('@')[0].title(), "email": helper.email}
        elif order.fulfilled == user.id:
            requester = db.query(Account).filter_by(id=order.account_id).first()
            if requester:
                other_user = {"name": requester.email.split('@')[0].title(), "email": requester.email}

        return jsonify({
            "messages": messages_list,
            "other_user": other_user,
            "order_id": order_id
        })


@app.route("/send-message", methods=["POST"])
@cross_origin(supports_credentials=True)
def send_message():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    email = get_user_email()
    data = request.get_json()
    order_id = data.get("order_id")
    content = data.get("content")

    if not order_id or not content:
        return jsonify({"error": "Missing data"}), 400

    with Session(engine) as db:
        user = db.query(Account).filter_by(email=email).first()
        order = db.query(Order).filter_by(id=order_id).first()
        
        if not order:
            return jsonify({"error": "Order not found"}), 404
        if order.account_id != user.id and order.fulfilled != user.id:
            return jsonify({"error": "Access denied"}), 403

        msg = Message(
            order_id=order_id,
            sender_email=email,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        db.add(msg)
        db.commit()

        return jsonify({
            "success": True,
            "message": {
                "id": msg.id,
                "sender_email": msg.sender_email,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "is_mine": True
            }
        })


@app.route("/my-chats")
@cross_origin(supports_credentials=True)
def get_my_chats():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    
    email = get_user_email()
    with Session(engine) as db:
        user = db.query(Account).filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        chats = []
        
        # Requests I made with a helper assigned
        my_requests = db.query(Order).filter(
            Order.account_id == user.id,
            Order.fulfilled != None
        ).all()
        
        for order in my_requests:
            helper = db.query(Account).filter_by(id=order.fulfilled).first()
            last_msg = db.query(Message).filter_by(order_id=order.id).order_by(Message.timestamp.desc()).first()
            helper_name = helper.email.split('@')[0].title() if helper else "Unknown"
            
            chats.append({
                "order_id": order.id,
                "role": "requester",
                "other_user": {"name": helper_name, "email": helper.email if helper else ""},
                "address": order.address,
                "last_message": {
                    "content": last_msg.content,
                    "timestamp": last_msg.timestamp,
                    "is_mine": last_msg.sender_email == email
                } if last_msg else None
            })

        # Orders I'm helping with
        my_commitments = db.query(Order).filter_by(fulfilled=user.id).all()
        
        for order in my_commitments:
            requester = db.query(Account).filter_by(id=order.account_id).first()
            last_msg = db.query(Message).filter_by(order_id=order.id).order_by(Message.timestamp.desc()).first()
            requester_name = requester.email.split('@')[0].title() if requester else "Unknown"
            
            chats.append({
                "order_id": order.id,
                "role": "helper",
                "other_user": {"name": requester_name, "email": requester.email if requester else ""},
                "address": order.address,
                "last_message": {
                    "content": last_msg.content,
                    "timestamp": last_msg.timestamp,
                    "is_mine": last_msg.sender_email == email
                } if last_msg else None
            })

        return jsonify({"chats": chats})


if __name__ == "__main__":
    port = int(env.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=env.get("FLASK_DEBUG", "false").lower() == "true")
