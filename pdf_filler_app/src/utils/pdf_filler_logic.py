import json
import os
from pdfrw import PdfReader, PdfWriter, IndirectPdfDict, PdfName, PdfDict, PdfObject, PdfString

# Define a base path for data files within the Flask app structure
# This assumes this script is in src/utils and data is in src/data
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(APP_ROOT, "data")
FIELD_MAP_PATH = os.path.join(DATA_PATH, "fieldMap.json")
TEMPLATE_BASE_PATH = os.path.join(DATA_PATH, "templates")

def fill_pdf_web(template_filename, output_pdf_path, user_data):
    input_pdf_path = os.path.join(TEMPLATE_BASE_PATH, template_filename)
    # The field_map_path is now fixed as FIELD_MAP_PATH
    # The template_key in fieldMap.json should match template_filename
    template_key = template_filename 

    try:
        if not os.path.exists(input_pdf_path):
            print(f"Error: Template PDF 	'{input_pdf_path}	' not found.")
            return False, f"Template PDF 	'{template_filename}	' not found."
        
        if not os.path.exists(FIELD_MAP_PATH):
            print(f"Error: Field map 	'{FIELD_MAP_PATH}	' not found.")
            return False, "Field map file not found."

        with open(FIELD_MAP_PATH, 'r') as f:
            full_field_map = json.load(f)

        if template_key not in full_field_map:
            print(f"Error: Template key 	'{template_key}	' not found in {FIELD_MAP_PATH}.")
            return False, f"Mappings for template 	'{template_key}	' not found."

        template_mappings = full_field_map[template_key]
        reader = PdfReader(input_pdf_path)
        
        for page in reader.pages:
            annotations = page.get('/Annots')
            if annotations:
                for annotation in annotations:
                    if annotation.get('/Subtype') == PdfName('Widget') and annotation.get('/T'):
                        raw_field_name_from_pdf = annotation['/T'].to_unicode().strip('()')
                        
                        friendly_key_for_this_field = None
                        for fk, rn in template_mappings.items():
                            if rn == raw_field_name_from_pdf:
                                friendly_key_for_this_field = fk
                                break
                        
                        if friendly_key_for_this_field and friendly_key_for_this_field in user_data:
                            value_to_fill = user_data[friendly_key_for_this_field]
                            field_type = annotation.get('/FT')

                            if field_type == PdfName('Tx'): # Text field
                                annotation.update(PdfDict(V=PdfString(str(value_to_fill))))
                            elif field_type == PdfName('Btn'): # Button (checkbox/radio)
                                if isinstance(value_to_fill, bool):
                                    checked_value = PdfName('Yes') 
                                    unchecked_value = PdfName('Off')
                                    if value_to_fill:
                                        annotation.update(PdfDict(V=checked_value, AS=checked_value))
                                    else:
                                        annotation.update(PdfDict(V=unchecked_value, AS=unchecked_value))
                                elif isinstance(value_to_fill, str) and value_to_fill.lower() in ["yes", "on", "true"]:
                                     annotation.update(PdfDict(V=PdfName(value_to_fill), AS=PdfName(value_to_fill)))
                                else: # Assume it's a specific name for radio button or unchecked checkbox
                                     annotation.update(PdfDict(V=PdfName('Off'), AS=PdfName('Off')))

                            elif field_type == PdfName('Ch'): # Choice field
                                annotation.update(PdfDict(V=PdfString(str(value_to_fill))))
                            
                            if PdfName('/AP') in annotation:
                                annotation.pop(PdfName('/AP'))

        if reader.Root.AcroForm:
            reader.Root.AcroForm.NeedAppearances = PdfObject('true')
        else:
            print("Warning: No AcroForm dictionary found in PDF Root.")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        PdfWriter().write(output_pdf_path, reader)
        print(f"Successfully filled PDF and saved to {output_pdf_path}")
        return True, output_pdf_path

    except Exception as e:
        print(f"An error occurred during PDF filling: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

# Removed the if __name__ == "__main__": block to make it a pure library module

