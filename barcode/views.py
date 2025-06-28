from django.shortcuts import render, redirect, get_object_or_404
from .models import Website
from .forms import WebsiteForm
from django.core.files.storage import default_storage
from django.conf import settings
import os
from google.cloud import vision


# Set Google Application Credentials properly (best: in settings or dynamically)
if "GOOGLE_VISION_JSON" in os.environ:
    service_account_json = os.environ["GOOGLE_VISION_JSON"]
    credentials_path = "/tmp/google_vision_key.json"
    with open(credentials_path, "w") as f:
        f.write(service_account_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path


def extract_text_from_image(image_path):
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    return ""


def submit_info(request):
    error = None
    if request.method == 'POST':
        form = WebsiteForm(request.POST, request.FILES)
        if form.is_valid():
            name_input = form.cleaned_data['name']
            amount_input = str(form.cleaned_data['amount'])
            receipt_image = request.FILES['receipt_image']

            # Save receipt image temporarily
            image_path = default_storage.save('temp_receipt.jpg', receipt_image)
            image_full_path = default_storage.path(image_path)

            # OCR using Google Cloud Vision
            extracted_text = extract_text_from_image(image_full_path)
            print("Extracted Text:", extracted_text)

            if name_input.lower() in extracted_text.lower() and amount_input in extracted_text:
                person = form.save(commit=False)
                person.save()  # Save to get the ID
                full_url = request.build_absolute_uri(f"/barcode/info/{person.pk}/")
                person.generate_qr(full_url) # Generate QR with URL to info page
                person.save()  # Save again to store the QR code
                return redirect('view_info', pk=person.pk)
            else:
                error = "Name or amount not found in the uploaded receipt image."
    else:
        form = WebsiteForm()
    return render(request, 'submit_info.html', {'form': form, 'error': error})


def view_info(request, pk):
    person = get_object_or_404(Website, pk=pk)
    return render(request, 'view_info.html', {'person': person})


def show_qr(request, pk):
    person = get_object_or_404(Website, pk=pk)
    return render(request, 'qr.html', {'person': person})
    # Inside submit_info or generate_qr()
