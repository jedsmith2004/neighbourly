#!/usr/bin/env python
"""
Populate the database with 100 sample requests across the UK.
Run this script to add demo data for testing/demonstration purposes.
"""
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import engine, Account, Order, OrderItem

# UK cities with approximate coordinates
UK_LOCATIONS = [
    {"city": "London", "lat": 51.5074, "lng": -0.1278},
    {"city": "Manchester", "lat": 53.4808, "lng": -2.2426},
    {"city": "Birmingham", "lat": 52.4862, "lng": -1.8904},
    {"city": "Leeds", "lat": 53.8008, "lng": -1.5491},
    {"city": "Glasgow", "lat": 55.8642, "lng": -4.2518},
    {"city": "Liverpool", "lat": 53.4084, "lng": -2.9916},
    {"city": "Newcastle", "lat": 54.9783, "lng": -1.6178},
    {"city": "Sheffield", "lat": 53.3811, "lng": -1.4701},
    {"city": "Bristol", "lat": 51.4545, "lng": -2.5879},
    {"city": "Edinburgh", "lat": 55.9533, "lng": -3.1883},
    {"city": "Cardiff", "lat": 51.4816, "lng": -3.1791},
    {"city": "Belfast", "lat": 54.5973, "lng": -5.9301},
    {"city": "Nottingham", "lat": 52.9548, "lng": -1.1581},
    {"city": "Southampton", "lat": 50.9097, "lng": -1.4044},
    {"city": "Oxford", "lat": 51.7520, "lng": -1.2577},
    {"city": "Cambridge", "lat": 52.2053, "lng": 0.1218},
    {"city": "Brighton", "lat": 50.8225, "lng": -0.1372},
    {"city": "Plymouth", "lat": 50.3755, "lng": -4.1427},
    {"city": "Leicester", "lat": 52.6369, "lng": -1.1398},
    {"city": "Coventry", "lat": 52.4068, "lng": -1.5197},
    {"city": "York", "lat": 53.9591, "lng": -1.0815},
    {"city": "Aberdeen", "lat": 57.1497, "lng": -2.0943},
    {"city": "Dundee", "lat": 56.4620, "lng": -2.9707},
    {"city": "Swansea", "lat": 51.6214, "lng": -3.9436},
    {"city": "Reading", "lat": 51.4543, "lng": -0.9781},
    {"city": "Derby", "lat": 52.9225, "lng": -1.4746},
    {"city": "Exeter", "lat": 50.7184, "lng": -3.5339},
    {"city": "Norwich", "lat": 52.6309, "lng": 1.2974},
    {"city": "Milton Keynes", "lat": 52.0406, "lng": -0.7594},
    {"city": "Bournemouth", "lat": 50.7192, "lng": -1.8808},
]

# Street name components for generating addresses
STREET_TYPES = ["Street", "Road", "Lane", "Avenue", "Drive", "Close", "Way", "Place", "Crescent", "Gardens"]
STREET_NAMES = ["High", "Church", "Station", "Park", "Victoria", "Queen", "King", "Mill", "Green", "North", 
                "South", "West", "East", "Oak", "Elm", "Maple", "Cedar", "Pine", "Willow", "Rose"]

# Food items
FOOD_ITEMS = [
    "Bread", "Milk", "Eggs", "Butter", "Cheese", "Rice", "Pasta", "Tinned beans", "Tinned soup",
    "Cereal", "Tea bags", "Coffee", "Sugar", "Flour", "Cooking oil", "Tinned tomatoes", "Potatoes",
    "Onions", "Carrots", "Apples", "Bananas", "Orange juice", "Biscuits", "Crackers", "Jam",
    "Peanut butter", "Honey", "Chicken", "Mince", "Fish fingers", "Frozen peas", "Frozen chips"
]

# Clothing items
CLOTHING_ITEMS = [
    "Warm coat", "Winter jacket", "Jumper", "Hoodie", "T-shirts", "Jeans", "Trousers", "Socks",
    "Underwear", "Gloves", "Scarf", "Beanie hat", "Trainers", "Boots", "Pyjamas", "Cardigan",
    "Fleece", "Raincoat", "Tracksuit", "Leggings"
]

# Essential items
ESSENTIAL_ITEMS = [
    "Toiletries", "Shampoo", "Soap", "Toothpaste", "Toothbrush", "Toilet roll", "Tissues",
    "Nappies", "Baby wipes", "Sanitary products", "Razors", "Deodorant", "Hand sanitiser",
    "Washing up liquid", "Laundry detergent", "Bin bags", "Kitchen roll", "Light bulbs",
    "Batteries", "Phone charger", "Blankets", "Towels", "Bedding", "Pillows"
]

# Message templates
MESSAGE_TEMPLATES = [
    "Hi! I'm struggling a bit this month and would really appreciate some help with these items. Thank you so much! 🙏",
    "Hello, I'm a single parent and things are tight right now. Any help would be amazing. Thank you!",
    "I've just moved to the area and could use a hand getting settled. Really grateful for any support!",
    "Times are tough at the moment. Would be so grateful if someone could help out. Thanks in advance!",
    "Hi there! I'm recovering from illness and can't get out easily. Would really appreciate the help! 💙",
    "Hello! I'm caring for my elderly mum and we're running low on supplies. Any help is wonderful!",
    "Just lost my job and trying to make ends meet. Anything you can spare would mean the world. Thank you!",
    "Hi! Student here, budget is stretched thin. Would be so grateful for any help with these basics!",
    "Hello neighbour! Could really use a hand this week. Happy to pay it forward when I can! 🏠",
    "Going through a rough patch. Would be incredibly thankful for any support. Bless you!",
    "Hi! New to the community and in need of some essentials. Thanks for being so welcoming!",
    "Running low on supplies and mobility isn't great. Would appreciate help getting these items!",
    "Hello! Family of 4, hit an unexpected expense. Any help with groceries would be a lifesaver!",
    "Hi there! Would really appreciate help with these items. Happy to chat if you have questions!",
    "Struggling this month but keeping positive! Any help is hugely appreciated. Thank you! ✨",
    "Hello! First time asking for help - bit nervous but grateful this community exists!",
    "Hi! Could use some support getting these basics. Will definitely help others when I can!",
    "Times are challenging right now. So grateful for kind neighbours like you! 🙌",
    "Hello, hoping someone can help with a few items. Thank you for your kindness!",
    "Hi! Anything from this list would be a huge help. Thanks for being amazing! 💛",
]

def generate_random_address(city):
    """Generate a random UK-style address."""
    house_num = random.randint(1, 150)
    street_name = random.choice(STREET_NAMES)
    street_type = random.choice(STREET_TYPES)
    return f"{house_num} {street_name} {street_type}, {city}"

def generate_random_time():
    """Generate a random collection time between 8am and 8pm."""
    hour = random.randint(8, 20)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}{minute:02d}"

def generate_random_date():
    """Generate a random date within the next 2 months."""
    today = datetime.now()
    days_ahead = random.randint(1, 60)  # 1 to 60 days from now
    future_date = today + timedelta(days=days_ahead)
    return future_date.strftime("%Y-%m-%d")

def generate_random_items():
    """Generate 1-5 random items from different categories."""
    num_items = random.randint(1, 5)
    items = []
    
    # Weighted category selection (more food requests)
    categories = [FOOD_ITEMS] * 5 + [ESSENTIAL_ITEMS] * 3 + [CLOTHING_ITEMS] * 2
    
    used_items = set()
    for _ in range(num_items):
        category = random.choice(categories)
        item = random.choice(category)
        
        # Avoid duplicates
        while item in used_items:
            category = random.choice(categories)
            item = random.choice(category)
        
        used_items.add(item)
        quantity = random.randint(1, 4)
        items.append({"name": item, "quantity": quantity})
    
    return items

def add_jitter_to_coords(lat, lng):
    """Add small random offset to coordinates to spread requests around a city."""
    lat_jitter = random.uniform(-0.05, 0.05)  # ~5km spread
    lng_jitter = random.uniform(-0.05, 0.05)
    return lat + lat_jitter, lng + lng_jitter

def create_demo_account(db):
    """Create or get the demo account for sample requests."""
    demo_email = "demo@neighbourly.app"
    account = db.query(Account).filter_by(email=demo_email).first()
    if not account:
        account = Account(email=demo_email)
        db.add(account)
        db.commit()
        db.refresh(account)
        print(f"Created demo account: {demo_email}")
    return account

def populate_database(num_requests=100):
    """Populate the database with sample requests."""
    print(f"🏠 Neighbourly - Populating database with {num_requests} sample requests...")
    print("-" * 60)
    
    with Session(engine) as db:
        # Create demo account
        demo_account = create_demo_account(db)
        
        # Track cities for distribution
        city_counts = {}
        
        for i in range(num_requests):
            # Pick a random UK location
            location = random.choice(UK_LOCATIONS)
            city = location["city"]
            city_counts[city] = city_counts.get(city, 0) + 1
            
            # Add jitter to coordinates
            lat, lng = add_jitter_to_coords(location["lat"], location["lng"])
            
            # Generate request details
            address = generate_random_address(city)
            message = random.choice(MESSAGE_TEMPLATES)
            collection_time = generate_random_time()
            collection_date = generate_random_date()
            items = generate_random_items()
            
            # Create order
            order = Order(
                message=message,
                account_id=demo_account.id,
                lat=str(lat),
                lng=str(lng),
                address=address,
                collectionTime=collection_time,
                collectionDate=collection_date,
                fulfilled=None
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            
            # Add items
            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    name=item["name"],
                    quantity=item["quantity"]
                )
                db.add(order_item)
            
            db.commit()
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  ✓ Created {i + 1}/{num_requests} requests...")
        
        print("-" * 60)
        print(f"✅ Successfully created {num_requests} sample requests!")
        print("\n📍 Distribution by city:")
        for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
            print(f"   {city}: {count}")

if __name__ == "__main__":
    populate_database(100)
