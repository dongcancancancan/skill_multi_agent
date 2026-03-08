import Vue from 'vue'
import App from './App.vue'
import ViewUI from 'view-design';
import 'view-design/dist/styles/iview.css';
import service from '@/api/service'
import router from './router'
import VueHtml2pdf from 'vue-html2pdf'

Vue.use(ViewUI);

Vue.config.productionTip = false

/**
 * @description 全局注册数据请求服务
 */
Vue.prototype.$service = service
Vue.component('vue-html2pdf', VueHtml2pdf)

new Vue({
  router,
  render: h => h(App),
}).$mount('#app')
