<template>
  <div>
    <!-- 可拖动圆形 -->
    <div 
      class="drag-circle"
      :style="circleStyle"  @mousedown="startDrag">
      <div class="ai" >
          <div>AI</div>
      </div>
      <div class="chart" @click="newCreateChart"> 
        <Tooltip content="新建对话" placement="right">
          <Icon class="icon" size="32" type="md-chatboxes"  /> 
          <!-- <div>对话</div> -->
        </Tooltip>
      </div>
      <div class="chart" @click="knowledgeSearch"> 
        <Tooltip content="知识库检索" placement="right">
          <Icon class="icon" size="32" type="ios-paper"  /> 
          <!-- <div>知识库检索</div> -->
        </Tooltip>
      </div>
       <div class="chart" @click="indexSearch"> 
        <Tooltip content="指标查询" placement="right">
          <Icon class="icon" size="32" type="ios-search"  /> 
          <!-- <div>指标查询</div> -->
        </Tooltip>
      </div>
      <div class="history" @click="expend">
        <Tooltip content="打开对话历史" placement="right" >
            <Icon class="icon" size="32" type="md-time"  /> 
            <!-- <div>历史</div> -->
        </Tooltip>
      </div>
    </div>
    <!-- iView抽屉组件 -->
    <!-- <Drawer 
      v-model="drawerVisible"
      title="AI助手"
      width="80%">
      <aiMain></aiMain>
    </Drawer> -->
  </div>
</template>

<script>
import aiMain from '@/view/ai/aiMain.vue'
const divWidth = 80
const divHeight = 260
export default {
  components: { aiMain },
  data() {
    return {
      position: {
        x: window.innerWidth - divWidth - 50, // 直径60px + 左右内边距20px + 右边缘50px
        y: window.innerHeight - divHeight - 30  //下边距30px
      },
      isDragging: false,
      dragOffset: { x: 0, y: 0 },
      drawerVisible: false,
      mousedownTime: 0
    }
  },
  computed: {
    circleStyle() {
      return {
        left: `${this.position.x}px`,
        top: `${this.position.y}px`,
        width: `${divWidth}px`,
        height: `${divHeight}px`
      }
    }
  },
  methods: {
    indexSearch(event){
      event.preventDefault()
      event.stopPropagation()
      this.isDragging = false
      this.showDrawer('indexSearch')
    },
    knowledgeSearch(event){
      event.preventDefault()
      event.stopPropagation()
      this.isDragging = false
      this.showDrawer('knowledgeSearch')
    },
    newCreateChart(event){
      console.log(event,'event')
      event.preventDefault()
      event.stopPropagation()
      this.isDragging = false
      this.showDrawer('newCreateChart')
    },
    expend(event){
      event.preventDefault()
      event.stopPropagation()
      this.isDragging = false
      this.showDrawer('expendHistory')
    },
    // 拖拽逻辑
    startDrag(e) {
      this.mousedownTime = Date.now()
      this.isDragging = true
      this.dragOffset = {
        x: e.clientX - this.position.x,
        y: e.clientY - this.position.y
      }
      document.addEventListener('mousemove', this.onDrag)
      document.addEventListener('mouseup', this.stopDrag)
    },
    onDrag(e) {
      if (!this.isDragging) return
      
      // 边界限制计算
      const maxX = window.innerWidth - divWidth
      const maxY = window.innerHeight - divHeight
      
      this.position.x = Math.max(0, Math.min(e.clientX - this.dragOffset.x, maxX))
      this.position.y = Math.max(0, Math.min(e.clientY - this.dragOffset.y, maxY))
    },
    stopDrag() {
      this.isDragging = false
      document.removeEventListener('mousemove', this.onDrag)
      document.removeEventListener('mouseup', this.stopDrag)
    },
    // 抽屉控制
    showDrawer(openType) {
      if(Date.now() - this.mousedownTime > 150)  return
      this.$Modal.slide({
        title: 'AI助手', width: '80%', footerHide: true, closable: true
      }, {
        propsData: { openType },
        component: aiMain
      })
    }
  },
  beforeDestroy() {
    document.removeEventListener('mousemove', this.onDrag)
    document.removeEventListener('mouseup', this.stopDrag)
  }
}
</script>

<style scoped>
.ai{
  font-size: 28px;
  margin-top: 10px; 
  color: #42b883
}
.ai:hover{
   color: #2d8cf0

}
.chart{
  margin: 16px 0;
}
.chart:hover{
  color: #2d8cf0
}
.history:hover{
  color: #2d8cf0
}
.drag-circle {
  position: fixed;
  background-color: #fff;
  border: 1px solid #c5c5c5;
  border-radius: 16px;
  cursor: grab;
  /* display: flex;
  align-items: center; */
  /* justify-content: center; */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s;
  user-select: none;
  font-size: 16px;
  text-align: center;
  z-index: 999;
  padding: 0 10px;
}

.drag-circle:active {
  cursor: grabbing;
  /* transform: scale(1.05); */
}

.drag-circle span {
  color: white;
  font-size: 16px;
  cursor: pointer;
  pointer-events: auto; /* 确保文字可点击 */
}
</style>