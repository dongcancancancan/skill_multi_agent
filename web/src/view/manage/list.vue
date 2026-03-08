<template>
  <div class="flex-s">
    <div class="left-panel btns">
      <div
        class="left-item"
        :class="{ active: activePath === '/' }"
        @click="newCreateChart"
      >
        <Icon class="icon" size="18" type="md-chatboxes" />
        <span>新建对话</span>
      </div>
      <div class="left-item" :class="{ active: activePath === '/list' }">
        <Icon class="icon" size="18" type="md-book" />
        <span>访前一页纸</span>
      </div>
      <div
        class="left-item"
        :class="{ active: activePath === '/tool' }"
        @click="gotoAnswerPage"
      >
        <Icon class="icon" size="18" type="md-chatbubbles" />
        <span>数智洞察</span>
      </div>
      <div class="left-item" @click="newCreateChart" title="刷新历史">
        <Icon class="icon" size="18" type="md-time" />
        <span>历史会话</span>
      </div>
    </div>
    <div class="manage-list">
      <div class="search-bar">
        <div class="inputs">
          <div class="field">
            <label>统一社会信用代码</label>
            <Input
              v-model="filters.uscc"
              placeholder="请输入统一社会信用代码"
              clearable
              style="width: 220px"
            />
          </div>
          <div class="field">
            <label>企业全称</label>
            <Input
              v-model="filters.corpNm"
              placeholder="请输入企业名称"
              clearable
              style="width: 220px"
            />
          </div>
          <div class="search-buttons">
            <Button type="primary" @click="search">查询</Button>
            <Button @click="reset">重置</Button>
          </div>
        </div>

        <div class="ops-buttons">
          <Button type="primary" @click="add">新增</Button>
          <!-- <Button @click="exportAll">导出</Button> -->
          <Button type="warning" @click="deleteSelected">删除</Button>
        </div>
      </div>

      <Table
        ref="table"
        border
        stripe
        :columns="columns"
        :data="tableData"
        :loading="loading"
      >
        <template slot="actions" slot-scope="{ row }">
          <Button
            type="text"
            size="small"
            @click="view(row)"
            v-if="row.rptStats !== '正在生成'"
            >详情</Button
          >
          <Button
            type="text"
            size="small"
            @click="exportRow(row)"
            v-if="row.rptStats !== '正在生成'"
            >导出</Button
          >
        </template>
      </Table>
      <Page
        show-total
        style="margin-top: 16px; text-align: right"
        :total="page.total"
        :page-size="page.pageSize"
        :current="page.pageNum"
        @on-change="changePageNum"
        @on-page-size-change="changePageSize"
      />

      <Modal
        v-model="showAddModal"
        :title="newForm.seqno ? '编辑' : '新增'"
        width="640"
        :closable="false"
        :mask-closable="false"
      >
        <Form
          ref="addForm"
          :model="newForm"
          :rules="rules"
          label-position="left"
          :label-width="140"
        >
          <FormItem label="统一社会信用代码" prop="uscc" required>
            <Input
              v-model="newForm.uscc"
              placeholder="请输入统一社会信用代码"
            />
          </FormItem>
          <FormItem label="企业名称" prop="corpNm" required>
            <Input v-model="newForm.corpNm" placeholder="请输入企业名称" />
          </FormItem>
        </Form>
        <div slot="footer" class="modal-footer">
          <Button @click="cancelAdd">取消</Button>
          <Button type="primary" @click="confirmAdd">确认</Button>
        </div>
      </Modal>
      <DoubleConfirm
        ref="doubleConfirm"
        first-content="确定要删除这条重要数据吗？"
        second-content="数据删除后将无法恢复！"
        warning-text="此操作会永久删除数据，请谨慎操作！"
        @on-confirm="handleRealDelete"
        @on-cancel="handleCancelDelete"
      />
    </div>
  </div>
</template>

<script>
import DoubleConfirm from "../../components/confirm/Confirm.vue";
export default {
  name: "ManageList",
  components: {
    DoubleConfirm,
  },
  data() {
    return {
      filters: {
        uscc: "",
        corpNm: "",
      },
      page: {
        pageNum: 1,
        pageSize: 10,
        total: 0,
      },
      columns: [
        { type: "selection", width: 60, align: "center" },
        { title: "查询时间", key: "qryTime", minWidth: 160 },
        { title: "统一社会信用代码", key: "uscc", minWidth: 200 },
        { title: "企业名称", key: "corpNm", minWidth: 240 },
        { title: "报告最后修改日期", key: "lstUpdateTm", minWidth: 180 },
        { title: "状态", key: "rptStats", minWidth: 180 },
        { title: "操作", slot: "actions", width: 200, align: "center" },
      ],
      tableData: [],
      selected: [],
      showAddModal: false,
      newForm: {
        uscc: "",
        corpNm: "",
      },
      rules: {
        uscc: [
          {
            required: true,
            message: "请输入统一社会信用代码",
            trigger: "blur",
          },
        ],
        corpNm: [
          { required: true, message: "请输入企业名称", trigger: "blur" },
        ],
      },
      loading: false
    };
  },
  watch: {
    $route(to, from) {
      // 监听路由变化以更新 activePath
      this.activePath = to.path;
      this.search();
    },
  },
  computed: {
    service() {
      return this.$service.manage.manageService;
    },
    activePath() {
      return this.$route.path;
    },
  },
  mounted() {
    this.search();
  },
  methods: {
    newCreateChart() {
      this.$router.push({ path: "/" });
    },
    gotoAnswerPage() {
      this.$router.push({ path: "/tool" });
    },
    changePageNum(pageNum) {
      this.page.pageNum = pageNum;
      this.search();
    },
    changePageSize(pageSize) {
      this.page.pageSize = pageSize;
      this.search();
    },
    search() {
      this.service
        .getManageList({ ...this.filters, ...this.page })
        .then((response) => {
          // 假设返回的数据在 response.data 中
          this.tableData = response.data;
          this.page.total = response.total;
        })
        .catch((error) => {
          console.error("获取列表失败:", error);
        });
    },
    reset() {
      this.filters.uscc = "";
      this.filters.corpNm = "";
      this.search();
    },
    add() {
      this.newForm.uscc = "";
      this.newForm.corpNm = "";
      this.newForm.seqno = null;
      this.showAddModal = true;
    },
    cancelAdd() {
      this.showAddModal = false;
      if (this.$refs.addForm) this.$refs.addForm.resetFields();
    },
    confirmAdd() {
      this.$refs.addForm.validate((valid) => {
        if (!valid) return;
        let method = this.newForm.seqno ? "updateCompany" : "addCompany";
        this.service[method](this.newForm)
          .then((res) => {
            if (res.success) {
              this.$Message.success("操作成功");
              this.search();
              this.showAddModal = false;
              this.$refs.addForm.resetFields();
            } else {
              this.$Message.error(res.message || "操作失败");
            }
          })
          .catch((error) => {
            console.error("操作失败:", error);
          });
      });
    },
    deleteSelected() {
      let selection = this.$refs.table.getSelection();
      if (selection.length === 0) {
        this.$Message.error("请先选择要删除的条目");
        return;
      }
      this.$refs.doubleConfirm.show();
    },
    handleCancelDelete() {
      this.$Message.info("已取消操作");
    },
    handleRealDelete() {
      let selection = this.$refs.table.getSelection();
      this.service
        .deleteCompany(selection.map((item) => item.seqno))
        .then((res) => {
          if (res.success) {
            this.$Message.success("删除成功");
            this.search();
          } else {
            this.$Message.error(res.message || "删除失败");
          }
        })
        .catch((error) => {
          console.error("删除失败:", error);
          this.$Message.error("删除过程中出现错误");
        });
    },
    view(row) {
      this.$router.push({ path: "/info", query: { id: row.seqno } });
    },
    edit(row) {
      this.newForm.uscc = row.uscc;
      this.newForm.corpNm = row.corpNm;
      this.newForm.seqno = row.seqno;
      this.showAddModal = true;
    },
    exportRow(row) {
      this.$router.push({
        path: "/info",
        query: { id: row.seqno, isExportNow: "1" },
      });
    },
  },
};
</script>

<style scoped>
.flex-s {
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
}
.left-panel {
  width: 250px;
  height: 100vh;
  border-right: 1px solid #e8e8e8;
  padding: 18px 0;
  box-sizing: border-box;
  background-color: #f9fbff;
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
.manage-list {
  padding: 18px;
  font-family: Arial, Helvetica, sans-serif;
  width: calc(100% - 250px);
}
.search-bar .inputs {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}
.field {
  display: flex;
  justify-content: flex-start;
  align-items: center;
}
.field label {
  font-size: 13px;
  color: #333;
  margin-right: 10px;
}
.search-buttons {
  display: flex;
  gap: 8px;
}
.ops-buttons {
  display: flex;
  gap: 10px;
  margin: 10px 0;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 6px;
}
</style>
