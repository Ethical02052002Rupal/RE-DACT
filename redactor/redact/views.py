from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from .REDACT import RedactText, RedactVideo, RedactImage
from django.http import JsonResponse, FileResponse, HttpResponse, HttpResponseBadRequest
from django.conf import settings
import cv2
from ultralytics import YOLO
import json
import os
import time

global entities_to_redact
entities_to_redact = []  # Initialize global variable

def upload_file(request):
    return render(request, 'Front_web_page.html')

def handle_image(request):
    if request.method == 'POST' and request.FILES.get('uploaded_file'):
        file = request.FILES['uploaded_file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_url = fs.url(filename)

        # Store face images for user to select in web_page2_image.html

        RedactImage.detect_faces('media/'+filename, 'media/')
        detected_texts, list_pii, text_coords = RedactImage.extract_pii('media/'+filename)

        request.session["image_url"] = file_url
        request.session.modified = True

        return render(request, 'web_page2_image.html', {
            'image_url': file_url,
            'ocr_detected_words': detected_texts,
            'nlp_detected_words': list_pii,
            'face': '/media/face.jpg',
        })

    return render(request, 'Front_web_page.html')

def handle_video(request):
    if request.method == 'POST' and request.FILES.get('uploaded_file'):
        file = request.FILES['uploaded_file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_url = fs.url(filename)
        return render(request, 'web_page2_video.html', {'file_url': file_url})
    return render(request, 'web_page2_video.html')

def handle_pdf(request):
    global entities_to_redact
    if request.method == 'POST' and request.FILES.get('uploaded_file'):
        file = request.FILES['uploaded_file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_url = fs.url(filename)
        
        # Generate list of entities and update global + session
        RedactText.generate_list('./' + file_url)
        entities_to_redact = list(RedactText.display_entities())

        # Store PDF path in session
        request.session["pdf_url"] = file_url  # ✅ FIX: Ensure PDF is stored
        request.session["entities_to_redact"] = entities_to_redact
        request.session.modified = True

        return render(request, 'web_page2_pdf.html', {
            'pdf_url': file_url,
            'entities_to_redact1': json.dumps(entities_to_redact),
            'entities_to_redact': entities_to_redact
        })

    return render(request, 'web_page2_pdf.html')

@csrf_exempt
def update_nlp_words(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            word = data.get("word")
            action = data.get("action")  # "add" or "remove"

            # Ensure session contains NLP words list
            if "nlp_detected_words" not in request.session:
                request.session["nlp_detected_words"] = []

            list_pii = request.session["nlp_detected_words"]

            if action == "add" and word not in list_pii:
                list_pii.append(word)
            elif action == "remove" and word in list_pii:
                list_pii.remove(word)

            # Save session
            request.session["nlp_detected_words"] = list_pii

            return JsonResponse({"status": "success", "nlp_detected_words": list_pii})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

def add_redacted_term(request):
    global entities_to_redact
    if request.method == "POST":
        data = json.loads(request.body)
        term = data.get("term", "").strip()
        if term:
            # Ensure we get a valid list from session
            entities_to_redact = request.session.get("entities_to_redact", [])
            
            if term not in entities_to_redact:
                entities_to_redact.append(term)
                request.session["entities_to_redact"] = entities_to_redact
                request.session.modified = True  # Ensure Django saves session changes
                
        return JsonResponse({"entities_to_redact": entities_to_redact})

def remove_redacted_term(request):
    global entities_to_redact
    if request.method == "POST":
        data = json.loads(request.body)
        term = data.get("term", "").strip()
        
        # Ensure we get a valid list from session
        entities_to_redact = request.session.get("entities_to_redact", [])
        
        if term in entities_to_redact:
            entities_to_redact.remove(term)
            request.session["entities_to_redact"] = entities_to_redact
            request.session.modified = True  # Ensure Django saves session change
        
        return JsonResponse({"entities_to_redact": entities_to_redact})

def detect_faces(request):
    video_path = request.GET.get('video_url', None)

    if not video_path:
        return JsonResponse({'error': 'No video URL provided'}, status=400)

    video_path = os.path.join("", video_path.strip("/"))

    # Open video file
    RedactVideo.process_faces(video_path)
    faces_dir = os.path.join(settings.MEDIA_ROOT, "")
    print(faces_dir)
    face_images = []

    # Collect all face image file URLs
    if os.path.exists(faces_dir):
        for filename in os.listdir(faces_dir):
            if filename.endswith(".jpg"):
                face_images.append(os.path.join(settings.MEDIA_URL, "", filename))

    return JsonResponse({'face_images': face_images})

def redact_pdf(request):
    if request.method == "POST":
        pdf_path = request.session.get("pdf_url")

        if not pdf_path:
            print("DEBUG: No PDF path found in session.")
            print("Current session data:", request.session.items())  # Log session data
            return JsonResponse({"error": "No PDF found in session."}, status=400)

        entities_to_redact = request.session.get("entities_to_redact", [])
        output_path = pdf_path.replace(".pdf", "_redacted.pdf")

        try:
            RedactText.redact("./" + pdf_path, entities_to_redact, "./" + output_path)
            request.session["pdf_url"] = output_path  # Update session with new PDF path
            print(output_path)
            request.session.modified = True
            return JsonResponse({"pdf_url": output_path})
        except Exception as e:
            print("ERROR during redaction:", str(e))  # Log error details
            return JsonResponse({"error": "Redaction failed.", "details": str(e)}, status=500)

def redact_image(request):
    if request.method == "POST":
        image_path = request.session.get("image_url")

        if not image_path:
            print("DEBUG: No image path found in session.")
            print("Current session data:", request.session.items())  # Log session data
            return JsonResponse({"error": "No image found in session."}, status=400)

        list_pii = request.session.get("nlp_detected_words", [])
        file_name, file_ext = os.path.splitext(image_path)
        output_path = f"{file_name}_redacted{file_ext}"
        print(output_path)

        try:
            RedactImage.process_image("./"+image_path, "."+output_path, list_pii, 'media/')
            request.session["image_url"] = output_path  # Update session with new PDF path
            print(output_path)
            request.session.modified = True
            return JsonResponse({"image_url": output_path})
        except Exception as e:
            print("ERROR during redaction:", str(e))  # Log error details
            return JsonResponse({"error": "Redaction failed.", "details": str(e)}, status=500)


@csrf_exempt
def redact_video(request):
    """Redacts selected faces from a video and updates the session."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    video_url = request.POST.get("video_url")
    selected_faces = request.POST.getlist("selected_faces[]")

    if not video_url or not selected_faces:
        return JsonResponse({"error": "Missing video URL or selected faces"}, status=400)

    video_path = os.path.join(settings.MEDIA_ROOT, video_url.replace(settings.MEDIA_URL, ""))
    output_filename = f"redacted_{os.path.basename(video_path)}"
    output_path = os.path.join(settings.MEDIA_ROOT, output_filename)

    try:
        selected_faces = [int(face_id) for face_id in selected_faces]
        RedactVideo.redact_faces(video_path, selected_faces, output_path)
        redacted_video_url = f"{settings.MEDIA_URL}{output_filename}"

        # Update session with the new redacted video URL
        request.session["video_url"] = redacted_video_url
        request.session.modified = True

        return JsonResponse({"success": True, "file_url": redacted_video_url})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def download_p(request):
    return render(request, "web_page3_d_pdf.html")

def download_v(request):
    return render(request, "web_page3_d_video.html")

def download_i(request):
    return render(request, "web_page3_d_image.html")

def download_pdf(request):
    pdf_path = request.session.get("pdf_url")

    if not pdf_path or not os.path.exists("." + pdf_path):
        return HttpResponse("Error: No redacted PDF found.", status=404)

    response = FileResponse(open("." + pdf_path, "rb"), as_attachment=True)

    # Get original and redacted file paths
    original_pdf = pdf_path.replace("_redacted.pdf", ".pdf")
    redacted_pdf = pdf_path

    # Delete both files after serving the response
    try:
        if os.path.exists("." + original_pdf):
            os.remove("." + original_pdf)
        if os.path.exists("." + redacted_pdf):
            os.remove("." + redacted_pdf)
    except Exception as e:
        print("Error deleting files:", e)

    # Clear session to prevent stale data issues
    request.session.pop("pdf_url", None)
    request.session.modified = True

    return response

def download_video(request):
    video_path = request.session.get("video_url")
    print(video_path)

    if not video_path or not os.path.exists("." + video_path):
        return HttpResponse("Error: No redacted video found.", status=404)

    response = FileResponse(open("." + video_path, "rb"), as_attachment=True)
    print(response)

    # Get original and redacted file paths
    original_video = video_path.replace("_redacted.mp4", ".mp4")
    redacted_video = video_path

    # Delete both files after serving the response
    try:
        if os.path.exists("." + original_video):
            os.remove("." + original_video)
        if os.path.exists("." + redacted_video):
            os.remove("." + redacted_video)
    except Exception as e:
        print("Error deleting files:", e)

    # Clear session to prevent stale data issues
    request.session.pop("video_url", None)
    request.session.modified = True

    return response

def download_image(request):
    image_path = request.session.get("image_url")
    print(image_path)

    if not image_path or not os.path.exists("." + image_path):
        return HttpResponse("Error: No redacted image found.", status=404)

    response = FileResponse(open("." + image_path, "rb"), as_attachment=True)
    print(response)

    # Get original and redacted file paths
    original_image = image_path.replace("_redacted.mp4", ".mp4")
    redacted_image = image_path

    # Delete both files after serving the response
    try:
        if os.path.exists("." + original_image):
            os.remove("." + original_image)
        if os.path.exists("." + redacted_image):
            os.remove("." + redacted_image)
    except Exception as e:
        print("Error deleting files:", e)

    # Clear session to prevent stale data issues
    request.session.pop("image_url", None)
    request.session.modified = True

    return response