import axios from 'axios'
// import store from '@/store'
// import router from '@/router'
// import config from '@/config'
// import { sessionRemove } from '@/libs/tools'
// import { AuthKey } from '@/libs/enum'
import { Modal, Notice } from 'view-design'

// const { loginName, homeName } = config
// import { Spin } from 'view-design'
// const addErrorLog = errorInfo => {
//   const { statusText, status, request: { responseURL } } = errorInfo
//   let info = {
//     type: 'ajax',
//     code: status,
//     mes: statusText,
//     url: responseURL
//   }
//   // if (!responseURL.includes('save_error_logger')) store.dispatch('addErrorLog', info)
// }

class HttpRequest {
  constructor (baseUrl = baseURL) {
    this.baseUrl = baseUrl
    this.queue = {}
  }
  getInsideConfig () {
    const config = {
      baseURL: this.baseUrl,
      responseType: 'json',
      headers: {
      }
    }
    return config
  }
  destroy (url) {
    delete this.queue[url]
    if (!Object.keys(this.queue).length) {
      // Spin.hide()
    }
  }
  interceptors (instance, url) {
    // 请求拦截
    instance.interceptors.request.use(config => {
      // 添加全局的loading...
      if (!Object.keys(this.queue).length) {
        // Spin.show() // 不建议开启，因为界面不友好
      }
      this.queue[url] = true
      return config
    }, error => {
      return Promise.reject(error)
    })
    // 响应拦截
    instance.interceptors.response.use(res => {
      this.destroy(url)
      const { data, status } = res
      // return { data, status }
      let headers = res['headers']
      if ('content-disposition' in headers) {
        if ((headers['content-type'] || '').indexOf('application/json') === -1) return res // 文件下载直接返回 response
      }
      return data // 其他请求返回 data
    }, error => { // 请求出现错误
      this.destroy(url)
      let data = error.response.data
      if (error.request.responseType === 'blob') { // download 请求报错，需要将返回的内容转换为 json
        let reader = new FileReader()
        reader.readAsText(data, 'utf-8')
        reader.onload = () => {
          data = JSON.parse(reader.result)
        }
      }
      if (!data) { // data 为空，则表示不是从后台返回的数据
        data = {
          hideNotice: () => {}
        }
        /*
        let status = error.response.status // 跳转到对应的页面
        router.push({
          name: 'error_' + status
        })
        */
        return Promise.reject(data)
      }
      let errCode = data.code
      let isHideNotice = false // 是否隐藏统一错误消息
      /** 无效 token 直接进入 login 页面 */
      if (errCode === '3006') {
        isHideNotice = true
        // sessionRemove(AuthKey.TOKEN_KEY)
        // store.commit('setToken', '')
        Modal.remove() // 先关闭所有的弹出框
        // router.push({
        //   name: loginName
        // })
      } else if (errCode === '3007') { // session 失效
        isHideNotice = true
        Modal.remove() // 先关闭所有的弹出框
        setTimeout(() => {
          Modal.error({
            title: '错误信息', // 需国际化
            content: '登录过期，请重新登录！', // 需国际化
            onOk: () => {
              // sessionRemove(AuthKey.TOKEN_KEY)
              // store.commit('setToken', '')
              // router.push({
              //   name: loginName
              // })
            }
          })
        }, 200)
      } else if (errCode === '3008') { // 没有操作权限
        isHideNotice = true
        setTimeout(() => {
          let url_ = error.config.url
          let method_ = error.config.method
          let params = error.config.params
          if (params) {
            let _method = params._method
            if (_method) method_ = _method
          }
          Notice.error({
            title: '错误信息', // 需国际化
            desc: `请求地址:${url_}，请求方法:${method_}，没有权限请联系管理员配置url权限！`,
            duration: 10
          })
        }, 100)
      }
      let hideNotice = () => { isHideNotice = true } // 在请求的 catch 中调用该方法，会将系统消息隐藏掉
      setTimeout(() => {
        if (isHideNotice) return
        let msg = ''
        if (typeof data === 'string') msg = data
        else msg = ((data.msg || data.message) || data.error) || ''
        if (msg === '当前用户没有系统信息') {
          msg = "没有系统权限，不能查看该模型"
          // router.push({
          //   name: homeName
          // })
        }
        // 只有当消息不为空时才显示错误消息，完全移除默认错误消息
        if (msg) {
          Notice.error({
            title: '错误信息', // 需国际化
            desc: msg // 国际化
          })
        }
      }, 200)
      // addErrorLog(error.response)
      data.hideNotice = hideNotice
      return Promise.reject(data)
    })
  }
  request (options, instance = axios.create()) {
    // const instance = axios.create()
    options = Object.assign(this.getInsideConfig(), options)
    // 设置请求头
    let headers = options.headers
    if (!('Content-Type' in headers)) {
      headers['Content-Type'] = 'application/x-www-form-urlencoded'
    }
    if (!('X-Requested-With' in headers)) {
      headers['X-Requested-With'] = 'XMLHttpRequest'
    }
    if (!('X-URL-PATH' in headers)) {
      headers['X-URL-PATH'] = location.pathname
    }
    if (!('Accept' in headers)) {
      headers['Accept'] = 'application/json'
    }
    // headers['token'] = store.getters.getToken() // 获取 vuex 中的 token，每一次请求都会在 header 中传递 token
    this.interceptors(instance, options.url)
    return instance(options)
  }
}
export default HttpRequest
