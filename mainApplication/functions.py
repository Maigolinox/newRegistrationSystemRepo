from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfWriter, PdfReader
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from django.templatetags.static import static


subject = " CIMPS 2024 - Diploma "
output_folder = "./static/diplomas"
os.makedirs(output_folder, exist_ok=True)


def create_diploma(template_path, name, output_image_path):
    # Abrir la plantilla de imagen
    image = Image.open(template_path)
    draw = ImageDraw.Draw(image)
    

    # Configurar la fuente
    font_path = os.path.join('static/fonts', 'Outfit-Regular.ttf')
    
    

    try:
        font = ImageFont.truetype('./static/fonts/Outfit-Regular.ttf', 200)
    except Exception as e:
        font=ImageFont.load_default()

    # Obtener tamaño del texto usando la fuente
    text_bbox = draw.textbbox((0, 0), name, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    width, height = image.size

    # Posicionar el texto en el centro de la imagen
    x = (width - text_width) / 2
    y = (height - text_height) / 2  # Centrar el texto verticalmente también

    # Añadir el nombre al diploma
    draw.text((x, y), name, font=font, fill="black")

    # Guardar la imagen con el nombre del diploma
    image.save(output_image_path)

def create_protected_pdf(image_path, pdf_path, owner_password):
    # Crear un PDF a partir de la imagen
    c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    c.drawImage(image_path, 0, 0, width=landscape(A4)[0], height=landscape(A4)[1])
    c.save()
    
    # Proteger el PDF con contraseña
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    # Permitir abrir el archivo sin contraseña, pero protegerlo contra edición
    writer.encrypt(user_pwd="", owner_pwd=owner_password, use_128bit=True)
    
    with open(pdf_path, "wb") as f:
        writer.write(f)

def send_email(receiver_email, subject, body, pdf_path):
    sender = "conferencecimps@cimat.mx"
    password = "HIPOCRATES@2022"

    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    with open(pdf_path, "rb") as f:
        attach = MIMEApplication(f.read(),_subtype="pdf")
        attach.add_header('Content-Disposition','attachment',filename=os.path.basename(pdf_path))
        message.attach(attach)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(message)