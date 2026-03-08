import requests
import json
import time

# 使用root用户登录
login_url = 'http://localhost:8888/api/auth/login'
login_data = {'username': 'root', 'password': 'root'}

print('登录获取token...')
login_response = requests.post(login_url, json=login_data)
token = login_response.json().get('token', '')

# 用户提供的会触发中断的问题
question = '查询项目名称为"太阳能光伏发电项目"的绿色准入情况，资金用途为"可再生能源项目融资"。'

print(f'\n测试问题: {question}')
print('这个问题应该会触发中断...')

url = 'http://localhost:8888/api/agents/main_graph'
headers = {'Content-Type': 'application/json'}

data = {
    'input': question,
    'token': token,
    'session_id': 'test-session-' + str(int(time.time())),
    'metadata': {
        'user_id': '',
        'company': '',
        'session_id': 'test-session-' + str(int(time.time())),
        'windowNo': 'test-window-' + str(int(time.time()))
    }
}

try:
    response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
    
    if response.status_code == 200:
        print(f'SSE连接成功! 状态码: {response.status_code}')
        print(f'响应头: {dict(response.headers)}')
        
        has_interrupt = False
        chunk_count = 0
        interrupt_data = None
        
        print('\n开始接收SSE流式数据...')
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    chunk_count += 1
                    json_data = line[6:]
                    
                    try:
                        parsed = json.loads(json_data)
                        if isinstance(parsed, dict):
                            event_type = parsed.get('event', '')
                            
                            if event_type == 'interrupt':
                                print(f'\n=== 发现中断事件! ===')
                                print(f'中断数据: {json.dumps(parsed, ensure_ascii=False, indent=2)}')
                                has_interrupt = True
                                interrupt_data = parsed
                                break
                            else:
                                # 显示其他事件
                                content = parsed.get('content', '')
                                if isinstance(content, dict):
                                    content_type = content.get('type', 'text')
                                    print(f'[{chunk_count}] 事件: {event_type}, 类型: {content_type}')
                                else:
                                    print(f'[{chunk_count}] 事件: {event_type}, 内容长度: {len(str(content))}')
                    except json.JSONDecodeError:
                        print(f'[{chunk_count}] 非JSON数据: {json_data[:50]}...')
                    except Exception as e:
                        print(f'[{chunk_count}] 解析错误: {e}')
                    
                    if chunk_count >= 30:  # 最多检查30个chunk
                        break
        
        if has_interrupt:
            print(f'\n✓ 成功触发中断!')
            print(f'  总chunk数: {chunk_count}')
            if interrupt_data and 'data' in interrupt_data and 'interrupt_data' in interrupt_data['data']:
                print(f'  中断类型: {interrupt_data["data"]["interrupt_data"].get("type", "unknown")}')
            else:
                print(f'  中断类型: 未知')
        else:
            print(f'\n✗ 没有触发中断')
            print(f'  总chunk数: {chunk_count}')
            print(f'  可能的原因:')
            print(f'  1. 问题没有触发中断逻辑')
            print(f'  2. 中断逻辑有bug')
            print(f'  3. Nginx配置可能仍然有问题')
            
    else:
        print(f'SSE请求失败: {response.status_code}')
        print(f'响应: {response.text}')
        
except Exception as e:
    print(f'请求异常: {e}')
    import traceback
    traceback.print_exc()
