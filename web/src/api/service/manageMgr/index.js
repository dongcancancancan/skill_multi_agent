import BaseService from '@/api/service/BaseService'


class ManageService extends BaseService {
  // 获取列表数据
  getManageList(data) {
    return this.get(`/ningbopoc/pv-op-list/list?pageNum=${data.pageNum}&pageSize=${data.pageSize}&uscc=${data.uscc}&corpNm=${data.corpNm}`)
  }


  // 新增公司数据
  addCompany(data) {
    return this.post('/ningbopoc/pv-op-list/save', data)
  }

  // 查看详情数据
  getCompanyDetail(id) {
    return this.get(`/ningbopoc/pv-op-list/corp/${id}`)
  }

  // 更新公司数据
  updateCompany(data) {
    return this.put('/ningbopoc/corp-info/update', data)
  }
  
  // 删除公司数据
  deleteCompany(id) {
    return this.post(`/ningbopoc/pv-op-list/delete`, id)
  }
}

export default {
  manageService: new ManageService()
}