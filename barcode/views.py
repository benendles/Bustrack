from django.shortcuts import render, redirect, get_object_or_404
from .models import Website
from .forms import WebsiteForm
from django.core.files.storage import default_storage
from django.contrib import messages
import os

def extract_text_from_image(image_path):
    """
    Extract text from image using OCR.
    Currently disabled to prevent Google Cloud Vision API errors.
    Returns a mock response for development.
    """
    try:
        # For development purposes, we'll simulate text extraction
        # In production, you would implement proper OCR here

        # Mock extracted text that includes common receipt information
        mock_text = """
        RECEIPT
        Name: John Doe
        Amount: 50.00
        Date: 2024-01-01
        Thank you for your payment
        """
        return mock_text

        # Uncomment below when Google Cloud Vision API is properly configured
        # from google.cloud import vision
        # client = vision.ImageAnnotatorClient()
        # with open(image_path, "rb") as image_file:
        #     content = image_file.read()
        # image = vision.Image(content=content)
        # response = client.text_detection(image=image)
        # texts = response.text_annotations
        # if texts:
        #     return texts[0].description
        # return ""

    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def submit_info(request):
    error = None
    if request.method == 'POST':
        form = WebsiteForm(request.POST, request.FILES)
        if form.is_valid():
            name_input = form.cleaned_data['name']
            amount_input = str(form.cleaned_data['amount'])
            receipt_image = request.FILES.get('receipt_image')

            try:
                if receipt_image:
                    # Save receipt image temporarily
                    image_path = default_storage.save('temp_receipt.jpg', receipt_image)
                    image_full_path = default_storage.path(image_path)

                    # OCR text extraction
                    extracted_text = extract_text_from_image(image_full_path)
                    print("Extracted Text:", extracted_text)

                    # For development: Accept any name and amount for now
                    # In production, you would validate against extracted text
                    verification_passed = True  # Simplified for development

                    # Uncomment below for actual OCR validation
                    # verification_passed = (name_input.lower() in extracted_text.lower() and
                    #                       amount_input in extracted_text)

                    if verification_passed:
                        person = form.save(commit=False)
                        person.save()  # Save to get the ID
                        person.generate_qr()  # Generate QR with URL to info page
                        person.save()  # Save again to store the QR code

                        # Clean up temporary file
                        try:
                            default_storage.delete(image_path)
                        except:
                            pass

                        messages.success(request, 'Receipt processed successfully! Your QR code has been generated.')
                        return redirect('view_info', pk=person.pk)
                    else:
                        error = "Name or amount not found in the uploaded receipt image."
                        # Clean up temporary file
                        try:
                            default_storage.delete(image_path)
                        except:
                            pass
                else:
                    # Allow submission without receipt for development
                    person = form.save(commit=False)
                    person.save()
                    person.generate_qr()
                    person.save()
                    messages.success(request, 'Information submitted successfully! Your QR code has been generated.')
                    return redirect('view_info', pk=person.pk)

            except Exception as e:
                error = f"An error occurred while processing your receipt: {str(e)}"
                messages.error(request, error)

    else:
        form = WebsiteForm()
    return render(request, 'submit_info.html', {'form': form, 'error': error})

def view_info(request, pk):
    person = get_object_or_404(Website, pk=pk)
    return render(request, 'view_info.html', {'person': person})
def show_qr(request, pk):
    person = get_object_or_404(Website, pk=pk)
    return render(request, 'qr.html', {'person': person})   