import axios from '@/libs/api.request'
import qs from 'qs'

export default class BaseService {
  axios = axios
  /**
   * 获取结果数据
   * @param { Boolean } success 是否返回成功数据
   * @param {*} data 成功数据时为返回数据，失败时为错误消息
   */
  result = (success, data) => {
    return {
      code: success ? '0000' : '1000',
      data: success ? data : null,
      msg: success ? '操作成功' : data, // 国际化
      success: success
    }
  }
  /**
   * 直接返回成功数据
   */
  success = (data) => {
    let res = this.result(true, data)
    return new Promise(function (resolve, reject) {
      try {
        resolve(res)
      } catch (err) {
        reject(err)
      }
    })
  }
  /**
   * 返回错误信息
   */
  error = (message) => {
    let res = this.result(false, message)
    return new Promise(function (resolve, reject) {
      try {
        resolve(res)
      } catch (err) {
        reject(err)
      }
    })
  }
  /**
   * 通过 get 方式去请求数据
   */
  get = (url, params, headers = {}) => {
    return this.axios.request({
      url,
      method: 'get',
      params,
      transformRequest: [function (data) {
        data = qs.stringify(data)
        return data
      }],
      headers
    })
  }
  /**
   * 通过 post 方式去修改
   */
  post = (url, params, headers = {}) => {
    return this.axios.request({
      url,
      method: 'post',
      data: params,
      transformRequest: [function (data) {
        data = JSON.stringify(data)
        return data
      }],
      headers: {
        ...headers,
        'Content-Type': 'application/json;charset=UTF-8'
      }
    })
  }
  /**
   * 通过 put 方式去修改
   */
  put = (url, params, headers = {}) => {
    return this.axios.request({
      url,
      method: 'put',
      // method: 'post', // 如果不允许使用 put，可以改用此方式
      // params: { _method: 'put' }, // 如果不允许使用 put，可以改用此方式
      data: params,
      transformRequest: [function (data) {
        data = JSON.stringify(data)
        return data
      }],
      headers: {
        ...headers,
        'Content-Type': 'application/json;charset=UTF-8'
      }
    })
  }
  /**
   * 通过 delete 方式去删除数据
   */
  delete = (url, headers = {}) => {
    return this.axios.request({
      url,
      method: 'delete',
      // method: 'post' // 如果不允许使用 delete，可以改用此方式
      // params: { _method: 'delete' }
      headers
    })
  }
  /**
   * 上传文件
   * @param {*} url
   * @param {*} params
   * @param {*} method
   * @returns
   */
  upload_ = (url, params, method = 'post') => {
    let fileKey = 'file'
    for (const key in params) {
      if(params.hasOwnProperty(key)){
        const value = params[key]
        // 文件
        if (value instanceof File) {
          fileKey = key
          break
        }
        // 文件列表fileKey = key
        if (value instanceof Array && value.length > 0 && value[0] instanceof File) {
          fileKey = key
          break
        }
      }
    }
    let formData = new FormData()
    formData.append(fileKey, params[fileKey])
    delete params[fileKey]
    return this.axios.request({
      url,
      method,
      params,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
  /**
   * 下载文件
   */
  download = (url, params, method = 'get') => {
    return new Promise((resolve, reject) => {
      this.axios.request({
        url,
        method: method,
        params: params,
        responseType: 'blob'
      }).then(response => {
        if (!response) return
        this.downloadFile(response)
        resolve()
      }).catch(err => {
        reject(err)
      })
    })
  }
  downloadOwn = (url, params, method = 'get') => {
    return new Promise((resolve, reject) => {
      this.axios.request({
        url,
        method: method,
        data: params,
        transformRequest: [function (data) {
          data = JSON.stringify(data)
          return data
        }],
        headers: {
          'Content-Type': 'application/json;charset=UTF-8'
        },
        responseType: 'blob'
      }).then(response => {
        if (!response) return
        this.downloadFile(response)
        resolve()
      }).catch(err => {
        reject(err)
      })
    })
  }
  /**
   * 处理下载的文件
   */
  downloadFile = (response) => {
    let headers = response['headers']
    let filename = headers['content-disposition']
    if (filename.indexOf('attachment;filename=') > -1) {
      filename = filename.substr('attachment;filename='.length)
      filename = decodeURI(filename)
    }
    let data = response['data']
    let url = window.URL.createObjectURL(new Blob([data]))
    let link = document.createElement('a')
    link.style.display = 'none'
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
  }
}
