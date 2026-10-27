import { createRouter, createWebHistory } from 'vue-router'
import CalendarView from '../views/CalendarView.vue'
import ScheduleView from '../views/ScheduleView.vue'
import ReportView from '../views/ReportView.vue'
import ProgressView from '../views/ProgressView.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', redirect: '/calendar' },
        { path: '/calendar', name: 'calendar', component: CalendarView },
        { path: '/schedule', name: 'schedule', component: ScheduleView },
        { path: '/report', name: 'report', component: ReportView },
        { path: '/progress', name: 'progress', component: ProgressView },
    ]
})

export default router