"""
API测试脚本
运行方式：python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("1. 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    return response.status_code == 200

def test_create_user():
    """测试创建用户"""
    print("\n2. 测试创建用户...")
    response = requests.post(f"{BASE_URL}/api/users", json={"username": "test_user"})
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    if response.status_code == 201:
        return response.json()["id"]
    return None

def test_get_user(user_id):
    """测试获取用户"""
    print(f"\n3. 测试获取用户 {user_id}...")
    response = requests.get(f"{BASE_URL}/api/users/{user_id}")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    return response.status_code == 200

def test_create_interview(user_id):
    """测试创建面试"""
    print("\n4. 测试创建面试...")
    data = {
        "user_id": user_id,
        "target_company": "字节跳动",
        "target_position": "后端工程师",
        "tech_stack": ["Python", "Redis", "MySQL"]
    }
    response = requests.post(f"{BASE_URL}/api/interviews", json=data)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    if response.status_code == 201:
        return response.json()["id"]
    return None

def test_start_interview(interview_id):
    """测试开始面试"""
    print(f"\n5. 测试开始面试 {interview_id}...")
    response = requests.post(f"{BASE_URL}/api/interviews/{interview_id}/start")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    return response.status_code == 200

def test_submit_answer(interview_id):
    """测试提交回答"""
    print(f"\n6. 测试提交回答...")
    data = {
        "user_answer": "Python是一种解释型、面向对象的高级编程语言。它的核心特性包括：动态类型、自动内存管理、丰富的标准库等。"
    }
    response = requests.post(f"{BASE_URL}/api/interviews/{interview_id}/answer", json=data)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    return response.status_code == 200

def test_get_state(interview_id):
    """测试获取面试状态"""
    print(f"\n7. 测试获取面试状态...")
    response = requests.get(f"{BASE_URL}/api/interviews/{interview_id}/state")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    return response.status_code == 200

def main():
    print("=" * 50)
    print("面试突破助手 - API测试")
    print("=" * 50)
    
    # 1. 健康检查
    if not test_health():
        print("❌ 服务未启动，请先运行 start_backend.bat")
        return
    
    # 2. 创建用户
    user_id = test_create_user()
    if not user_id:
        print("❌ 创建用户失败")
        return
    
    # 3. 获取用户
    test_get_user(user_id)
    
    # 4. 创建面试
    interview_id = test_create_interview(user_id)
    if not interview_id:
        print("❌ 创建面试失败")
        return
    
    # 5. 开始面试
    test_start_interview(interview_id)
    
    # 6. 提交回答
    test_submit_answer(interview_id)
    
    # 7. 获取状态
    test_get_state(interview_id)
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()
