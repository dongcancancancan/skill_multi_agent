// 前端会话管理示例代码
// 这个文件展示了如何在前端集成会话历史功能

class SessionManager {
  constructor() {
    this.currentSessionId = null;
    this.baseUrl = 'http://localhost:8001/api/agents';
  }

  // 获取所有会话列表
  async getAllSessions() {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/list`);
      const data = await response.json();
      
      if (data.status === 'success') {
        return data.sessions;
      } else {
        console.error('获取会话列表失败:', data);
        return [];
      }
    } catch (error) {
      console.error('获取会话列表错误:', error);
      return [];
    }
  }

  // 创建新会话
  async createNewSession() {
    try {
      const response = await fetch(`${this.baseUrl}/new_session`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.currentSessionId = data.session_id;
        console.log('新会话创建成功:', data.session_id);
        return data.session_id;
      } else {
        console.error('创建新会话失败:', data);
        return null;
      }
    } catch (error) {
      console.error('创建新会话错误:', error);
      return null;
    }
  }

  // 获取特定会话的历史记录
  async getSessionHistory(sessionId) {
    try {
      const response = await fetch(`${this.baseUrl}/${sessionId}/history`);
      const data = await response.json();
      
      if (data.status === 'success') {
        return data.messages;
      } else {
        console.error('获取会话历史失败:', data);
        return [];
      }
    } catch (error) {
      console.error('获取会话历史错误:', error);
      return [];
    }
  }

  // 保存消息到当前会话
  async saveMessage(message) {
    if (!this.currentSessionId) {
      console.error('没有当前会话，请先创建或选择会话');
      return false;
    }

    try {
      const response = await fetch(`${this.baseUrl}/${this.currentSessionId}/save_message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(message)
      });
      
      const data = await response.json();
      return data.status === 'success';
    } catch (error) {
      console.error('保存消息错误:', error);
      return false;
    }
  }

  // 切换到指定会话
  async switchToSession(sessionId) {
    const history = await this.getSessionHistory(sessionId);
    if (history.length > 0) {
      this.currentSessionId = sessionId;
      console.log(`已切换到会话: ${sessionId}`);
      return history;
    } else {
      console.error('会话不存在或为空');
      return null;
    }
  }

  // 示例：完整的使用流程
  async demoUsage() {
    console.log('=== 会话管理功能演示 ===');
    
    // 1. 获取所有历史会话
    console.log('1. 获取所有历史会话...');
    const sessions = await this.getAllSessions();
    console.log('可用会话:', sessions);
    
    // 2. 创建新会话
    console.log('2. 创建新会话...');
    const newSessionId = await this.createNewSession();
    
    if (newSessionId) {
      // 3. 保存测试消息
      console.log('3. 保存测试消息...');
      const testMessage = {
        role: 'user',
        content: '这是一个测试消息',
        timestamp: new Date().toISOString(),
        agent_type: 'user_input'
      };
      
      const saveSuccess = await this.saveMessage(testMessage);
      console.log('消息保存结果:', saveSuccess ? '成功' : '失败');
      
      // 4. 查看新会话的历史
      console.log('4. 查看新会话历史...');
      const newHistory = await this.getSessionHistory(newSessionId);
      console.log('新会话历史:', newHistory);
      
      // 5. 再次获取所有会话（应该包含新会话）
      console.log('5. 再次获取所有会话...');
      const updatedSessions = await this.getAllSessions();
      console.log('更新后的会话列表:', updatedSessions);
    }
  }
}

// 使用示例
const sessionManager = new SessionManager();

// 在Vue组件中的使用示例
/*
export default {
  data() {
    return {
      sessions: [],
      currentSession: null,
      messages: []
    }
  },
  methods: {
    async loadSessions() {
      this.sessions = await sessionManager.getAllSessions();
    },
    async createNewSession() {
      const newSessionId = await sessionManager.createNewSession();
      if (newSessionId) {
        this.currentSession = newSessionId;
        this.messages = []; // 清空当前对话内容
        await this.loadSessions(); // 重新加载会话列表
      }
    },
    async switchSession(sessionId) {
      const history = await sessionManager.switchToSession(sessionId);
      if (history) {
        this.currentSession = sessionId;
        this.messages = history;
      }
    },
    async sendMessage(content) {
      const message = {
        role: 'user',
        content: content,
        timestamp: new Date().toISOString(),
        agent_type: 'user_input'
      };
      
      const success = await sessionManager.saveMessage(message);
      if (success) {
        this.messages.push(message);
        // 这里可以添加获取AI回复的逻辑
      }
    }
  },
  mounted() {
    this.loadSessions();
  }
}
*/
