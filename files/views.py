from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404, StreamingHttpResponse
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from users.permissions import IsAdminRole
from rest_framework.permissions import IsAuthenticated
from .models import (
    UploadedWheelFile, 
    UploadedModelFile, 
    UploadedInputFile,
    UploadedClassFile,
    UploadedGroundTruthFile
)
from django.conf import settings
from .serializers import (
    UploadedInputFileSerializer,
    UploadedWheelFileSerializer,
    UploadedModelFileSerializer,
    UploadedClassFileSerializer,
    UploadedGroundTruthFileSerializer
)
import os
import shutil, mimetypes

file_view_mapper = {
    'input': UploadedInputFile,
    'wheel': UploadedWheelFile,
    'model': UploadedModelFile,
    'class': UploadedClassFile,
    'groundtruth': UploadedGroundTruthFile
}

file_view_serializer_mapper = {
    'input': UploadedInputFileSerializer,
    'wheel': UploadedWheelFileSerializer,
    'model': UploadedModelFileSerializer,
    'class': UploadedClassFileSerializer,
    'groundtruth': UploadedGroundTruthFileSerializer
}

class ListView(APIView):
    def get(self, request, file_type):
        if not file_type:
            return Response({"error": "Missing file_type"}, status=400)

        qs = file_view_mapper[file_type].objects.all()

        serializer = file_view_serializer_mapper[file_type](qs, many=True)
        return Response(serializer.data)

class UploadInputFolderView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        upload_type = request.POST.get("upload_type")
        folder = request.POST.get("folder")
        files = request.FILES.getlist("files")

        if not folder:
            return Response({"error": "Missing folder name"}, status=400)

        if not files:
            return Response({"error": "No files uploaded"}, status=400)

        # Compute storage base path
        base_path = os.path.join(settings.MEDIA_ROOT, upload_type or '', folder)
        os.makedirs(base_path, exist_ok=True)

        total_size = 0
        for f in files:
            file_path = os.path.join(base_path, f.name)
            with open(file_path, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            total_size += f.size

        # single DB record for the folder
        UploadedInputFile.objects.create(
            name=folder,
            path=base_path,
            uploaded_by=request.user.username,
            description=request.data.get("description", ""),
            size=total_size,
            input_type='folder'
        )

        return Response({"message": f"Folder '{folder}' uploaded with {len(files)} files."})



class DeleteInputFolderView(APIView):
    def delete(self, request, pk):
        try:
            folder_record = UploadedInputFile.objects.get(pk=pk, input_type='folder')
        except UploadedInputFile.DoesNotExist:
            return Response({"error": "Folder not found"}, status=404)

        full_path = os.path.join(settings.MEDIA_ROOT, folder_record.path)

        # delete folder and all its contents from disk
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)

        # delete folder record
        folder_record.delete()

        return Response({"message": f"Folder '{folder_record.path}' deleted"}, status=200)


class UploadInputFileView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        upload_type = request.POST.get("upload_type")
        files = request.FILES.getlist("files")
        description = request.data.get("description", "")
        input_type = 'file'

        if not upload_type:
            return Response({"error": "Missing 'upload_type'"}, status=400)

        if not files:
            return Response({"error": "No files uploaded"}, status=400)

        uploaded_by = request.user.username

        for f in files:
            relative_path = os.path.join(upload_type, f.name)
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

            # Prevent path traversal
            if not os.path.realpath(full_path).startswith(os.path.realpath(settings.MEDIA_ROOT)):
                return Response({"error": f"Invalid path for file {f.name}"}, status=400)

            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "wb+") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            # Save each file record
            UploadedInputFile.objects.create(
                name=f.name,
                path=relative_path,
                uploaded_by=uploaded_by,
                description=description,
                size=f.size,
                input_type='file'
            )

        return Response(
            {
                "message": f"{len(files)} files uploaded",
                "files": [f.name for f in files]
            },
            status=201
        )

class DeleteFileView(APIView):
    def delete(self, request, pk, file_type):

        if not file_type:
            return Response({"error": "Missing file_type"}, status=400)

        try:
            file_record = file_view_mapper[file_type].objects.get(pk=pk)
        except file_view_mapper[file_type].DoesNotExist:
            return Response({"error": "File not found"}, status=404)

        full_path = os.path.join(settings.MEDIA_ROOT, file_record.path)

        # delete file from disk
        if os.path.isfile(full_path):
            os.remove(full_path)

        # delete record
        file_record.delete()

        return Response({"message": f"File '{file_record.path}' deleted"}, status=200)

class UploadFileView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, upload_type):
        files = request.FILES.getlist("files")
        description = request.data.get("description", "")
        input_type = 'file'

        if not upload_type:
            return Response({"error": "Missing 'upload_type'"}, status=400)

        if not files:
            return Response({"error": "No files uploaded"}, status=400)

        uploaded_by = request.user.username

        for f in files:
            relative_path = os.path.join(upload_type, f.name)
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

            # Prevent path traversal
            if not os.path.realpath(full_path).startswith(os.path.realpath(settings.MEDIA_ROOT)):
                return Response({"error": f"Invalid path for file {f.name}"}, status=400)

            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "wb+") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            # Save each file record
            file_view_mapper[upload_type].objects.create(
                name=f.name,
                path=relative_path,
                uploaded_by=uploaded_by,
                description=description,
                size=f.size,
            )

        return Response(
            {
                "message": f"{len(files)} files uploaded",
                "files": [f.name for f in files]
            },
            status=201
        )

class DownloadFolderView(APIView):

    def post(self, request):
        relative_path = request.data.get('relative_path')
        folder_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise Http404("Folder not found")

        folder_path = folder_path.rstrip('/')

        zip_base = folder_path
        zip_path = f"{zip_base}.zip"

        # Create zip archive
        shutil.make_archive(zip_base, 'zip', folder_path)

        # Return file response
        return FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=os.path.basename(zip_path))

class DownloadFileView(APIView):
    def post(self, request):
        relative_path = request.data.get('relative_path')

        if not relative_path:
            raise Http404("Missing relative path")

        # Prevent directory traversal
        safe_path = os.path.normpath(relative_path)
        if safe_path.startswith(".."):
            raise Http404("Invalid path")

        file_path = os.path.join(settings.MEDIA_ROOT, safe_path)

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise Http404("File not found")

        # Guess MIME type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "application/octet-stream"  # default fallback

        # Return file response with correct filename and content type
        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path),
            content_type=content_type
        )

        return response


class ServeVideoView(APIView):
    def get(self,request):
        # Get the relative path from query parameter
        relative_path = request.GET.get('path')
        if not relative_path:
            raise Http404("No path provided.")

        # Construct full absolute path
        abs_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        # Check if the file exists
        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            raise Http404("Video not found.")

        # Return file as a streaming response
        return FileResponse(open(abs_path, 'rb'), content_type='video/mp4')
