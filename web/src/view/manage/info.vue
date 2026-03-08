<template>
  <div>
    <!-- 页面初始化加载状态 -->
    <Spin size="large" fix v-if="pageLoading"></Spin>
    <vue-html2pdf
      :show-layout="true"
      :float-layout="false"
      :enable-download="true"
      :preview-modal="false"
      :pdf-quality="2"
      :manual-pagination="useManualPagination"
      :paginate-elements-by-height="paginateHeight"
      :pdf-format="pdfFormat"
      pdf-orientation="portrait"
      pdf-content-width="100%"
      ref="html2Pdf"
    >
      <div
        :class="['company-visit-page', { 'export-mode': exportMode }]"
        slot="pdf-content"
        id="pdf-content"
        ref="pdfContentWrap"
      >
        <!-- 标题部分 -->
        <div class="header company-header">
          <h1>{{ infoData.corpCustInfo.corpNm || "" }}访前一页纸</h1>
          <div>数据日期：{{ infoData.corpCustInfo.txDt }}</div>
          <Button @click="exportData" class="export-btn">导出</Button>
        </div>

        <!-- 企业简介部分 -->
        <div class="section company-intro">
          <h2 class="section-title">企业简介</h2>
          <div class="company-name">
            {{ infoData.corpCustInfo.corpNm }}（{{ infoData.corpCustInfo.uscc }}）
          </div>

          <div class="tags">
            <span
              v-for="(tag, index) in tags"
              :key="index"
              :class="['tag', getTagClass(index)]"
            >
              {{ tag }}
            </span>
          </div>

          <div class="company-info">
            <div class="info-item">
              <span class="label">法人：</span>
              <span class="value">{{ infoData.corpCustInfo.lglNm }}</span>
            </div>
            <div class="info-item">
              <span class="label">注册资本：</span>
              <span class="value"
                >{{ infoData.corpCustInfo.regCapitalAmt }}万</span
              >
            </div>
            <div class="info-item">
              <span class="label">成立时间：</span>
              <span class="value">{{ infoData.corpCustInfo.estabDt }}</span>
            </div>
            <div class="info-item">
              <span class="label">注册地址：</span>
              <span class="value">{{ infoData.corpCustInfo.regAddr }}</span>
            </div>
          </div>
          <!-- <div style="text-align: left; margin: 10px 0">
            {{ infoData.corpInfo.introduction }}
          </div> -->
        </div>

        <!-- AI智能企业档案部分 -->
        <div class="section ai-profile">
          <div class="flex-b">
            <h2 class="section-title">
              AI 智能企业档案 <span>（多源数据聚合画像，AI 输出仅供决策参考）</span>
            </h2>
            <Button type="primary" @click="openTextEdit" class="">编辑</Button>
          </div>

          <div class="profile-item">
            <div class="profile-content" v-html="analysis"></div>
          </div>
        </div>

        <!-- 我行合作情况部分 -->
        <div class="section cooperation">
          <div class="flex-b">
            <h2 class="section-title">我行合作情况</h2>
            <Button @click="gotoAnswerPage" type="primary">数智洞察</Button>
          </div>

          <div class="cooperation-grid">
            <div
              class="coop-item"
              v-for="(item, index) in cooperationItems"
              :key="index"
            >
              <div class="coop-value">
                {{ infoData.corpCoopInfo[item.name] }}万
              </div>
              <div class="coop-label">{{ item.label }}</div>
              <div class="coop-change">
                <span
                  :class="[
                    'change-indicator',
                    infoData.corpCoopInfo[item.year] > 0 ? 'up' : 'down',
                  ]"
                  >{{ infoData.corpCoopInfo[item.year] > 0 ? "+" : ""
                  }}{{ infoData.corpCoopInfo[item.year] }}</span
                >
                <span
                  :class="[
                    'change-indicator',
                    infoData.corpCoopInfo[item.month] > 0 ? 'up' : 'down',
                  ]"
                  >{{ infoData.corpCoopInfo[item.month] > 0 ? "+" : ""}}{{ infoData.corpCoopInfo[item.month] }}</span
                >
              </div>
              <div class="label-flex">
                  <div class="change-label">比年初</div>
                  <div class="change-label">比月初</div>
                </div>
            </div>
          </div>

          <div class="credit-info">
            <h3>授信情况</h3>

            <div
              class="credit-table"
              v-for="item in infoData.corpCredInfo"
              :key="item.corpId"
            >
              <div class="table-title">{{ item.corpNm }}总授信情况</div>
              <div class="table-row header">
                <div class="table-cell">授信批复敞口金额</div>
                <div class="table-cell">当前敞口余额</div>
                <div class="table-cell">表内贷款可用（储备）敞口金额</div>
                <div class="table-cell">资产业务（授信）市场占比情况</div>
              </div>
              <div class="table-row">
                <div class="table-cell">{{ item.credApprExpAmt }}万</div>
                <div class="table-cell">{{ item.currExpBalAmt }}万</div>
                <div class="table-cell">{{ item.onBsLoanAvlExpAmt }}万</div>
                <div class="table-cell">{{ item.ourBankCredRatio }}%</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 持有产品情况 -->
        <div class="section product-holdings">
          <h2 class="section-title">持有产品情况</h2>

          <div class="product-tags">
            <span
              class="product-tag"
              v-for="(product, index) in infoData.corpProdHoldDtl"
              :key="index"
            >
              {{ product.prodNm }}
            </span>
          </div>
        </div>

        <!-- 营销历史 -->
        <div class="section marketing-history">
          <h2 class="section-title">营销历史</h2>
          <div class="timeline">
            <div
              class="timeline-item"
              v-for="(item, index) in historyList"
              :key="index"
            >
              <div class="timeline-left">
                <div class="date-pill">{{ item.txDt }}</div>
                <div
                  class="axis-line"
                  v-if="index < infoData.mkContact.length - 1"
                ></div>
              </div>
              <div class="timeline-card">
                <div class="card-header">
                  <div class="card-title">{{ item.type }}</div>
                  <span
                    class="status-chip"
                    v-if="item.implStatus || item.visitStatus"
                    >{{ item.visitStatus || item.implStatus }}</span
                  >
                </div>
                <div class="marketing-details-grid">
                  <div class="detail" v-if="item.initiateInstNm">
                    <span class="detail-label">发起机构：</span
                    >{{ item.initiateInstNm }}
                  </div>
                  <div class="detail" v-if="item.visitorNm">
                    <span class="detail-label">拜访人：</span>{{ item.visitorNm }}
                  </div>
                  <div class="detail" v-if="item.coVisitorNm">
                    <span class="detail-label">协同拜访人：</span
                    >{{ item.coVisitorNm }}
                  </div>
                  <div class="detail" v-if="item.grpUnifNm">
                    <span class="detail-label">所属集团：</span
                    >{{ item.grpUnifNm }}
                  </div>
                  <div class="detail" v-if="item.corpNm">
                    <span class="detail-label">客户名称：</span>{{ item.corpNm }}
                  </div>
                  <div class="detail" v-if="item.visitObjNm">
                    <span class="detail-label">拜访对象：</span
                    >{{ item.visitObjNm }}
                  </div>
                  <div class="detail full" v-if="item.mktContent">
                    <span class="detail-label">会议内容：</span
                    >{{ item.mktContent }}
                  </div>
                  <div class="detail full" v-if="item.implStatus">
                    <span class="detail-label">落实/落地情况：</span
                    >{{ item.implStatus }}
                  </div>
                  <div class="detail" v-if="item.attentionNote">
                    <span class="detail-label">注意事项：</span
                    >{{ item.attentionNote }}
                  </div>
                  <div class="detail" v-if="item.compSvcSchmUrl">
                    <span class="detail-label">综合服务方案：</span
                    >{{ item.compSvcSchmUrl }}
                  </div>
                  <!-- <div class="detail" v-if="item.status"><span class="detail-label">落地情况：</span>{{ item.status }}</div> -->
                  <div class="detail" v-if="item.custName">
                    <span class="detail-label">营销对象：</span
                    >{{ item.custName }}
                  </div>
                  <div class="detail" v-if="item.visitStatus">
                    <span class="detail-label">营销状态：</span
                    >{{ item.visitStatus }}
                  </div>
                  <div class="detail" v-if="item.mktActiName">
                    <span class="detail-label">营销活动：</span
                    >{{ item.mktActiName }}
                  </div>
                  <div class="detail" v-if="item.visitContent">
                    <span class="detail-label">营销内容：</span
                    >{{ item.visitContent }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 访客建议 -->
        <div class="section visit-suggestions">
          <h2 class="section-title">访客建议</h2>

          <div class="suggestion-section">
            <h3>产品推荐</h3>
            <div class="product-recommendation">
              <div class="recommendation-header">
                <!-- <span>客户群</span> -->
                <span>客户群+大销售最多产品持有客户数</span>
              </div>
              <div class="flex-b-s">
                <div class="recommendation-bars">
                  <div
                    class="bar-item"
                    v-for="(product, index) in infoData.custGrpProdRec"
                    :key="index"
                  >
                    <div class="bar-label">{{ product.prodNm }}</div>
                    <div class="bar-container">
                      <div
                        class="bar-fill"
                        :style="{ width: product.percentage + '%' }"
                      ></div>
                    </div>
                    <div class="bar-value">{{ product.prodHoldCustCnt }}</div>
                  </div>
                </div>
                <div class="product-desc recommendation-summary">
                  <div>推荐产品集合</div>
                  <div>
                    系统锚定客群内持有客户数排名前十的热销产品:{{infoData.custProdRec.holdProdNm}}，结合客群成员的业务属性与需求偏好，优先推荐市场接受度高、适配性强的产品，推荐结果如下:
                    {{ infoData.custProdRec.recProdList }}
                  </div>
                </div>
              </div>


              <!-- <div class="scale">
                <span>0</span>
                <span>50</span>
                <span>100</span>
                <span>150</span>
                <span>200</span>
                <span>250</span>
              </div> -->
            </div>
          </div>

          <div class="suggestion-section">
            <h3>交易拓新线索</h3>
            <div class="subtitle">TOP榜 近期行外回款汇路（客户）</div>

            <div class="transaction-table">
              <div class="table-row header">
                <div class="table-cell">排行</div>
                <div class="table-cell">客户名称</div>
                <div class="table-cell">本年有效汇款金额</div>
                <div class="table-cell">交易笔数</div>
                <div class="table-cell">比同期</div>
              </div>
              <div
                class="table-row"
                v-for="(client, index) in infoData.outbkRemtRtDet"
                :key="index"
              >
                <div class="table-cell">
                  <span class="rank-index">{{ index + 1 }}</span>
                </div>
                <div class="table-cell">{{ client.remitCorpNm }}</div>
                <div class="table-cell">{{ client.transAmt }}</div>
                <div class="table-cell">{{ client.transCnt }}</div>
                <div class="table-cell">
                  <span class="change-indicator up">{{ client.yoyGrowthRate }}</span>
                </div>
              </div>
            </div>

            <!-- <div class="recommendation-summary">
              <h4>推荐产品集合</h4>
              <p>
                系统确定客户内持有客户数排名前十的热销产品，结合客户群成员的业务属性与需求偏好，优先推荐市场接受度高、适配性强的产品。推荐结果如下：线上市值用证、结构性存款、公司理财、国内信用证、应收账款、代发工资、本币活期存款、一般流动性贷款、企业网银、本币活期，以此提升推荐成功率。
              </p>
            </div> -->
          </div>
        </div>

        <!-- 资金外流线索和关注事项 -->
        <div class="section fund-outflow">
          <h2 class="section-title">资金外流线索</h2>

          <div class="outflow-content">
            <p v-for="(item,index) in infoData.coreBizClues" :key="index">
              {{index + 1}}、{{ item.clueContent }}
            </p>
          </div>

          <div class="attention-items">
            <h3>关注事项</h3>
            <ul>
              <li v-for="(item, index) in infoData.busAttnDtl" :key="index">
                {{ item.attnType }}: {{ item.corpNm }}{{ item.attnContent }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </vue-html2pdf>
    <!-- 文本编辑弹框（textarea） -->
      <Modal
        v-model="showEditModal"
        title="编辑内容"
        width="800"
        :closable="false"
        :mask-closable="false"
      >
        <Input
          type="textarea"
          v-model="editText"
          :autosize="{ minRows: 6, maxRows: 16 }"
          placeholder="请输入编辑内容"
        />
        <div slot="footer" class="modal-footer">
          <Button @click="cancelEdit">取消</Button>
          <Button type="primary" @click="confirmEdit">保存</Button>
        </div>
      </Modal>
  </div>
</template>

<script>
import { marked } from "marked";
export default {
  name: "CompanyVisitPage",
  data() {
    return {
      // 固定为 A4 尺寸（英寸）
      pdfFormat: [8.27, 11.69],
      // 导出时是否使用手动分页：A4分页应为 false（自动分页）
      useManualPagination: false,
      // 每页高度（px），约 A4 高度：11.69in * 96dpi ≈ 1122px
      paginateHeight: 4000,
      // 页面初始化加载状态
      pageLoading: true,
     // 导出模式：true 时去除左右 padding，减少分页留白
     exportMode: false,
      cooperationItems: [
        {
          label: "存款余额",
          name: "depBalAmt",
          year: "depBalChgYtd",
          month: "depBalChgMtd",
        },
        {
          label: "存款年日均",
          name: "depAvgBalYear",
          year: "depAvgBalChgYtd",
          month: "depAvgBalChgMtd",
        },
        {
          label: "对公贷款余额",
          name: "corpLoanBalAmt",
          year: "corpLoanBalChgYtd",
          month: "corpLoanBalChgMtd",
        },
        {
          label: "对公理财余额",
          name: "corpFinProdBalAmt",
          year: "corpFinProdBalChgYtd",
          month: "corpFinProdBalChgMtd",
        },
        {
          label: "存款利息净收入",
          name: "depNetIntIncAmt",
          year: "depNetIntIncChgYtd",
          month: "depNetIntIncChgMtd",
        },
        {
          label: "贷款利息净收入",
          name: "loanNetIntIncAmt",
          year: "loanNetIntIncChgYtd",
          month: "loanNetIntIncChgMtd",
        },
        {
          label: "中间业务收入",
          name: "midBizIncAmt",
          year: "midBizIncChgYtd",
          month: "midBizIncChgMtd",
        },
        {
          label: "经济增加值",
          name: "eva",
          year: "evaChgYtd",
          month: "evaChgMtd",
        },
      ],
      infoData: {
        corpCustInfo: {},
        corpInfo: {},
        corpAnalysis: {},
        corpCoopInfo: {},
        visProfile: [],
        mkContact: [],
        execVisitRcd: [],
        custProdRec: {},
        coreBizClues: []
      },
      loading: false,
      // 文本编辑弹框状态
      showEditModal: false,
      editText: ""
    };
  },
  computed: {
    service() {
      return this.$service.manage.manageService;
    },
    tags() {
      return this.infoData.corpCustInfo.labelName
        ? this.infoData.corpCustInfo.labelName.split("、")
        : [];
    },
    analysis() {
      return this.infoData.corpInfo.introduction
        ? marked.parse(this.infoData.corpInfo.introduction)
        : "";
    },
    historyList() {
      return [
        ...this.infoData.visProfile.map(item => ({...item, type: '访客档案'})),
        ...this.infoData.mkContact.map(item => ({...item, type: '营销接触'})),
        ...this.infoData.execVisitRcd.map(item => ({...item, type: '高层拜访'})),
      ];
    },
  },
  watch: {
    '$route.query.id'(to, from) {
      this.initData();
      this.updatePdfFormat();
    },
  },
  mounted() {
    this.initData();
    this.updatePdfFormat();
  },
  methods: {
    cancelEdit() {
      this.showEditModal = false;
      this.editText = "";
    },
    async confirmEdit() {
      this.service
        .updateCompany({
          corpId: this.infoData.corpCustInfo.corpId,
          introduction: this.editText
        })
        .then((res) => {
          if (res.success) {
            this.$Message.success("已保存编辑内容");
            this.cancelEdit();
            this.initData();
          } else {
            this.$Message.error(res.message || "保存失败");
          }
        })
        .catch((error) => {
          console.error("保存失败:", error);
          this.$Message.error("保存过程中出现错误");
        });
    },
    // 打开文本编辑弹框
    openTextEdit() {
      this.editText = this.infoData.corpInfo.introduction || "";
      this.showEditModal = true;
    },
    gotoAnswerPage () {
      this.$router.push({ path: "/tool" });
    },
    exportData() {
      // 使用 A4 分页导出：关闭手动分页，固定 A4 尺寸
      this.useManualPagination = false;
      this.pdfFormat = [8.27, 11.69];
     // 打开导出模式，去除左右内边距，导出完成后恢复
     this.exportMode = true;
     this.$nextTick(() => {
       const p = this.$refs.html2Pdf.generatePdf();
       if (p && p.then) {
         p.then(() => { setTimeout(() => { this.exportMode = false; }, 300); })
          .catch(() => { this.exportMode = false; });
       } else {
         setTimeout(() => { this.exportMode = false; }, 1000);
       }
     });
    },
    updatePdfFormat() {
      this.$nextTick(() => {
        // 根据模式切换：
        // - A4分页：固定 A4 尺寸
        // - 单页长文档（如果开启 useManualPagination）：按内容动态加高
        if (!this.useManualPagination) {
          this.pdfFormat = [8.27, 11.69];
          return;
        }
        const el = this.$refs.pdfContentWrap;
        if (!el) return;
        const pxHeight = el.scrollHeight || 0;
        const pxToInch = 1 / 96;
        const bufferInches = 2;
        const inchesHeight = pxHeight * pxToInch + bufferInches;
        const minHeight = 11.69;
        this.pdfFormat = [8.27, Math.max(inchesHeight, minHeight)];
      });
    },
    getTagClass(tag) {
      const map = {
        0: "tag-red",
        1: "tag-green",
        2: "tag-orange",
        3: "tag-purple",
        4: "tag-blue",
        5: "tag-cyan",
      };
      return map[tag] || "tag-gray";
    },
    initData() {
      this.pageLoading = true;
      let id = this.$route.query.id;
      let isExportNow = this.$route.query.isExportNow
      if (!id) {
        this.updatePdfFormat();
        this.pageLoading = false;
        return;
      }
      this.service
        .getCompanyDetail(id)
        .then((res) => {
          this.infoData = res.data;
          this.updatePdfFormat();
          if (isExportNow == '1') {
            this.exportData()
            this.$router.back(-1)
          }
          this.pageLoading = false;
        })
        .catch((err) => {
          console.error("Error fetching company visit info:", err);
          this.pageLoading = false;
        });
    },
  },
};
</script>

<style scoped lang="less">
.company-visit-page {
  font-family: "Microsoft YaHei", Arial, sans-serif;
  margin: 0 auto;
  color: #333;
  background-color: #fff;
  padding: 0 100px;
}

.company-header {
  background: rgb(36, 99, 235);
  color: #fff;
  padding-top: 10px;
  position: relative;
}

.export-btn {
  position: absolute;
  bottom: 15px;
  right: 20px;
  background-color: #fff;
  color: #1a5f7a;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}
.header {
  text-align: center;
  margin-bottom: 30px;
  border-bottom: 2px solid #c1d5dd;
  padding-bottom: 15px;
}

.title {
  font-size: 24px;
  color: #1a5f7a;
  margin-bottom: 8px;
}

.date {
  font-size: 16px;
  color: #666;
}

.section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #fff;
}

.section-title {
  font-size: 18px;
  color: rgb(152, 37, 37);
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
  text-align: left;
  &::before {
    content: "";
    display: inline-block;
    width: 4px;
    height: 16px;
    background-color: rgb(152, 37, 37);
    margin-right: 8px;
    vertical-align: baseline;
  }
}

.company-name {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
  text-align: left;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 15px;
}

.tag {
  background-color: #e8f4fd;
  color: #1a5f7a;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 13px;
  border: 1px solid transparent;
}

.tag-red {
  background: #ffecec;
  color: #d64747;
  border-color: #f7b3b3;
}

.tag-green {
  background: #e8f7f0;
  color: #2e9b5c;
  border-color: #b8e6ca;
}

.tag-orange {
  background: #fff4e5;
  color: #e89a25;
  border-color: #f8d7a5;
}

.tag-purple {
  background: #f3ebff;
  color: #7c4dd2;
  border-color: #d5c4ff;
}

.tag-blue {
  background: #e9f2ff;
  color: #2f75d7;
  border-color: #bad4ff;
}

.tag-cyan {
  background: #e7f8f8;
  color: #1f9c9c;
  border-color: #b6e7e7;
}

.tag-gray {
  background: #f4f5f7;
  color: #666;
  border-color: #e1e4e8;
}

.ai-profile {
  background: rgb(248, 250, 252);
  border-radius: 8px;
  border: 1px solid #d1d9e6;
  // padding: 20px;
  // margin: 20px;
  text-align: left;
  .section-title {
    color: rgb(146, 149, 247);
    &::before {
      display: none;
    }
    span {
      color: #000;
      font-size: 14px;
    }
  }
}

.company-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 10px;
  margin-top: 15px;
}

.info-item {
  display: flex;
}

.label {
  font-weight: bold;
  min-width: 80px;
}

.value {
  color: #555;
}

.profile-item {
  margin-bottom: 20px;
}

.profile-subtitle {
  font-size: 16px;
  color: rgb(105, 136, 246);
  margin-bottom: 8px;
}

.profile-content {
  color: #555;
  line-height: 1.6;
}

.industry-item,
.product-item,
.executive-item {
  margin-bottom: 5px;
}

.cooperation-grid {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}

.second-row {
  margin-top: 30px;
}

.coop-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  text-align: center;
  background-color: #f9f9f9;
  width: 24%;
  margin-bottom: 20px;
}

.coop-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
}

.coop-label {
  color: #666;
  margin-bottom: 10px;
  font-size: 14px;
}

.coop-change {
  font-size: 13px;
}

.change-indicator {
  margin: 0 3px;
  font-weight: bold;
}

.up {
  color: #e74c3c;
}

.down {
  color: #27ae60;
}

.change-label {
  margin-top: 5px;
  color: #999;
  font-size: 12px;
  width: 80px;
}
.label-flex {
  display: flex;
  justify-content: flex-start;
  margin: 0 auto;
  width: fit-content;
}

.change-indicator {
  width: 80px;
  display: inline-block;
}

.credit-info {
  margin-top: 30px;
  text-align: left;
}

.credit-info h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 15px;
}

.credit-table {
  margin-bottom: 25px;
  background: rgb(249, 249, 249);
  border-radius: 8px;
  border: solid #dcdcdc 1px;
  padding: 10px;
}

.table-title {
  font-weight: bold;
  color: rgb(105, 136, 246);
  margin-bottom: 10px;
  padding-left: 10px;
}

.table-row {
  display: flex;
  // border-bottom: 1px solid #e0e0e0;
}

.table-row.header {
  background-color: #f2f6fa;
  font-weight: bold;
}

.table-cell {
  flex: 1;
  padding: 12px 10px;
  text-align: center;
  color: #000;
  font-weight: bold;
}

.product-holdings {
  text-align: center;
}

.product-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  gap: 10px;
}

.product-tag {
  padding: 6px 15px;
  border-radius: 20px;
  font-size: 14px;
  background: rgb(253, 235, 235);
  color: rgb(181, 93, 93);
}

.marketing-history {
  text-align: left;
}

.timeline {
  position: relative;
}

.timeline-item {
  display: flex;
  gap: 16px;
  position: relative;
  padding-bottom: 24px;
}

.timeline-left {
  width: 90px;
  position: relative;
  display: flex;
  justify-content: center;
}

.date-pill {
  padding: 8px 14px;
  border-radius: 16px;
  font-weight: 700;
  font-size: 13px;
  min-width: 64px;
  text-align: center;
  color: rgb(54, 64, 145);
  flex-shrink: 0;
}

.axis-line {
  position: absolute;
  top: 46px;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 96%;
  background: #d7def3;
  border-radius: 2px;
}

.timeline-card {
  flex: 1;
  background: #fff;
  border: 1px solid #e6e8f1;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(78, 101, 181, 0.1);
  padding: 16px 18px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-title {
  font-weight: 700;
  color: #4e5f8b;
  font-size: 16px;
}

.status-chip {
  background: #f2f4fb;
  color: #6675ad;
  border-radius: 14px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
}

.marketing-details-grid {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  .detail {
    width: 48%;
    margin-bottom: 10px;
  }
}

.detail-label {
  font-weight: 700;
  color: #3a4c7a;
  margin-right: 4px;
}

.detail.full {
  grid-column: 1 / -1;
}

.visit-suggestions .suggestion-section {
  margin-bottom: 30px;
}

.visit-suggestions h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 15px;
  text-align: left;
}

.product-recommendation {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 6px;
}

.recommendation-header {
  display: flex;
  justify-content:center;
  margin-bottom: 20px;
  font-weight: bold;
  color: #333;
}

.recommendation-bars {
  margin-bottom: 10px;
  width: 80%;
  background: #fff;
  padding: 10px;
}
.flex-b-s {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.product-desc {
  width: 20%;
  border-radius: 20px;
  text-align: left;
  background: rgb(248, 250, 252);
  margin-left: 20px;
}

.bar-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.bar-label {
  width: 150px;
  font-size: 14px;
  color: #333;
}

.bar-container {
  flex: 1;
  height: 20px;
  background-color: #e0e0e0;
  border-radius: 4px;
  margin: 0 10px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background-color: #3498db;
  border-radius: 4px;
}

.bar-value {
  width: 50px;
  text-align: right;
  font-size: 14px;
  font-weight: bold;
  color: #333;
}

.scale {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  color: #666;
  font-size: 12px;
}

.subtitle {
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
  font-style: italic;
}

.transaction-table {
  margin-bottom: 20px;
}

.rank-index {
  font-weight: bold;
  color: rgb(84, 84, 159);
  background: rgb(254, 245, 194);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: block;
  margin: 0 auto;
}

.recommendation-summary {
  background-color: #f2f6fa;
  padding: 15px;
  border-radius: 6px;
  border-left: 4px solid #3498db;
  text-align: left;
}

.recommendation-summary h4 {
  font-size: 15px;
  color: #333;
  margin-bottom: 10px;
}

.recommendation-summary p {
  color: #555;
  line-height: 1.6;
}

.outflow-content p {
  margin-bottom: 12px;
  line-height: 1.6;
  text-align: left;
}

.attention-items {
  margin-top: 20px;
  padding: 15px;
  background-color: #fff8e1;
  border-radius: 6px;
  border-left: 4px solid #ff9800;
  text-align: left;
}

.attention-items h3 {
  color: #333;
  margin-bottom: 10px;
}

.attention-items ul {
  padding-left: 20px;
}

.attention-items li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.flex-b {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

@media (max-width: 768px) {
  .cooperation-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .table-row {
    flex-direction: column;
  }

  .table-cell {
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
  }

  .bar-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .bar-label {
    width: 100%;
    margin-bottom: 5px;
  }

  .bar-container {
    width: 100%;
    margin: 5px 0;
  }
}

/* 导出时去除左右内边距，避免 A4 导出左右留白 */
.company-visit-page.export-mode {
  padding-left: 5px !important;
  padding-right: 5px !important;
  max-width: none !important;
  width: 100%;
}

/* 导出时隐藏页面上的导出按钮（避免覆盖） */
.company-visit-page.export-mode .export-btn {
  display: none !important;
}

/* 导出时可进一步压缩区块间距（按需开启） */
.company-visit-page.export-mode .section {
  margin-bottom: 10px;
  padding-left: 12px;
  padding-right: 12px;
}
</style>
