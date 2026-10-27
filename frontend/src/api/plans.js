import request from './request'

// ═══════ 月计划 ═══════
export function getMonthPlans() {
    return request.get('/month-plans')
}

export function createMonthPlan(data) {
    return request.post('/month-plans', data)
}

export function updateMonthPlan(id, data) {
    return request.put(`/month-plans/${id}`, data)
}

export function deleteMonthPlan(id) {
    return request.delete(`/month-plans/${id}`)
}

// ═══════ 周计划 ═══════
export function getWeekPlans() {
    return request.get('/week-plans')
}

export function createWeekPlan(data) {
    return request.post('/week-plans', data)
}

export function updateWeekPlan(id, data) {
    return request.put(`/week-plans/${id}`, data)
}

export function deleteWeekPlan(id) {
    return request.delete(`/week-plans/${id}`)
}

// ═══════ 日程 ═══════
export function getSchedules() {
    return request.get('/schedules')
}

export function createSchedule(data) {
    return request.post('/schedules', data)
}

export function updateSchedule(id, data) {
    return request.put(`/schedules/${id}`, data)
}

export function deleteSchedule(id) {
    return request.delete(`/schedules/${id}`)
}

// ═══════ 日报 ═══════
export function getReports(params) {
    return request.get('/reports', { params })
}

export function getReport(id) {
    return request.get(`/reports/${id}`)
}

export function createReport(data) {
    return request.post('/reports', data)
}

export function updateReport(id, data) {
    return request.put(`/reports/${id}`, data)
}

export function deleteReport(id) {
    return request.delete(`/reports/${id}`)
}

// 导入单文件
export function importReport(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/reports/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
}

// 导出（返回 Blob）
export async function exportReports(params) {
    // 手动构建参数，过滤掉 undefined 和空字符串
    const cleanParams = new URLSearchParams()
    if (params.name) cleanParams.append('name', params.name)
    if (params.date) cleanParams.append('date', params.date)
    if (params.date_start) cleanParams.append('date_start', params.date_start)
    if (params.date_end) cleanParams.append('date_end', params.date_end)

    const queryString = cleanParams.toString()
    const url = queryString ? `/api/reports/export?${queryString}` : '/api/reports/export'

    const response = await fetch(url)
    if (!response.ok) throw new Error('导出失败')
    return await response.blob()
}
