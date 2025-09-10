from django.urls import path
from .views import (
    ListView,
    UploadFileView,
    UploadInputFolderView,
    UploadInputFileView,
    DeleteInputFolderView,
    DeleteFileView,
    DownloadFolderView,
    DownloadFileView,
    ServeVideoView
)

urlpatterns = [
    path('list/<str:file_type>/', ListView.as_view(), name='file-list'),

    path('upload/folder', UploadInputFolderView.as_view(), name='upload-input-folder'),
    path('upload/file', UploadInputFileView.as_view(), name='upload-input-file'),

    path('upload/<str:upload_type>/', UploadFileView.as_view(), name='upload-file'),

    path('delete/folder/<int:pk>/', DeleteInputFolderView.as_view(), name='delete-folder'),
    path('delete/file/<int:pk>/<str:file_type>/', DeleteFileView.as_view(), name='delete-file'),
    path('download/output_path/', DownloadFolderView.as_view(), name='download-output-folder'),
    path('downloadfile/', DownloadFileView.as_view(), name='download-file'),

    path('download/serve-video/', ServeVideoView.as_view())

    # path('download/wheel/<int:pk>/', WheelFileDownloadView.as_view(), name='download-wheel-file'),
    # path('download/model/<int:pk>/', ModelFileDownloadView.as_view(), name='download-model-file'),
    # path('download/input/<int:pk>/', InputFileDownloadView.as_view(), name='download-input-file'),

]