import sys
import os

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
# Remove unused user model and blueprint if not needed for this app
# from src.models.user import db 
# from src.routes.user import user_bp
from src.routes.pdf_routes import pdf_bp # Import the PDF blueprint

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'a_very_secret_key_for_pdf_app' # Changed secret key

# Register the PDF blueprint
app.register_blueprint(pdf_bp, url_prefix='/pdf') # Changed from /api to /pdf to match frontend calls

# Database setup is commented out as it's not used for PDF filling
# app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db.init_app(app)
# with app.app_context():
#     db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        # Serve specific files if they exist (e.g., /data/fieldMap.json)
        return send_from_directory(static_folder_path, path)
    else:
        # Default to serving index.html for SPA-like behavior or root access
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    # Ensure the host is 0.0.0.0 for accessibility when exposing port
    app.run(host='0.0.0.0', port=5000, debug=True)

