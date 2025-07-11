from flask import Flask, request, jsonify, send_file
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
import io
import base64

app = Flask(__name__)

def buat_qr_code(isi, jenis):
    if jenis.lower() == "whatsapp":
        if not isi.startswith("https://wa.me/"):
            isi = "https://wa.me/" + isi.lstrip("+")
    elif jenis.lower() == "website":
        if not isi.startswith(("http://", "https://")):
            isi = "https://" + isi

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(isi)
    qr.make(fit=True)
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=RadialGradiantColorMask(
            center_color=(0, 0, 255),
            edge_color=(255, 0, 0)
        )
    )
    return img

@app.route("/")
def home():
    return {
        "message": "QR Code Generator API - POST to /generate with JSON {isi, jenis, format}"
    }

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    isi = data.get("isi")
    jenis = data.get("jenis", "teks")
    format_output = data.get("format", "base64")

    if not isi:
        return jsonify({"error": "Field 'isi' is required"}), 400

    img = buat_qr_code(isi, jenis)

    img_io = io.BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)

    if format_output == "image":
        return send_file(img_io, mimetype="image/png")
    else:
        img_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")
        return jsonify({
            "success": True,
            "image": f"data:image/png;base64,{img_base64}"
        })

# ====== Handler untuk Vercel ======
app = Flask(__name__)

