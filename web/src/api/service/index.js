import config from '@/config'

/** 系统管理 START */
import BaseService from './BaseService'
/** 建模工具 END */
const { module: configModule } = config
const service = {
  base: new BaseService() // 基础服务提供普通的 get,put,post,delete 等请求方法
}
Object.keys(configModule).forEach((name) => {
  const value = configModule[name] // 对应的 service
  let map = require(`./${value}`).default || {} // 动态加载 service 列表
  service[name] = map
})
export default service
