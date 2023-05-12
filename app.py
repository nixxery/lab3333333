from flask import Flask, render_template, request, abort, send_from_directory
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image
import os
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1 MB limit for uploaded files
UPLOAD_FOLDER = './uploads'  # folder for uploaded files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
RECAPTCHA_SITE_KEY = '6LcZaf8lAAAAAP7VmVPopieoDDN-xoCapufM03BS'


# Image merging endpoint
@app.route('/merge', methods=['POST'])
def merge():
    # Get the uploaded files and merge type from the request
    file1 = request.files.get('file1')
    file2 = request.files.get('file2')
    merge_type = request.form.get('merge_type')

    # Check if both files were uploaded
    if not file1 or not file2:
        abort(400, 'Two files were not uploaded')

    # Check if the uploaded files are images
    if not file1.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) or not file2.filename.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.gif')):
        abort(400, 'One or both files are not images')

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
    # Load the images
    img1 = Image.open(file1)
    img2 = Image.open(file2)

    # Merge the images based on the merge type
    if merge_type == 'vertical':
        merged_img = Image.new('RGB', (max(img1.width, img2.width), img1.height + img2.height))
        merged_img.paste(img1, (0, 0))
        merged_img.paste(img2, (0, img1.height))
    elif merge_type == 'horizontal':
        merged_img = Image.new('RGB', (img1.width + img2.width, max(img1.height, img2.height)))
        merged_img.paste(img1, (0, 0))
        merged_img.paste(img2, (img1.width, 0))
    else:
        abort(400, 'Invalid merge type')

    # Save the merged image to a file
    merged_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'merged.png')
    merged_img.save(merged_filename)

    # Calculate color distributions of original images and merged image
    colors1 = get_color_distribution(img1)
    colors2 = get_color_distribution(img2)
    merged_colors = get_color_distribution(merged_img)

    # Plot color distributions as bar graphs
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Color Distribution')
    plot_color_distribution(ax1, colors1, 'Original Image 1')
    plot_color_distribution(ax2, colors2, 'Original Image 2')
    plot_color_distribution(ax3, merged_colors, 'Merged Image')
    plt.tight_layout()

    # Save the plot to a file
    plot_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot.png')
    plt.savefig(plot_filename)

    # Render the result page
    merged_filename = os.path.basename(merged_filename)  # get just the filename from the path
    plot_filename = os.path.basename(plot_filename)
    return render_template('result.html', merged=merged_filename, plot=plot_filename)


# Utility function to get color distribution of an image
def get_color_distribution(img):
    colors = img.getcolors(img.size[0] * img.size[1])
    return sorted(colors, key=lambda x: x[0], reverse=True)[:10]


# Utility function to plot color distribution as a bar graph
def plot_color_distribution(ax, colors, title):
    ax.bar(np.arange(len(colors)), [c[0] / 255 for c in colors], color=[tuple(np.array(c[1]) / 255) for c in colors])
    ax.set_xticks(np.arange(len(colors)))
    ax.set_xticklabels([c[1] for c in colors], rotation=45)
    ax.set_title(title)


# Home page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', sitekey=RECAPTCHA_SITE_KEY)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
