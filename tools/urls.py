from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    # 工具箱首页
    path('', views.tool_dashboard, name='dashboard'),

    # === 工具 1: C++ 在线运行 ===
    path('cpp/', views.cpp_runner, name='cpp_runner'),
    path('api/run-cpp/', views.run_cpp_api, name='run_cpp_api'),
    path('api/sys-info/', views.get_sys_info, name='sys_info'),
    path('api/unlock/', views.api_unlock_tool, name='api_unlock'),

    # === 工具 2: AI测试数据在线生成 ===
    path('testcase-generator/', views.testcase_generator, name='testcase_generator'),
    path('api-ai-generate/', views.api_ai_generate, name='api_ai_generate'),
    path('api-run-testgen/', views.api_run_testgen, name='api_run_testgen'),
    path('api/download-zip/<str:zip_id>/', views.download_testcase_zip, name='download_zip'),
    path('api/check-task/', views.api_check_task, name='api_check_task'),

]