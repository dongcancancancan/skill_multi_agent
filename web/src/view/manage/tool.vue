<template>
  <div class="page-container">
      <div class="left-panel btns">
      <div
        class="left-item"
        :class="{ active: activePath === '/' }"
        @click="newCreateChart"
      >
        <Icon class="icon" size="18" type="md-chatboxes" />
        <span>新建对话</span>
      </div>
      <div
        class="left-item"
        :class="{ active: activePath === '/list' }"
        @click="gotoList"
      >
        <Icon class="icon" size="18" type="md-book" />
        <span>访前一页纸</span>
      </div>
      <div
        class="left-item"
        :class="{ active: activePath === '/tool' }"
      >
        <Icon class="icon" size="18" type="md-chatbubbles" />
        <span>数智洞察</span>
      </div>
      <div class="left-item" @click="newCreateChart" title="刷新历史">
        <Icon class="icon" size="18" type="md-time" />
        <span>历史会话</span>
      </div>
    </div>
    <iframe ref="chatIframe" id="chatIframe" class="chat-iframe" src="https://dg2.miscity.cn:20081/webapp/chat/external" style="width: 100%; height: 100vh; border: none;" />
  </div>
</template>
<script>
export default {
  name: "ToolView",
  data() {
    return {};
  },
  computed: {
    activePath() {
      return this.$route.path;
    }
  },
    methods: {
      // 获取 iframe 内部指定选择器的 class 列表（同域可用）
      getIframeClasses(selector) {
        const iframe = this.$refs.chatIframe;
        if (!iframe) return [];
        try {
          const doc = iframe.contentWindow && iframe.contentWindow.document;
          if (!doc) return [];
          const el = doc.querySelector(selector);
          return el ? Array.from(el.classList || []) : [];
        } catch (e) {
          // 跨域时无法访问 iframe 内容
          console.warn("无法访问 iframe 内容，可能是跨域限制", e);
          return [];
        }
      },
      newCreateChart () {
        this.$router.push({ path: '/' });
      },
      gotoList () {
        this.$router.push({ path: '/list' });
      },
    },
  mounted() {
    this.getIframeClasses('.agentList')
  }
};
</script>
<style scoped lang="less">
.page-container {
  position: relative;
  display: flex;
}
.left-panel {
  width: 238px;
  background-color: #f5f5f5;
  border-right: 1px solid #ddd;
  // position: absolute;
  // left: 0;
  // top: 0;
  height: 100vh;
  // z-index: 1;
}
.chat-iframe {
  width: calc(100% - 238px);
}
.left-panel .icon {
  cursor: pointer;
  margin: 10px;
}
.left-panel .icon:hover {
  color: #2d8cf0;
}
.left-panel .left-item {
  cursor: pointer;
  text-align: left;
}
.left-panel .left-item:hover {
  color: #2d8cf0;
}
.left-panel .left-item.active {
  color: #2d8cf0;
  font-weight: 600;
}
</style>