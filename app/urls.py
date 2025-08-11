from django.urls import path
from .views import (
    TriggerWorkFlowView,
    WorkFlowView,
    WorkflowListView,
    ModelPerformanceView,
    ModelPerformanceListView,
    WorkflowDetailView, 
    WorkflowRunListView,
    WorkflowRunView,
    WorkflowPinView
)

urlpatterns = [
    path('workflow/create/', WorkFlowView.as_view(), name='create-workflow'),
    path('workflow/execute/<int:pk>/', TriggerWorkFlowView.as_view(), name='trigger-workflow'),
    path('workflow/', WorkflowListView.as_view(), name='all_workflows'),
    path('workflow/<int:pk>/', WorkflowDetailView.as_view(), name='workflow'),
    path('workflow/run/', WorkflowRunListView.as_view(), name='all_workflow_runs'),
    path('workflow/run/<int:pk>/', WorkflowRunView.as_view(), name='workflow_run'),
    path('modelperformance/<int:pk>/', ModelPerformanceView.as_view(), name='model_performance'),
    path('modelperformance/', ModelPerformanceListView.as_view(), name='model_performance_list'),
    path('pinworkflow/<int:pk>/', WorkflowPinView.as_view(), name='pin_workflow'),
]
