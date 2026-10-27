<template>
  <div class="schedule-view">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button size="small" @click="goToday">Today</el-button>
        <el-button size="small" :icon="ArrowLeft" circle @click="prevWeek" />
        <span class="week-title">{{ weekTitle }}</span>
        <el-button size="small" :icon="ArrowRight" circle @click="nextWeek" />
      </div>
      <div class="toolbar-right">
        <span class="work-hours">本周工时：{{ totalHours }} 小时</span>
        <el-button type="primary" size="small" @click="openDialog">新建</el-button>
      </div>
    </div>

    <!-- 日历主体 -->
    <div class="calendar-body">
      <!-- 星期表头 -->
      <div class="week-header">
        <div class="time-gutter-header">
          <span class="gmt-label">GMT</span>
        </div>
        <div
            v-for="(day, i) in weekDays"
            :key="i"
            class="day-header"
            :class="{ today: day.isToday }"
        >
          <div class="day-name">{{ day.name }}</div>
          <div class="day-date">{{ day.dayOfMonth }}</div>
        </div>
      </div>

      <!-- 时间轴 + 日程 -->
      <div class="time-grid">
        <div class="time-gutter">
          <div
              v-for="h in hours"
              :key="h"
              class="time-slot"
              :style="{ height: hourHeight + 'px' }"
          >
            <span class="time-label">{{ formatHour(h) }}</span>
          </div>
        </div>

        <div class="days-container">
          <div
              v-for="h in hours"
              :key="h"
              class="hour-line"
              :style="{ top: (h - startHour) * hourHeight + 'px' }"
          ></div>

          <div
              v-for="(day, dayIdx) in weekDays"
              :key="dayIdx"
              class="day-column"
          >
            <el-tooltip
                v-for="event in eventsOfDay(day.dateStr)"
                :key="event.id"
                placement="top"
                effect="light"
                :show-after="180"
                popper-class="schedule-event-tooltip"
            >
              <template #content>
                <div class="event-tooltip-content">
                  <strong>{{ event.title }}</strong>
                  <span>{{ day.dateStr }} · {{ formatEventTime(event) }}</span>
                  <span v-if="getWeekPlanTitle(event.week_plan_id)">所属周计划：{{ getWeekPlanTitle(event.week_plan_id) }}</span>
                </div>
              </template>
              <div
                  class="event-block"
                  :class="'color-' + event.color"
                  :style="eventStyle(event)"
                  @click="handleEventClick(event)"
              >
                <div class="event-time">{{ formatEventTime(event) }}</div>
                <div class="event-title">{{ event.title }}</div>
              </div>
            </el-tooltip>
          </div>

          <div
              v-if="showNowLine"
              class="now-line"
              :style="{ top: nowLineTop + 'px' }"
          >
            <span class="now-label">{{ nowTimeText }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建/编辑日程对话框 -->
    <el-dialog
        v-model="dialogVisible"
        :title="isEdit ? '编辑日程' : '新建日程'"
        width="520px"
        :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="110px">
        <el-form-item label="日程名称">
          <el-input v-model="form.title" placeholder="请输入日程名称" />
        </el-form-item>

        <!-- 挂靠周计划 -->
        <el-form-item label="所属周计划">
          <el-select
              v-model="form.week_plan_id"
              placeholder="可不选"
              clearable
              style="width: 100%"
          >
            <el-option
                v-for="wp in weekPlans"
                :key="wp.id"
                :label="wp.title"
                :value="wp.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="日期">
          <el-date-picker
              v-model="form.date"
              type="date"
              placeholder="选择日期"
              style="width: 100%"
              value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-time-picker
              v-model="form.startTime"
              placeholder="选择开始时间"
              style="width: 100%"
              format="HH:mm"
              value-format="HH:mm"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-time-picker
              v-model="form.endTime"
              placeholder="选择结束时间"
              style="width: 100%"
              format="HH:mm"
              value-format="HH:mm"
          />
        </el-form-item>
        <el-form-item label="颜色">
          <el-radio-group v-model="form.color">
            <el-radio value="blue">蓝</el-radio>
            <el-radio value="green">绿</el-radio>
            <el-radio value="orange">橙</el-radio>
            <el-radio value="red">红</el-radio>
            <el-radio value="purple">紫</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEvent">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted,watch} from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import {
  getSchedules, createSchedule, updateSchedule, deleteSchedule,
  getWeekPlans,
} from '../api/plans'
const route = useRoute()

// 监听路由变化，重新加载数据
watch(() => route.query.t, () => {
  loadSchedules() // 你的日程加载函数
})
// ─── 时间轴配置 ───
// const startHour = 8
const startHour = 12
const endHour = 23
const hourHeight = 60

const hours = computed(() => {
  const arr = []
  for (let h = startHour; h <= endHour; h++) arr.push(h)
  return arr
})

// ─── 周视图 ───
const today = new Date()
const currentDate = ref(new Date())

// 计算一周的 7 天（周日到周六）
const weekDays = computed(() => {
  const names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const d = new Date(currentDate.value)
  const dayOfWeek = d.getDay()
  const sunday = new Date(d)
  sunday.setDate(d.getDate() - dayOfWeek)

  return names.map((name, i) => {
    const date = new Date(sunday)
    date.setDate(sunday.getDate() + i)
    // YYYY-MM-DD 格式
    const dateStr = formatDateStr(date)
    return {
      name,
      dayOfMonth: date.getDate(),
      dateStr,
      isToday: date.toDateString() === today.toDateString(),
    }
  })
})

const formatDateStr = (d) => {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const weekTitle = computed(() => {
  const first = weekDays.value[0]
  const last = weekDays.value[6]
  return `${first.dateStr} ~ ${last.dateStr}`
})

const goToday = () => { currentDate.value = new Date() }
const prevWeek = () => {
  const d = new Date(currentDate.value)
  d.setDate(d.getDate() - 7)
  currentDate.value = d
}
const nextWeek = () => {
  const d = new Date(currentDate.value)
  d.setDate(d.getDate() + 7)
  currentDate.value = d
}

// ─── 后端数据 ───
const schedules = ref([])       // 后端原始数据
const weekPlans = ref([])       // 用于挂靠下拉

// 加载日程
const loadSchedules = async () => {
  try {
    const res = await getSchedules()
    schedules.value = res.map(s => {
      // 转换：后端格式 → 前端展示格式
      const startDec = timeStrToDecimal(s.start_time)
      const endDec = timeStrToDecimal(s.end_time)
      return {
        id: s.id,
        title: s.title,
        date: s.date,                   // "2026-11-03"
        week_plan_id: s.week_plan_id,
        start: startDec,                 // 14.0
        duration: Math.max(endDec - startDec, 0.5),
        color: s.color || 'blue',
        start_time: s.start_time,       // 保留原始
        end_time: s.end_time,
      }
    })
  } catch (e) {
    ElMessage.error('加载日程失败')
  }
}

// 加载周计划（用于下拉）
const loadWeekPlans = async () => {
  try {
    weekPlans.value = await getWeekPlans()
  } catch (e) {
    console.error(e)
  }
}

// "14:00:00" → 14.0
const timeStrToDecimal = (timeStr) => {
  if (!timeStr) return 0
  const [h, m] = timeStr.split(':').map(Number)
  return h + m / 60
}

// "14.5" → "14:30"
const decimalToTime = (dec) => {
  const h = Math.floor(dec)
  const m = Math.round((dec - h) * 60)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

// 只显示当前周的日程
const eventsOfDay = (dateStr) => {
  return schedules.value.filter(s => s.date === dateStr)
}

const getWeekPlanTitle = (weekPlanId) => {
  if (!weekPlanId) return ''
  return weekPlans.value.find(plan => plan.id === weekPlanId)?.title || ''
}

const eventStyle = (event) => {
  const top = (event.start - startHour) * hourHeight
  const height = event.duration * hourHeight - 4
  return {
    top: top + 'px',
    height: height + 'px',
  }
}

const formatEventTime = (event) => {
  return `${decimalToTime(event.start)} - ${decimalToTime(event.start + event.duration)}`
}

const formatHour = (h) => {
  if (h === 12) return '12 PM'
  if (h > 12) return (h - 12) + ' PM'
  return h + ' AM'
}

// 当前时间红线
const nowHour = today.getHours() + today.getMinutes() / 60
const showNowLine = computed(() => nowHour >= startHour && nowHour <= endHour)
const nowLineTop = computed(() => (nowHour - startHour) * hourHeight)
const nowTimeText = computed(() => {
  return `${String(today.getHours()).padStart(2, '0')}:${String(today.getMinutes()).padStart(2, '0')}`
})

// 总工时
const totalHours = computed(() => {
  // 只统计当前周
  const weekDateStrs = weekDays.value.map(d => d.dateStr)
  return schedules.value
      .filter(s => weekDateStrs.includes(s.date))
      .reduce((sum, s) => sum + s.duration, 0)
      .toFixed(1)
})

// ─── 新建/编辑 ───
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref(getEmptyForm())

function getEmptyForm() {
  return {
    id: null,
    title: '',
    week_plan_id: null,
    date: formatDateStr(new Date()),
    startTime: '09:00',
    endTime: '10:00',
    color: 'blue',
  }
}

const openDialog = () => {
  isEdit.value = false
  form.value = getEmptyForm()
  dialogVisible.value = true
}

const saveEvent = async () => {
  if (!form.value.title) {
    ElMessage.warning('请输入日程名称')
    return
  }
  if (!form.value.date || !form.value.startTime || !form.value.endTime) {
    ElMessage.warning('请填写完整日期和时间')
    return
  }

  const payload = {
    title: form.value.title,
    week_plan_id: form.value.week_plan_id || null,
    date: form.value.date,
    start_time: form.value.startTime + ':00',
    end_time: form.value.endTime + ':00',
    color: form.value.color,
    repeat_type: 'none',
  }

  try {
    if (isEdit.value) {
      await updateSchedule(form.value.id, payload)
      ElMessage.success('修改成功')
    } else {
      await createSchedule(payload)
      ElMessage.success('日程已保存')
    }
    dialogVisible.value = false
    await loadSchedules()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
  }
}

// ─── 点击日程块 ───
const handleEventClick = (event) => {
  ElMessageBox.confirm(`是否删除日程「${event.title}」？`, '确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
    showClose: true,
    customClass: 'delete-confirm-box',
    confirmButtonClass: 'delete-confirm-btn',
  })
      .then(async () => {
        await deleteSchedule(event.id)
        ElMessage.success('已删除')
        await loadSchedules()
      })
      .catch(() => {})
}

// ─── 页面加载 ───
onMounted(() => {
  // 如果 URL 带了日期参数，定位到那一周
  const dateParam = route.query.date
  if (dateParam) {
    const parsed = new Date(dateParam)
    if (!isNaN(parsed.getTime())) {
      currentDate.value = parsed
    }
  }

  loadSchedules()
  loadWeekPlans()
})

watch(
    () => route.query.date,
    (newDate) => {
      if (newDate) {
        const parsed = new Date(newDate)
        if (!isNaN(parsed.getTime())) {
          currentDate.value = parsed
        }
      }
    }
)
</script>

<style scoped>
.schedule-view {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.week-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.work-hours {
  font-size: 13px;
  color: #999;
}

.calendar-body {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

.week-header {
  display: flex;
  border-bottom: 1px solid #e8e8e8;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 2;
}

.time-gutter-header {
  width: 70px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding-left: 12px;
  border-right: 1px solid #f0f0f0;
}

.gmt-label {
  font-size: 12px;
  color: #999;
}

.day-header {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  border-right: 1px solid #f5f5f5;
}

.day-header.today .day-name {
  color: #409eff;
  font-weight: 700;
}

.day-name {
  font-size: 13px;
  color: #666;
  margin-bottom: 2px;
}

.day-date {
  font-size: 12px;
  color: #999;
}

.day-header.today .day-date {
  color: #409eff;
  font-weight: 600;
}

.time-grid {
  display: flex;
  position: relative;
}

.time-gutter {
  width: 70px;
  flex-shrink: 0;
  border-right: 1px solid #f0f0f0;
}

.time-slot {
  position: relative;
  border-bottom: 1px dashed #f0f0f0;
  box-sizing: border-box;
}

.time-label {
  position: absolute;
  top: -8px;
  left: 12px;
  font-size: 12px;
  color: #999;
  background: #fff;
  padding: 0 4px;
}

.days-container {
  flex: 1;
  position: relative;
  display: flex;
  min-width: 700px;
}

.hour-line {
  position: absolute;
  left: 0;
  right: 0;
  border-top: 1px dashed #f0f0f0;
  pointer-events: none;
}

.day-column {
  flex: 1;
  position: relative;
  border-right: 1px solid #f5f5f5;
  height: calc((20 - 8 + 1) * 60px);
}

.event-block {
  position: absolute;
  left: 4px;
  right: 4px;
  border-radius: 6px;
  padding: 6px 8px;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.event-block:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
}

.event-block.color-red { background: #f56c6c; }
.event-block.color-blue { background: #409eff; }
.event-block.color-green { background: #52c41a; }
.event-block.color-orange { background: #faad14; }
.event-block.color-purple { background: #9254de; }

.event-time {
  font-size: 10px;
  opacity: 0.9;
  margin-bottom: 2px;
}

.event-title {
  font-size: 12px;
  font-weight: 500;
  line-height: 1.3;
}

:deep(.schedule-event-tooltip) {
  max-width: 300px;
  border: 1px solid #dce5f1 !important;
  border-radius: 10px !important;
  box-shadow: 0 8px 24px rgba(31, 48, 74, 0.16) !important;
}

.event-tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #65748a;
  font-size: 12px;
  line-height: 1.45;
}

.event-tooltip-content strong {
  color: #263449;
  font-size: 13px;
  overflow-wrap: anywhere;
}

.now-line {
  position: absolute;
  left: 0;
  right: 0;
  border-top: 2px solid #f56c6c;
  z-index: 3;
  pointer-events: none;
}

.now-line::before {
  content: '';
  position: absolute;
  left: 0;
  top: -5px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
}

.now-label {
  position: absolute;
  left: 4px;
  top: -18px;
  background: #f56c6c;
  color: #fff;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
}
</style>
