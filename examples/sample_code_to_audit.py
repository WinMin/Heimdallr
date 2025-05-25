def vulnerable_function(user_input):
    # 一个简单的缓冲区溢出示例 (概念上的，Python 通常会处理)
    buffer = [None] * 10
    if len(user_input) > 10:
        print("输入过长!") # 应该在这里处理或截断，而不是继续
    
    # 模拟将输入复制到缓冲区
    for i in range(len(user_input)):
        if i < len(buffer): # 应该检查 i < len(buffer)
            buffer[i] = user_input[i]
        else:
            # 潜在的越界写入，如果上面的检查不当或逻辑复杂
            # 在 Python 中，这会是 IndexError，但在 C/C++ 中可能是溢出
            print(f"警告: 尝试写入索引 {i}，但缓冲区大小为 {len(buffer)}")
            # 真实场景下，这里可能没有显式错误，而是覆盖了其他内存
            pass # 简化示例

    data_to_process = "".join(filter(None, buffer))
    print(f"处理数据: {data_to_process}")
    return f"处理完成: {data_to_process}"

def another_function(x, y):
    # 另一个可能存在逻辑问题的函数
    if y == 0:
        # 除零错误风险
        # print("错误：y 不能为零")
        # return None # 应该有错误处理
        pass # 假设忘记了错误处理
    result = x / y
    return result

def check_user_permissions(user_id, action):
    # 模拟权限检查
    # 假设 user_id 1 是管理员，可以执行 "delete"
    # 其他用户不能执行 "delete"
    if action == "delete":
        if user_id == 1:
            return True # 管理员可以删除
        else:
            return False # 其他用户不能删除 (潜在的权限绕过，如果逻辑不严谨)
    return True # 其他操作默认允许

def main_vulnerable_example():
    user_data = "This is a very long string that will cause issues"
    vulnerable_function(user_data)
    
    short_data = "short"
    vulnerable_function(short_data)

    print(f"10 / 2 = {another_function(10, 2)}")
    # print(f"10 / 0 = {another_function(10, 0)}") # 会导致 ZeroDivisionError

    user_trying_delete = 2
    if check_user_permissions(user_trying_delete, "delete"):
        print(f"用户 {user_trying_delete} 成功执行删除操作 (不应发生)")
    else:
        print(f"用户 {user_trying_delete} 删除操作被阻止 (正确)")
    
    admin_trying_delete = 1
    if check_user_permissions(admin_trying_delete, "delete"):
        print(f"用户 {admin_trying_delete} 成功执行删除操作 (正确)")
    else:
        print(f"用户 {admin_trying_delete} 删除操作被阻止 (不应发生)")

if __name__ == "__main__":
    main_vulnerable_example() 