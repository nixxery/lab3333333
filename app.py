from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageEnhance
import requests
import os
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1 MB limit for uploaded files
UPLOAD_FOLDER = './uploads'  # папка для загруженных файлов
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
RECAPTCHA_SITE_KEY = '6LcZaf8lAAAAAP7VmVPopieoDDN-xoCapufM03BS'

# Image resizing endpoint
@app.route('/contrast', methods=['POST'])
def contrast():
    # Get the uploaded file and contrast value from the request
    file = request.files.get('file')
    contrast = float(request.form.get('contrast'))

    # Check if a file was uploaded
    if not file:
        abort(400, 'No file was uploaded')

    # Check if the uploaded file is an image
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        abort(400, 'File is not an image')
    # Verify the captcha
    recaptcha_response = request.form.get('g-recaptcha-response')
    if not recaptcha_response:
        abort(400, 'reCAPTCHA verification failed')
    payload = {
        'secret': '6LcZaf8lAAAAAP395pmCF33ej4pr3mtdttF58CJH',
        'response': recaptcha_response
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', payload).json()
    if not response['success']:
        abort(400, 'reCAPTCHA verification failed')

    # Load the image and apply contrast enhancement
    img = Image.open(file)
    contrasted_img = ImageEnhance.Contrast(img).enhance(contrast)
    

    # Calculate color distributions of original and contrasted images
    orig_colors = get_color_distribution(img)
    contrasted_colors = get_color_distribution(contrasted_img)

    # Plot color distributions as bar graphs
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('Color Distribution')
    ax1.bar(np.arange(len(orig_colors)), [c[0]/255 for c in orig_colors], color=[tuple(np.array(c[1])/255) for c in orig_colors])
    ax1.set_xticks(np.arange(len(orig_colors)))
    ax1.set_xticklabels([c[1] for c in orig_colors], rotation=45)
    ax1.set_title('Original Image')
    ax2.bar(np.arange(len(contrasted_colors)), [c[0]/255 for c in contrasted_colors], color=[tuple(np.array(c[1])/255) for c in contrasted_colors])
    ax2.set_xticks(np.arange(len(contrasted_colors)))
    ax2.set_xticklabels([c[1] for c in contrasted_colors], rotation=45)
    ax2.set_title('Contrasted Image')
    plt.tight_layout()
    # Save the plot to a file
    plot_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot.png')
    plt.savefig(plot_filename)
    # Save the contrasted image to a file
    contrasted_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'contrasted.png')
    contrasted_img.save(contrasted_filename)  
    orig_filename = os.path.join(app.config['UPLOAD_FOLDER'],'orig.png')
    img.save(orig_filename)
    # Render the result page
    result_filename = os.path.basename(plot_filename) # get just the filename from the path
    # Open the plot image as a binary file
    with open(plot_filename, 'rb') as f:
        plot_bytes = f.read()

    # Encode the plot image as base64 for display in the HTML page
    plot_base64 = base64.b64encode(plot_bytes).decode('utf-8')

    return render_template('result.html', orig=orig_filename, plot=plot_base64, result_filename=result_filename)


# Home page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', sitekey=RECAPTCHA_SITE_KEY)

# Utility function to get color distribution of an image
def get_color_distribution(img):
    colors = img.getcolors(img.size[0] * img.size[1])
    return sorted(colors, key=lambda x: x[0], reverse=True)[:10]


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
