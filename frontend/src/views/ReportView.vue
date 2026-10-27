<template>
  <div class="report-view">
    <!-- 第一行：查询条件 + 查询按钮（靠右） -->
    <div class="query-row">
      <span class="label">项目名称</span>
      <el-input
          v-model="filter.name"
          placeholder="请输入项目名称"
          class="filter-input"
          clearable
          @keyup.enter="handleQuery"
      />
      <span class="label">时间</span>
      <el-date-picker
          v-model="filter.dateStart"
          type="date"
          placeholder="开始日期"
          class="date-filter"
          format="YYYY年MM月DD日"
          value-format="YYYY-MM-DD"
          clearable
      />
      <span class="date-range-separator">至</span>
      <el-date-picker
          v-model="filter.dateEnd"
          type="date"
          placeholder="截止日期"
          class="date-filter"
          format="YYYY年MM月DD日"
          value-format="YYYY-MM-DD"
          clearable
      />
      <div class="spacer"></div>
      <el-button type="primary" @click="handleQuery">查询</el-button>
    </div>

    <!-- 第二行：导入/导出按钮（靠右） -->
    <div class="action-row">
      <el-button type="primary" @click="openCreate">新建</el-button>
      <el-button @click="handleImport">导入</el-button>
      <el-button @click="handleExport">导出</el-button>
      <el-button @click="handleBatchImport">批量导入</el-button>
      <el-button @click="handleBatchExport">批量导出</el-button>
    </div>

    <!-- 表格 -->
    <el-table
        :data="reports"
        border
        stripe
        class="report-table"
        header-cell-class-name="table-header"
        @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="45" />
      <el-table-column prop="name" label="项目名称" align="center" />
      <el-table-column prop="source" label="项目来源" align="center" />
      <el-table-column prop="date" label="项目日期" align="center" />
      <el-table-column
          prop="problem"
          label="遇到的问题"
          align="center"
          show-overflow-tooltip
      />
      <el-table-column
          prop="tomorrow"
          label="明日计划"
          align="center"
          show-overflow-tooltip
      />
      <el-table-column label="操作" align="center" width="220">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">修改</el-button>
          <el-button link type="primary" @click="handleDelete(row)">删除</el-button>
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-row">
      <el-config-provider :locale="paginationLocale">
        <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[5, 10, 20, 50, 100]"
            :total="allReports.length"
            layout="total, sizes, prev, pager, next, jumper"
            background
        />
      </el-config-provider>
    </div>

    <!-- 新建/修改对话框 -->
    <el-dialog
        v-model="formDialogVisible"
        :title="isEdit ? '日报修改' : '新建日报'"
        width="600px"
        :close-on-click-modal="false"
        class="report-dialog"
    >
      <div class="dialog-scroll-body">
        <el-form :model="form" label-width="100px" class="report-form">
          <el-form-item label="项目名称">
            <el-input v-model="form.name" placeholder="请输入项目名称" />
          </el-form-item>
          <el-form-item label="项目来源">
            <el-select v-model="form.source" placeholder="请选择所属周项目" clearable style="width: 100%">
              <el-option v-for="wp in weekPlanOptions" :key="wp.id" :label="wp.title" :value="wp.title" />
            </el-select>
          </el-form-item>
          <el-form-item label="项目日期">
            <el-date-picker
                v-model="form.date"
                type="date"
                placeholder="请选择日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
            />
          </el-form-item>

          <el-form-item label="项目痛点">
            <el-input
                v-model="form.pain"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 12 }"
                placeholder="请描述项目痛点"
            />
          </el-form-item>

          <el-form-item label="解决方法">
            <el-input
                v-model="form.solution"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 12 }"
                placeholder="请列出针对项目痛点的解决方法"
            />
          </el-form-item>

          <el-form-item label="遇到的问题">
            <el-input
                v-model="form.problem"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 12 }"
                placeholder="请列出期间所遇到的问题及解决方法"
            />
          </el-form-item>

          <el-form-item label="明日计划">
            <el-input
                v-model="form.tomorrow"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 12 }"
                placeholder="请输入明日计划"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveReport">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
        v-model="detailDialogVisible"
        title="日报详情"
        width="600px"
        class="report-dialog"
    >
      <div class="dialog-scroll-body">
        <el-form label-width="100px" class="report-form">
          <el-form-item label="项目名称">
            <el-input :model-value="detailData.name" readonly />
          </el-form-item>
          <el-form-item label="项目来源">
            <el-input :model-value="detailData.source" readonly />
          </el-form-item>
          <el-form-item label="项目日期">
            <el-input :model-value="detailData.date" readonly />
          </el-form-item>

          <el-form-item label="项目痛点">
            <el-input
                :model-value="detailData.pain"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 12 }"
                readonly
            />
          </el-form-item>

          <el-form-item label="解决方法">
            <el-input
                :model-value="detailData.solution"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 12 }"
                readonly
            />
          </el-form-item>

          <el-form-item label="遇到的问题">
            <el-input
                :model-value="detailData.problem"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 12 }"
                readonly
            />
          </el-form-item>

          <el-form-item label="明日计划">
            <el-input
                :model-value="detailData.tomorrow"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 12 }"
                readonly
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button type="primary" @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 隐藏的文件选择器 -->
    <input ref="importInputRef" type="file" accept=".txt" style="display: none" @change="onImportFileSelected" />
    <input ref="batchImportInputRef" type="file" accept=".txt" multiple style="display: none" @change="onBatchImportFilesSelected" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted , watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { useRoute } from 'vue-router'
import {
  getReports, createReport, updateReport, deleteReport,
  importReport, exportReports, getWeekPlans,
} from '../api/plans'

const route = useRoute()
const paginationLocale = {
  ...zhCn,
  el: {
    ...zhCn.el,
    pagination: {
      ...zhCn.el.pagination,
      goto: '跳转到',
      total: '总共 {total} 条',
    },
  },
}

// ─── 筛选 ───
const filter = ref({ name: '', dateStart: '', dateEnd: '' })

// ─── 表格数据 ───
const allReports = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const reports = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return allReports.value.slice(start, start + pageSize.value)
})
const weekPlanOptions = ref([])
const selectedRows = ref([])

const loadReports = async () => {
  try {
    allReports.value = await getReports({
      name: filter.value.name || undefined,
      date_start: filter.value.dateStart || undefined,
      date_end: filter.value.dateEnd || undefined,
    })
    currentPage.value = 1
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

const loadWeekPlans = async () => {
  try {
    weekPlanOptions.value = await getWeekPlans()
  } catch (e) {
    console.error(e)
  }
}

const handleQuery = () => {
  loadReports()
}

const handleSelectionChange = (val) => {
  selectedRows.value = val
}

// ─── 新建/编辑 ───
const formDialogVisible = ref(false)
const isEdit = ref(false)
const form = ref(getEmptyForm())

function getEmptyForm() {
  return {
    id: null, name: '', source: '', date: '',
    pain: '', solution: '', problem: '', tomorrow: '',
  }
}

const openCreate = () => {
  isEdit.value = false
  form.value = getEmptyForm()
  formDialogVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  form.value = { ...row }
  formDialogVisible.value = true
}

const saveReport = async () => {
  if (!form.value.name) {
    ElMessage.warning('请输入项目名称')
    return
  }
  try {
    if (isEdit.value) {
      await updateReport(form.value.id, form.value)
      ElMessage.success('修改成功')
    } else {
      await createReport(form.value)
      ElMessage.success('新建成功')
    }
    formDialogVisible.value = false
    await loadReports()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

// ─── 详情 ───
const detailDialogVisible = ref(false)
const detailData = ref(getEmptyForm())

const openDetail = (row) => {
  detailData.value = { ...row }
  detailDialogVisible.value = true
}

// ─── 删除 ───
const handleDelete = (row) => {
  ElMessageBox.confirm('是否删除?', '确认', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning',
    showClose: true,
    customClass: 'delete-confirm-box',
    confirmButtonClass: 'delete-confirm-btn',
  })
      .then(async () => {
        await deleteReport(row.id)
        ElMessage.success('已删除')
        await loadReports()
      })
      .catch(() => {})
}

// ─── 导入 ───
const importInputRef = ref(null)
const handleImport = () => {
  importInputRef.value?.click()
}

const onImportFileSelected = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  try {
    const res = await importReport(file)
    ElMessage.success(`成功导入 ${res.count} 条日报`)
    await loadReports()
  } catch (err) {
    ElMessage.error('导入失败：' + (err.response?.data?.detail || err.message))
  }
  e.target.value = ''
}

// ─── 批量导入 ───
const batchImportInputRef = ref(null)
const handleBatchImport = () => {
  batchImportInputRef.value?.click()
}

const onBatchImportFilesSelected = async (e) => {
  const files = Array.from(e.target.files)
  if (!files.length) return

  let total = 0
  let failed = 0

  for (const file of files) {
    try {
      const res = await importReport(file)
      total += res.count
    } catch (err) {
      failed++
      console.error(`导入 ${file.name} 失败：`, err)
    }
  }

  ElMessage.success(`成功导入 ${total} 条日报${failed ? `，${failed} 个文件失败` : ''}`)
  await loadReports()
  e.target.value = ''
}

// 辅助函数：将单行数据格式化为 txt 文本
const formatRowToTxt = (r) => {
  return `项目名称：${r.name || ''}\n` +
      `项目来源：${r.source || ''}\n` +
      `项目日期：${r.date || ''}\n` +
      `项目痛点：${r.pain || ''}\n` +
      `解决方法：${r.solution || ''}\n` +
      `遇到的问题：${r.problem || ''}\n` +
      `明日计划：${r.tomorrow || ''}\n---`
}

// 修改后的 导出 按钮逻辑
const handleExport = async () => {
  // 1. 如果用户勾选了行，直接在前端拼接并下载（单行或多行）
  if (selectedRows.value.length > 0) {
    let content = ''
    let fileName = ''

    if (selectedRows.value.length === 1) {
      // 单行导出：文件名用日报的日期
      const row = selectedRows.value[0]
      content = formatRowToTxt(row)
      fileName = row.date ? `${row.date}.txt` : `日报_${Date.now()}.txt`
    } else {
      // 多行导出：文件名加时间戳
      content = selectedRows.value.map(r => formatRowToTxt(r)).join('\n')
      fileName = `日报批量_${Date.now()}.txt`
    }

    // 加 BOM 防止中文乱码
    const BOM = new Uint8Array([0xEF, 0xBB, 0xBF])
    const blob = new Blob([BOM, content], { type: 'text/plain;charset=utf-8' })
    downloadBlob(blob, fileName)
    ElMessage.success(`已导出 ${selectedRows.value.length} 条`)
    return
  }

  // 2. 如果用户没有勾选任何行，则走后端接口，导出当前筛选条件下的所有数据
  try {
    const blob = await exportReports({
      name: filter.value.name || undefined,
      date_start: filter.value.dateStart || undefined,
      date_end: filter.value.dateEnd || undefined,
    })
    const BOM = new Uint8Array([0xEF, 0xBB, 0xBF])
    const newBlob = new Blob([BOM, blob], { type: 'text/plain;charset=utf-8' })
    downloadBlob(newBlob, `日报全量_${Date.now()}.txt`)
    ElMessage.success('全部导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

// 让“批量导出”按钮直接复用 handleExport 的逻辑，保持代码整洁
const handleBatchExport = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先勾选要导出的日报')
    return
  }
  handleExport() // 直接调用刚才的逻辑
}

const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// 监听时间戳，自动刷新
watch(() => route.query.t, () => {
  loadReports()
})

// ─── 页面加载 ───
onMounted(() => {
  loadReports()
  loadWeekPlans()
})
</script>

<style scoped>
.report-view {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 查询行 */
.query-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-shrink: 0;
}

@media (max-width: 760px) {
  .query-row { flex-wrap: wrap; }
  .query-row .spacer { display: none; }
  .date-filter { width: min(100%, 190px); }
}

.label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  white-space: nowrap;
}

.filter-input {
  width: 200px;
}

.date-filter { width: 190px; }
.date-range-separator { color: #8793a5; font-size: 13px; white-space: nowrap; }

.spacer {
  flex: 1;
}

/* 操作行 */
.action-row {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

/* 表格 */
.report-table {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

.pagination-row {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  flex-shrink: 0;
}

.pagination-row :deep(.el-pagination) {
  color: #69778b;
}

@media (max-width: 720px) {
  .pagination-row { justify-content: center; overflow-x: auto; }
}

:deep(.table-header) {
  background: #d9ecff !important;
  color: #333;
  font-weight: 600;
}

:deep(.el-table__row) {
  height: 48px;
}

:deep(.el-button.is-link) {
  font-size: 14px;
}

/* 对话框 body：去掉内边距，不加任何高度限制 */
.report-dialog :deep(.el-dialog__body) {
  padding: 0 !important;
  max-height: none !important;
  overflow: visible !important;
}

/* 滚动容器：自己控制高度和滚动 */
.dialog-scroll-body {
  max-height: 55vh;
  overflow-y: auto;
  padding: 20px 30px;
}

/* 美化滚动条 */
.dialog-scroll-body::-webkit-scrollbar {
  width: 8px;
}

.dialog-scroll-body::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 4px;
}

.dialog-scroll-body::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 4px;
}

.dialog-scroll-body::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}

.report-form :deep(.el-form-item__label) {
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

/* textarea 行高紧凑一点 */
.report-form :deep(.el-textarea__inner) {
  line-height: 1.6;
  font-size: 14px;
  resize: none;              /* 禁用用户手动拉伸 */
  padding: 8px 12px;
}
</style>
