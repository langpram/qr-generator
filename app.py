import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
import os
import sys
import argparse

def buat_qr_code(isi, jenis, nama_file="qr_code.png"):
    # Menyesuaikan isi berdasarkan jenis QR code
    if jenis.lower() == "whatsapp":
        if not isi.startswith("https://wa.me/") and not isi.startswith("http://wa.me/"):
            if not isi.startswith("+"):
                isi = "https://wa.me/" + isi
            else:
                isi = "https://wa.me/" + isi[1:] if isi.startswith("+") else isi
    elif jenis.lower() == "website":
        if not isi.startswith(("http://", "https://")):
            isi = "https://" + isi
    elif jenis.lower() == "teks":
        # Tambah prefix agar jelas ini teks, bukan search query
        if not isi.startswith("TEXT:"):
            isi = "TEXT: " + isi
    # jenis "teks_murni" tidak diubah isinya
    
    # Membuat QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    qr.add_data(isi)
    qr.make(fit=True)
    
    # Membuat gambar QR code dengan style
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=RadialGradiantColorMask(
            center_color=(0, 0, 255),  # Biru di tengah
            edge_color=(255, 0, 0)     # Merah di tepi
        )
    )
    
    # Menyimpan gambar (hanya untuk CLI mode)
    if nama_file:
        img.save(nama_file)
        print(f"QR code berhasil dibuat dan disimpan sebagai {nama_file}")
        print(f"Lokasi file: {os.path.abspath(nama_file)}")
    
    return img

def main_cli():
    """Fungsi untuk menjalankan dalam mode CLI"""
    print("=== Program Pembuat QR Code ===")
    print("Pilih jenis QR code yang ingin dibuat:")
    print("1. Teks Biasa")
    print("2. Link WhatsApp")
    print("3. Link Website")
    
    pilihan = input("Masukkan pilihan (1/2/3): ")
    
    if pilihan == "1":
        isi = input("Masukkan teks untuk QR code: ")
        print("\n⚠️  PERHATIAN: Teks biasa di QR code mungkin akan otomatis")
        print("   di-Google search oleh beberapa scanner HP.")
        print("   Gunakan QR scanner yang bisa tampilkan teks langsung.")
        
        format_choice = input("\nTambahkan prefix 'TEXT:' agar jelas ini teks? (y/n, default: y): ").lower()
        if format_choice != 'n':
            jenis = "teks"
        else:
            jenis = "teks_murni"
    elif pilihan == "2":
        isi = input("Masukkan nomor WhatsApp (contoh: 6281234567890): ")
        jenis = "whatsapp"
    elif pilihan == "3":
        isi = input("Masukkan alamat website (contoh: example.com): ")
        jenis = "website"
    else:
        print("Pilihan tidak valid!")
        return
    
    nama_file = input("Masukkan nama file untuk menyimpan QR code (default: qr_code.png): ") or "qr_code.png"
    
    if not nama_file.lower().endswith(('.png', '.jpg', '.jpeg')):
        nama_file += ".png"
    
    buat_qr_code(isi, jenis, nama_file)

def main_cli_args():
    """Fungsi untuk menjalankan dengan command line arguments"""
    parser = argparse.ArgumentParser(description='Generate QR Code')
    parser.add_argument('--isi', required=True, help='Content for QR code')
    parser.add_argument('--jenis', choices=['teks', 'whatsapp', 'website'], 
                       default='teks', help='Type of QR code')
    parser.add_argument('--file', default='qr_code.png', help='Output filename')
    
    args = parser.parse_args()
    
    buat_qr_code(args.isi, args.jenis, args.file)

# =================== API MODE ===================
try:
    from flask import Flask, request, jsonify, send_file
    import io
    import base64
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return '''
        <h1>QR Code Generator API</h1>
        <p>Endpoints:</p>
        <ul>
            <li><strong>POST /generate</strong> - Generate QR code</li>
            <li><strong>GET /</strong> - This page</li>
        </ul>
        
        <h2>How to use:</h2>
        <p>Send POST request to <code>/generate</code> with JSON body:</p>
        <pre>
{
    "isi": "your content here",
    "jenis": "teks|whatsapp|website",
    "format": "base64|image" (optional, default: base64)
}
        </pre>
        '''
    
    @app.route('/generate', methods=['POST'])
    def generate_qr():
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            isi = data.get('isi')
            jenis = data.get('jenis', 'teks')
            format_output = data.get('format', 'base64')
            
            if not isi:
                return jsonify({"error": "Field 'isi' is required"}), 400
            
            if jenis not in ['teks', 'whatsapp', 'website']:
                return jsonify({"error": "Field 'jenis' must be one of: teks, whatsapp, website"}), 400
            
            # Generate QR code (tanpa save file)
            img = buat_qr_code(isi, jenis, None)
            
            if format_output == 'image':
                # Return image directly
                img_io = io.BytesIO()
                img.save(img_io, 'PNG')
                img_io.seek(0)
                return send_file(img_io, mimetype='image/png')
            else:
                # Return base64 encoded image
                img_io = io.BytesIO()
                img.save(img_io, 'PNG')
                img_io.seek(0)
                img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
                
                return jsonify({
                    "success": True,
                    "image": f"data:image/png;base64,{img_base64}",
                    "content": isi,
                    "type": jenis
                })
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Untuk Vercel
    def handler(request):
        return app(request.environ, lambda *args: None)
    
    FLASK_AVAILABLE = True
    
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask tidak terinstall. Hanya mode CLI yang tersedia.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'api':
            # Mode API
            if FLASK_AVAILABLE:
                print("Menjalankan dalam mode API...")
                print("Buka http://localhost:5000 di browser")
                app.run(debug=True)
            else:
                print("Flask tidak terinstall. Install dengan: pip install flask")
        elif sys.argv[1] == '--help' or any(arg.startswith('--') for arg in sys.argv[1:]):
            # Mode CLI dengan arguments
            main_cli_args()
        else:
            print("Usage:")
            print("  python app.py              # Interactive CLI mode")
            print("  python app.py api          # API mode")
            print("  python app.py --isi 'text' --jenis teks --file output.png")
    else:
        # Mode CLI interaktif (default)
        main_cli()