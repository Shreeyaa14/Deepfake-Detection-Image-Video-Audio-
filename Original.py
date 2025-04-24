import os
import uuid
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'wav', 'mp3', 'm4a'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Simulated detection functions (replace with real models for production)
def detect_deepfake_image(filepath):
    import random
    confidence = random.uniform(0, 1)
    morphed = confidence > 0.5
    region = (random.randint(0, 100), random.randint(0, 100), random.randint(100, 200), random.randint(100, 200))
    return {
        'is_morphed': morphed,
        'confidence': round(confidence * 100, 2),
        'region': region if morphed else None
    }

def detect_deepfake_video(filepath):
    import random
    confidence = random.uniform(0, 1)
    morphed = confidence > 0.5
    frame = random.randint(1, 30)
    region = (random.randint(0, 100), random.randint(0, 100), random.randint(100, 200), random.randint(100, 200))
    return {
        'is_morphed': morphed,
        'confidence': round(confidence * 100, 2),
        'frame': frame if morphed else None,
        'region': region if morphed else None
    }

def detect_deepfake_audio(filepath):
    import random
    confidence = random.uniform(0, 1)
    morphed = confidence > 0.5
    segment = (round(random.uniform(0, 5), 2), round(random.uniform(5, 10), 2))
    return {
        'is_morphed': morphed,
        'confidence': round(confidence * 100, 2),
        'segment': segment if morphed else None
    }

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Deepfake Detection</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body {
            background: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1500&q=80') no-repeat center center fixed;
            background-size: cover;
        }
        .overlay {
            background: rgba(0,0,0,0.65);
            min-height: 100vh;
            width: 100vw;
            position: fixed;
            top: 0; left: 0;
            z-index: 0;
        }
        .content {
            position: relative;
            z-index: 2;
        }
        .glass {
            background: rgba(255,255,255,0.13);
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(7px);
            -webkit-backdrop-filter: blur(7px);
            border: 1px solid rgba(255,255,255,0.18);
            padding: 2rem 2.5rem;
            margin-top: 3rem;
        }
        .header-img {
            width: 80px;
            height: 80px;
            margin-bottom: 1rem;
        }
        h1, h2, label, p, .btn, .form-label {
            color: #fff !important;
        }
        .form-control {
            background: rgba(255,255,255,0.7);
        }
    </style>
</head>
<body>
<div class="overlay"></div>
<div class="container content d-flex flex-column align-items-center justify-content-center" style="min-height: 100vh;">
    <div class="glass text-center">
        <img src="https://cdn-icons-png.flaticon.com/512/3062/3062634.png" alt="AI Icon" class="header-img">
        <h1 class="mb-4">Advanced Deepfake Detection</h1>
        <form method="post" action="/upload" enctype="multipart/form-data" class="mb-3">
            <div class="mb-3">
                <label for="file" class="form-label">Upload Image, Video, or Audio</label>
                <input class="form-control" type="file" id="file" name="file" required>
            </div>
            <button class="btn btn-primary w-100" type="submit">Analyze</button>
        </form>
    </div>
</div>
</body>
</html>
'''

RESULT_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Detection Result</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body {
            background: url('https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=1500&q=80') no-repeat center center fixed;
            background-size: cover;
        }
        .overlay {
            background: rgba(0,0,0,0.65);
            min-height: 100vh;
            width: 100vw;
            position: fixed;
            top: 0; left: 0;
            z-index: 0;
        }
        .content {
            position: relative;
            z-index: 2;
        }
        .glass {
            background: rgba(255,255,255,0.13);
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(7px);
            -webkit-backdrop-filter: blur(7px);
            border: 1px solid rgba(255,255,255,0.18);
            padding: 2rem 2.5rem;
            margin-top: 3rem;
        }
        .header-img {
            width: 80px;
            height: 80px;
            margin-bottom: 1rem;
        }
        h1, h2, label, p, .btn, .form-label, b {
            color: #fff !important;
        }
        .card, .glass {
            background: rgba(0,0,0,0.45) !important;
        }
        .btn-secondary {
            background: #1e293b !important;
        }
    </style>
</head>
<body>
<div class="overlay"></div>
<div class="container content d-flex flex-column align-items-center justify-content-center" style="min-height: 100vh;">
    <div class="glass text-center">
        <img src="https://cdn-icons-png.flaticon.com/512/3062/3062634.png" alt="AI Icon" class="header-img">
        <h2 class="mb-4">Analysis Result</h2>
        <div class="card p-4 mb-3">
            <p><b>File Type:</b> {{ filetype|capitalize }}</p>
            <p><b>Is Morphed/Deepfake?:</b> {{ 'Yes' if result['is_morphed'] else 'No' }}</p>
            <p><b>Confidence %:</b> {{ result['confidence'] }}%</p>
            {% if filetype == 'image' and result['region'] %}
                <p><b>Morphed Region (x1,y1,x2,y2):</b> {{ result['region'] }}</p>
                <img src="/uploads/{{ filename }}" class="img-fluid mt-3" style="max-width:400px; border: 3px solid #fff;">
            {% elif filetype == 'video' and result['region'] %}
                <p><b>Morphed Frame:</b> {{ result['frame'] }}</p>
                <p><b>Morphed Region (x1,y1,x2,y2):</b> {{ result['region'] }}</p>
                <video controls class="mt-3" style="max-width:400px; border: 3px solid #fff;">
                    <source src="/uploads/{{ filename }}">
                </video>
            {% elif filetype == 'audio' and result['segment'] %}
                <p><b>Morphed Segment (seconds):</b> {{ result['segment'] }}</p>
                <audio controls class="mt-3">
                    <source src="/uploads/{{ filename }}">
                </audio>
            {% endif %}
        </div>
        <a href="/" class="btn btn-secondary mt-4">Try Another File</a>
    </div>
</div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(str(uuid.uuid4()) + '_' + file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        ext = filename.rsplit('.', 1)[1].lower()
        if ext in {'png', 'jpg', 'jpeg', 'gif'}:
            result = detect_deepfake_image(filepath)
            filetype = 'image'
        elif ext in {'mp4', 'avi', 'mov'}:
            result = detect_deepfake_video(filepath)
            filetype = 'video'
        elif ext in {'wav', 'mp3', 'm4a'}:
            result = detect_deepfake_audio(filepath)
            filetype = 'audio'
        else:
            result = {'error': 'Unsupported file type'}
            filetype = 'unknown'
        return render_template_string(RESULT_HTML, result=result, filetype=filetype, filename=filename)
    return redirect(request.url)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
