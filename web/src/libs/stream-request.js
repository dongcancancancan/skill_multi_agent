/**
 * SSE流式请求工具
 * 用于处理Server-Sent Events流式响应
 */

class StreamRequest {
  constructor() {
    this.controller = null;
    this.eventSource = null;
  }

  /**
   * 发起SSE流式请求
   * @param {string} url 请求URL
   * @param {Object} data 请求数据
   * @param {Object} callbacks 回调函数
   * @param {Function} callbacks.onMessage 消息回调
   * @param {Function} callbacks.onError 错误回调
   * @param {Function} callbacks.onInterrupt 中断回调
   * @param {Function} callbacks.onHeartbeat 心跳回调
   * @param {Function} callbacks.onEnd 结束回调
   * @param {Function} callbacks.onOpen 连接打开回调
   */
  async streamPost(url, data, callbacks = {}) {
    // 取消之前的请求
    if (this.controller) {
      this.controller.abort();
    }

    this.controller = new AbortController();
    const signal = this.controller.signal;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(data),
        signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (callbacks.onOpen) {
        callbacks.onOpen();
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          if (callbacks.onEnd) {
            callbacks.onEnd();
          }
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // 保留未完成的行

        let currentEventType = 'message'; // 默认事件类型
        
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventType = line.substring(7).trim();
            continue;
          }

          if (line.startsWith('data: ')) {
            const jsonData = line.substring(6).trim();
            
            if (jsonData) {
              try {
                const parsedData = JSON.parse(jsonData);
                console.log('Received SSE data: - stream-request.js:84', parsedData, currentEventType)
                
                // 根据事件类型调用对应的回调
                switch (currentEventType) {
                  case 'message':
                    if (callbacks.onMessage) {
                      callbacks.onMessage(parsedData);
                    }
                    break;
                  case 'error':
                    if (callbacks.onError) {
                      callbacks.onError(parsedData);
                    }
                    break;
                  case 'interrupt':
                    if (callbacks.onInterrupt) {
                      callbacks.onInterrupt(parsedData);
                    }
                    break;
                  case 'heartbeat':
                    if (callbacks.onHeartbeat) {
                      callbacks.onHeartbeat(parsedData);
                    }
                    break;
                  case 'end':
                    if (callbacks.onEnd) {
                      callbacks.onEnd(parsedData);
                    }
                    break;
                  case 'thinking':
                    // 思考过程事件，优先调用onThinking回调，如果没有则调用onMessage
                    if (callbacks.onThinking) {
                      callbacks.onThinking(parsedData);
                    } else if (callbacks.onMessage) {
                      callbacks.onMessage(parsedData);
                    }
                    break;
                  case 'trace_info':
                    // 知识库溯源信息事件
                    if (callbacks.onTraceInfo) {
                      callbacks.onTraceInfo(parsedData);
                    }
                    break;
                  case 'progress':
                    if (callbacks.onProgress) {
                        callbacks.onProgress(parsedData);
                    }
                    break;
                  case 'tip':
                    if (callbacks.onTip) {
                      callbacks.onTip(parsedData);
                    }
                    break;
                  default:
                    console.warn('Unknown event type: - stream-request.js:133', currentEventType, parsedData);
                    // 对于未知事件类型，也尝试调用onMessage回调
                    if (callbacks.onMessage && parsedData.content) {
                      callbacks.onMessage(parsedData);
                    }
                    break;
                }
              } catch (parseError) {
                console.error('Failed to parse SSE data: - stream-request.js:141', parseError, jsonData);
              }
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request was aborted - stream-request.js:149');
      } else {
        console.error('Stream request failed: - stream-request.js:151', error);
        if (callbacks.onError) {
          callbacks.onError({ message: error.message });
        }
      }
    } finally {
      this.controller = null;
    }
  }

  /**
   * 取消当前请求
   */
  abort() {
    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }
  }

  /**
   * 使用EventSource的SSE实现（备选方案）
   */
  streamWithEventSource(url, data, callbacks = {}) {
    // 取消之前的连接
    if (this.eventSource) {
      this.eventSource.close();
    }

    // 创建URL参数
    const params = new URLSearchParams();
    params.append('data', JSON.stringify(data));
    
    this.eventSource = new EventSource(`${url}?${params}`);

    this.eventSource.onopen = () => {
      if (callbacks.onOpen) {
        callbacks.onOpen();
      }
    };

    this.eventSource.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        if (callbacks.onMessage) {
          callbacks.onMessage(parsedData);
        }
      } catch (error) {
        console.error('Failed to parse SSE message: - stream-request.js:199', error, event.data);
      }
    };

    this.eventSource.addEventListener('error', (event) => {
      if (callbacks.onError) {
        callbacks.onError({ message: 'SSE connection error' });
      }
    });

    this.eventSource.addEventListener('interrupt', (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        if (callbacks.onInterrupt) {
          callbacks.onInterrupt(parsedData);
        }
      } catch (error) {
        console.error('Failed to parse interrupt event: - stream-request.js:216', error, event.data);
      }
    });

    this.eventSource.addEventListener('heartbeat', (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        if (callbacks.onHeartbeat) {
          callbacks.onHeartbeat(parsedData);
        }
      } catch (error) {
        console.error('Failed to parse heartbeat event: - stream-request.js:227', error, event.data);
      }
    });

    this.eventSource.addEventListener('end', (event) => {
      if (callbacks.onEnd) {
        callbacks.onEnd();
      }
      this.eventSource.close();
    });

    return this.eventSource;
  }

  /**
   * 关闭EventSource连接
   */
  closeEventSource() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

export default new StreamRequest();
