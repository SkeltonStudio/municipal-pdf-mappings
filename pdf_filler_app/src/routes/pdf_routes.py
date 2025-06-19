import sys
import os
from flask import Blueprint, request, jsonify, send_file
import tempfile

# Ensure the src directory is in the Python path
# This is a common way to handle imports in Flask apps structured with a src directory
# Adjust if your project structure or execution context differs
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir)) # Add src to path

from utils.pdf_filler_logic import fill_pdf_web

pdf_bp = Blueprint("pdf", __name__, url_prefix="/pdf")

# Define the path to the templates directory relative to the app's data path
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(APP_ROOT, "data")
TEMPLATE_BASE_PATH = os.path.join(DATA_PATH, "templates")

@pdf_bp.route("/fill", methods=["POST"])
def handle_fill_pdf():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    template_name = data.get("template_name")
    user_form_data = data.get("form_data")

    if not template_name:
        return jsonify({"error": "Missing \"template_name\" in request"}), 400
    if not user_form_data:
        return jsonify({"error": "Missing \"form_data\" in request"}), 400
    if not isinstance(user_form_data, dict):
        return jsonify({"error": "\"form_data\" must be an object"}), 400

    # For security and simplicity, ensure template_name is just a filename
    if "/" in template_name or ".." in template_name:
        return jsonify({"error": "Invalid template name"}), 400

    # Create a temporary file for the output PDF
    try:
        temp_dir = tempfile.mkdtemp()
        output_pdf_name = f"filled_{template_name}"
        output_pdf_path = os.path.join(temp_dir, output_pdf_name)

        success, result_message = fill_pdf_web(
            template_filename=template_name,
            output_pdf_path=output_pdf_path,
            user_data=user_form_data
        )

        if success:
            return send_file(
                output_pdf_path,
                as_attachment=True,
                download_name=output_pdf_name,
                mimetype="application/pdf"
            )
        else:
            # Log the error on the server if needed
            print(f"PDF filling failed: {result_message}")
            return jsonify({"error": "PDF filling failed", "details": result_message}), 500

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An unexpected server error occurred"}), 500
    finally:
        # Clean up the temporary file and directory if it was created
        if os.path.exists(output_pdf_path):
            try:
                os.remove(output_pdf_path)
            except Exception as e_remove:
                print(f"Error removing temp file {output_pdf_path}: {e_remove}")
        if os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except Exception as e_rmdir:
                print(f"Error removing temp dir {temp_dir}: {e_rmdir}")

@pdf_bp.route("/templates", methods=["GET"])
def list_templates():
    try:
        templates = [f for f in os.listdir(TEMPLATE_BASE_PATH) if os.path.isfile(os.path.join(TEMPLATE_BASE_PATH, f)) and f.lower().endswith(".pdf")]
        return jsonify({"templates": templates}), 200
    except Exception as e:
        print(f"Error listing templates: {e}")
        return jsonify({"error": "Could not retrieve template list"}), 500


