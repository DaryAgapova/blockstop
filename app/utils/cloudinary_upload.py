import cloudinary
import cloudinary.uploader
from flask import current_app


def init_cloudinary():
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET'],
        secure=True,
    )


def upload_image(file, folder='blockstop/products'):
    """Upload file to Cloudinary, return URL string or None."""
    init_cloudinary()
    try:
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit', 'quality': 'auto'},
            ]
        )
        return result.get('secure_url')
    except Exception as e:
        print(f'[Cloudinary] Upload error: {e}')
        return None


def delete_image(url):
    """Delete image from Cloudinary by URL."""
    if not url or 'cloudinary' not in url:
        return
    init_cloudinary()
    try:
        # Extract public_id from URL
        # URL format: https://res.cloudinary.com/cloud/image/upload/v123/folder/filename.ext
        parts = url.split('/upload/')
        if len(parts) == 2:
            public_id = parts[1].rsplit('.', 1)[0]  # remove extension
            # remove version prefix v123/
            if '/' in public_id:
                segments = public_id.split('/')
                if segments[0].startswith('v') and segments[0][1:].isdigit():
                    public_id = '/'.join(segments[1:])
            cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f'[Cloudinary] Delete error: {e}')
