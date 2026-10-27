<template>
  <div class="calendar-view">
    <!-- 月计划 -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">月计划</span>
        <el-button type="primary" size="small" @click="openMonthDialog">新建</el-button>
      </div>
      <div class="month-plans" @wheel.prevent="handleMonthPlansWheel">
        <div
            v-for="plan in sortedMonthPlans"
            :key="plan.id"
            class="plan-card"
        >
          <span class="plan-close" @click="removeMonthPlan(plan.id)">×</span>
          <div class="plan-text">{{ plan.title }}</div>
          <div class="plan-deadline" v-if="plan.deadline">截止：{{ plan.deadline }}</div>
        </div>
      </div>
    </div>

    <!-- 下半部分 -->
    <div class="bottom-section">
      <!-- 日历 -->
      <div class="calendar-container">
        <div class="calendar-header">
          <span class="nav-arrow" @click="prevMonth">‹ 上个月</span>
          <span class="calendar-title">{{ currentYear }}年{{ currentMonth }}月</span>
          <span class="nav-arrow" @click="nextMonth">下个月 ›</span>
        </div>

        <div class="calendar-grid">
          <div v-for="day in weekDays" :key="day" class="week-day">{{ day }}</div>

          <div
              v-for="(day, i) in calendarDays"
              :key="i"
              class="calendar-day"
              :class="{
        empty: !day,
        today: isToday(day),
        selected: isSelected(day)
      }"
              @click="selectDay(day)"
          >
            <span v-if="day" class="day-number">{{ isToday(day) ? '今' : day }}</span>
          </div>
        </div>
      </div>

      <!-- 周计划 -->
      <div class="week-plans-container">
        <div class="section-header">
          <span class="section-title">周计划</span>
          <el-button type="primary" size="small" @click="openWeekDialog">新建</el-button>
        </div>
        <div class="week-plans">
          <div
              v-for="plan in sortedWeekPlans"
              :key="plan.id"
              class="week-plan-card"
          >
            <span class="plan-close" @click="removeWeekPlan(plan.id)">×</span>
            <div class="plan-text">{{ plan.title }}</div>
            <div class="plan-deadline">截止：{{ plan.deadline || '未设置' }}</div>
            <!-- 显示所属月计划 -->
            <div class="plan-parent" v-if="plan.month_plan_id">
              ↳ 所属：{{ getMonthPlanTitle(plan.month_plan_id) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建月计划模态框 -->
    <el-dialog
        v-model="monthDialogVisible"
        title="新建月计划"
        width="480px"
        :close-on-click-modal="false"
    >
      <el-form :model="monthForm" label-width="100px">
        <el-form-item label="月计划">
          <el-input v-model="monthForm.title" placeholder="请输入月计划内容" />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
              v-model="monthForm.deadline"
              type="date"
              placeholder="年 / 月 / 日"
              style="width: 100%"
              value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="monthDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMonthPlan">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建周计划模态框 -->
    <el-dialog
        v-model="weekDialogVisible"
        title="新建周计划"
        width="520px"
        :close-on-click-modal="false"
    >
      <el-form :model="weekForm" label-width="110px">
        <el-form-item label="周计划">
          <el-input v-model="weekForm.title" placeholder="请输入周计划内容" />
        </el-form-item>

        <!-- 新增：所属月计划（可为空） -->
        <el-form-item label="所属月计划">
          <el-select
              v-model="weekForm.month_plan_id"
              placeholder="可不选"
              clearable
              style="width: 100%"
          >
            <el-option
                v-for="opt in monthPlanOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="开始日期">
          <el-date-picker
              v-model="weekForm.start_date"
              type="date"
              placeholder="年 / 月 / 日"
              style="width: 100%"
              value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="截至日期">
          <el-date-picker
              v-model="weekForm.deadline"
              type="date"
              placeholder="年 / 月 / 日"
              style="width: 100%"
              value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="weekDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveWeekPlan">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted , watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter,useRoute } from 'vue-router'
import {
  getMonthPlans, createMonthPlan, deleteMonthPlan,
  getWeekPlans, createWeekPlan, deleteWeekPlan,
} from '../api/plans'
const router = useRouter()

const handleMonthPlansWheel = (event) => {
  const container = event.currentTarget
  const delta = Math.abs(event.deltaY) > Math.abs(event.deltaX) ? event.deltaY : event.deltaX
  container.scrollLeft += delta
}

// ─── 月计划 ───
const monthPlans = ref([])

const loadMonthPlans = async () => {
  try {
    monthPlans.value = await getMonthPlans()
  } catch (e) {
    ElMessage.error('加载月计划失败')
  }
}

const monthDialogVisible = ref(false)
const monthForm = ref({ title: '', deadline: '' })

const openMonthDialog = () => {
  monthForm.value = { title: '', deadline: '' }
  monthDialogVisible.value = true
}

const saveMonthPlan = async () => {
  if (!monthForm.value.title) {
    ElMessage.warning('请输入月计划内容')
    return
  }
  try {
    await createMonthPlan({
      title: monthForm.value.title,
      deadline: monthForm.value.deadline || null,
    })
    monthDialogVisible.value = false
    ElMessage.success('月计划已保存')
    await loadMonthPlans()          // 重新加载
    await loadWeekPlans()           // 周计划可能也受影响
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const route = useRoute()

watch(() => route.query.t, () => {
  loadMonthPlans()
  loadWeekPlans()
})

const removeMonthPlan = (id) => {
  ElMessageBox.confirm('是否删除?', '确认', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning',
    showClose: true,
    customClass: 'delete-confirm-box',
    confirmButtonClass: 'delete-confirm-btn',
  })
      .then(async () => {
        await deleteMonthPlan(id)
        ElMessage.success('已删除')
        await loadMonthPlans()
        await loadWeekPlans()
      })
      .catch(() => {})
}

// 挂靠筛选（下面阶段 2 会用）
const monthPlanOptions = computed(() =>
    monthPlans.value.map(p => ({ label: p.title, value: p.id }))
)

// 排序 computed
const sortedMonthPlans = computed(() => {
  const monthKey = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}`
  return monthPlans.value
      .filter(plan => plan.deadline?.slice(0, 7) === monthKey)
      .sort((a, b) => {
    return new Date(a.deadline) - new Date(b.deadline)
  })
})

// ─── 页面加载 ───
onMounted(() => {
  loadMonthPlans()
  loadWeekPlans()
})

// ─── 周计划 ───
const weekPlans = ref([])

const loadWeekPlans = async () => {
  try {
    weekPlans.value = await getWeekPlans()
  } catch (e) {
    ElMessage.error('加载周计划失败')
  }
}

const weekDialogVisible = ref(false)
const weekForm = ref({
  title: '',
  month_plan_id: null,      // 挂靠的月计划（可为 null）
  start_date: '',
  deadline: '',
})

const openWeekDialog = () => {
  weekForm.value = {
    title: '',
    month_plan_id: null,
    start_date: '',
    deadline: '',
  }
  weekDialogVisible.value = true
}

const saveWeekPlan = async () => {
  if (!weekForm.value.title) {
    ElMessage.warning('请输入周计划内容')
    return
  }
  try {
    await createWeekPlan({
      title: weekForm.value.title,
      month_plan_id: weekForm.value.month_plan_id,   // 可能为 null
      start_date: weekForm.value.start_date || null,
      deadline: weekForm.value.deadline || null,
    })
    weekDialogVisible.value = false
    ElMessage.success('周计划已保存')
    await loadWeekPlans()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const removeWeekPlan = (id) => {
  ElMessageBox.confirm('是否删除?', '确认', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning',
    showClose: true,
    customClass: 'delete-confirm-box',
    confirmButtonClass: 'delete-confirm-btn',
  })
      .then(async () => {
        await deleteWeekPlan(id)
        ElMessage.success('已删除')
        await loadWeekPlans()
      })
      .catch(() => {})
}

// 排序 computed
const sortedWeekPlans = computed(() => {
  const monthKey = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}`
  return weekPlans.value
      .filter(plan => plan.deadline?.slice(0, 7) === monthKey)
      .sort((a, b) => {
    return new Date(a.deadline) - new Date(b.deadline)
  })
})

// 挂靠关系展示（可选，卡片上显示"所属：XXX"）
const getMonthPlanTitle = (monthPlanId) => {
  if (!monthPlanId) return '未挂靠'
  const found = monthPlans.value.find(p => p.id === monthPlanId)
  return found ? found.title : '未知'
}

// ─── 日历状态 ───
const today = new Date()
const currentYear = ref(today.getFullYear())
const currentMonth = ref(today.getMonth() + 1)
const selectedDay = ref(today.getDate())

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month - 1, 1).getDay()
  const daysInMonth = new Date(year, month, 0).getDate()

  const days = []
  for (let i = 0; i < firstDay; i++) days.push(null)
  for (let i = 1; i <= daysInMonth; i++) days.push(i)
  while (days.length % 7 !== 0) days.push(null)
  return days
})

const prevMonth = () => {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

const nextMonth = () => {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

const isToday = (day) => {
  return day === today.getDate() &&
      currentMonth.value === today.getMonth() + 1 &&
      currentYear.value === today.getFullYear()
}

const isSelected = (day) => day === selectedDay.value

const selectDay = (day) => {
  if (!day) return
  selectedDay.value = day

  // 拼日期 YYYY-MM-DD
  const y = currentYear.value
  const m = String(currentMonth.value).padStart(2, '0')
  const d = String(day).padStart(2, '0')
  const dateStr = `${y}-${m}-${d}`

  // 跳转到日程页，带日期
  router.push({
    path: '/schedule',
    query: { date: dateStr },
  })
}
</script>

<style scoped>
/* ─── 页面容器 ─── */
.calendar-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
  height: 100%;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #263449;
}

/* ─── 月计划 ─── */
.section {
  flex-shrink: 0;
}

.month-plans {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 8px;
}

.plan-card {
  position: relative;
  min-width: 220px;
  flex-shrink: 0;
  padding: 16px 18px;
  border: 1px solid #e5eaf1;
  border-radius: 12px;
  background: #fff;
  text-align: left;
  box-shadow: 0 2px 8px rgba(34, 52, 79, 0.025);
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.plan-card:hover {
  border-color: #b7cef0;
  box-shadow: 0 6px 18px rgba(42, 87, 151, 0.09);
  transform: translateY(-1px);
}

.plan-close {
  position: absolute;
  top: 8px;
  right: 12px;
  cursor: pointer;
  color: #a0aaba;
  font-size: 18px;
  opacity: 0.65;
  transition: opacity 0.2s, color 0.2s;
}

.plan-card:hover .plan-close,
.week-plan-card:hover .plan-close { opacity: 1; }

.plan-close:hover {
  color: #d95b61;
}

.plan-text {
  font-size: 14px;
  line-height: 1.5;
  font-weight: 600;
  color: #344258;
  padding-right: 12px;
}

.plan-deadline {
  font-size: 12px;
  color: #8793a5;
  margin-top: 8px;
}

/* ─── 下半部分 ─── */
.bottom-section {
  flex: 1;
  display: flex;
  gap: 18px;
  align-items: stretch;      /*  让日历和周计划都撑满 */
  min-height: 0;
  overflow: hidden;
}

/* ─── 日历容器 ─── */
.calendar-container {
  flex: 2;
  border: 1px solid #e5eaf1;
  border-radius: 14px;
  padding: 18px 20px;
  background: #fff;
  box-shadow: 0 3px 12px rgba(34, 52, 79, 0.035);
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;          /*  不出现滚动条 */
}

/* ─── 日历头部：三段式布局 ─── */
.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.nav-arrow {
  cursor: pointer;
  color: #77859a;
  font-size: 14px;
  transition: color 0.2s;
  user-select: none;
  width: 90px;               /*  固定宽度，左右对称 */
}

.nav-arrow:last-child {
  text-align: right;
}

.nav-arrow:hover {
  color: #3978d4;
}

.calendar-title {
  font-size: 16px;
  font-weight: 600;
  color: #263449;
  flex: 1;
  text-align: center;        /*  标题居中 */
}

/* ─── 日历网格 ─── */
.calendar-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-auto-rows: 1fr;       /*  每行等高，自动分配剩余高度 */
  gap: 2px;
  min-height: 0;
}

.week-day {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: #8490a1;
}

.calendar-day {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
  min-height: 0;
  border-radius: 10px;
  transition: background 0.18s;
}

/*  日期数字的圆形 —— 用单独的 class */
.day-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.calendar-day:hover .day-number {
  background: #edf4ff;
}

.calendar-day.empty {
  cursor: default;
}

.calendar-day.today .day-number {
  background: #3978d4;
  color: #fff;
  font-weight: 600;
}

.calendar-day.selected:not(.today) .day-number {
  background: #edf4ff;
  color: #3978d4;
  font-weight: 600;
}

/* ─── 周计划 ─── */
.week-plans-container {
  flex: 1;
  min-width: 240px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 2px 2px 2px 0;
}

.week-plans {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 8px;
  min-height: 0;
}

.week-plan-card {
  position: relative;
  padding: 16px;
  border: 1px solid #e5eaf1;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(34, 52, 79, 0.025);
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
  flex-shrink: 0;
}

.week-plan-card:hover {
  border-color: #b7cef0;
  box-shadow: 0 6px 18px rgba(42, 87, 151, 0.09);
  transform: translateY(-1px);
}

.week-plan-card .plan-text {
  font-size: 14px;
  margin-bottom: 6px;
}

.plan-parent {
  font-size: 11px;
  color: #3978d4;
  margin-top: 4px;
  opacity: 0.8;
}
@media (max-width: 900px) {
  .calendar-view { overflow-y: auto; }
  .bottom-section { flex-direction: column; overflow: visible; }
  .calendar-container { flex: none; min-height: 390px; }
  .week-plans-container { flex: none; min-height: 220px; }
}
</style>
