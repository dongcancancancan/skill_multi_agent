export default {
  /**
   * @description token在Cookie中存储的天数，默认1天
   */
  cookieExpires: 1,
  /**
   * @description 是否使用国际化，默认为false
   *              如果不使用，则需要在路由中给需要在菜单中展示的路由设置meta: {title: 'xxx'}
   *              用来在菜单中显示文字
   */
  useI18n: false,
  /**
   * @description api请求基础路径
   */
  baseUrl: {
    dev: '/api', // 'https://www.easy-mock.com/mock/5add9213ce4d0e69998a6f51/iview-admin/',
    pro: '/api'
  },
  /**
   * @description 默认打开的首页的路由name值，默认为home
   */
  homeName: 'home',
  /**
   *  @description 默认打开的登录页的路由name值，默认为login
   */
  loginName: 'login',
  /**
   * 授权路由的名称
   */
  authName: 'authorize',
  /**
   * 授权KEY的名称
   */
  authKey: 'authorization',
  /**
   * 需要跳转到的界面的url地址
   */
  redirectKey: 'redirect',
  /**
   * @description 需要加载的插件
   */
  plugin: {
    // 'error-store': {
    //   showInHeader: true, // 设为false后不会在顶部显示错误日志徽标
    //   developmentOff: false // 设为true后在开发环境不会收集错误信息，方便开发中排查错误
    // }
    'modal-open': {
      iView: null
    },
    // 自动注册自定的公共组件
    'custom-component': ''
  },
  /**
   * @description 工程中的模块，有的地方需要通过此方式区加载 js 文件，比如 service 中
   * key: 简写
   * value: 全写
   */
  module: {
    'ai': 'aiMgr', // ai助手
    'manage': 'manageMgr' // 企业管理
  }
}
