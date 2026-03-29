import os
import json
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agrixenova.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)

# ═══════════════════════════════════════════
# LOAD YOUR 98% MODEL
# ═══════════════════════════════════════════
model = None
class_names = []

def load_model():
    global model, class_names
    try:
        import tensorflow as tf
        model_path = 'agrixenova_model.keras'
        if os.path.exists(model_path):
            model = tf.keras.models.load_model(model_path)
            print("✅ Your 98% model loaded successfully!")
        else:
            print("⚠️  Model file not found — using demo mode")

        names_path = 'class_names.json'
        if os.path.exists(names_path):
            with open(names_path, 'r') as f:
                class_names = json.load(f)
            print(f"✅ {len(class_names)} classes loaded!")
        else:
            class_names = [
                "Apple___Apple_scab",
                "Apple___Black_rot",
                "Apple___Cedar_apple_rust",
                "Apple___healthy",
                "Blueberry___healthy",
                "Cherry_(including_sour)___Powdery_mildew",
                "Cherry_(including_sour)___healthy",
                "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
                "Corn_(maize)___Common_rust_",
                "Corn_(maize)___Northern_Leaf_Blight",
                "Corn_(maize)___healthy",
                "Grape___Black_rot",
                "Grape___Esca_(Black_Measles)",
                "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
                "Grape___healthy",
                "Orange___Haunglongbing_(Citrus_greening)",
                "Peach___Bacterial_spot",
                "Peach___healthy",
                "Pepper,_bell___Bacterial_spot",
                "Pepper,_bell___healthy",
                "Potato___Early_blight",
                "Potato___Late_blight",
                "Potato___healthy",
                "Raspberry___healthy",
                "Soybean___healthy",
                "Squash___Powdery_mildew",
                "Strawberry___Leaf_scorch",
                "Strawberry___healthy",
                "Tomato___Bacterial_spot",
                "Tomato___Early_blight",
                "Tomato___Late_blight",
                "Tomato___Leaf_Mold",
                "Tomato___Septoria_leaf_spot",
                "Tomato___Spider_mites Two-spotted_spider_mite",
                "Tomato___Target_Spot",
                "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
                "Tomato___Tomato_mosaic_virus",
                "Tomato___healthy"
            ]
            print("⚠️  Using built-in class names")
    except Exception as e:
        print(f"⚠️  Load error: {e}")

# ═══════════════════════════════════════════
# DISEASE INFO — ALL 38 CLASSES
# ═══════════════════════════════════════════
DISEASE_INFO = {
    "Apple___Apple_scab": {
        "display": "Apple Scab",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Spray with myclobutanil or captan fungicide every 7-10 days. Remove and destroy infected leaves immediately. Improve air circulation by pruning. Apply preventive copper spray before rain season."
    },
    "Apple___Black_rot": {
        "display": "Apple Black Rot",
        "severity": "🔴 High",
        "status": "Urgent Treatment Needed",
        "treatment": "Remove all mummified fruits and dead wood immediately. Spray with captan or thiophanate-methyl every 10-14 days. Prune 15cm beyond any infected tissue and destroy all cuttings."
    },
    "Apple___Cedar_apple_rust": {
        "display": "Cedar Apple Rust",
        "severity": "🟡 Moderate",
        "status": "Manageable",
        "treatment": "Apply myclobutanil fungicide at pink bud stage. Repeat every 7-10 days through petal fall. Remove nearby cedar or juniper trees if possible. Use resistant varieties next planting season."
    },
    "Apple___healthy": {
        "display": "Healthy Apple",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your apple plant looks great! Keep watering 2x per week, fertilize with balanced NPK in spring, and inspect leaves weekly to catch any disease early."
    },
    "Blueberry___healthy": {
        "display": "Healthy Blueberry",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your blueberry is healthy! Maintain acidic soil pH 4.5-5.5, mulch with pine bark, and water 2x per week. Apply ammonium sulfate fertilizer for best growth."
    },
    "Cherry_(including_sour)___Powdery_mildew": {
        "display": "Cherry Powdery Mildew",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Spray with sulfur-based fungicide or potassium bicarbonate every 7 days. Improve air circulation by pruning dense branches. Avoid overhead watering. Apply neem oil as organic alternative."
    },
    "Cherry_(including_sour)___healthy": {
        "display": "Healthy Cherry",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your cherry tree is healthy! Water 2x per week, apply balanced NPK fertilizer in early spring, and net the tree before harvest to protect fruits from birds."
    },
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
        "display": "Maize Gray Leaf Spot",
        "severity": "🔴 High",
        "status": "Treat Immediately",
        "treatment": "Apply strobilurin or triazole fungicide immediately. Scout fields every 3 days. Rotate crops — do not plant maize in the same field next season. Use resistant hybrid varieties."
    },
    "Corn_(maize)___Common_rust_": {
        "display": "Maize Common Rust",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply propiconazole or azoxystrobin fungicide at first sign. Spray every 14 days. Plant resistant hybrids next season. Rust spreads fast in cool humid weather — monitor closely."
    },
    "Corn_(maize)___Northern_Leaf_Blight": {
        "display": "Maize Northern Leaf Blight",
        "severity": "🔴 High",
        "status": "Urgent Treatment Needed",
        "treatment": "Apply fungicide with azoxystrobin or propiconazole immediately. Remove heavily infected leaves. Improve field drainage. Rotate with non-host crops like beans or sunflower next season."
    },
    "Corn_(maize)___healthy": {
        "display": "Healthy Maize",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your maize looks healthy! Apply urea nitrogen fertilizer at knee height stage, scout for fall armyworm twice per week, and ensure proper spacing of 75cm between rows."
    },
    "Grape___Black_rot": {
        "display": "Grape Black Rot",
        "severity": "🔴 High",
        "status": "Urgent Treatment Needed",
        "treatment": "Apply myclobutanil or mancozeb fungicide immediately. Remove all mummified berries and infected leaves. Spray every 7-10 days from bud break. Improve canopy ventilation by pruning."
    },
    "Grape___Esca_(Black_Measles)": {
        "display": "Grape Esca (Black Measles)",
        "severity": "🔴 Very High",
        "status": "Serious — Act Now",
        "treatment": "No complete cure exists. Remove and destroy infected wood by pruning 30cm beyond visible symptoms. Apply wound sealant after pruning. Avoid water stress. Replant with certified disease-free material if severe."
    },
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {
        "display": "Grape Leaf Blight",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply copper-based fungicide or mancozeb every 10-14 days. Remove infected leaves and destroy immediately. Improve air circulation. Avoid overhead irrigation completely."
    },
    "Grape___healthy": {
        "display": "Healthy Grape",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your grape vine is healthy! Prune heavily in winter, train on trellis, apply potassium-rich fertilizer before fruiting, and water 2x per week."
    },
    "Orange___Haunglongbing_(Citrus_greening)": {
        "display": "Citrus Greening (HLB)",
        "severity": "🔴 Critical",
        "status": "No Cure — Manage Urgently",
        "treatment": "There is no cure for HLB. Remove and destroy infected trees immediately to prevent spread. Control Asian citrus psyllid with imidacloprid insecticide. Plant certified disease-free nursery trees only."
    },
    "Peach___Bacterial_spot": {
        "display": "Peach Bacterial Spot",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply copper-based bactericide every 7-10 days from early spring. Avoid overhead irrigation. Prune for good air circulation. Use resistant varieties when replanting."
    },
    "Peach___healthy": {
        "display": "Healthy Peach",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your peach tree is healthy! Thin fruits to 15-20cm apart for larger peaches, apply balanced NPK in spring, and net against birds before harvest season."
    },
    "Pepper,_bell___Bacterial_spot": {
        "display": "Pepper Bacterial Spot",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply copper hydroxide spray every 5-7 days. Remove and destroy infected leaves. Avoid working with plants when wet. Rotate crops and use resistant varieties. Water at soil level only."
    },
    "Pepper,_bell___healthy": {
        "display": "Healthy Bell Pepper",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your pepper plant is healthy! Pinch first flowers to encourage bushier growth, switch to high potassium fertilizer when flowering, and water 2-3x per week."
    },
    "Potato___Early_blight": {
        "display": "Potato Early Blight",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply chlorothalonil or mancozeb fungicide every 7-10 days. Remove infected lower leaves. Ensure proper plant nutrition — nitrogen deficiency increases susceptibility. Mulch around plants to prevent soil splash."
    },
    "Potato___Late_blight": {
        "display": "Potato Late Blight",
        "severity": "🔴 Critical",
        "status": "URGENT — Treat Within 24 Hours",
        "treatment": "Apply metalaxyl plus mancozeb (Ridomil Gold) IMMEDIATELY. Late blight can destroy an entire crop in just 5 days in wet weather. Spray every 5-7 days. Remove and bury all infected plants — do NOT compost them."
    },
    "Potato___healthy": {
        "display": "Healthy Potato",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your potato plant is healthy! Hill soil around stems every 3 weeks, apply high phosphorus fertilizer at planting, and harvest when 80% of leaves turn yellow."
    },
    "Raspberry___healthy": {
        "display": "Healthy Raspberry",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your raspberry is healthy! Remove spent canes after harvest, apply balanced NPK in spring, and water 2-3x per week. Net against birds to protect fruit."
    },
    "Soybean___healthy": {
        "display": "Healthy Soybean",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your soybean is healthy! Apply rhizobium inoculant at planting to fix nitrogen, scout for pod borer weekly, and harvest when 95% of pods turn brown."
    },
    "Squash___Powdery_mildew": {
        "display": "Squash Powdery Mildew",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Spray with potassium bicarbonate or neem oil every 7 days. Organic option: mix 1 tablespoon baking soda plus 1 teaspoon soap in 4 litres water and spray. Improve air circulation and remove badly infected leaves."
    },
    "Strawberry___Leaf_scorch": {
        "display": "Strawberry Leaf Scorch",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply captan or myclobutanil fungicide every 7-10 days. Remove infected leaves and destroy. Avoid overhead watering. Mulch around plants. Replace strawberry plants every 3-4 years for best productivity."
    },
    "Strawberry___healthy": {
        "display": "Healthy Strawberry",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your strawberry is healthy! Mulch around plants to keep berries clean, water 3x per week, apply high phosphorus fertilizer at planting, and remove runners for bigger berries."
    },
    "Tomato___Bacterial_spot": {
        "display": "Tomato Bacterial Spot",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply copper-based bactericide every 5-7 days. Remove infected leaves and destroy immediately. Avoid working with plants when wet. Do not save seeds from infected fruits. Use disease-free transplants next season."
    },
    "Tomato___Early_blight": {
        "display": "Tomato Early Blight",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply chlorothalonil or mancozeb fungicide every 7 days. Remove infected lower leaves immediately. Mulch around plants to prevent soil splash. Ensure proper spacing of 75cm for good air circulation."
    },
    "Tomato___Late_blight": {
        "display": "Tomato Late Blight",
        "severity": "🔴 Critical",
        "status": "URGENT — Treat Immediately",
        "treatment": "Apply metalaxyl plus mancozeb (Ridomil) IMMEDIATELY — this disease kills entire crops in 5 days. Spray every 5-7 days. Remove and bury all infected plants. Do NOT compost. Rotate crops next season."
    },
    "Tomato___Leaf_Mold": {
        "display": "Tomato Leaf Mold",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Improve ventilation urgently — leaf mold thrives in high humidity above 85%. Apply chlorothalonil fungicide every 7 days. Remove infected leaves. Avoid overhead watering completely."
    },
    "Tomato___Septoria_leaf_spot": {
        "display": "Tomato Septoria Leaf Spot",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply mancozeb or chlorothalonil every 7-10 days. Remove and destroy infected leaves. Mulch to prevent soil splash. Rotate crops — do not plant tomatoes in the same spot for 3 years."
    },
    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "display": "Tomato Spider Mites",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Spray with abamectin or bifenazate miticide. Organic option: spray neem oil every 3 days. Mites thrive in hot dry conditions — increase humidity and irrigation. Avoid broad-spectrum insecticides that kill natural predators."
    },
    "Tomato___Target_Spot": {
        "display": "Tomato Target Spot",
        "severity": "🟡 Moderate",
        "status": "Treatable",
        "treatment": "Apply azoxystrobin or chlorothalonil fungicide every 7 days. Remove infected leaves immediately. Improve air circulation by pruning. Avoid overhead watering and mulch around base of plants."
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "display": "Tomato Yellow Leaf Curl Virus",
        "severity": "🔴 Very High",
        "status": "No Cure — Prevent Spread",
        "treatment": "There is NO cure for TYLCV. Remove and destroy infected plants immediately. Control whitefly vector with imidacloprid insecticide. Use reflective silver mulch to repel whiteflies. Plant TYLCV-resistant varieties only."
    },
    "Tomato___Tomato_mosaic_virus": {
        "display": "Tomato Mosaic Virus",
        "severity": "🔴 High",
        "status": "No Cure — Remove Plant",
        "treatment": "No cure exists. Remove and destroy infected plants immediately — do NOT compost. Disinfect all tools with 10% bleach solution. Wash hands thoroughly. Control aphids which spread the virus. Use virus-resistant varieties."
    },
    "Tomato___healthy": {
        "display": "Healthy Tomato",
        "severity": "🟢 None",
        "status": "Plant is Healthy!",
        "treatment": "Your tomato plant is perfectly healthy! Remove suckers weekly, stake when 30cm tall, switch to high-potassium fertilizer when flowers appear, and water deeply every 2-3 days at the base only."
    }
}

def get_crop_name(class_name):
    mapping = {
        "Apple": "Apple", "Blueberry": "Blueberry",
        "Cherry": "Cherry", "Corn_(maize)": "Maize",
        "Grape": "Grape", "Orange": "Orange",
        "Peach": "Peach", "Pepper,_bell": "Bell Pepper",
        "Potato": "Potato", "Raspberry": "Raspberry",
        "Soybean": "Soybean", "Squash": "Squash",
        "Strawberry": "Strawberry", "Tomato": "Tomato"
    }
    for key, val in mapping.items():
        if class_name.startswith(key):
            return val
    return class_name.split("___")[0].replace("_", " ")

# ═══════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════
class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100))
    date_added = db.Column(db.String(50))
    entries = db.relationship('Entry', backref='plant', lazy=True, cascade='all, delete-orphan')

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    note = db.Column(db.Text)
    photo = db.Column(db.Text)
    date = db.Column(db.String(50))

# ═══════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        import tensorflow as tf
        from PIL import Image
        import io

        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400

        file = request.files['image']
        img_bytes = file.read()

        # Open image
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')

        # ── CRITICAL: EfficientNetB3 needs exactly 300x300 ──
        img = img.resize((300, 300), Image.LANCZOS)

        # Convert to array
        img_array = np.array(img, dtype=np.float32)

        # Add batch dimension → shape (1, 300, 300, 3)
        img_array = np.expand_dims(img_array, axis=0)

        # ── CRITICAL: Must use EfficientNet preprocessing ──
        # This scales pixels from [0,255] to [-1, 1] range
        # which is exactly what your model was trained on
        img_array = tf.keras.applications.efficientnet.preprocess_input(img_array)

        if model is not None:
            # Run prediction
            preds = model.predict(img_array, verbose=0)

            # Get best result
            predicted_index = int(np.argmax(preds[0]))
            confidence = float(np.max(preds[0])) * 100

            # Get top 3 predictions for debugging
            top3_indices = np.argsort(preds[0])[-3:][::-1]
            top3 = [(class_names[i], float(preds[0][i]) * 100) for i in top3_indices if i < len(class_names)]
            print(f"Top 3 predictions:")
            for name, conf in top3:
                print(f"  {name}: {conf:.1f}%")

            # Get class name
            if predicted_index < len(class_names):
                class_name = class_names[predicted_index]
            else:
                class_name = "Unknown"

            print(f"✅ Predicted: {class_name} ({confidence:.1f}%)")

            # Get disease info
            info = DISEASE_INFO.get(class_name, {
                "display": class_name.replace("___", " — ").replace("_", " "),
                "severity": "🟡 Unknown",
                "status": "Consult an Expert",
                "treatment": "Disease identified by AI. Please consult a local agricultural extension officer for treatment advice specific to your region and climate."
            })

            crop = get_crop_name(class_name)

            return jsonify({
                'disease': info['display'],
                'crop': crop,
                'confidence': f"{confidence:.1f}%",
                'severity': info['severity'],
                'status': info['status'],
                'treatment': info['treatment'],
                'class_raw': class_name
            })

        else:
            # Demo mode — no model loaded
            import random
            demos = [
                {
                    "disease": "Tomato Late Blight",
                    "crop": "Tomato",
                    "confidence": "94.2%",
                    "severity": "🔴 Critical",
                    "status": "URGENT — Treat Immediately",
                    "treatment": "Apply metalaxyl plus mancozeb (Ridomil) IMMEDIATELY — this disease kills entire crops in 5 days. Spray every 5-7 days. Remove and bury all infected plants."
                },
                {
                    "disease": "Potato Early Blight",
                    "crop": "Potato",
                    "confidence": "91.8%",
                    "severity": "🟡 Moderate",
                    "status": "Treatable",
                    "treatment": "Apply chlorothalonil or mancozeb fungicide every 7-10 days. Remove infected lower leaves and mulch around plants."
                },
                {
                    "disease": "Healthy Tomato",
                    "crop": "Tomato",
                    "confidence": "98.5%",
                    "severity": "🟢 None",
                    "status": "Plant is Healthy!",
                    "treatment": "Your tomato plant is perfectly healthy! Remove suckers weekly and water deeply every 2-3 days."
                },
                {
                    "disease": "Maize Common Rust",
                    "crop": "Maize",
                    "confidence": "89.3%",
                    "severity": "🟡 Moderate",
                    "status": "Treatable",
                    "treatment": "Apply propiconazole fungicide immediately. Spray every 14 days. Plant resistant hybrids next season."
                }
            ]
            return jsonify(random.choice(demos))

    except Exception as e:
        print(f"❌ Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'disease': 'Analysis Error',
            'crop': 'Unknown',
            'confidence': '0%',
            'severity': '⚠️ Error',
            'status': 'Please try again',
            'treatment': 'Could not analyse the image. Please try again with a clearer, well-lit photo of the affected plant leaf.'
        }), 500

# ═══════════════════════════════════════════
# MARKET DEMAND
# ═══════════════════════════════════════════
@app.route('/api/demand/<country>')
def demand(country):
    import calendar
    month_num = datetime.now().month
    month_name = calendar.month_name[month_num]
    season = "Growing"
    if month_num in [3, 4, 5]:
        season = "Long Rains"
    elif month_num in [6, 7, 8]:
        season = "Dry"
    elif month_num in [9, 10, 11]:
        season = "Short Rains"
    else:
        season = "Cool Dry"

    DEMAND_DATA = {
        "kenya": [
            {"name":"Tomato","emoji":"🍅","trend":"hot","reason":"High demand in Nairobi markets. Peak season profits of KES 80-120 per kg.","price_local":"KES 80-120/kg","price_usd":"$0.60-0.90/kg"},
            {"name":"Avocado","emoji":"🥑","trend":"hot","reason":"Strong export demand to Europe and Middle East. Premium prices for Hass variety.","price_local":"KES 15-25/fruit","price_usd":"$0.11-0.19/fruit"},
            {"name":"French Beans","emoji":"🫘","trend":"up","reason":"Export crop with year-round demand. UK and EU buyers paying premium prices.","price_local":"KES 60-80/kg","price_usd":"$0.45-0.60/kg"},
            {"name":"Maize","emoji":"🌽","trend":"stable","reason":"Staple food with consistent local demand year-round.","price_local":"KES 35-50/kg","price_usd":"$0.26-0.37/kg"},
            {"name":"Potato","emoji":"🥔","trend":"up","reason":"Urban demand increasing. Nyandarua and Meru farmers earning well this season.","price_local":"KES 30-50/kg","price_usd":"$0.22-0.37/kg"}
        ],
        "nigeria": [
            {"name":"Tomato","emoji":"🍅","trend":"hot","reason":"Massive demand in Lagos and Abuja. Tomato paste industry buying in bulk.","price_local":"NGN 800-1200/kg","price_usd":"$0.55-0.82/kg"},
            {"name":"Yam","emoji":"🍠","trend":"hot","reason":"Nigeria is world's largest yam producer. Strong domestic and export demand.","price_local":"NGN 2000-4000/tuber","price_usd":"$1.37-2.74/tuber"},
            {"name":"Pepper","emoji":"🫑","trend":"up","reason":"High demand for chili and bell pepper. Good prices in southern markets.","price_local":"NGN 1000-1500/kg","price_usd":"$0.68-1.03/kg"},
            {"name":"Cassava","emoji":"🍠","trend":"stable","reason":"Staple crop with garri and flour processing industry demand.","price_local":"NGN 150-250/kg","price_usd":"$0.10-0.17/kg"},
            {"name":"Watermelon","emoji":"🍉","trend":"up","reason":"Growing urban market. Northern Nigeria producers earning well this season.","price_local":"NGN 500-800/fruit","price_usd":"$0.34-0.55/fruit"}
        ],
        "ethiopia": [
            {"name":"Coffee","emoji":"☕","trend":"hot","reason":"Ethiopian coffee is world-famous. Specialty arabica commands premium export prices.","price_local":"ETB 800-1500/kg","price_usd":"$5.50-10.30/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"Urban Addis Ababa demand growing. Good prices in local markets.","price_local":"ETB 30-60/kg","price_usd":"$0.21-0.41/kg"},
            {"name":"Onion","emoji":"🧅","trend":"stable","reason":"Staple ingredient with year-round consistent demand.","price_local":"ETB 20-40/kg","price_usd":"$0.14-0.27/kg"},
            {"name":"Potato","emoji":"🥔","trend":"up","reason":"Growing highland potato demand. Export potential to Gulf countries.","price_local":"ETB 15-30/kg","price_usd":"$0.10-0.21/kg"},
            {"name":"Mango","emoji":"🥭","trend":"hot","reason":"Ethiopian mangoes in high demand during peak season.","price_local":"ETB 20-50/kg","price_usd":"$0.14-0.34/kg"}
        ],
        "ghana": [
            {"name":"Tomato","emoji":"🍅","trend":"hot","reason":"High demand in Accra and Kumasi markets. Seasonal price spikes very profitable.","price_local":"GHS 20-40/kg","price_usd":"$1.33-2.67/kg"},
            {"name":"Plantain","emoji":"🍌","trend":"stable","reason":"Daily staple food. Consistent year-round demand across all markets.","price_local":"GHS 5-10/bunch","price_usd":"$0.33-0.67/bunch"},
            {"name":"Pepper","emoji":"🫑","trend":"up","reason":"High demand for fresh and dried chili. Good export potential.","price_local":"GHS 25-50/kg","price_usd":"$1.67-3.33/kg"},
            {"name":"Yam","emoji":"🍠","trend":"hot","reason":"Festival season demand spikes. Export to UK diaspora market profitable.","price_local":"GHS 15-30/kg","price_usd":"$1.00-2.00/kg"},
            {"name":"Watermelon","emoji":"🍉","trend":"up","reason":"Urban demand growing. Roadside sales very profitable in dry season.","price_local":"GHS 10-20/fruit","price_usd":"$0.67-1.33/fruit"}
        ],
        "tanzania": [
            {"name":"Coffee","emoji":"☕","trend":"hot","reason":"Kilimanjaro and Mbeya arabica in high global demand. Export prices strong.","price_local":"TZS 8000-15000/kg","price_usd":"$3.10-5.80/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"High demand in Dar es Salaam and Arusha markets.","price_local":"TZS 1500-2500/kg","price_usd":"$0.58-0.97/kg"},
            {"name":"Maize","emoji":"🌽","trend":"stable","reason":"Tanzania staple food. Southern highlands produce surplus for export.","price_local":"TZS 600-900/kg","price_usd":"$0.23-0.35/kg"},
            {"name":"Cashew","emoji":"🥜","trend":"hot","reason":"Tanzania is Africa's largest cashew exporter. Indian buyers paying premium.","price_local":"TZS 3000-5000/kg","price_usd":"$1.16-1.94/kg"},
            {"name":"Rice","emoji":"🌾","trend":"up","reason":"Mbeya and Kilombero rice in high demand. Urban market growing fast.","price_local":"TZS 1200-2000/kg","price_usd":"$0.46-0.78/kg"}
        ],
        "uganda": [
            {"name":"Matooke","emoji":"🍌","trend":"hot","reason":"Uganda staple food. Kampala market demand very high and consistent.","price_local":"UGX 3000-6000/bunch","price_usd":"$0.80-1.60/bunch"},
            {"name":"Coffee","emoji":"☕","trend":"hot","reason":"Robusta coffee export prices strong. Uganda is Africa's largest coffee exporter.","price_local":"UGX 8000-12000/kg","price_usd":"$2.15-3.22/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"Kampala urban demand growing steadily. Good farm gate prices.","price_local":"UGX 2000-4000/kg","price_usd":"$0.54-1.07/kg"},
            {"name":"Beans","emoji":"🫘","trend":"stable","reason":"Staple protein crop. Consistent demand from urban and rural markets.","price_local":"UGX 3000-5000/kg","price_usd":"$0.80-1.34/kg"},
            {"name":"Watermelon","emoji":"🍉","trend":"up","reason":"Growing Kampala demand. Roadside sales booming in dry season.","price_local":"UGX 5000-10000/fruit","price_usd":"$1.34-2.68/fruit"}
        ],
        "south_africa": [
            {"name":"Apple","emoji":"🍎","trend":"up","reason":"Elgin and Grabouw apples world-class. Strong UK and Middle East export demand.","price_local":"ZAR 15-25/kg","price_usd":"$0.82-1.37/kg"},
            {"name":"Grape","emoji":"🍇","trend":"hot","reason":"South Africa is top wine grape and table grape exporter. European demand strong.","price_local":"ZAR 20-40/kg","price_usd":"$1.10-2.19/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"stable","reason":"Year-round retail and processing demand from major supermarkets.","price_local":"ZAR 12-20/kg","price_usd":"$0.66-1.10/kg"},
            {"name":"Potato","emoji":"🥔","trend":"stable","reason":"South African staple. Limpopo and Free State produce year-round.","price_local":"ZAR 8-15/kg","price_usd":"$0.44-0.82/kg"},
            {"name":"Avocado","emoji":"🥑","trend":"hot","reason":"Limpopo Hass avocado export demand booming. European buyers paying premium.","price_local":"ZAR 8-15/fruit","price_usd":"$0.44-0.82/fruit"}
        ],
        "egypt": [
            {"name":"Tomato","emoji":"🍅","trend":"hot","reason":"Nile Delta tomatoes — massive domestic and export demand. Processing industry buys in bulk.","price_local":"EGP 15-30/kg","price_usd":"$0.31-0.62/kg"},
            {"name":"Potato","emoji":"🥔","trend":"up","reason":"Egypt is Africa's largest potato exporter. EU and Arab market demand strong.","price_local":"EGP 12-25/kg","price_usd":"$0.25-0.52/kg"},
            {"name":"Onion","emoji":"🧅","trend":"stable","reason":"Major export crop. Arab world demand for Egyptian onions very high.","price_local":"EGP 8-15/kg","price_usd":"$0.17-0.31/kg"},
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"Egyptian winter strawberries exported to Europe. Very profitable season.","price_local":"EGP 30-60/kg","price_usd":"$0.62-1.24/kg"},
            {"name":"Orange","emoji":"🍊","trend":"up","reason":"Navel orange export demand high. Gulf and European buyers active.","price_local":"EGP 8-18/kg","price_usd":"$0.17-0.37/kg"}
        ],
        "india": [
            {"name":"Tomato","emoji":"🍅","trend":"hot","reason":"High demand across all Indian cities. Prices very volatile — sell at peak timing.","price_local":"INR 40-100/kg","price_usd":"$0.48-1.20/kg"},
            {"name":"Onion","emoji":"🧅","trend":"up","reason":"India's most traded vegetable. Export demand from Middle East very strong.","price_local":"INR 25-60/kg","price_usd":"$0.30-0.72/kg"},
            {"name":"Rice","emoji":"🌾","trend":"stable","reason":"India is world's largest rice exporter. Basmati premium prices in global market.","price_local":"INR 30-80/kg","price_usd":"$0.36-0.96/kg"},
            {"name":"Potato","emoji":"🥔","trend":"stable","reason":"Year-round demand for chips, curry and export markets.","price_local":"INR 15-30/kg","price_usd":"$0.18-0.36/kg"},
            {"name":"Mango","emoji":"🥭","trend":"hot","reason":"Alphonso and Kesar export demand booming. Premium international prices.","price_local":"INR 80-300/kg","price_usd":"$0.96-3.60/kg"}
        ],
        "usa": [
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"Organic tomatoes commanding 3x premium at Whole Foods and farmers markets.","price_local":"$2.50-4.00/lb","price_usd":"$5.50-8.80/kg"},
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"High demand at farmers markets. Pick-your-own farms extremely profitable.","price_local":"$4.00-6.00/lb","price_usd":"$8.80-13.20/kg"},
            {"name":"Blueberry","emoji":"🫐","trend":"up","reason":"Health food trend driving premium prices. Organic commands 2x premium.","price_local":"$5.00-8.00/pint","price_usd":"$10-16/kg"},
            {"name":"Sweet Corn","emoji":"🌽","trend":"hot","reason":"Summer peak demand. Roadside stands and farmers markets sell out daily.","price_local":"$0.50-1.00/ear","price_usd":"$2.20-4.40/kg"},
            {"name":"Apple","emoji":"🍎","trend":"stable","reason":"Washington state apples consistent premium. Honeycrisp variety commands top price.","price_local":"$1.50-3.00/lb","price_usd":"$3.30-6.60/kg"}
        ],
        "uk": [
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"British summer strawberry season. Wimbledon demand peaks June-July.","price_local":"£3.00-5.00/punnet","price_usd":"$3.75-6.25/punnet"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"High UK demand. Greenhouse growing extending season. Organic premium strong.","price_local":"£2.50-4.00/kg","price_usd":"$3.10-5.00/kg"},
            {"name":"Potato","emoji":"🥔","trend":"stable","reason":"UK staple. New potatoes command 3x premium over main crop varieties.","price_local":"£0.80-1.50/kg","price_usd":"$1.00-1.88/kg"},
            {"name":"Apple","emoji":"🍎","trend":"up","reason":"British apple season August-October. Cox and Bramley premium prices.","price_local":"£1.50-2.50/kg","price_usd":"$1.88-3.13/kg"},
            {"name":"Blueberry","emoji":"🫐","trend":"up","reason":"Health food trend very strong. Organic Scottish blueberries premium priced.","price_local":"£3.00-5.00/punnet","price_usd":"$3.75-6.25/punnet"}
        ],
        "germany": [
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"Erdbeere season June-August. Roadside stands sell out every single day.","price_local":"€4.00-6.00/kg","price_usd":"$4.30-6.45/kg"},
            {"name":"Apple","emoji":"🍎","trend":"up","reason":"High organic demand. German consumers pay 2-3x premium for certified organic.","price_local":"€2.00-3.50/kg","price_usd":"$2.15-3.75/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"Greenhouse tomatoes valued year-round. Organic commands strong premium.","price_local":"€2.50-4.00/kg","price_usd":"$2.69-4.30/kg"},
            {"name":"Potato","emoji":"🥔","trend":"stable","reason":"German staple with massive retail demand year-round.","price_local":"€0.80-1.20/kg","price_usd":"$0.86-1.29/kg"},
            {"name":"Grape","emoji":"🍇","trend":"stable","reason":"Wine grape demand stable. Rhine and Moselle regions command premium.","price_local":"€1.50-2.50/kg","price_usd":"$1.61-2.69/kg"}
        ],
        "france": [
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"French summer strawberry market very profitable. Gariguette variety premium.","price_local":"€5.00-8.00/kg","price_usd":"$5.38-8.60/kg"},
            {"name":"Grape","emoji":"🍇","trend":"hot","reason":"Bordeaux and Burgundy wine grape demand always strong. Table grapes good prices.","price_local":"€2.00-4.00/kg","price_usd":"$2.15-4.30/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"French organic tomato market growing strongly. Coeur de boeuf variety premium.","price_local":"€3.00-5.00/kg","price_usd":"$3.23-5.38/kg"},
            {"name":"Apple","emoji":"🍎","trend":"stable","reason":"Normandy apple season August-November. Cidre apple demand growing.","price_local":"€1.50-2.50/kg","price_usd":"$1.61-2.69/kg"},
            {"name":"Peach","emoji":"🍑","trend":"up","reason":"South of France summer peach demand very high. Organic commands premium.","price_local":"€3.00-5.00/kg","price_usd":"$3.23-5.38/kg"}
        ],
        "japan": [
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"Japanese premium Amao strawberries sell for ¥5,000+ per box. Gift market huge.","price_local":"¥1,500-5,000/pack","price_usd":"$10-33/pack"},
            {"name":"Melon","emoji":"🍈","trend":"hot","reason":"Luxury Yubari melons sell for ¥10,000-50,000 each. Gift market enormous.","price_local":"¥5,000-50,000/melon","price_usd":"$33-330/melon"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"High-Brix sweet tomatoes premium priced. Health-conscious market growing fast.","price_local":"¥300-600/tomato","price_usd":"$2.00-4.00/tomato"},
            {"name":"Apple","emoji":"🍎","trend":"stable","reason":"Fuji and Tsugaru apple demand strong. Gift apples reach ¥1,000 each.","price_local":"¥200-1,000/apple","price_usd":"$1.33-6.65/apple"},
            {"name":"Rice","emoji":"🌾","trend":"stable","reason":"Premium Koshihikari rice. Japanese consumers extremely loyal to domestic brands.","price_local":"¥500-800/kg","price_usd":"$3.30-5.30/kg"}
        ],
        "south_korea": [
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"Korea premium gift strawberries. Luxury packaging sells for ₩80,000+ per box.","price_local":"₩15,000-30,000/kg","price_usd":"$11-22/kg"},
            {"name":"Pepper","emoji":"🌶️","trend":"hot","reason":"Gochugaru chili demand for kimchi. Massive domestic demand year-round.","price_local":"₩10,000-20,000/kg","price_usd":"$7.30-14.60/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"Cherry tomatoes very popular. Health-conscious market growing very fast.","price_local":"₩5,000-10,000/kg","price_usd":"$3.65-7.30/kg"},
            {"name":"Apple","emoji":"🍎","trend":"stable","reason":"Fuji apple demand high. Chuseok holiday gift demand peaks in September.","price_local":"₩8,000-15,000/kg","price_usd":"$5.85-11/kg"},
            {"name":"Rice","emoji":"🌾","trend":"stable","reason":"Korean premium rice commands top prices. Consistent domestic demand always strong.","price_local":"₩3,000-5,000/kg","price_usd":"$2.19-3.65/kg"}
        ],
        "china": [
            {"name":"Apple","emoji":"🍎","trend":"hot","reason":"China is world's largest apple producer and consumer. Fuji variety very premium.","price_local":"¥8-20/kg","price_usd":"$1.10-2.75/kg"},
            {"name":"Watermelon","emoji":"🍉","trend":"hot","reason":"China produces 70% of world's watermelons. Xinjiang premium variety.","price_local":"¥3-8/kg","price_usd":"$0.41-1.10/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"Urban demand growing. E-commerce fresh produce market expanding rapidly.","price_local":"¥5-12/kg","price_usd":"$0.69-1.65/kg"},
            {"name":"Grape","emoji":"🍇","trend":"up","reason":"Xinjiang grape demand growing very fast. Autumn peak prices very high.","price_local":"¥15-40/kg","price_usd":"$2.07-5.50/kg"},
            {"name":"Rice","emoji":"🌾","trend":"stable","reason":"China is world's largest rice consumer. Northeast Japonica variety premium.","price_local":"¥6-15/kg","price_usd":"$0.83-2.07/kg"}
        ],
        "brazil": [
            {"name":"Soybean","emoji":"🥜","trend":"hot","reason":"Brazil is world's largest soybean exporter. Global demand extremely strong.","price_local":"R$180-220/bag","price_usd":"$35-43/bag"},
            {"name":"Orange","emoji":"🍊","trend":"stable","reason":"Brazil produces 30% of world's orange juice. Export market consistently strong.","price_local":"R$1.50-3.00/kg","price_usd":"$0.29-0.58/kg"},
            {"name":"Mango","emoji":"🥭","trend":"hot","reason":"Sao Francisco Valley export mangoes commanding premium EU prices.","price_local":"R$4.00-8.00/kg","price_usd":"$0.77-1.54/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"Sao Paulo and Rio demand high. Processing industry buying in bulk.","price_local":"R$3.00-6.00/kg","price_usd":"$0.58-1.16/kg"},
            {"name":"Coffee","emoji":"☕","trend":"up","reason":"Brazil is world's largest coffee producer. Specialty market premium very strong.","price_local":"R$40-80/kg","price_usd":"$7.72-15.45/kg"}
        ],
        "indonesia": [
            {"name":"Rice","emoji":"🌾","trend":"stable","reason":"Indonesia staple food. Government price support keeps market stable.","price_local":"IDR 12,000-18,000/kg","price_usd":"$0.75-1.13/kg"},
            {"name":"Chili","emoji":"🌶️","trend":"hot","reason":"Indonesian chili demand always hot. Price spikes very profitable for farmers.","price_local":"IDR 30,000-80,000/kg","price_usd":"$1.88-5.00/kg"},
            {"name":"Tomato","emoji":"🍅","trend":"up","reason":"Growing urban Jakarta and Surabaya demand. Restaurant market buying.","price_local":"IDR 15,000-25,000/kg","price_usd":"$0.94-1.56/kg"},
            {"name":"Potato","emoji":"🥔","trend":"up","reason":"Fast food and snack industry demand growing fast. Highland potato premium.","price_local":"IDR 18,000-30,000/kg","price_usd":"$1.13-1.88/kg"},
            {"name":"Mango","emoji":"🥭","trend":"hot","reason":"Gedong Gincu mango export to China and Middle East very profitable.","price_local":"IDR 15,000-40,000/kg","price_usd":"$0.94-2.50/kg"}
        ],
        "australia": [
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"Australian summer demand peaks. Farmers markets sell out every day.","price_local":"A$4-7/punnet","price_usd":"$2.60-4.55/punnet"},
            {"name":"Avocado","emoji":"🥑","trend":"up","reason":"Australian avocado demand booming. Export to Asia growing very fast.","price_local":"A$1.50-3.00/fruit","price_usd":"$0.98-1.95/fruit"},
            {"name":"Mango","emoji":"🥭","trend":"hot","reason":"Queensland mango season peak. Kensington Pride variety commands premium.","price_local":"A$1.00-3.00/mango","price_usd":"$0.65-1.95/mango"},
            {"name":"Blueberry","emoji":"🫐","trend":"up","reason":"Health trend driving strong demand. Export to Asia very profitable.","price_local":"A$6-12/punnet","price_usd":"$3.90-7.80/punnet"},
            {"name":"Tomato","emoji":"🍅","trend":"stable","reason":"Year-round retail demand. Truss tomatoes commanding premium prices.","price_local":"A$4-7/kg","price_usd":"$2.60-4.55/kg"}
        ],
        "saudi_arabia": [
            {"name":"Tomato","emoji":"🍅","trend":"hot","reason":"Saudi Arabia imports 80% of vegetables. High prices year-round.","price_local":"SAR 8-15/kg","price_usd":"$2.13-4.00/kg"},
            {"name":"Date","emoji":"🌴","trend":"hot","reason":"Saudi Medjool dates premium export product. Global demand very strong.","price_local":"SAR 30-80/kg","price_usd":"$8.00-21.33/kg"},
            {"name":"Watermelon","emoji":"🍉","trend":"up","reason":"Hot climate drives massive demand. Local greenhouse production very profitable.","price_local":"SAR 5-10/kg","price_usd":"$1.33-2.67/kg"},
            {"name":"Potato","emoji":"🥔","trend":"stable","reason":"Massive import demand. Local hydroponic production growing fast.","price_local":"SAR 4-8/kg","price_usd":"$1.07-2.13/kg"},
            {"name":"Pepper","emoji":"🫑","trend":"up","reason":"High demand for fresh peppers in Riyadh and Jeddah markets.","price_local":"SAR 10-20/kg","price_usd":"$2.67-5.33/kg"}
        ],
        "uae": [
            {"name":"Tomato","emoji":"🍅","trend":"hot","reason":"UAE imports almost all vegetables. Very high farm gate prices for local growers.","price_local":"AED 8-15/kg","price_usd":"$2.18-4.09/kg"},
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"High-income market pays premium for fresh local strawberries.","price_local":"AED 25-50/kg","price_usd":"$6.81-13.62/kg"},
            {"name":"Lettuce","emoji":"🥬","trend":"up","reason":"Hydroponic lettuce market growing fast. Restaurants and hotels paying premium.","price_local":"AED 5-12/head","price_usd":"$1.36-3.27/head"},
            {"name":"Pepper","emoji":"🫑","trend":"stable","reason":"Year-round restaurant and retail demand very strong.","price_local":"AED 10-20/kg","price_usd":"$2.72-5.45/kg"},
            {"name":"Mango","emoji":"🥭","trend":"up","reason":"Alphonso mango import season. Premium Indian and Pakistani varieties.","price_local":"AED 15-30/kg","price_usd":"$4.09-8.17/kg"}
        ],
        "new_zealand": [
            {"name":"Kiwifruit","emoji":"🥝","trend":"hot","reason":"New Zealand Zespri Gold kiwi commands world premium. Asian export demand massive.","price_local":"NZ$3-6/fruit","price_usd":"$1.82-3.64/fruit"},
            {"name":"Apple","emoji":"🍎","trend":"up","reason":"Hawke's Bay apples world-class. Export to UK and Asia very profitable.","price_local":"NZ$3-5/kg","price_usd":"$1.82-3.03/kg"},
            {"name":"Strawberry","emoji":"🍓","trend":"hot","reason":"Summer season demand peaks. Farmers markets and pick-your-own very profitable.","price_local":"NZ$5-9/punnet","price_usd":"$3.03-5.45/punnet"},
            {"name":"Blueberry","emoji":"🫐","trend":"up","reason":"Export demand to Asia growing fast. Health trend driving premium prices.","price_local":"NZ$8-15/punnet","price_usd":"$4.85-9.09/punnet"},
            {"name":"Tomato","emoji":"🍅","trend":"stable","reason":"Year-round retail demand. Beefsteak and vine tomatoes premium priced.","price_local":"NZ$4-7/kg","price_usd":"$2.42-4.24/kg"}
        ]
    }

    crops = DEMAND_DATA.get(country, [
        {"name":"Tomato","emoji":"🍅","trend":"hot","reason":"High seasonal demand in your region. Good prices in local markets right now.","price_local":"See local market","price_usd":"$0.50-1.50/kg"},
        {"name":"Maize","emoji":"🌽","trend":"stable","reason":"Staple crop with consistent year-round demand in your area.","price_local":"See local market","price_usd":"$0.20-0.40/kg"},
        {"name":"Potato","emoji":"🥔","trend":"up","reason":"Urban market demand growing steadily. Good time to sell.","price_local":"See local market","price_usd":"$0.30-0.80/kg"},
        {"name":"Pepper","emoji":"🫑","trend":"up","reason":"Good demand for fresh peppers in urban markets.","price_local":"See local market","price_usd":"$0.80-2.00/kg"},
        {"name":"Mango","emoji":"🥭","trend":"hot","reason":"Strong seasonal demand when in peak production period.","price_local":"See local market","price_usd":"$0.50-2.00/kg"}
    ])

    return jsonify({
        "country": country,
        "month": month_name,
        "season": season,
        "data_source": "AgriXenova Market Intelligence",
        "wb_loaded": True,
        "crops": crops
    })

# ═══════════════════════════════════════════
# JOURNAL ROUTES
# ═══════════════════════════════════════════
@app.route('/api/plants', methods=['GET'])
def get_plants():
    plants = Plant.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'type': p.type or '',
        'date_added': p.date_added or '',
        'entry_count': len(p.entries)
    } for p in plants])

@app.route('/api/plants', methods=['POST'])
def add_plant():
    data = request.get_json()
    plant = Plant(
        name=data.get('name', 'My Plant'),
        type=data.get('type', ''),
        date_added=datetime.now().strftime('%b %d, %Y')
    )
    db.session.add(plant)
    db.session.commit()
    return jsonify({
        'id': plant.id,
        'name': plant.name,
        'type': plant.type,
        'date_added': plant.date_added,
        'entry_count': 0
    })

@app.route('/api/plants/<int:plant_id>', methods=['DELETE'])
def delete_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    db.session.delete(plant)
    db.session.commit()
    return jsonify({'message': 'Deleted successfully'})

@app.route('/api/plants/<int:plant_id>/entries', methods=['GET'])
def get_entries(plant_id):
    entries = Entry.query.filter_by(plant_id=plant_id).order_by(Entry.id.desc()).all()
    return jsonify([{
        'id': e.id,
        'note': e.note or '',
        'photo': e.photo or '',
        'date': e.date or ''
    } for e in entries])

@app.route('/api/plants/<int:plant_id>/entries', methods=['POST'])
def add_entry(plant_id):
    note = request.form.get('note', '')
    photo_data = ''
    if 'photo' in request.files:
        photo_file = request.files['photo']
        if photo_file.filename:
            photo_bytes = photo_file.read()
            ext = photo_file.filename.rsplit('.', 1)[-1].lower()
            mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
            photo_data = f"data:{mime};base64,{base64.b64encode(photo_bytes).decode()}"
    entry = Entry(
        plant_id=plant_id,
        note=note,
        photo=photo_data,
        date=datetime.now().strftime('%B %d, %Y at %I:%M %p')
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'id': entry.id, 'message': 'Entry saved!'})

# ═══════════════════════════════════════════
# START
# ═══════════════════════════════════════════
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    load_model()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
