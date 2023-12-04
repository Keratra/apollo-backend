from flask_jwt_extended import JWTManager, get_jwt, create_access_token, jwt_required
from pyrebase import pyrebase
import datetime
from flask import Flask, request
from flask_cors import CORS

JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=5)
JWT_SECRET_KEY = "keremsecret"

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES
jwt = JWTManager(app)
CORS(app)

fb_conf = {
  "apiKey": "AIzaSyDLpnUXs90wHnTsstqRh99FGUJcbVc2-aQ",
  "authDomain": "apollo-database-943bc.firebaseapp.com",
  "databaseURL": "https://apollo-database-943bc-default-rtdb.europe-west1.firebasedatabase.app",
  "projectId": "apollo-database-943bc",
  "storageBucket": "apollo-database-943bc.appspot.com",
  "messagingSenderId": "356351390862",
  "appId": "1:356351390862:web:56f3ea51800fbca0cd05df"
}

firebase = pyrebase.initialize_app(fb_conf)
db = firebase.database()

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'

@app.route("/admin/login", methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data["username"]
        password = data["password"]

        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            return {"message": "Invalid credentials"}, 401

        access_token = create_access_token(identity={"type": "admin"})
        return {"access_token": access_token}, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/admin/add-coffee", methods=['POST'])
@jwt_required()
def admin_add_coffee():
    try:
        jwt_token = get_jwt()
        if jwt_token["sub"]["type"] != "admin":
            return {"message": "Unauthorized"}, 401

        data = request.get_json()

        coffees = db.child("coffees").get().val()
        coffees = coffees if coffees is not None else {}
        for coffee in coffees:
            if coffees[coffee]["name"] == data["name"]:
                return {"message": "Coffee already exists"}, 400

        coffee = {
            "name": data["name"],
            "tall_price": data["tall_price"],
            "grande_price": data["grande_price"],
            "venti_price": data["venti_price"],
            "image_url": data["image_url"]
        }

        db.child("coffees").push(coffee)
        return {"message": "Coffee added successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/admin/get-coffees", methods=['GET'])
@jwt_required()
def admin_get_coffees():
    try:
        jwt_token = get_jwt()
        if jwt_token["sub"]["type"] != "admin":
            return {"message": "Unauthorized"}, 401

        coffees = db.child("coffees").get().val() if db.child("coffees").get().val() is not None else {}

        return coffees, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/admin/get-coffee", methods=['POST'])
@jwt_required()
def admin_get_coffee():
    try:
        jwt_token = get_jwt()
        if jwt_token["sub"]["type"] != "admin":
            return {"message": "Unauthorized"}, 401

        data = request.get_json()

        if "id" not in data:
            return {"message": "No coffee id is found"}, 400

        coffee_id = data["id"]
        coffee = db.child("coffees").child(coffee_id).get().val()

        if coffee is None:
            return {"message": "Coffee not found"}, 404

        return coffee, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/admin/delete-coffee", methods=['POST'])
@jwt_required()
def admin_delete_coffee():
    try:
        data = request.get_json()

        if "id" not in data:
            return {"message": "No coffee id is found"}, 400

        coffee_id = data["id"]
        db.child("coffees").child(coffee_id).remove()
        return {"message": "Coffee deleted successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/admin/get-orders", methods=['GET'])
@jwt_required()
def admin_get_orders():
    try:
        orders = db.child("orders").get().val()
        orders = orders if orders is not None else {}
        return orders, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500


@app.route("/customer/login", methods=['POST'])
def customer_login():
    try:
        data = request.get_json()
        email = data["email"]
        password = data["password"]

        users = db.child("users").get().val()
        for user in users:
            if users[user]["email"] == email:
                if users[user]["password"] != password:
                    return {"message": "Invalid credentials"}, 401
                token_identity = {"type": "customer", "id": user}
                access_token = create_access_token(identity=token_identity)
                return {"access_token": access_token}, 200

        return {"message": "Invalid credentials"}, 401

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/customer/register", methods=['POST'])
def customer_register():
    try:
        data = request.get_json()

        users = db.child("users").get().val()

        if users is not None:
            for user in users:
                if users[user]["email"] == data["email"]:
                    return {"message": "User already exists"}, 400

        db.child("users").push({
            "email": data["email"],
            "password": data["password"],
            "name": data["name"],
            "surname": data["surname"],
            "phone_number": data["phone_number"],
            "address": data["address"]
        })
        return {"message": "User added successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/customer/get-user", methods=['GET'])
@jwt_required()
def customer_get_user():
    try:
        jwt_token = get_jwt()
        if jwt_token["sub"]["type"] != "customer":
            return {"message": "Unauthorized"}, 401

        id = jwt_token["sub"]["id"]
        user = db.child("users").child(id).get().val()
        if user is None:
            return {"message": "User not found"}, 404

        user["id"] = id
        return user, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/customer/update-user", methods=['POST'])
@jwt_required()
def customer_update_user():
    try:
        jwt_token = get_jwt()
        if jwt_token["sub"]["type"] != "customer":
            return {"message": "Unauthorized"}, 401

        id = jwt_token["sub"]["id"]
        user = db.child("users").child(id).get().val()
        if user is None:
            return {"message": "User not found"}, 404

        data = request.get_json()

        db.child("users").child(id).update({
            "email": data["email"],
            "password": data["password"],
            "name": data["name"],
            "surname": data["surname"],
            "phone_number": data["phone_number"],
            "address": data["address"]
        })
        return {"message": "User updated successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/customer/get-coffees", methods=['GET'])
@jwt_required()
def customer_get_coffees():
    try:
        jwt_token = get_jwt()
        if jwt_token["sub"]["type"] != "customer":
            return {"message": "Unauthorized"}, 401

        id = jwt_token["sub"]["id"]
        user = db.child("users").child(id).get().val()
        if user is None:
            return {"message": "User not found"}, 404

        coffees = db.child("coffees").get().val()
        coffees = coffees if coffees is not None else {}

        return coffees, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/customer/make-order", methods=['POST'])
@jwt_required()
def customer_make_order():
    try:
        jwt_token = get_jwt()
        if jwt_token["sub"]["type"] != "customer":
            return {"message": "Unauthorized"}, 401

        user_id = jwt_token["sub"]["id"]
        user = db.child("users").child(user_id).get().val()
        if user is None:
            return {"message": "User not found"}, 404

        data = request.get_json()

        if "deliver_time" not in data or "coffees" not in data:
            return {"message": "Invalid data"}, 400

        if len(data["coffees"]) == 0:
            return {"message": "No coffees found"}, 400

        order = {
            "user_id": user_id,
            "user_name": user["name"],
            "user_surname": user["surname"],
            "user_address": user["address"],
            "user_phone_number": user["phone_number"],
            "deliver_time": data["deliver_time"],
            "coffees": []
        }

        order_coffees = data["coffees"]
        temp_coffees = []
        for order_coffee in order_coffees:
            coffee = db.child("coffees").child(order_coffee["id"]).get().val()
            if coffee is None:
                return {"message": "Coffee not found"}, 404

            if order_coffee["size"] not in ["tall", "grande", "venti"]:
                return {"message": "Invalid size for {}".format(order_coffee["name"])}, 400

            if order_coffee["quantity"] not in range(1, 21):
                return {"message": "Invalid size for {}".format(order_coffee["name"])}, 400

            coff = {
                "id": order_coffee["id"],
                "name": coffee["name"],
                "size": order_coffee["size"],
                "quantity": order_coffee["quantity"],
                "price": coffee[order_coffee["size"] + "_price"]
            }

            temp_coffees.append(coff)

        db.child("orders").push({
            "user_id": user_id,
            "user_name": user["name"],
            "user_surname": user["surname"],
            "user_address": user["address"],
            "user_phone_number": user["phone_number"],
            "deliver_time": data["deliver_time"],
            "coffees": temp_coffees,
            "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        })

        orders = db.child("orders").get().val()
        order_id = ""
        for order in orders:
            if orders[order]["user_id"] == user_id:
                order_id = order

        return {"message": "Order added successfully", "order_id": order_id}, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500

@app.route("/customer/get-orders", methods=['GET'])
@jwt_required()
def customer_get_orders():
    try:
        jwt_token = get_jwt()
        if jwt_token["sub"]["type"] != "customer":
            return {"message": "Unauthorized"}, 401

        user_id = jwt_token["sub"]["id"]
        user = db.child("users").child(user_id).get().val()
        if user is None:
            return {"message": "User not found"}, 404

        orders = db.child("orders").get().val()
        if orders is None:
            return {"message": "No orders found"}, 404

        user_orders = []
        for order in orders:
            if orders[order]["user_id"] == user_id:
                user_order = orders[order]
                user_order["id"] = order
                user_orders.append(user_order)

        if len(user_orders) == 0:
            return {"message": "No orders found"}, 404

        return {"user_orders": user_orders}, 200

    except Exception as e:
        print(e)
        return {"message": "Some errors are occured"}, 500


