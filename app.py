import requests
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Shopware API Credentials
SHOPWARE_URL = "http://localhost/api"
CLIENT_ID = "SWIATVFODMHYZXL0UKNPM1DVDG"
CLIENT_SECRET = "d0xmRmxMMU5YenVORkhKdU9MUWtNbTM2QzN1T2NaZGR0R1RhQVo"
OPENAI_KEY = "sk-proj-5Eiv22yTbgiMlMxyMSoWT3BlbkFJeNvkqhoDOiGsv1pmXSKw"

openai_client = openai.OpenAI(api_key=OPENAI_KEY)

def get_shopware_token():
    """Generate a new Shopware API token."""
    try:
        endpoint = f"{SHOPWARE_URL}/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
        response = requests.post(endpoint, json=payload)
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("Generated new Shopware token.")
            return token
        else:
            print(f"Error getting token: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Exception in get_shopware_token: {str(e)}")
        return None

SHOPWARE_ACCESS_TOKEN = get_shopware_token()


HEADERS = {
    "Authorization": f"Bearer {SHOPWARE_ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def fetch_products():
    """Fetch products from Shopware store"""
    try:
        endpoint = f"{SHOPWARE_URL}/product"
        response = requests.get(endpoint, headers=HEADERS)

        if response.status_code == 200:
            products = response.json().get('data', [])
            print(f"Fetched {len(products)} products from Shopware")
            return products
        else:
            print(f"Error fetching products: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        print(f"Exception in fetch_products: {str(e)}")
        return []

def fetch_orders():
    """Fetch orders from Shopware store"""
    try:
        endpoint = f"{SHOPWARE_URL}/order"
        response = requests.get(endpoint, headers=HEADERS)

        if response.status_code == 200:
            orders = response.json().get('data', [])
            print(f"Fetched {len(orders)} orders from Shopware")
            return orders
        else:
            print(f"Error fetching orders: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        print(f"Exception in fetch_orders: {str(e)}")
        return []

def format_product_context():
    """Format product data for AI response"""
    products = fetch_products()
    print(f"Formatting {len(products)} products")

    context = f"Store Products (Total: {len(products)}):\n"
    
    for product in products:
        try:
            title = product.get('name', 'No Name')
            price = product.get('price', {}).get('gross', 'N/A')
            stock = product.get('stock', 'N/A')
            
            context += f"- {title} | Price: ${price} | Stock: {stock} units\n"
        except Exception as e:
            print(f"Error formatting product {product.get('name', 'unknown')}: {str(e)}")
            continue
    
    print("Product context created successfully")
    return context

def format_order_context():
    """Format order data for AI response"""
    orders = fetch_orders()
    print(f"Formatting {len(orders)} orders")

    context = f"Recent Orders (Total: {len(orders)}):\n"
    
    for order in orders:
        try:
            order_number = order.get('orderNumber', 'N/A')
            email = order.get('orderCustomer', {}).get('email', 'N/A')
            total = order.get('price', {}).get('totalPrice', 'N/A')
            
            context += f"- Order #{order_number} | Customer: {email} | Total: ${total}\n"
        except Exception as e:
            print(f"Error formatting order {order.get('orderNumber', 'unknown')}: {str(e)}")
            continue
    
    print("Order context created successfully")
    return context

def get_gpt_response(question: str, context: str):
    """Get AI-generated response using OpenAI"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Shopware store assistant. Answer questions based on store data."},
                {"role": "user", "content": f"Store Data:\n\n{context}\n\nQuestion: {question}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in GPT response: {str(e)}")
        return f"Sorry, I encountered an error: {str(e)}"

@app.route('/ask/product', methods=['POST'])
def ask_product():
    """Handle product-related questions"""
    try:
        print("Received product question request")
        data = request.json
        question = data.get("question", "")
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        context = format_product_context()
        print(f"Product context created: {len(context)} characters")
        
        answer = get_gpt_response(question, context)
        print("Generated GPT response successfully")
        
        return jsonify({"answer": answer})
    
    except Exception as e:
        print(f"Error in product endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/ask/order', methods=['POST'])
def ask_order():
    """Handle order-related questions"""
    try:
        print("Received order question request")
        data = request.json
        question = data.get("question", "")
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        context = format_order_context()
        print(f"Order context created: {len(context)} characters")
        
        answer = get_gpt_response(question, context)
        print("Generated GPT response successfully")
        
        return jsonify({"answer": answer})
    
    except Exception as e:
        print(f"Error in order endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
