from flask import Flask, render_template, request, abort, send_from_directory
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1 MB limit for uploaded files
UPLOAD_FOLDER = './uploads'  # folder for uploaded files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

    # Save the uploaded files as orig1.png and orig2.png
    orig1_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'orig1.png')
    orig2_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'orig2.png')
    file1.save(orig1_filename)
    file2.save(orig2_filename)

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

    # Save the merged image
    merged_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'merged.png')
    merged_img.save(merged_filename)

    # Calculate and save color distribution plots
    plot1_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot1.png')
    plot2_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot2.png')
    plot_merged_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot_merged.png')

    plot_color_distribution(img1, plot1_filename)
    plot_color_distribution(img2, plot2_filename)
    plot_color_distribution(merged_img, plot_merged_filename)

    return render_template('result.html', merged=merged_filename, plot1=plot1_filename, plot2=plot2_filename,
                           plot_merged=plot_merged_filename, orig1=orig1_filename, orig2=orig2_filename)


def plot_color_distribution(image, plot_filename):
    # Convert the image to numpy array
    img_array = np.array(image)

    # Calculate the color distribution for each channel separately
    color_dist_r, _ = np.histogram(img_array[..., 0].flatten(), bins=256, range=(0, 255))
    color_dist_g, _ = np.histogram(img_array[..., 1].flatten(), bins=256, range=(0, 255))
    color_dist_b, _ = np.histogram(img_array[..., 2].flatten(), bins=256, range=(0, 255))

    # Normalize the color distribution
    color_dist_normalized_r = color_dist_r / np.sum(color_dist_r)
    color_dist_normalized_g = color_dist_g / np.sum(color_dist_g)
    color_dist_normalized_b = color_dist_b / np.sum(color_dist_b)

    # Create the color distribution plot
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(color_dist_normalized_r, color='red', label='Red')
    ax.plot(color_dist_normalized_g, color='green', label='Green')
    ax.plot(color_dist_normalized_b, color='blue', label='Blue')

    # Set the plot title and labels
    ax.set_title('Color Distribution')
    ax.set_xlabel('Pixel Value')
    ax.set_ylabel('Normalized Frequency')

    # Add a legend
    ax.legend()

    # Save the plot to a file
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    with open(plot_filename, 'wb') as file:
        file.write(buf.getvalue())


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
