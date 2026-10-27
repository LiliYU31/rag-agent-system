import request from './request'

// 获取今日完成
export function getTodayDone() {
    return request.get('/todo/done/today')
}

// 获取明日待办
export function getTomorrowTodo() {
    return request.get('/todo/todo/tomorrow')
}

// 添加完成
export function addDone(task) {
    return request.post('/todo/done', { task })
}

// 添加待办
export function addTodo(task) {
    return request.post('/todo/todo', { task })
}