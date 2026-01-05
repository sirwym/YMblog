from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    # 工具箱首页
    path('', views.tool_dashboard, name='dashboard'),

    # === 工具 1: C++ 在线运行 ===
    # 注意：这里的 name='cpp_runner' 配合 app_name，
    # 在后台添加工具时，url_name 字段应填写 "tools:cpp_runner"
    path('cpp/', views.cpp_runner, name='cpp_runner'),
    path('api/run-cpp/', views.run_cpp_api, name='run_cpp_api'),
    path('api/sys-info/', views.get_sys_info, name='sys_info'),
    path('api/unlock/', views.api_unlock_tool, name='api_unlock'),
]