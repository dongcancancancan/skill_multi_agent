<template>
  <Modal
    v-model="visible"
    :title="title"
    :width="width"
    :loading="loading"
    @on-ok="handleOk"
    @on-cancel="handleCancel"
  >
    <div v-if="step === 1">
      <p>{{ firstContent }}</p>
    </div>
    <div v-if="step === 2">
      <p>{{ secondContent }}</p>
      <Alert v-if="warningText" type="warning" show-icon>
        {{ warningText }}
      </Alert>
    </div>
  </Modal>
</template>

<script>
export default {
  name: 'DoubleConfirm',
  props: {
    // 基本配置
    title: {
      type: String,
      default: '确认提示'
    },
    width: {
      type: Number,
      default: 400
    },
    // 第一步内容
    firstContent: {
      type: String,
      default: '确定要执行此操作吗？'
    },
    // 第二步内容
    secondContent: {
      type: String,
      default: '请再次确认，此操作不可逆！'
    },
    warningText: {
      type: String,
      default: ''
    },
    // 确认按钮文本
    okText: {
      type: Array,
      default: () => ['第一步确认', '最终确认']
    },
    cancelText: {
      type: String,
      default: '取消'
    }
  },
  data() {
    return {
      visible: false,
      step: 1,
      loading: true
    };
  },
  methods: {
    show() {
      this.visible = true;
      this.step = 1;
    },
    
    handleOk() {
      if (this.step === 1) {
        // 第一步确认，进入第二步
        this.step = 2;
        // 阻止Modal关闭
        this.loading = false;
        this.$nextTick(() => {
          this.loading = true;
        });
      } else {
        // 第二步确认，执行操作
        this.$emit('on-confirm');
        this.visible = false;
      }
    },
    
    handleCancel() {
      this.visible = false;
      this.$emit('on-cancel');
    }
  },
  watch: {
    step(val) {
      // 更新标题
      this.$emit('update:title', val === 1 ? '第一次确认' : '最终确认');
    }
  }
};
</script>