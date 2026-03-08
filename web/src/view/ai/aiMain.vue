<style lang="less" scoped>
@import "styles/aiMain.less";

.group-title {
  margin: 12px 0 4px 12px;
  font-size: 12px;
  color: #999;
  font-weight: normal;
  line-height: 1.5;
}

.history-group {
  margin-bottom: 8px;
}

// 通用禁用状态样式
.interrupt-action-button[data-disabled="true"] {
  cursor: not-allowed !important;
  pointer-events: none;
  opacity: 0.6;
}

// 审批操作的禁用样式
.grey-disabled-action {
  color: #999 !important;
  background: #f5f5f5 !important;
  border: 1px solid #e8e8e8 !important;
}

// 可点击公司名称的禁用样式
.disabled-clickable-company {
  color: #999 !important;
  background: #f5f5f5 !important;
  border: 1px solid #e8e8e8 !important;
  text-decoration: none !important;
}

// 资金用途选择的禁用样式
.disabled-fund-usage-selection {
  color: #999 !important;
  background: #f5f5f5 !important;
  border: 1px solid #e8e8e8 !important;
  text-decoration: none !important;
}
</style>

<style lang="less">
/* --- Progress 呼吸灯与流光字特效 --- */

/* 容器样式：基础样式 */
.progress-container {
  margin: 8px 0;
  padding: 10px 12px;
  background-color: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  display: flex;
  align-items: center;
  font-size: 14px;
  transition: all 0.3s;
  width: fit-content;
  max-width: 100%;
}

/* 容器激活状态：无蓝色边框，仅保留微弱阴影 */
.progress-container.active-breathing {
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.08); 
}

/* 文字基础样式 (静止状态) */
.progress-text-gradient {
  margin-left: 8px;
  font-weight: 500;
  color: #333333; 
}

/* 文字激活状态：流光呼吸效果 */
.active-breathing .progress-text-gradient {
  background: linear-gradient(90deg, #999999 0%, #000000 50%, #999999 100%);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  animation: text-flow 2s linear infinite;
}

@keyframes text-flow {
  0% { background-position: 200% 0; }
  100% { background-position: 0% 0; }
}

/* --- 思考过程 UI (Industry-Leading Aesthetic) --- */

/* 外层包装：防止抖动 */
.thinking-wrapper {
  width: 100%;
  margin-bottom: 12px;
  border-radius: 8px;
  background-color: #f7f8fa; /* 极浅灰背景 */
  border: 1px solid #ebedf0; /* 柔和边框 */
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 头部样式 */
.thinking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  background: #f7f8fa;
  user-select: none;
  transition: background-color 0.2s;
}
.thinking-header:hover {
  background-color: #f0f2f5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
}

/* 图标容器 */
.icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
}

.spin-icon {
  font-size: 14px;
  color: #1890ff;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.static-icon {
  font-size: 14px;
  opacity: 0.8;
}

/* 箭头动画 */
.arrow-icon {
  font-size: 14px;
  color: #909399;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.rotate-arrow {
  transform: rotate(180deg);
}

/* 内容区域：折叠动画核心 */
.thinking-body {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  background-color: #ffffff;
  border-top: 1px solid transparent;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); /* 丝滑过渡 */
}

/* 展开状态 */
.body-expanded {
  max-height: 2000px; /* 设置足够大的高度以容纳内容 */
  opacity: 1;
  border-top-color: #ebedf0;
}

.thinking-content-inner {
  padding: 12px 16px;
  display: flex;
  gap: 12px;
}

.quote-line {
  width: 2px;
  background-color: #e0e3e9;
  border-radius: 2px;
  flex-shrink: 0;
}

/* 思考文本排版 */
.thinking-text {
  flex: 1;
  font-size: 13px;
  line-height: 1.6;
  color: #555666;
  word-break: break-word;
}
.thinking-text p { margin-bottom: 8px; }
.thinking-text p:last-child { margin-bottom: 0; }
.thinking-text pre, .thinking-text code {
  background-color: #f2f4f7;
  border-radius: 4px;
  font-size: 12px;
  color: #444;
}

/* 流式传输时的头部文字呼吸动效 */
.is-streaming .header-title {
  background: linear-gradient(90deg, #606266 0%, #1890ff 50%, #606266 100%);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  animation: text-shimmer 2s infinite linear;
}
@keyframes text-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}
</style>

<template>
  <div class="aiMain">
    <div class="split-pane-left" :style="{ width: splitLeftWidth }">
      <div class="btns">
        <div class="left-item" @click="newCreateChart">
          <Icon class="icon" size="18" type="md-chatboxes" />
          <span>新建对话</span>
        </div>
        <div class="left-item" @click="gotoListPage">
          <Icon class="icon" size="18" type="md-book" />
          <span>访前一页纸</span>
        </div>
        <div class="left-item" @click="gotoAnswerPage">
          <Icon class="icon" size="18" type="md-chatbubbles" />
          <span>数智洞察</span>
        </div>
        <div class="left-item" @click="onRefreshIconClick" title="刷新历史">
          <Icon class="icon" size="18" type="md-time" />
          <span>历史会话</span>
        </div>
      </div>

      <div
        v-if="
          (groupFlowHistory && groupFlowHistory.length > 0) ||
          (flowHistory &&
            flowHistory.length > 0 &&
            flowHistory[0].list &&
            flowHistory[0].list.length > 0)
        "
        style="margin-top: 10px"
      >
        <div class="historyList" style="max-height: 400px; overflow-y: auto">
          <template v-if="groupFlowHistory && groupFlowHistory.length > 0">
            <div
              v-for="group in groupFlowHistory"
              :key="group.title"
              class="history-group"
            >
              <h3 class="group-title">{{ group.title }}</h3>
              <div
                class="historyList-item"
                v-for="item in group.list"
                :key="item.windows_no || item.id"
                :class="{ 'active-state': historyListItemIndex == item.id }"
                @click="historyItemClick(item)"
                @mouseenter="hoverItem = item.id"
                @mouseleave="hoverItem = null"
              >
                <div class="query-text">
                  {{
                    item.query.length > 10
                      ? item.query.substring(0, 10) + "..."
                      : item.query
                  }}
                </div>
                <div class="history-actions" v-show="hoverItem === item.id">
                  <div class="dots-menu" @click.stop="toggleMenu(item.id)">
                    <span>⋮</span>
                  </div>
                  <div class="dropdown-menu" v-if="activeMenu === item.id">
                    <div @click.stop="deleteFlow(item)">删除</div>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <template
            v-else-if="
              flowHistory &&
              flowHistory.length > 0 &&
              flowHistory[0].list &&
              flowHistory[0].list.length > 0
            "
          >
            <div
              class="historyList-item"
              v-for="item in flowHistory[0].list"
              :key="item.windows_no || item.id"
              :class="{ 'active-state': historyListItemIndex == item.id }"
              @click="historyItemClick(item)"
            >
              <div
                class="flex-space-between"
                style="align-items: center; padding: 4px 0"
              >
                <div
                  style="
                    flex: 1;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                  "
                >
                  {{ item.title }}
                </div>
                <div>
                  <Icon
                    @click.stop="deleteFlow(item)"
                    class="delIcon"
                    type="md-trash"
                  />
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div
        v-else
        class="empty-history"
        style="margin-top: 10px; text-align: center; color: #999"
      >
        暂无历史记录
      </div>
    </div>

    <div
      :class="[
        'main',
        'split-pane-right',
        chatList.length == 0 ? 'main-centered' : '',
      ]"
      :style="{ width: `calc(100% - ${splitLeftWidth})` }"
      v-cloak
    >
      <div class="title" v-if="chatList.length == 0">
        <p style="fontSize: 30px; fontWeight: 600">
          你好，我是XX银行对公金融助手
        </p>
        <p style="fontsize: 12px; margin: 8px 0 12px">
          想知道客户潜力？需要政策支持？我来帮您解读文档、生成方案，让您的蓝绿色金融业务，每一步都稳健有力。
        </p>
      </div>
      <div class="qsAnswer" v-if="chatList.length > 0" ref="qsAnswer">
        <div v-for="(item, index) in chatList" :key="index">
          <div class="qs" v-if="item.length > 0 && item[0] && item[0].trim()">
            <div
              class="qs-content"
              v-if="item.length > 0 && item[0] && item[0].trim()"
            >
              {{ item[0] }}
            </div>
            <Avatar
              style="
                margin-left: 12px;
                background-color: #87d068;
                flex-shrink: 0;
              "
              >ME</Avatar
            >
          </div>
          <div class="answer">
            <img :src="require('@/assets/ai.jpg')" alt="" class="ai-icon" />
            <div class="answer-content" v-if="item.length > 1 && item[1]">
              <div
                v-if="item[1].thinking && item[1].thinking.trim()"
                class="thinking-wrapper"
              >
                <div
                  class="thinking-header"
                  :class="{
                    'is-expanded': !item[1].thinkingCollapsed,
                    'is-streaming': item[1].status === 'streaming',
                  }"
                  @click="toggleThinking(index)"
                >
                  <div class="header-left">
                    <div class="icon-container">
                      <Icon
                        v-if="item[1].status === 'streaming'"
                        type="ios-loading"
                        class="spin-icon"
                      />
                      <span v-else class="static-icon">💡</span>
                    </div>

                    <span class="header-title">
                      {{
                        item[1].status === "streaming"
                          ? "深度思考中..."
                          : "思考过程"
                      }}
                    </span>
                  </div>

                  <div class="header-right">
                    <Icon
                      type="ios-arrow-down"
                      class="arrow-icon"
                      :class="{ 'rotate-arrow': !item[1].thinkingCollapsed }"
                    />
                  </div>
                </div>

                <div
                  class="thinking-body"
                  :class="{ 'body-expanded': !item[1].thinkingCollapsed }"
                >
                  <div class="thinking-content-inner">
                    <div class="quote-line"></div>
                    <div
                      class="markdown-body thinking-text"
                      v-html="item[1].formattedThinking"
                    ></div>
                  </div>
                </div>
              </div>

              <div>
                <div
                  v-html="item[1].formattedAnswer"
                  ref="displayElement"
                ></div>
                <div
                  v-if="item[1].status === 'streaming'"
                  class="thinking-indicator"
                >
                  <div class="thinking-text"></div>
                  <div class="thinking-dots">
                    <span class="dot dot-1"></span>
                    <span class="dot dot-2"></span>
                    <span class="dot dot-3"></span>
                  </div>
                </div>
              </div>

              <div v-if="recommend.length > 0">
                <div style="font-weight: 600; margin-top: 8px">
                  您可以试着这样问：
                </div>
                <div
                  style="cursor: pointer; margin: 4px 0"
                  @click="submit('recommend', recm)"
                  v-for="(recm, inx) in recommend"
                  :key="inx"
                >
                  {{ recm }}
                </div>
              </div>

              <div
                v-if="
                  knowledgeBaseDocuments && knowledgeBaseDocuments.length > 0
                "
                class="knowledge-base-section"
              >
                <div
                  style="
                    margin-top: 20px;
                    padding: 16px;
                    background: #ffffff;
                    border-radius: 8px;
                    border: 1px solid #e8e8e8;
                  "
                >
                  <div
                    style="
                      font-weight: 600;
                      margin-bottom: 12px;
                      color: #1890ff;
                    "
                  >
                    📚 知识库参考文档
                  </div>
                  <Collapse accordion>
                    <Panel
                      v-for="(doc, docIndex) in knowledgeBaseDocuments"
                      :key="doc.document_id"
                      :name="'doc-' + docIndex"
                    >
                      {{ doc.name }}
                      <template #content>
                        <div
                          v-for="(segment, segIndex) in doc.segments"
                          :key="segIndex"
                          class="segment-item"
                        >
                          <div style="margin-bottom: 8px; font-weight: 500">
                            内容 {{ segIndex + 1 }}:
                          </div>
                          <div
                            style="
                              background: white;
                              padding: 12px;
                              border-radius: 4px;
                              border: 1px solid #e8e8e8;
                            "
                          >
                            {{ segment.content }}
                          </div>
                          <div
                            style="
                              margin-top: 4px;
                              font-size: 12px;
                              color: #666;
                            "
                          >
                            匹配度: {{ (segment.score * 100).toFixed(1) }}%
                          </div>
                          <div
                            v-if="segIndex < doc.segments.length - 1"
                            style="
                              height: 1px;
                              background: #e8e8e8;
                              margin: 12px 0;
                            "
                          ></div>
                        </div>
                      </template>
                    </Panel>
                  </Collapse>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="search" ref="parentEl">
        <Poptip
          placement="top"
          popper-class="poptip"
          :width="parentWidth"
          :disabled="true"
        >
          <Input
            size="large"
            v-model="value"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 8 }"
            :border="false"
            placeholder="请输入问题"
            @keyup.enter.native="submit('input')"
            @on-focus="onFocus"
            @on-blur="onBlur"
          />
          <template #content>
            <div class="list" v-for="(item, index) in recommend" :key="index">
              <div class="list-item" @click="submit('recommend', item)">
                {{ item }}
              </div>
            </div>
          </template>
        </Poptip>
        <div class="searchBtns">
          <Tooltip :content="submitTip" placement="bottom">
            <Button
              type="primary"
              shape="circle"
              icon="md-arrow-round-up"
              size="small"
              :loading="searchLoading"
              @click="submit('input')"
            >
            </Button>
          </Tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from "marked";
export default {
  name: "aiMain",
  props: {
    openType: {
      default: "",
      type: String,
    },
  },
  data() {
    return {
      interruptUiCounter: 0,
      activeMenu: null,
      hoverItem: null,
      progressWord: "",
      splitLeftWidth: "250px",
      isExpend: true,
      value: "",
      recommend: [],
      prompt: "",
      searchLoading: false,
      parentWidth: 0,
      searchDiv: null,
      applicationConfigId: "",
      appName: "",
      flowId: "",
      title: "",
      chatList: [],
      query: "",
      docs: "",
      flag: 0,
      answer: "",
      isChart: true,
      isCreateChart: true,
      isKnowledgeSearch: false,
      isIndexSearch: false,
      historyListItemIndex: "",
      flowHistory: [],
      showAllHistory: false,
      userId: "",
      userName: "",
      // 流式相关状态
      isStreaming: false,
      currentStreamAnswer: "",
      currentThinkingContent: "",
      streamAbortController: null,
      // 中断相关状态
      currentInterruptData: null,
      knowledgeBaseDocuments: [],
      historyRefreshInProgress: false,
      groupFlowHistory: [],
      tipList: [] // 角标信息统计
    };
  },
  computed: {
    service() {
      return this.$service.ai.deepSeekAI;
    },
    tilte() {
      return this.isCreateChart ? "对话" : "知识库检索";
    },
    submitTip() {
      let tip = "对话";
      if (this.isKnowledgeSearch) tip = "知识库检索";
      if (this.isIndexSearch) tip = "指标查询";
      return tip;
    },
  },
  methods: {
    safeReplaceAll(source, target, replacement) {
      if (!source || !target) return source || ''
      const escape = s => s.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')
      const regex = new RegExp(escape(target), 'g')
      return String(source).replace(regex, replacement)
    },
    toggleMenu(id) {
      event.stopPropagation();
      if (this.activeMenu === id) {
        this.activeMenu = null;
      } else {
        this.activeMenu = null;
        this.$nextTick(() => {
          this.activeMenu = id;
        });
      }
    },

    handleDocumentClick(event) {
      if (!event.target.closest(".history-actions")) {
        this.activeMenu = null;
      }
    },

    // =========================================================
    // 关键方法：停止呼吸灯效果
    // =========================================================
    stopBreathing() {
      if (this.currentStreamAnswer) {
        // 使用正则移除 'active-breathing' 类名
        this.currentStreamAnswer = this.currentStreamAnswer.replace(
          /active-breathing/g,
          ""
        );
      }
    },

    async sendInterruptResumeRequest(
      requestData,
      interruptType,
      userInput,
      currentIndex,
      retryCount = 0
    ) {
      try {
        const actionText = this.getInterruptActionText(
          interruptType,
          userInput
        );
        if (actionText) {
          this.$Message.info({
            content: actionText,
            duration: 3,
            closable: true,
            style: {
              position: "fixed",
              top: "20px",
              left: "50%",
              transform: "translateX(-50%)",
              zIndex: 1000,
            },
          });
        }

        await this.service.mainGraphStream(requestData, {
          onOpen: () => {
            console.log(`${interruptType} 中断恢复SSE连接已建立`);
          },
          onMessage: (data) => {
            if (data.content && !data.event) {
              if (data.content.type == "knowledge_base") {
                this.$set(
                  this,
                  "knowledgeBaseDocuments",
                  data.content?.data?.content?.original_data?.documents || []
                );
              } else {
                // 修复：只有当内容不为空（忽略纯空格/换行）时，才停止呼吸
                // 防止流式响应中的间隔符打断动画
                if (data.content && data.content.trim().length > 0) {
                  this.stopBreathing();
                }
                this.currentStreamAnswer += data.content;
                this.updateChatItemStatus(currentIndex, "streaming");
              }
            }
          },
          onThinking: (data) => {
            if (data.content && data.content.data) {
              this.stopBreathing();
              this.currentThinkingContent = data.content.data;
              this.updateChatItemStatus(currentIndex, "streaming");
            }
          },
          onProgress: (data) => {
            if (data.content && data.content.data) {
              // 1. 停止之前的动画
              this.stopBreathing();

              const progressContent = data.content.data;

              // 2. 拼接带有样式和动画的 HTML
              // active-breathing: 触发流光动画
              const newProgressHtml = `
                <div class="progress-container active-breathing">
                  <span style="font-size: 16px; margin-right: 8px;">🔨</span>
                  <span class="progress-text-gradient">${progressContent}</span>
                </div>`;

              this.currentStreamAnswer += newProgressHtml;
              this.updateChatItemStatus(currentIndex, "streaming");
            }
          },
          onTraceInfo: (data) => {
            const newDocuments =
              data.content?.data?.content?.original_data?.documents || [];
            if (newDocuments.length > 0) {
              this.$set(this, "knowledgeBaseDocuments", [
                ...this.knowledgeBaseDocuments,
                ...newDocuments,
              ]);
              this.$forceUpdate();
            }
          },
          onTip: (data) => {
            if (data.content && data.content.data) {
              const { citation_key, source_description } = data.content.data;
              this.tipList.push({
                key: citation_key,
                value: source_description
              })
            }
          },
          onError: (data) => {
            console.error(`${interruptType} 中断恢复SSE错误:`, data);
            this.$Message.error(
              `中断恢复请求出错: ${data.message || "未知错误"}`
            );
            this.searchLoading = false;
            this.stopBreathing();
          },
          onInterrupt: (data) => {
            this.stopBreathing();
            const newInterruptData = this.parseInterruptData(
              data.interrupt_data
            );
            this.currentInterruptData = newInterruptData;
            const interruptUI = this.generateInterruptUI(
              newInterruptData,
              currentIndex
            );

            this.currentStreamAnswer += interruptUI;
            this.updateChatItemStatus(currentIndex, "interrupted");
          },
          onHeartbeat: (data) => {},
          onEnd: () => {
            this.changeTips(currentIndex)
            this.stopBreathing();
            this.isStreaming = false;
            this.searchLoading = false;
            if (
              !this.currentInterruptData ||
              this.currentInterruptData.type === interruptType
            ) {
              this.currentInterruptData = null;
            }

            this.$nextTick(() => {
              this.rebindEventDelegation();
            });
          },
        });
      } catch (error) {
        console.error(`${interruptType} 中断恢复请求异常:`, error);
        this.$Message.error("中断恢复请求失败");
        this.searchLoading = false;
        this.stopBreathing();
      }
    },

    buildInterruptRequestData(interruptType, userInput) {
      const sessionId = this.applicationConfigId;
      const token = localStorage.getItem("session_token") || "";
      return {
        input: userInput,
        token: token,
        is_resume: true,
        session_id: sessionId,
        metadata: {
          user_id: "",
          company: "",
          session_id: sessionId,
          windowNo: sessionId,
        },
      };
    },

    parseInterruptData(interruptData) {
      let parsedInterruptData = null;
      try {
        if (typeof interruptData === "string") {
          if (interruptData.startsWith("{") || interruptData.startsWith("[")) {
            parsedInterruptData = JSON.parse(interruptData);
          } else {
            parsedInterruptData = { type: "unknown", message: interruptData };
          }
        } else if (
          typeof interruptData === "object" &&
          interruptData !== null
        ) {
          parsedInterruptData = interruptData;
        } else {
          parsedInterruptData = {
            type: "unknown",
            message: String(interruptData),
          };
        }
      } catch (error) {
        parsedInterruptData = {
          type: "unknown",
          message: String(interruptData),
        };
      }
      return parsedInterruptData;
    },

    getInterruptActionText(interruptType, userInput) {
      const actionTexts = {
        enterprise_selection_required: `用户选择：${userInput}`,
        human_approval_required: `用户操作：${
          userInput === "approve" ? "通过计划" : "拒绝计划"
        }`,
        fund_usage_selection_required: `用户选择：${userInput}`,
      };
      return actionTexts[interruptType] || `用户操作：${userInput}`;
    },

    updateChatItemStatus(currentIndex, status, isCompleted = false) {
      let formattedAnswer;
      // 优化：如果包含中断容器标记，直接使用原始HTML，避免Markdown解析破坏DOM结构
      // 或者状态为interrupted时
      if (
        status === "interrupted" ||
        (this.currentStreamAnswer &&
          this.currentStreamAnswer.includes("data-interrupt-container"))
      ) {
        // 使用原始HTML (其中包含了我们变灰的UI) + 新的Markdown内容
        // 但这里我们需要对新加的部分进行Markdown解析，这比较复杂
        // 简单策略：全量解析，但Marked通常会保留HTML块
        formattedAnswer = this.parseMarkdown(this.currentStreamAnswer);
      } else {
        formattedAnswer = this.parseMarkdown(this.currentStreamAnswer);
      }

      if (!this.chatList[currentIndex]) return;
      this.searchLoading = false;

      this.$set(this.chatList, currentIndex, [
        this.chatList[currentIndex][0],
        {
          answer: this.currentStreamAnswer,
          thinking: this.currentThinkingContent,
          progress: this.progressWord,
          dataType: "",
          result: [],
          formattedAnswer: formattedAnswer,
          formattedThinking: this.parseMarkdown(this.currentThinkingContent),
          status: status,
          thinkingCollapsed: isCompleted,
          interruptData:
            status === "interrupted" ? this.currentInterruptData : null,
        },
      ]);
      this.$nextTick(() => {
        let qsAnswer = document.querySelector(".qsAnswer");
        if (qsAnswer) qsAnswer.scrollTop = qsAnswer.scrollHeight;
      });
    },

    generateInterruptUI(interruptData, currentIndex) {
      if (typeof interruptData === "string") {
        try {
          interruptData = JSON.parse(interruptData);
        } catch (e) {
          interruptData = { type: "unknown", message: interruptData };
        }
      }

      let interruptUI = "";
      const interruptType = interruptData.type || "unknown";

      switch (interruptType) {
        case "enterprise_selection_required":
          interruptUI = this.generateEnterpriseSelectionUI(
            interruptData,
            currentIndex
          );
          break;
        case "human_approval_required":
          interruptUI = this.generateHumanApprovalUI(
            interruptData,
            currentIndex
          );
          break;
        case "fund_usage_selection_required":
          interruptUI = this.generateFundUsageSelectionUI(
            interruptData,
            currentIndex
          );
          break;
        case "enterprise_name_required":
          interruptUI = this.generateEnterpriseNameRequiredUI(
            interruptData,
            currentIndex
          );
          break;
        default:
          const defaultMessage =
            interruptData.message || JSON.stringify(interruptData, null, 2);
          interruptUI = `<div style="margin-top: 16px; padding: 16px; background: #fff2f0; border-radius: 8px; border: 1px solid #ffccc7;">
                  <div style="font-weight: 600; margin-bottom: 8px; color: #ff4d4f;">⚠️ 需要您的操作</div>
                  <div style="white-space: pre-wrap;">${defaultMessage}</div>
                </div>`;
      }
      return interruptUI;
    },

    generateHistoryInterruptUI(interruptData, currentIndex) {
      return this.generateInterruptUI(interruptData, currentIndex);
    },

    generateDisabledInterruptUI(originalHtml) {
      let disabledHtml = originalHtml;
      // 样式替换
      disabledHtml = disabledHtml.replace(
        /color: #1890ff|background: #f0f8ff|border: 1px solid #1890ff|approve-action|reject-action|background: #1890ff/g,
        (match) => {
          switch (match) {
            case "color: #1890ff":
              return "color: #999999";
            case "background: #f0f8ff":
              return "background: #f5f5f5";
            case "border: 1px solid #1890ff":
              return "border: 1px solid #e8e8e8";
            case "approve-action":
              return "grey-disabled-action";
            case "reject-action":
              return "grey-disabled-action";
            case "background: #1890ff":
              return "background: #d9d9d9"; // 提交按钮
            default:
              return match;
          }
        }
      );
      // 移除交互属性
      disabledHtml = disabledHtml.replace(
        /cursor: pointer;?/g,
        "cursor: not-allowed;"
      );
      disabledHtml = disabledHtml.replace(
        /text-decoration: underline;?/g,
        "text-decoration: none;"
      );
      disabledHtml = disabledHtml.replace(
        /class="([^"]*?clickable-company[^"]*?)"/g,
        'class="$1 disabled-clickable-company"'
      );
      disabledHtml = disabledHtml.replace(
        /class="([^"]*?fund-usage-selection[^"]*?)"/g,
        'class="$1 disabled-fund-usage-selection"'
      );
      disabledHtml = disabledHtml.replace(
        /class="([^"]*?human-approval-action[^"]*?)"/g,
        'class="$1 disabled-human-approval-action"'
      );

      // 移除数据属性
      disabledHtml = disabledHtml.replace(/data-interrupt-type="[^"]*"/g, "");
      disabledHtml = disabledHtml.replace(/data-action-type="[^"]*"/g, "");
      disabledHtml = disabledHtml.replace(/data-company="[^"]*"/g, "");
      disabledHtml = disabledHtml.replace(/data-index="[^"]*"/g, "");
      disabledHtml = disabledHtml.replace(/data-funds-tip-id="[^"]*"/g, "");

      // 添加禁用标记
      disabledHtml = disabledHtml.replace(
        /class="([^"]*?interrupt-action-button[^"]*?)"/g,
        'class="$1" data-disabled="true"'
      );

      return disabledHtml;
    },

    generateHumanApprovalUI(interruptData, currentIndex) {
      const plan = interruptData.plan || {};
      const summary = plan.summary || "无计划摘要";
      const steps = plan.steps || [];
      const availableActions = interruptData.available_actions || [];

      this.interruptUiCounter += 1;
      const uiId = `interrupt-ui-${currentIndex}-${this.interruptUiCounter}`;

      let planContent = `<div style="margin-top: 20px; padding: 16px; background: #ffffff;; border-radius: 8px; border: 1px solid #e8e8e8;" data-interrupt-container="${uiId}">`;
      planContent +=
        '<div style="font-weight: 600; font-size: 16px; color: #1890ff; margin-bottom: 12px;">📋 计划审批</div>';
      planContent += `<div style="margin-bottom: 16px;"><div style="font-weight: 500; margin-bottom: 8px;">计划摘要：</div><div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #e8e8e8;">${summary}</div></div>`;

      if (steps.length > 0) {
        planContent +=
          '<div style="margin-bottom: 16px;"><div style="font-weight: 500; margin-bottom: 8px;">执行步骤：</div><div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #e8e8e8;">';
        steps.forEach((step, index) => {
          const marginBottom = index < steps.length - 1 ? "8px" : "0";
          planContent += `<div style="margin-bottom: ${marginBottom};"><span style="font-weight: 500;">${step.stepId}：</span><span>${step.goal}</span></div>`;
        });
        planContent += "</div></div>";
      }

      if (availableActions.length > 0) {
        planContent +=
          '<div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e8e8e8;"><div style="font-weight: 500; margin-bottom: 12px;">请选择操作：</div><div style="display: flex; gap: 12px;">';
        availableActions.forEach((action) => {
          const actionType = action.type || "";
          const actionLabel = action.label || actionType;
          let linkStyle =
            actionType === "approve"
              ? "approve-action"
              : actionType === "reject"
              ? "reject-action"
              : "default-action";
          planContent += `<a class="interrupt-action-button human-approval-action ${linkStyle}" data-ui-id="${uiId}" data-chat-index="${currentIndex}" data-action-type="${actionType}" data-interrupt-type="human_approval_required">${actionLabel}</a>`;
        });
        planContent += "</div></div>";
      }
      planContent += "</div>";
      return planContent;
    },

    generateEnterpriseSelectionUI(interruptData, currentIndex) {
      const options = interruptData.options || [];
      const message = interruptData.message || "请选择以下企业：";

      this.interruptUiCounter += 1;
      const uiId = `interrupt-ui-${currentIndex}-${this.interruptUiCounter}`;

      let clickableList = options
        .map(
          (company) =>
            `<span class="interrupt-action-button clickable-company" data-ui-id="${uiId}" data-chat-index="${currentIndex}" style="cursor: pointer; color: #1890ff; text-decoration: underline; margin-right: 10px; padding: 4px 8px; border: 1px solid #1890ff; border-radius: 4px;" data-company="${company}" data-interrupt-type="enterprise_selection_required">${company}</span>`
        )
        .join("<br>");

      let selectionContent = `<div style="margin-top: 16px; padding: 16px; background: #f0f8ff; border-radius: 8px; border: 1px solid #d1e9ff;" data-interrupt-container="${uiId}">`;
      selectionContent +=
        '<div style="font-weight: 600; margin-bottom: 12px; color: #1890ff;">🔍 企业选择</div>';
      selectionContent += `<div style="margin-bottom: 16px;"><div style="font-weight: 500; margin-bottom: 8px;">选择提示：</div><div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #d1e9ff;">${message}</div></div>`;

      if (options.length > 0) {
        selectionContent += `<div style="margin-bottom: 16px;"><div style="font-weight: 500; margin-bottom: 8px;">可选企业：</div><div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #d1e9ff;"><div style="line-height: 2;">${clickableList}</div></div></div>`;
      }
      selectionContent += "</div>";
      return selectionContent;
    },

    generateFundUsageSelectionUI(interruptData, currentIndex) {
      const fundOptions = interruptData.options_detail || [];
      const fundMessage =
        interruptData.message || "检测到多个可能的资金用途场景，请选择：";

      this.interruptUiCounter += 1;
      const uiId = `interrupt-ui-${currentIndex}-${this.interruptUiCounter}`;

      let fundClickableList = fundOptions
        .map(
          (opt) =>
            `<span class="interrupt-action-button fund-usage-selection" data-ui-id="${uiId}" data-chat-index="${currentIndex}" style="cursor: pointer; color: #1890ff; text-decoration: underline; margin: 8px 0; display: block; padding: 8px 12px; background: #f0f8ff; border-radius: 4px; border: 1px solid #d1e9ff;" data-index="${opt.index}" data-interrupt-type="fund_usage_selection_required" data-funds-tip-id="${opt.fundsTipId}">${opt.index} - ${opt.fundsTip}</span>`
        )
        .join("");

      let fundContent = `<div style="margin-top: 16px; padding: 16px; background: #ffffff; border-radius: 8px; border: 1px solid #e8e8e8;" data-interrupt-container="${uiId}">`;
      fundContent +=
        '<div style="font-weight: 600; margin-bottom: 12px; color: #1890ff;">💰 资金用途选择</div>';
      fundContent += `<div style="margin-bottom: 16px;"><div style="font-weight: 500; margin-bottom: 8px;">选择提示：</div><div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #e8e8e8;">${fundMessage}</div></div>`;

      if (fundOptions.length > 0) {
        fundContent += `<div style="margin-bottom: 16px;"><div style="font-weight: 500; margin-bottom: 8px;">可用选项：</div><div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #e8e8e8;"><div>${fundClickableList}</div></div></div>`;
      }
      fundContent += "</div>";
      return fundContent;
    },

    generateEnterpriseNameRequiredUI(interruptData, currentIndex) {
      const inputMessage =
        interruptData.message ||
        "没有找到相关的企业基本信息，请您提供企业的工商注册全称，以便我进行精准查询。";

      this.interruptUiCounter += 1;
      const uiId = `interrupt-ui-${currentIndex}-${this.interruptUiCounter}`;

      let inputContent = `<div style="margin-top: 16px; padding: 16px; background: #ffffff; border-radius: 8px; border: 1px solid #e8e8e8;" data-interrupt-container="${uiId}">`;
      inputContent +=
        '<div style="font-weight: 600; margin-bottom: 12px; color: #1890ff;">🔍 企业名称输入</div>';
      inputContent += `<div style="margin-bottom: 16px;"><div style="font-weight: 500; margin-bottom: 8px;">输入提示：</div><div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #e8e8e8;">${inputMessage}</div></div>`;
      inputContent += `<div style="margin-bottom: 16px;"><div style="font-weight: 500; margin-bottom: 8px;">企业名称：</div><div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #e8e8e8;"><div style="display: flex; gap: 8px; align-items: center;"><input type="text" class="enterprise-name-input" placeholder="请输入企业工商注册全称" style="flex: 1; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 14px;">`;
      inputContent += `<button class="interrupt-action-button enterprise-name-submit" data-ui-id="${uiId}" data-chat-index="${currentIndex}" data-interrupt-type="enterprise_name_required" style="padding: 8px 16px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">提交</button>`;
      inputContent += "</div></div></div>";
      inputContent +=
        '<div style="margin-bottom: 16px;"><div style="font-weight: 500; margin-bottom: 8px;">使用说明：</div><div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #e8e8e8;"><div style="font-size: 12px; color: #666;">提示：请确保输入完整的企业工商注册名称，以便获得最准确的结果。</div></div></div>';
      inputContent += "</div>";
      return inputContent;
    },

    validateInterrupt(expectedType) {
      if (!this.currentInterruptData) {
        this.$Message.warning("当前没有可恢复的中断会话");
        return false;
      }
      const currentType = this.currentInterruptData.type;
      if (currentType !== expectedType) {
        this.$Message.warning(`当前中断类型为 ${currentType}，不支持此操作`);
        return false;
      }
      return true;
    },

    checkAndRecoverInterruptState() {
      return !!this.currentInterruptData;
    },

    async handleEnterpriseSelection(
      companyName,
      interruptType = "enterprise_selection_required"
    ) {
      if (!this.currentInterruptData) {
        this.$Message.warning("当前没有可恢复的中断会话");
        return;
      }
      const currentInterruptType = this.currentInterruptData.type;
      if (
        currentInterruptType !== "enterprise_selection_required" &&
        currentInterruptType !== "enter_selection_required"
      ) {
        this.$Message.warning(
          `当前中断类型为 ${currentInterruptType}，不支持企业选择操作`
        );
        return;
      }

      this.searchLoading = true;
      const currentIndex = this.chatList.length - 1;

      try {
        const sessionId = this.applicationConfigId;
        const token = localStorage.getItem("session_token");
        const requestData = {
          input: companyName,
          token: token,
          is_resume: true,
          session_id: sessionId,
          metadata: {
            user_id: "",
            company: "",
            session_id: sessionId,
            windowNo: sessionId,
          },
        };

        const userSelectionText = `\n\n**用户选择：${companyName}**\n\n`;
        this.currentStreamAnswer += userSelectionText;

        await this.sendInterruptResumeRequest(
          requestData,
          interruptType,
          companyName,
          currentIndex
        );
      } catch (error) {
        console.error("企业选择请求异常:", error);
        this.$Message.error("企业选择请求失败");
        this.searchLoading = false;
      }
    },

    async handleEnterpriseNameSubmit(enterpriseName, interruptType) {
      const interruptData = this.currentInterruptData;
      if (
        interruptData.type !== "enter_selection_required" &&
        interruptData.type !== "enterprise_name_required"
      ) {
        this.$Message.warning(
          `当前中断类型为 ${interruptData.type}，不支持此操作`
        );
        return;
      }

      this.searchLoading = true;
      try {
        const sessionId = this.applicationConfigId;
        const token = localStorage.getItem("session_token") || "";
        const requestData = {
          input: enterpriseName,
          token: token,
          is_resume: true,
          session_id: sessionId,
          metadata: {
            user_id: "",
            company: "",
            session_id: sessionId,
            windowNo: sessionId,
          },
        };

        const currentIndex = this.chatList.length - 1;
        const userInputText = `\n\n**用户提供：${enterpriseName}**\n\n`;
        this.currentStreamAnswer += userInputText;

        await this.sendInterruptResumeRequest(
          requestData,
          interruptType,
          enterpriseName,
          currentIndex
        );
        this.$Message.success(`已提交企业名称: ${enterpriseName}，正在思考...`);
      } catch (error) {
        this.$Message.error("企业名称提交请求失败");
        this.searchLoading = false;
      }
    },

    async handleHumanApprovalAction(actionType) {
      if (!this.validateInterrupt("human_approval_required")) return;
      this.searchLoading = true;
      const currentIndex = this.chatList.length - 1;
      const requestData = this.buildInterruptRequestData(
        "human_approval_required",
        actionType
      );
      await this.sendInterruptResumeRequest(
        requestData,
        "human_approval_required",
        actionType,
        currentIndex
      );
    },

    async handleFundUsageSelection(index) {
      if (!this.validateInterrupt("fund_usage_selection_required")) return;
      const selectedOption = this.currentInterruptData.options_detail.find(
        (opt) => opt.index == index
      );
      if (!selectedOption) {
        this.$Message.warning("未找到对应的资金用途选项");
        return;
      }
      this.searchLoading = true;
      const currentIndex = this.chatList.length - 1;
      const requestData = this.buildInterruptRequestData(
        "fund_usage_selection_required",
        index
      );
      await this.sendInterruptResumeRequest(
        requestData,
        "fund_usage_selection_required",
        selectedOption.fundsTip,
        currentIndex
      );
    },

    setParam(val, setName, paramName) {
      this.$set(
        this.form.formFields.find((item) => item.fieldKey == setName),
        "queryParam",
        { [paramName]: val }
      );
      this.$set(
        this.form.formFields.find((item) => item.fieldKey == setName),
        "disabled",
        false
      );
    },

    rebindEventDelegation() {
      const qsAnswer = document.querySelector(".qsAnswer");
      if (qsAnswer) {
        qsAnswer.removeEventListener("click", this.handleGlobalClick);
        qsAnswer.addEventListener("click", this.handleGlobalClick);
      }
    },

    // ========== 全局点击处理 (关键修复逻辑在这里) ==========
    handleGlobalClick(event) {
      const target = event.target;

      const isInterruptButton =
        target.classList.contains("interrupt-action-button") ||
        target.closest(".enterprise-name-submit");

      if (isInterruptButton) {
        const uiId = target.getAttribute("data-ui-id");
        const chatIndex = parseInt(target.getAttribute("data-chat-index"));
        const interruptType = target.getAttribute("data-interrupt-type");

        if (target.getAttribute("data-disabled") === "true") {
          event.preventDefault();
          return;
        }

        if (chatIndex !== this.chatList.length - 1) {
          this.$Message.warning("只能操作最新一次对话中的中断项");
          event.preventDefault();
          return;
        }

        // --- 核心修复：防止颜色回退 ---
        const chatItem = this.chatList[chatIndex][1];
        if (chatItem && chatItem.answer) {
          const originalInterruptContainer = target.closest(
            `div[data-interrupt-container="${uiId}"]`
          );

          if (originalInterruptContainer) {
            const originalHtml = originalInterruptContainer.outerHTML;
            const disabledHtml = this.generateDisabledInterruptUI(originalHtml);

            // 1. 立即更新 DOM (视觉反馈)
            originalInterruptContainer.outerHTML = disabledHtml;

            // 2. 核心：从 DOM 中读取完整的、最新的 HTML 字符串
            // 因为 replace 可能因为字符串差异失败，读取 DOM 是最稳妥的方式
            const newFullHtml = this.$refs.displayElement[chatIndex].innerHTML;

            // 3. 更新 Local State
            this.$set(chatItem, "answer", newFullHtml);
            this.$set(chatItem, "formattedAnswer", newFullHtml);

            // 4. 关键：同步更新 currentStreamAnswer
            // 这样当新的流式数据到达时，它会基于变灰后的内容进行追加，而不是覆盖回原色
            this.currentStreamAnswer = newFullHtml;
          }
        }
        // ------------------------------

        switch (interruptType) {
          case "enterprise_selection_required":
            const companyName = target.getAttribute("data-company");
            if (this.validateInterrupt("enterprise_selection_required")) {
              this.handleEnterpriseSelection(companyName, interruptType);
            }
            break;
          case "human_approval_required":
            const actionType = target.getAttribute("data-action-type");
            if (this.validateInterrupt("human_approval_required")) {
              this.handleHumanApprovalAction(actionType);
            }
            break;
          case "fund_usage_selection_required":
            const index = target.getAttribute("data-index");
            if (this.validateInterrupt("fund_usage_selection_required")) {
              this.handleFundUsageSelection(index);
            }
            break;
          case "enterprise_name_required":
            const inputContainer = target.closest(
              "div[data-interrupt-container]"
            );
            const inputElement = inputContainer
              ? inputContainer.querySelector(".enterprise-name-input")
              : null;
            if (inputElement && inputElement.value.trim()) {
              const enterpriseName = inputElement.value.trim();
              if (this.validateInterrupt("enterprise_name_required")) {
                this.handleEnterpriseNameSubmit(
                  enterpriseName,
                  "enterprise_name_required"
                );
              }
            } else {
              this.$Message.warning("请输入企业工商注册全称");
            }
            break;
        }

        event.preventDefault();
        event.stopPropagation();
        return;
      }

      if (target.classList.contains("openLink")) {
        let url = target.getAttribute("url");
        let params = target.getAttribute("params");
        if (!url || !params) {
          this.$Message.warning("查询返回缺少url或参数!");
          return false;
        }
        let obj = {};
        params.split(", ").forEach((item) => {
          let arr = item.split(": ");
          if (arr.length == 2) obj[arr[0]] = arr[1] || "";
        });
        params = Object.keys(obj)
          .map((key) => `${key}=${obj[key]}`)
          .join("&");
        const urlParams = `${url}?${params}`;
        window.open(urlParams, "_blank");
        return;
      }

      if (
        target.classList.contains("enterprise-name-input") &&
        event.key === "Enter"
      ) {
        const interruptType = target
          .closest("div[data-interrupt-container]")
          ?.querySelector(".enterprise-name-submit")
          ?.getAttribute("data-interrupt-type");
        if (interruptType && target.value.trim()) {
          this.handleEnterpriseNameSubmit(target.value.trim(), interruptType);
        }
        return;
      }
    },

    collapse() {
      this.splitLeftWidth = "52px";
      this.isExpend = false;
    },

    onRefreshIconClick() {
      this.getFlowHistory();
      this.$Message.success("历史记录已刷新");
    },

    gotoListPage () {
      this.$router.push({ path: "/list" });
    },

    gotoAnswerPage () {
      this.$router.push({ path: "/tool" });
    },

    async newCreateChart() {
      if (this.typingInterval) {
        clearInterval(this.typingInterval);
        this.typingInterval = null;
      }
      this.isCreateChart = true;
      this.isKnowledgeSearch = false;
      this.isIndexSearch = false;
      this.historyListItemIndex = "";
      this.chatList = [];
      this.value = "";
      this.recommend = [];
      this.prompt = "";
      this.query = "";
      this.answer = "";
      this.docs = [];
      this.flag = 0;
      this.currentStreamAnswer = "";
      this.isStreaming = false;
      this.knowledgeBaseDocuments = [];
      this.currentInterruptData = null;
      this.interruptUiCounter = 0;

      this.searchLoading = true;
      try {
        let res = await this.service.start({ name: "dags" });
        this.applicationConfigId = res.data || "";
        this.flowId = "";
        this.title = "";
        this.$Message.success("已创建新对话");
        this.getFlowHistory();
      } catch (error) {
        console.error("新建对话失败:", error);
        this.$Message.error("新建对话失败，请重试");
      } finally {
        this.searchLoading = false;
      }
    },

    async knowledgeSearch() {
      this.isCreateChart = false;
      this.isKnowledgeSearch = true;
      this.isIndexSearch = false;
      this.historyListItemIndex = "";
      this.chatList = [];
      this.value = "";
      this.searchLoading = true;
      let res = await this.service.start({ name: "dags" });
      this.searchLoading = false;
      this.applicationConfigId = res.data || "";
    },

    historyItemClick(data) {
      this.historyListItemIndex = data.id;
      this.service
        .pageFlowQa({
          current: 1,
          size: 200,
          flowId: data.id,
          windowsNo: data.windows_no || null,
        })
        .then((res) => {
          this.flowId = data.id;
          this.title = data.title;
          this.chatList = [];
          if (res.data && res.data.records) {
            this.chatList = res.data.records.map((item, index) => {
              let answerContent = "";
              if (typeof item.answer === "string") {
                answerContent = item.answer;
              } else if (item.answer && typeof item.answer === "object") {
                answerContent =
                  item.answer.answer ||
                  item.answer.content ||
                  JSON.stringify(item.answer);
              }

              let interruptData = null;
              if (item.interrupt_data) {
                interruptData =
                  typeof item.interrupt_data === "string"
                    ? JSON.parse(item.interrupt_data)
                    : item.interrupt_data;
                interruptData = this.parseInterruptData(interruptData);
              }

              let displayAnswer = answerContent;
              return [
                item.query,
                {
                  answer: displayAnswer,
                  thinking: item.think_content || "",
                  dataType: "",
                  result: [],
                  formattedAnswer: displayAnswer.includes(
                    "<div data-interrupt-container"
                  )
                    ? displayAnswer
                    : this.parseMarkdown(displayAnswer),
                  formattedThinking: this.parseMarkdown(
                    item.think_content || ""
                  ),
                  status: "completed",
                  thinkingCollapsed: true,
                  interruptData: interruptData,
                  uniqueKey: `${item.id}_${item.windows_no}_${index}`,
                },
              ];
            });

            if (this.chatList.length > 0) {
              const lastItem = this.chatList[this.chatList.length - 1][1];
              if (lastItem.interruptData) {
                this.currentInterruptData = lastItem.interruptData;
              }
            }
          }
        })
        .catch((err) => {
          console.log(err, "err");
        });
    },

    deleteFlow(data) {
      this.$Modal.confirm({
        title: "提示",
        content: "确定要删除该记录吗?",
        onOk: () => {
          this.activeMenu = null;
          this.hoverItem = null;
          const isCurrentSession = this.historyListItemIndex === data.id;
          this.removeSessionFromLocalHistory(data);
          this.$forceUpdate();

          this.service
            .delete_session_by_windows_no(data.windows_no)
            .then((res) => {
              if (res.status == "success") {
                this.$Message.success("删除成功");
                if (isCurrentSession) {
                  this.newCreateChart().then(() => {
                    this.getFlowHistory();
                  });
                } else {
                  this.getFlowHistory();
                }
              } else {
                this.$Message.warning(res.msg);
              }
            })
            .catch((err) => {
              console.error("删除失败:", err);
              this.$Message.error("删除失败，请重试");
              this.getFlowHistory();
            });
        },
      });
    },

    async submitStream(type, item) {
      if (type === "recommend") this.value = item;
      if (!this.value) {
        this.$Message.warning("请输入问题！");
        return;
      }

      this.searchLoading = true;
      this.isStreaming = true;
      let value = this.value;

      this.value = "";
      this.prompt = "";
      this.query = "";
      this.answer = "";
      this.docs = [];
      this.recommend = [];
      this.flag = 0;
      this.currentStreamAnswer = "";
      this.currentThinkingContent = "";
      this.progressWord = "";

      let arr = [
        value,
        {
          answer: "",
          thinking: "",
          dataType: "",
          result: [],
          formattedAnswer: "",
          status: "streaming",
        },
      ];
      this.chatList.push(arr);
      const currentIndex = this.chatList.length - 1;

      this.$nextTick(() => {
        let qsAnswer = document.querySelector(".qsAnswer");
        qsAnswer.scrollTop = qsAnswer.scrollHeight;
      });
      const token = localStorage.getItem("session_token");

      if (!this.applicationConfigId) {
        try {
          const startRes = await this.service.start({ name: "dags" });
          this.applicationConfigId = startRes.data || "";
        } catch (error) {
          this.$Message.error("获取会话ID失败，请重试");
          this.isStreaming = false;
          this.searchLoading = false;
          return;
        }
      }

      const sessionId = this.applicationConfigId;
      const requestData = {
        input: value,
        token: token,
        session_id: sessionId,
        metadata: {
          user_id: "",
          company: "",
          session_id: sessionId,
          windowNo: this.applicationConfigId,
        },
      };

      try {
        await this.service.mainGraphStream(requestData, {
          onOpen: () => {
            console.log("SSE连接已建立");
          },
          onMessage: (data) => {
            if (data.content && !data.event) {
              if (data.content.type == "knowledge_base") {
                this.$set(
                  this,
                  "knowledgeBaseDocuments",
                  data.content?.data?.content?.original_data?.documents || []
                );
              } else {
                // 修复：只有当内容不为空（忽略纯空格/换行）时，才停止呼吸
                // 防止流式响应中的间隔符打断动画
                if (data.content && data.content.trim().length > 0) {
                  this.stopBreathing();
                }
                this.currentStreamAnswer += data.content;
                this.updateChatItemStatus(currentIndex, "streaming");
              }
            }
          },
          onThinking: (data) => {
            if (data.content && data.content.data) {
              this.stopBreathing(); // 思考时停止动画
              this.currentThinkingContent = data.content.data;
              this.updateChatItemStatus(currentIndex, "streaming");
            }
          },
          onProgress: (data) => {
            if (data.content && data.content.data) {
              // 1. 停止之前的动画
              this.stopBreathing();

              const progressContent = data.content.data;

              // 2. 拼接带有样式和动画的 HTML
              // progress-container: 负责边框和背景
              // active-breathing: 负责呼吸动画
              // progress-text-gradient: 负责字体渐变
              const newProgressHtml = `
                <div class="progress-container active-breathing">
                  <span style="font-size: 16px; margin-right: 8px;">🔨</span>
                  <span class="progress-text-gradient">${progressContent}</span>
                </div>`;

              this.currentStreamAnswer += newProgressHtml;
              this.updateChatItemStatus(currentIndex, "streaming");
            }
          },
          onTraceInfo: (data) => {
            const newDocuments =
              data.content?.data?.content?.original_data?.documents || [];
            if (newDocuments.length > 0) {
              this.$set(this, "knowledgeBaseDocuments", [
                ...this.knowledgeBaseDocuments,
                ...newDocuments,
              ]);
              this.$forceUpdate();
            }
          },
          onError: (data) => {
            this.$Message.error(`请求出错: ${data.message || "未知错误"}`);
            this.isStreaming = false;
            this.searchLoading = false;
            this.stopBreathing();
          },
          onInterrupt: (data) => {
            this.stopBreathing();
            const parsedInterruptData = this.parseInterruptData(
              data.interrupt_data
            );
            this.currentInterruptData = parsedInterruptData;
            const interruptUI = this.generateInterruptUI(
              parsedInterruptData,
              currentIndex
            );
            this.currentStreamAnswer += interruptUI;
            this.updateChatItemStatus(currentIndex, "interrupted");
            this.$nextTick(() => {
              this.rebindEventDelegation();
            });
          },
          onTip: (data) => {
            if (data.content && data.content.data) {
              const { citation_key, source_description } = data.content.data;
              this.tipList.push({
                key: citation_key,
                value: source_description
              })
            }
          },
          onHeartbeat: (data) => {},
          onEnd: () => {
            this.changeTips(currentIndex)
            this.stopBreathing();
          },
        });
      } catch (error) {
        console.error("流式请求异常:", error);
        this.$Message.error("流式请求失败");
        this.isStreaming = false;
        this.searchLoading = false;
      }
    },

    async submit(type, item) {
      await this.submitStream(type, item);
    },

    changeTips(currentIndex) {
      // 按角标表全量替换所有出现的位置
      const applyTips = (text = '') => {
        let out = text
        this.tipList.forEach(({ key, value }) => {
          if (!key) return
          out = this.safeReplaceAll(out, key, `<a title="${value}" class="tip-a">${key}</a>`)
        })
        return out
      }

      this.currentStreamAnswer = applyTips(this.currentStreamAnswer)

      // 已有渲染内容同步替换，避免只改 raw 导致页面不变
      const chat = this.chatList[currentIndex] && this.chatList[currentIndex][1]
      if (chat) {
        const formatted = applyTips(chat.formattedAnswer || '')
        this.$set(this.chatList, currentIndex, [
          this.chatList[currentIndex][0],
          { ...chat, answer: this.currentStreamAnswer, formattedAnswer: formatted }
        ])
      }

      this.updateChatItemStatus(currentIndex, 'completed', true)
      this.$forceUpdate()
    },

    start() {
      this.service
        .start({ name: "dags" })
        .then((res) => {
          this.applicationConfigId = res.data;
          this.getFlowHistory();
        })
        .catch((err) => {
          console.log(err, "err");
        });
    },

    getAppId() {
      this.service
        .getByName({ name: "dags" })
        .then((res) => {
          this.applicationConfigId = res.data.id;
          this.getFlowHistory();
        })
        .catch((err) => {
          console.log(err, "err");
        });
    },

    getFlowHistory() {
      if (this.historyRefreshInProgress) return Promise.resolve();
      this.historyRefreshInProgress = true;
      return new Promise((resolve, reject) => {
        const token = localStorage.getItem("session_token") || "";
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        this.service
          .getFlowHistory(
            {
              applicationConfigId: this.applicationConfigId,
              userName: this.userName,
            },
            headers
          )
          .then((res) => {
            if (res.data) {
              this.setFlowHistoryData(res.data);
              this.groupFlowHistory = this.groupByDate(res.data);
            }
            this.historyRefreshInProgress = false;
            resolve(res);
          })
          .catch((err) => {
            console.log(err, "err");
            this.historyRefreshInProgress = false;
            reject(err);
          });
      });
    },

    groupByDate(data) {
      if (!data || !data.length) return [];
      const allRecords = data.reduce(
        (acc, window) => acc.concat(window.records),
        []
      );
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      const normalizeDate = (dateStr) => new Date(dateStr.replace(/-/g, "/"));

      return [
        {
          title: "今天",
          list: allRecords.filter(
            (item) =>
              item.create_time &&
              normalizeDate(item.create_time).toDateString() ===
                today.toDateString()
          ),
        },
        {
          title: "昨天",
          list: allRecords.filter(
            (item) =>
              item.create_time &&
              normalizeDate(item.create_time).toDateString() ===
                yesterday.toDateString()
          ),
        },
        {
          title: "最近7天",
          list: allRecords.filter((item) => {
            if (!item.create_time) return false;
            const date = normalizeDate(item.create_time);
            return (
              date > new Date(today - 7 * 24 * 60 * 60 * 1000) &&
              date.toDateString() !== today.toDateString() &&
              date.toDateString() !== yesterday.toDateString()
            );
          }),
        },
        {
          title: "更早",
          list: allRecords.filter((item) => {
            if (!item.create_time) return true;
            const date = normalizeDate(item.create_time);
            return date <= new Date(today - 7 * 24 * 60 * 60 * 1000);
          }),
        },
      ].filter((group) => group.list.length > 0);
    },

    setFlowHistoryData(data) {
      if (!this.flowHistory || this.flowHistory.length === 0) {
        this.flowHistory = [{ title: "历史", list: [] }];
      }
      if (!data) {
        this.flowHistory[0] = { title: "历史", list: [] };
        return;
      }
      if (
        Array.isArray(data) &&
        data.length > 0 &&
        data[0].hasOwnProperty("windows_no") &&
        data[0].hasOwnProperty("records")
      ) {
        const groupedList = data.map((group) => {
          const recs = Array.isArray(group.records) ? group.records : [];
          const first = recs[0] || {};
          return {
            id: first.id || group.windows_no || "",
            title:
              first.query && first.query.length > 0
                ? first.query
                : group.windows_no || "会话",
            startTime:
              first.create_time || (recs[0] && recs[0].create_time) || "",
            windows_no: group.windows_no || null,
            _records: recs,
          };
        });
        this.flowHistory[0] = { title: "历史", list: groupedList };
        return;
      }
      this.flowHistory[0] = { title: "历史", list: [] };
    },

    onFocus() {
      this.searchDiv.style.border = "1px solid #2196F3";
    },
    onBlur() {
      this.searchDiv.style.border = "1px solid #ccc";
    },

    setCss() {
      let qsAnswer = document.querySelector(".qsAnswer");
      const observer = new ResizeObserver((entries) => {
        entries.forEach((entry) => {
          const { width, height } = entry.contentRect;
          if (!qsAnswer) return;
          qsAnswer.style.maxHeight = `calc(100% - ${height + 50}px)`;
        });
      });
      this.searchDiv = document.querySelector(".search");
      observer.observe(this.searchDiv);
      this.parentWidth = this.searchDiv.offsetWidth;
      new ResizeObserver(() => {
        this.parentWidth = this.searchDiv.offsetWidth;
      }).observe(this.searchDiv);
    },

    parseEnterpriseProfile(text) {
      const sections = [];
      const sectionRegex = /#### (.*?)\n([\s\S]*?)(?=#### |$)/g;
      let match;
      while ((match = sectionRegex.exec(text)) !== null) {
        const title = match[1].trim();
        let content = match[2].trim();
        content = this.parseMarkdown(content).replace(
          /<think>.*?<\/think>/g,
          ""
        );
        sections.push({ title, content });
      }
      if (sections.length === 0)
        return [{ title: "企业画像报告", content: this.parseMarkdown(text) }];
      return sections;
    },

    parseMarkdown(text) {
      if (!text) return "";
      let parsed = marked.parse(text);
      parsed = parsed.replace(/#\s+(.+)/, "<h1>$1</h1>");
      return parsed;
    },

    getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(";").shift();
      return null;
    },

    toggleThinking(index) {
      if (this.chatList[index] && this.chatList[index][1]) {
        const currentThinkingCollapsed = this.chatList[index][1].thinkingCollapsed;
        this.$set(this.chatList[index][1], "thinkingCollapsed", !currentThinkingCollapsed);
      }
    },

    removeSessionFromLocalHistory(data) {
      if (!this.flowHistory || this.flowHistory.length === 0) return;
      const currentList = this.flowHistory[0].list || [];
      const filteredList = currentList.filter((item) => {
        if (!data.windows_no) return true;
        return item.windows_no !== data.windows_no;
      });
      this.$set(this.flowHistory[0], "list", [...filteredList]);
      this.$nextTick(() => {
        this.$forceUpdate();
      });
    },

    async verifyTokenOnLoad() {
      const token = localStorage.getItem("session_token");
      if (!token) return;
      try {
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const response = await this.service.verifyToken(headers);
        if (!(response && response.valid)) {
          this.clearAuthStorage();
          this.redirectToLogin();
        }
      } catch (error) {
        this.clearAuthStorage();
        this.redirectToLogin();
      }
    },

    redirectToLogin() {
      if (this.$router) this.$router.push("/login");
      else window.location.href = "/login";
    },

    clearAuthStorage() {
      localStorage.removeItem("session_token");
      localStorage.removeItem("token_expires");
      localStorage.removeItem("login_time");
      localStorage.removeItem("username");
    },
  },
  watch: {},
  mounted() {
    this.setCss();
    this.verifyTokenOnLoad();
    this.start();
    this.getFlowHistory();

    if (this.openType === "newCreateChart") this.newCreateChart();
    else if (this.openType === "knowledgeSearch") this.knowledgeSearch();
    else if (this.openType === "indexSearch") this.indexSearch();
    else if (this.openType === "expendHistory") this.expend();

    this.$nextTick(() => {
      const qsAnswer = document.querySelector(".qsAnswer");
      if (qsAnswer) qsAnswer.addEventListener("click", this.handleGlobalClick);
      document.addEventListener("click", this.handleDocumentClick);
    });
  },

  beforeDestroy() {
    const qsAnswer = document.querySelector(".qsAnswer");
    if (qsAnswer) qsAnswer.removeEventListener("click", this.handleGlobalClick);
    document.removeEventListener("click", this.handleDocumentClick);
  },
};
</script>