import BaseService from '@/api/service/BaseService'
import streamRequest from '@/libs/stream-request'

// 首页接口
class deepSeekService extends BaseService {

  // 根据名称获取应用
  start = (param) => {
    return this.post('/ai/start', param)
  }
  // 根据名称获取应用
  getByName = (param) => {
    return this.get('/application/getByName', param)
  }
  // 新建会话记录
  addFlow = (param) => {
    return this.post('/applicationChat/addFlow', param)
  }
  // 保存最终对话记录
  addFlowQa = (param) => {
    return this.post('/applicationChat/addFlowQa', param)
  }
  // 从知识库获取Prompt和知识检索结果
  qaPromptAndDocs = (param) => {
    return this.post('/applicationChat/qaPromptAndDocs', param)
  }
  // 通过大模型进行问答，确定知识问答的答案
  chat = (param) => {
    return this.post('/agents/main_graph', param)
  }
  knowledge = (param) => {
    return this.post('/ai/knowledge', param)
  }
  text2sql = (param) => {
    return this.post('/ai/text2sql', param)
  }
  // 多Agent系统主图接口
  mainGraph = (param) => {
    return this.post('/agents/main_graph', param)
  }

  // 多Agent系统主图接口 - 流式版本
  mainGraphStream = (param, callbacks = {}) => {
    const baseUrl = process.env.VUE_APP_API_BASE_URL || '/api';
    const url = `${baseUrl}/agents/main_graph`;
    console.log(url)
    return streamRequest.streamPost(url, param, callbacks);
  }

  // 取消流式请求
  cancelMainGraphStream = () => {
    streamRequest.abort();
  }
  // 恢复中断的会话
  restoreSession = (param) => {
    return this.post('/agents/restore_session', param)
  }
  // 通过大模型进行问答，确定知识问答的答案
  qa = (param) => {
    return this.post('/applicationChat/qa', param)
  }
  // 点击左侧历史 查看当前问答详情
  pageFlowQa = (param) => {
    return this.get('/applicationChat/pageFlowQa', param)
  }
  // 删除某次查询记录
  deleteFlow = (id) => {
    return this.delete(`/applicationChat/deleteFlow?flowId=${id}`)
  }
  // 根据窗口编号删除会话记录
  deleteFlowByWindowNo = (windowNo) => {
    return this.delete(`/applicationChat/deleteFlowByWindowNo?windowNo=${windowNo}`)
  }
  // 根据窗口编号删除会话记录（新接口）
  delete_session_by_windows_no = (windowsNo) => {
    return this.delete(`/applicationChat/deleteSessionByWindowsNo?windowsNo=${windowsNo}`)
  }
  // 
  getFlowHistory = (param, headers = {}) => {
    return this.get('/applicationChat/getFlowHistory', param, headers)
  }

  // 验证token有效性
  verifyToken = (headers = {}) => {
    return this.get('/auth/verify', null, headers)
  }



}
export default deepSeekService
